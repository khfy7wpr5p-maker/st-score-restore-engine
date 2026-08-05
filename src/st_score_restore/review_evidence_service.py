"""Composition of review-evidence processing, access, review, and safety guards."""
from __future__ import annotations

from .review_evidence_access import ReviewEvidenceAccessMixin
from .review_evidence_guard import ReviewEvidenceGuardMixin
from .review_evidence_processing import ReviewEvidenceProcessingMixin
from .review_evidence_review import ReviewEvidenceReviewMixin


class ReviewEvidenceMixin(
    ReviewEvidenceGuardMixin,
    ReviewEvidenceReviewMixin,
    ReviewEvidenceAccessMixin,
    ReviewEvidenceProcessingMixin,
):
    pass
