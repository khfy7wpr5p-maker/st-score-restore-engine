"""Processing and snapshot integration for immutable review evidence."""
from __future__ import annotations

import json
from typing import Any

from .job_api_types import JobApiError
from .job_service_support import _artifact_id
from .review_evidence import ReviewEvidenceError, generate_review_evidence


class ReviewEvidenceProcessingMixin:
    """Generate evidence after validation while the worker claim is still active."""

    def process_job(self, job_id: str, *, actor: str = "worker") -> dict[str, Any]:
        snapshot = super().process_job(job_id, actor=actor)
        if snapshot.get("state") == "AWAITING_REVIEW":
            self._generate_current_review_evidence(job_id, actor=actor)
            with self.store.lock:
                return self._snapshot(self._job(job_id))
        return snapshot

    def _generate_current_review_evidence(self, job_id: str, *, actor: str) -> None:
        with self.store.lock:
            job = self._job(job_id)
            if job["state"] != "AWAITING_REVIEW":
                return
            attempt_id = job["currentAttemptId"]
            work: list[dict[str, Any]] = []
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
                work.append(
                    {
                        "pageNumber": page["pageNumber"],
                        "attemptId": attempt_id,
                        "sourceArtifactId": source_id,
                        "candidateArtifactId": candidate_id,
                        "safetyReportArtifactId": report_id,
                        "sourceBytes": self._artifact_bytes(self._artifact(job_id, source_id)),
                        "candidateBytes": self._artifact_bytes(self._artifact(job_id, candidate_id)),
                        "safetyReport": json.loads(
                            self._artifact_bytes(self._artifact(job_id, report_id)).decode("utf-8")
                        ),
                    }
                )

        generated = []
        try:
            for item in work:
                generated.append(
                    (
                        item,
                        generate_review_evidence(
                            item["sourceBytes"],
                            item["candidateBytes"],
                            item["safetyReport"],
                            source_artifact_id=item["sourceArtifactId"],
                            candidate_artifact_id=item["candidateArtifactId"],
                            safety_report_artifact_id=item["safetyReportArtifactId"],
                            page_number=item["pageNumber"],
                            attempt_id=item["attemptId"],
                        ),
                    )
                )
        except ReviewEvidenceError as error:
            raise JobApiError(error.code, error.message, http_status=500, details=error.details) from error

        with self.store.lock:
            job = self._job(job_id)
            if job["state"] != "AWAITING_REVIEW" or job["currentAttemptId"] != attempt_id:
                raise JobApiError(
                    "stale_review_evidence_generation",
                    "The current attempt changed while review evidence was being generated.",
                    http_status=409,
                )
            for item, result in generated:
                page = self._page(job, item["pageNumber"])
                if (
                    page["currentAttemptId"] != item["attemptId"]
                    or page["currentCandidateArtifactId"] != item["candidateArtifactId"]
                    or page["currentSafetyReportArtifactId"] != item["safetyReportArtifactId"]
                ):
                    raise JobApiError(
                        "stale_review_evidence_generation",
                        "Page inputs changed while review evidence was being generated.",
                        http_status=409,
                        details={"pageNumber": item["pageNumber"]},
                    )
                for artifact in result.artifacts:
                    self._store_artifact(
                        job,
                        artifact_id=artifact.artifact_id,
                        attempt_id=item["attemptId"],
                        page_number=item["pageNumber"],
                        role=artifact.role,
                        name=artifact.name,
                        media_type=artifact.media_type,
                        data=artifact.data,
                    )
                bundle_id = _artifact_id(result.bundle_bytes)
                self._store_artifact(
                    job,
                    artifact_id=bundle_id,
                    attempt_id=item["attemptId"],
                    page_number=item["pageNumber"],
                    role="review_evidence_bundle",
                    name=f"page-{item['pageNumber']}.review-evidence.json",
                    media_type="application/json",
                    data=result.bundle_bytes,
                )
                page["currentEvidenceBundleArtifactId"] = bundle_id
                self._append_event(
                    job,
                    "REVIEW_EVIDENCE_CREATED",
                    actor,
                    {
                        "pageNumber": item["pageNumber"],
                        "evidenceBundleArtifactId": bundle_id,
                        "sourceArtifactId": item["sourceArtifactId"],
                        "candidateArtifactId": item["candidateArtifactId"],
                        "safetyReportArtifactId": item["safetyReportArtifactId"],
                        "cropArtifactIds": [artifact.artifact_id for artifact in result.artifacts],
                        "regionalFindingCount": result.bundle["navigation"]["regionalFindingCount"],
                        "semanticRecognitionClaimed": False,
                    },
                    item["attemptId"],
                )

    def _create_attempt_locked(
        self,
        job: dict[str, Any],
        *,
        target_pages: list[int],
        actor: str,
        restoration_config: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        super()._create_attempt_locked(
            job,
            target_pages=target_pages,
            actor=actor,
            restoration_config=restoration_config,
            reason=reason,
        )
        for page_number in target_pages:
            self._page(job, int(page_number))["currentEvidenceBundleArtifactId"] = None
        return self._snapshot(job)

    def _snapshot(self, job: dict[str, Any]) -> dict[str, Any]:
        snapshot = super()._snapshot(job)
        source_pages = {page["pageNumber"]: page for page in job["pages"]}
        for page in snapshot["pages"]:
            current = source_pages[page["pageNumber"]]
            bundle_id = current.get("currentEvidenceBundleArtifactId")
            page["currentEvidenceBundleArtifactId"] = bundle_id
            page["reviewEvidence"] = self._review_evidence_summary(job, bundle_id)
        return snapshot

    def _review_evidence_summary(
        self,
        job: dict[str, Any],
        bundle_id: str | None,
    ) -> dict[str, Any] | None:
        if not bundle_id:
            return None
        artifact = self.store.artifacts.get((job["jobId"], bundle_id))
        if not artifact or artifact.get("data") is None:
            return {"artifactId": bundle_id, "available": False}
        bundle = json.loads(bytes(artifact["data"]).decode("utf-8"))
        return {
            "artifactId": bundle_id,
            "available": True,
            "attemptId": bundle["attemptId"],
            "findingCount": bundle["navigation"]["findingCount"],
            "regionalFindingCount": bundle["navigation"]["regionalFindingCount"],
        }