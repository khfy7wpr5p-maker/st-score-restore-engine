"""Teacher review, retry, artifact, and retention workflow."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Iterable, Mapping

from .job_api_types import API_SCHEMA_VERSION, API_VERSION, JobApiError
from .job_service_support import _artifact_id, _canonical_json_bytes, _iso


class JobReviewMixin:
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
            raise JobApiError(
                "invalid_review_decision",
                "Every review decision must be an object.",
            )
        supplied = [dict(item) for item in raw_decisions]
        try:
            page_numbers = [int(item.get("pageNumber", 0)) for item in supplied]
        except (TypeError, ValueError) as error:
            raise JobApiError(
                "invalid_page_number",
                "Review pageNumber values must be integers.",
            ) from error
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

    def create_attempt(
        self,
        job_id: str,
        *,
        target_pages: Iterable[int] | None,
        actor: str,
        restoration_config: Mapping[str, Any] | None = None,
        reason: str = "manual_retry",
    ) -> dict[str, Any]:
        if restoration_config is not None and not isinstance(restoration_config, Mapping):
            raise JobApiError(
                "invalid_restoration_config",
                "restoration_config must be an object.",
            )
        if target_pages is not None and isinstance(target_pages, (str, bytes, Mapping)):
            raise JobApiError(
                "invalid_target_pages",
                "target_pages must be an array of page numbers.",
            )
        with self.store.lock:
            job = self._job(job_id)
            try:
                pages = list(target_pages or [page["pageNumber"] for page in job["pages"]])
            except TypeError as error:
                raise JobApiError(
                    "invalid_target_pages",
                    "target_pages must be an array of page numbers.",
                ) from error
            return self._create_attempt_locked(
                job,
                target_pages=pages,
                actor=actor,
                restoration_config=dict(restoration_config or {}),
                reason=reason,
            )

    def cancel_job(self, job_id: str, *, actor: str) -> dict[str, Any]:
        with self.store.lock:
            job = self._job(job_id)
            if job["state"] == "EXPIRED":
                raise JobApiError("job_expired", "The job has expired.", http_status=410)
            if job["state"] in {"APPROVED", "EXPORTING", "COMPLETED", "REJECTED", "FAILED", "CANCELLED"}:
                raise JobApiError(
                    "job_not_cancellable",
                    "The job is already terminal for the current attempt.",
                    http_status=409,
                    details={"state": job["state"]},
                )
            job["cancelRequested"] = True
            self._append_event(
                job,
                "CANCELLATION_REQUESTED",
                actor,
                {"state": job["state"]},
                job["currentAttemptId"],
            )
            if job["state"] in {"UPLOADED", "READY_FOR_PROCESSING", "AWAITING_REVIEW"}:
                self._transition(job, "CANCELLED", actor)
                self._current_attempt(job)["state"] = "CANCELLED"
                self._current_attempt(job)["completedAt"] = _iso(self._now())
            return self._snapshot(job)

    def record_training_consent(
        self,
        job_id: str,
        *,
        consent: str,
        reviewer_id: str,
        scope: str,
        terms_version: str,
        notes: str = "",
    ) -> dict[str, Any]:
        if consent not in {"granted", "denied"}:
            raise JobApiError("invalid_consent", "Consent must be granted or denied.")
        if scope not in {"source", "approved_derivatives", "source_and_approved_derivatives"}:
            raise JobApiError("invalid_consent_scope", "Unsupported training-consent scope.")
        if not reviewer_id.strip() or not terms_version.strip():
            raise JobApiError(
                "invalid_consent_record",
                "Reviewer identity and terms version are required.",
            )
        with self.store.lock:
            job = self._job(job_id)
            if job["state"] == "EXPIRED":
                raise JobApiError("job_expired", "The job has expired.", http_status=410)
            record = {
                "consent": consent,
                "scope": scope,
                "termsVersion": terms_version.strip(),
                "reviewerId": reviewer_id.strip(),
                "notes": notes,
                "recordedAt": _iso(self._now()),
            }
            job["trainingConsentRecords"].append(record)
            self._append_event(
                job,
                "TRAINING_CONSENT_RECORDED",
                reviewer_id.strip(),
                record,
                job["currentAttemptId"],
            )
            return self._snapshot(job)

    def expire_job(self, job_id: str, *, actor: str = "cleanup") -> dict[str, Any]:
        with self.store.lock:
            job = self._job(job_id)
            if job["state"] == "EXPIRED":
                return self._snapshot(job)
            deleted = []
            now = _iso(self._now())
            for artifact in self.store.artifacts.values():
                if artifact["jobId"] != job_id or artifact["data"] is None:
                    continue
                artifact["data"] = None
                artifact["deletedAt"] = now
                deleted.append(artifact["artifactId"])
            self._transition(job, "EXPIRED", actor)
            self._append_event(
                job,
                "ARTIFACT_BYTES_REMOVED",
                actor,
                {"artifactIds": sorted(deleted), "auditTombstoneRetained": True},
                job["currentAttemptId"],
            )
            return self._snapshot(job)

    def cleanup_expired(self, *, actor: str = "cleanup") -> list[str]:
        now = self._now()
        with self.store.lock:
            targets = [
                job["jobId"]
                for job in self.store.jobs.values()
                if job["state"] != "EXPIRED"
                and datetime.fromisoformat(job["expiresAt"]) <= now
            ]
        for job_id in targets:
            self.expire_job(job_id, actor=actor)
        return targets

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self.store.lock:
            return self._snapshot(self._job(job_id))

    def get_pages(self, job_id: str) -> list[dict[str, Any]]:
        with self.store.lock:
            return deepcopy(self._snapshot(self._job(job_id))["pages"])

    def get_candidates(self, job_id: str, page_number: int) -> list[dict[str, Any]]:
        with self.store.lock:
            job = self._job(job_id)
            self._page(job, page_number)
            records = []
            for artifact in self.store.artifacts.values():
                if artifact["jobId"] != job_id:
                    continue
                for reference in artifact["references"]:
                    if reference["pageNumber"] == page_number and reference["role"] == "restoration_candidate":
                        records.append(self._artifact_metadata(artifact, reference=reference))
            return sorted(records, key=lambda item: (item["createdAt"], item["artifactId"], item.get("attemptId") or ""))

    def get_safety_report(self, job_id: str, page_number: int) -> dict[str, Any]:
        with self.store.lock:
            job = self._job(job_id)
            page = self._page(job, page_number)
            return deepcopy(self._safety_report(job, page))

    def get_audit(self, job_id: str) -> dict[str, Any]:
        with self.store.lock:
            job = self._job(job_id)
            return {
                "schemaVersion": API_SCHEMA_VERSION,
                "apiVersion": API_VERSION,
                "jobId": job_id,
                "events": deepcopy(job["audit"]),
                "headEventHash": job["audit"][-1]["eventHash"] if job["audit"] else None,
            }

    def get_artifact(
        self,
        job_id: str,
        artifact_id: str,
        *,
        role: str,
        purpose: str | None,
        actor: str,
    ) -> tuple[dict[str, Any], bytes]:
        with self.store.lock:
            job = self._job(job_id)
            artifact = self._artifact(job_id, artifact_id)
            if artifact["jobId"] != job_id:
                raise JobApiError("artifact_not_found", "Artifact not found.", http_status=404)
            if artifact["data"] is None:
                raise JobApiError("artifact_expired", "Artifact bytes are unavailable.", http_status=410)

            references = list(artifact["references"])
            roles = {item["role"] for item in references}
            allowed = False
            access_kind = "metadata"
            selected_reference = references[0]
            has_source = "immutable_source" in roles
            has_candidate = "restoration_candidate" in roles
            if has_candidate:
                candidate_references = [item for item in references if item["role"] == "restoration_candidate"]
                approved = any(
                    page["reviewDecision"] is not None
                    and page["reviewDecision"]["action"] == "approve"
                    and page["selectedArtifactId"] == artifact_id
                    for page in job["pages"]
                )
                if approved and role in {"client", "reviewer"} and purpose in {None, "final"}:
                    allowed = True
                    access_kind = "approved_output"
                    selected_reference = candidate_references[0]
                elif role == "reviewer" and purpose == "review":
                    allowed = True
                    access_kind = "review_preview"
                    selected_reference = candidate_references[0]
                elif has_source and role in {"client", "reviewer"} and purpose == "original":
                    allowed = True
                    access_kind = "original_fallback"
                    selected_reference = next(item for item in references if item["role"] == "immutable_source")
            elif has_source and role in {"client", "reviewer"}:
                allowed = True
                access_kind = "original_fallback"
                selected_reference = next(item for item in references if item["role"] == "immutable_source")
            elif roles & {"safety_report", "approved_export_manifest"} and role in {"client", "reviewer"}:
                allowed = True
                access_kind = "report"
                selected_reference = next(item for item in references if item["role"] in {"safety_report", "approved_export_manifest"})
            if not allowed:
                raise JobApiError(
                    "artifact_access_forbidden",
                    "The artifact is not available under the requested access policy.",
                    http_status=403,
                )

            self._append_event(
                job,
                "ARTIFACT_ACCESSED",
                actor,
                {
                    "artifactId": artifact_id,
                    "artifactRoles": sorted(roles),
                    "accessKind": access_kind,
                },
                selected_reference["attemptId"],
            )
            return self._artifact_metadata(artifact, reference=selected_reference), bytes(artifact["data"])
