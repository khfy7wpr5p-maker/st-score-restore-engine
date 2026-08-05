"""Fail-closed review-evidence preparation before review-ready state."""
from __future__ import annotations

import json
from typing import Any

from .job_api_types import JobApiError
from .job_service_support import _artifact_id
from .review_evidence import generate_review_evidence


class ReviewEvidenceGuardMixin:
    """Generate evidence while a job is still VALIDATING."""

    def _transition(self, job: dict[str, Any], target: str, actor: str) -> None:
        if target == "AWAITING_REVIEW":
            self._prepare_review_evidence_locked(job, actor=actor)
        super()._transition(job, target, actor)

    def _prepare_review_evidence_locked(
        self,
        job: dict[str, Any],
        *,
        actor: str,
    ) -> None:
        if job["state"] != "VALIDATING":
            raise JobApiError(
                "invalid_review_evidence_state",
                "Review evidence may be generated only during validation.",
                http_status=500,
                details={"state": job["state"]},
            )
        attempt_id = job["currentAttemptId"]
        for page_number in self._current_attempt(job)["targetPages"]:
            page = self._page(job, int(page_number))
            if page.get("currentEvidenceBundleArtifactId"):
                continue
            candidate_id = page["currentCandidateArtifactId"]
            report_id = page["currentSafetyReportArtifactId"]
            if not candidate_id or not report_id:
                raise JobApiError(
                    "review_evidence_inputs_missing",
                    "Review evidence requires current candidate and safety report artifacts.",
                    http_status=500,
                    details={"pageNumber": page["pageNumber"]},
                )
            source_id = page["sourceArtifactId"]
            source_bytes = self._artifact_bytes(
                self._artifact(job["jobId"], source_id)
            )
            candidate_bytes = self._artifact_bytes(
                self._artifact(job["jobId"], candidate_id)
            )
            safety_report = json.loads(
                self._artifact_bytes(
                    self._artifact(job["jobId"], report_id)
                ).decode("utf-8")
            )
            result = generate_review_evidence(
                source_bytes,
                candidate_bytes,
                safety_report,
                source_artifact_id=source_id,
                candidate_artifact_id=candidate_id,
                safety_report_artifact_id=report_id,
                page_number=page["pageNumber"],
                attempt_id=attempt_id,
            )
            for artifact in result.artifacts:
                self._store_artifact(
                    job,
                    artifact_id=artifact.artifact_id,
                    attempt_id=attempt_id,
                    page_number=page["pageNumber"],
                    role=artifact.role,
                    name=artifact.name,
                    media_type=artifact.media_type,
                    data=artifact.data,
                )
            bundle_id = _artifact_id(result.bundle_bytes)
            self._store_artifact(
                job,
                artifact_id=bundle_id,
                attempt_id=attempt_id,
                page_number=page["pageNumber"],
                role="review_evidence_bundle",
                name=f"page-{page['pageNumber']}.review-evidence.json",
                media_type="application/json",
                data=result.bundle_bytes,
            )
            page["currentEvidenceBundleArtifactId"] = bundle_id
            self._append_event(
                job,
                "REVIEW_EVIDENCE_CREATED",
                actor,
                {
                    "pageNumber": page["pageNumber"],
                    "evidenceBundleArtifactId": bundle_id,
                    "sourceArtifactId": source_id,
                    "candidateArtifactId": candidate_id,
                    "safetyReportArtifactId": report_id,
                    "cropArtifactIds": [
                        artifact.artifact_id for artifact in result.artifacts
                    ],
                    "regionalFindingCount": result.bundle["navigation"][
                        "regionalFindingCount"
                    ],
                    "semanticRecognitionClaimed": False,
                },
                attempt_id,
            )
