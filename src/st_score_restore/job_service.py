"""Auditable restoration-job orchestration and teacher-review domain service."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from typing import Any, Iterable, Mapping
from uuid import uuid4

from .job_api_types import JobApiConfig, JobApiError
from .job_store import ACTIVE_WORK_STATES, InMemoryJobStore, StaleWorkClaimError, WorkClaim
from .job_service_internal import JobInternalMixin
from .job_service_processing import JobProcessingMixin
from .job_service_review import JobReviewMixin
from .review_evidence_service import ReviewEvidenceMixin


class RestorationJobService(
    ReviewEvidenceMixin,
    JobProcessingMixin,
    JobReviewMixin,
    JobInternalMixin,
):
    """Coordinates inspection, restoration, validation, and evidence-bound review."""

    def __init__(
        self,
        store: InMemoryJobStore,
        config: JobApiConfig,
        *,
        clock=None,
        id_factory=None,
    ) -> None:
        self.store = store
        self.config = config
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or (
            lambda prefix: f"{prefix}_{uuid4().hex}"
        )

    def process_job(self, job_id: str, *, actor: str = "worker") -> dict[str, Any]:
        """Reject durable processing that bypasses the worker-claim boundary."""

        require_claim = getattr(self.store, "require_processing_claim", None)
        if callable(require_claim):
            require_claim(job_id)
        return super().process_job(job_id, actor=actor)

    def run_pending(
        self,
        *,
        actor: str = "worker",
        lease_owner: str | None = None,
    ) -> str | None:
        """Process one item with durable fencing when the store supports it."""

        processing_claim = getattr(self.store, "processing_claim", None)
        if not callable(processing_claim):
            return super().run_pending(actor=actor)
        lease_seconds = int(getattr(self.store, "worker_lease_seconds", 300))
        claim = self.store.claim_next_job(
            now=self._now(),
            lease_owner=(lease_owner or actor).strip() or "worker",
            lease_seconds=lease_seconds,
        )
        if claim is None:
            return None
        try:
            with processing_claim(claim, now_provider=self._now):
                with self.store.lock:
                    job = self._job(claim.job_id)
                    self._validate_claimed_attempt_locked(job, claim)
                    if job["state"] not in {"UPLOADED", "READY_FOR_PROCESSING"}:
                        self._recover_claimed_attempt_locked(job, claim, actor)
                self.process_job(claim.job_id, actor=actor)
            return claim.job_id
        finally:
            self.store.release_claim(claim)

    def _validate_claimed_attempt_locked(
        self,
        job: dict[str, Any],
        claim: WorkClaim,
    ) -> None:
        if (
            job.get("currentAttemptId") != claim.attempt_id
            or job.get("state") not in ACTIVE_WORK_STATES
        ):
            raise StaleWorkClaimError()

    def _recover_claimed_attempt_locked(
        self,
        job: dict[str, Any],
        claim: WorkClaim,
        actor: str,
    ) -> None:
        """Restart one expired in-flight attempt without accepting partial output."""

        source_state = str(job["state"])
        if source_state not in ACTIVE_WORK_STATES:
            raise StaleWorkClaimError()
        attempt = self._current_attempt(job)
        if attempt["attemptId"] != claim.attempt_id:
            raise StaleWorkClaimError()
        for page_number in attempt["targetPages"]:
            page = self._page(job, int(page_number))
            page["currentCandidateArtifactId"] = None
            page["currentSafetyReportArtifactId"] = None
            page["currentEvidenceBundleArtifactId"] = None
            page["reviewDecision"] = None
            page["selectedArtifactId"] = None
        attempt["state"] = "READY_FOR_PROCESSING"
        attempt["completedAt"] = None
        attempt["error"] = None
        job["state"] = "READY_FOR_PROCESSING"
        self._append_event(
            job,
            "WORK_LEASE_RECOVERED",
            actor,
            {
                "fromState": source_state,
                "leaseOwner": claim.lease_owner,
                "partialArtifactsRetainedForAudit": True,
                "partialArtifactsSelected": False,
            },
            claim.attempt_id,
        )
        self._append_event(
            job,
            "STATE_TRANSITION",
            actor,
            {"from": source_state, "to": "READY_FOR_PROCESSING", "recovery": True},
            claim.attempt_id,
        )

    def review_job(
        self,
        job_id: str,
        decisions: Iterable[Mapping[str, Any]],
        *,
        reviewer_id: str,
        notes: str = "",
    ) -> dict[str, Any]:
        """Validate the whole page-decision batch before any mutation."""

        raw = list(decisions)
        if not raw:
            return super().review_job(
                job_id, raw, reviewer_id=reviewer_id, notes=notes
            )
        if any(not isinstance(item, Mapping) for item in raw):
            return super().review_job(
                job_id, raw, reviewer_id=reviewer_id, notes=notes
            )
        supplied = [dict(item) for item in raw]
        try:
            page_numbers = [int(item.get("pageNumber", 0)) for item in supplied]
        except (TypeError, ValueError):
            return super().review_job(
                job_id, supplied, reviewer_id=reviewer_id, notes=notes
            )
        if len(page_numbers) == len(set(page_numbers)):
            with self.store.lock:
                job = self._job(job_id)
                if job["state"] == "AWAITING_REVIEW":
                    for item, page_number in zip(supplied, page_numbers):
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
                            self._artifact_bytes(
                                self._artifact(job_id, current_bundle_id)
                            ).decode("utf-8")
                        )
                        self._validate_current_bundle(page, current_bundle_id, bundle)
                        if action == "approve":
                            candidate_id = item.get("candidateArtifactId")
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
        return super().review_job(
            job_id, supplied, reviewer_id=reviewer_id, notes=notes
        )
