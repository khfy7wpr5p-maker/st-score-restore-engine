"""Evidence-bound teacher review transaction."""
from __future__ import annotations

import json
from typing import Any, Iterable, Mapping

from .job_api_types import API_SCHEMA_VERSION, API_VERSION, JobApiError
from .job_service_support import _artifact_id, _canonical_json_bytes, _iso


class ReviewEvidenceReviewMixin:
    def review_job(
        self,
        job_id: str,
        decisions: Iterable[Mapping[str, Any]],
        *,
        reviewer_id: str,
        notes: str = "",
    ) -> dict[str, Any]:
        reviewer = reviewer_id.strip()
        if not reviewer:
            raise JobApiError("invalid_reviewer", "A reviewer identifier is required.")
        raw_decisions = list(decisions)
        if not raw_decisions:
            raise JobApiError("missing_review_decisions", "At least one page decision is required.")
        if any(not isinstance(item, Mapping) for item in raw_decisions):
            raise JobApiError("invalid_review_decision", "Every review decision must be an object.")
        supplied = [dict(item) for item in raw_decisions]
        try:
            page_numbers = [int(item.get("pageNumber", 0)) for item in supplied]
        except (TypeError, ValueError) as error:
            raise JobApiError("invalid_page_number", "Review pageNumber values must be integers.") from error
        if len(page_numbers) != len(set(page_numbers)):
            raise JobApiError("duplicate_page_decision", "Each page may be decided once per request.")

        reprocess_pages: list[int] = []
        with self.store.lock:
            job = self._job(job_id)
            if job["state"] != "AWAITING_REVIEW":
                raise JobApiError(
                    "job_not_awaiting_review",
                    "Page decisions are accepted only while the job awaits review.",
                    http_status=409,
                    details={"state": job["state"]},
                )
            normalized_records = []
            for item in supplied:
                page_number = int(item.get("pageNumber", 0))
                page = self._page(job, page_number)
                action = str(item.get("action", "")).lower()
                if action not in {"approve", "reject", "reprocess"}:
                    raise JobApiError(
                        "invalid_review_action",
                        "Review action must be approve, reject, or reprocess.",
                        details={"pageNumber": page_number},
                    )
                current_bundle_id = page.get("currentEvidenceBundleArtifactId")
                supplied_bundle_id = item.get("evidenceBundleArtifactId")
                if supplied_bundle_id is None:
                    supplied_bundle_id = current_bundle_id
                if not current_bundle_id:
                    raise JobApiError(
                        "review_evidence_not_ready",
                        "The page review evidence bundle is not ready.",
                        http_status=409,
                        details={"pageNumber": page_number},
                    )
                if supplied_bundle_id != current_bundle_id:
                    raise JobApiError(
                        "stale_review_evidence",
                        "The supplied review evidence bundle is not current.",
                        http_status=409,
                        details={
                            "pageNumber": page_number,
                            "currentEvidenceBundleArtifactId": current_bundle_id,
                        },
                    )
                bundle = json.loads(
                    self._artifact_bytes(self._artifact(job_id, current_bundle_id)).decode("utf-8")
                )
                self._validate_current_bundle(page, current_bundle_id, bundle)

                candidate_id = item.get("candidateArtifactId")
                if action == "approve":
                    if candidate_id != page["currentCandidateArtifactId"]:
                        raise JobApiError(
                            "candidate_not_current",
                            "The selected candidate is not the current page candidate.",
                            http_status=409,
                            details={"pageNumber": page_number},
                        )
                    report = self._safety_report(job, page)
                    if report["verdict"] == "reject":
                        raise JobApiError(
                            "rejected_candidate_cannot_be_approved",
                            "A safety-rejected candidate cannot be teacher-approved.",
                            http_status=409,
                            details={"pageNumber": page_number},
                        )
                    selected = candidate_id
                elif action == "reject":
                    selected = page["sourceArtifactId"]
                    candidate_id = page["currentCandidateArtifactId"]
                else:
                    selected = None
                    candidate_id = page["currentCandidateArtifactId"]
                    reprocess_pages.append(page_number)

                record = {
                    "action": action,
                    "candidateArtifactId": candidate_id,
                    "selectedArtifactId": selected,
                    "evidenceBundleArtifactId": current_bundle_id,
                    "reviewerId": reviewer,
                    "notes": str(item.get("notes", notes)),
                    "reviewedAt": _iso(self._now()),
                    "attemptId": page["currentAttemptId"],
                    "trainingLabelCreated": False,
                    "trainingUseConsent": None,
                }
                page["reviewDecision"] = record
                page["selectedArtifactId"] = selected
                normalized_records.append({"pageNumber": page_number, **record})

            self._append_event(
                job,
                "TEACHER_REVIEW_RECORDED",
                reviewer,
                {
                    "decisions": normalized_records,
                    "trainingConsentImplied": False,
                    "reviewEvidenceBound": True,
                },
                job["currentAttemptId"],
            )

            if reprocess_pages:
                return self._create_attempt_locked(
                    job,
                    target_pages=reprocess_pages,
                    actor=reviewer,
                    restoration_config={},
                    reason="teacher_reprocess",
                )

            if all(page["reviewDecision"] is not None for page in job["pages"]):
                self._transition(job, "APPROVED", reviewer)
                self._transition(job, "EXPORTING", "exporter")
                export = {
                    "schemaVersion": API_SCHEMA_VERSION,
                    "apiVersion": API_VERSION,
                    "jobId": job["jobId"],
                    "createdAt": _iso(self._now()),
                    "pages": [
                        {
                            "pageNumber": page["pageNumber"],
                            "decision": page["reviewDecision"]["action"],
                            "selectedArtifactId": page["selectedArtifactId"],
                            "candidateArtifactId": page["currentCandidateArtifactId"],
                            "sourceArtifactId": page["sourceArtifactId"],
                            "evidenceBundleArtifactId": page["reviewDecision"]["evidenceBundleArtifactId"],
                        }
                        for page in job["pages"]
                    ],
                    "trainingConsent": self._current_training_consent(job),
                }
                export_bytes = _canonical_json_bytes(export)
                export_id = _artifact_id(export_bytes)
                self._store_artifact(
                    job,
                    artifact_id=export_id,
                    attempt_id=job["currentAttemptId"],
                    page_number=None,
                    role="approved_export_manifest",
                    name="approved-export-manifest.json",
                    media_type="application/json",
                    data=export_bytes,
                )
                job["exportArtifactId"] = export_id
                self._append_event(
                    job,
                    "EXPORT_MANIFEST_CREATED",
                    "exporter",
                    {"artifactId": export_id},
                    job["currentAttemptId"],
                )
                self._transition(job, "COMPLETED", "exporter")
            return self._snapshot(job)