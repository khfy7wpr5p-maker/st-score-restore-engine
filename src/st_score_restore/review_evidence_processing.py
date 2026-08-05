"""Retry and snapshot integration for immutable review evidence."""
from __future__ import annotations

import json
from typing import Any


class ReviewEvidenceProcessingMixin:
    """Keep current evidence pointers aligned with attempts and snapshots."""

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
