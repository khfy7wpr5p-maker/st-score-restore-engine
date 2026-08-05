"""Auditable restoration-job orchestration and teacher-review domain service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from .job_api_types import JobApiConfig
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
