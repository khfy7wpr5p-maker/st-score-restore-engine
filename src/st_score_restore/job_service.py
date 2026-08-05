"""Auditable restoration-job orchestration and teacher-review domain service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, Mapping
from uuid import uuid4

from .job_api_types import JobApiConfig, JobApiError
from .job_store import InMemoryJobStore
from .job_service_internal import JobInternalMixin
from .job_service_processing import JobProcessingMixin
from .job_service_review import JobReviewMixin


class RestorationJobService(
    JobProcessingMixin,
    JobReviewMixin,
    JobInternalMixin,
):
    """Coordinates existing inspection, OpenCV, and music/TAB safety components."""

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
            # Delegate stable error construction to the review mixin.
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
