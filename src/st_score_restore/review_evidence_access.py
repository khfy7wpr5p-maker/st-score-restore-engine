"""Reviewer-only evidence retrieval and stale-bundle validation."""
from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Mapping

from .job_api_types import API_SCHEMA_VERSION, API_VERSION, JobApiError

_EVIDENCE_ROLES = {
    "review_evidence_bundle",
    "review_source_crop",
    "review_candidate_crop",
}


class ReviewEvidenceAccessMixin:
    def get_review_bundle(
        self,
        job_id: str,
        page_number: int,
        *,
        actor: str,
    ) -> dict[str, Any]:
        with self.store.lock:
            job = self._job(job_id)
            page = self._page(job, page_number)
            bundle_id = page.get("currentEvidenceBundleArtifactId")
            if not bundle_id:
                raise JobApiError(
                    "review_evidence_not_ready",
                    "The page review evidence bundle is not ready.",
                    http_status=409,
                    details={"pageNumber": page_number},
                )
            artifact = self._artifact(job_id, bundle_id)
            bundle = json.loads(
                self._artifact_bytes(artifact).decode("utf-8")
            )
            self._validate_current_bundle(page, bundle_id, bundle)
            self._append_event(
                job,
                "REVIEW_EVIDENCE_ACCESSED",
                actor,
                {
                    "pageNumber": page_number,
                    "evidenceBundleArtifactId": bundle_id,
                },
                page["currentAttemptId"],
            )
            return {
                "schemaVersion": API_SCHEMA_VERSION,
                "apiVersion": API_VERSION,
                "jobId": job_id,
                "pageNumber": page_number,
                "evidenceBundleArtifactId": bundle_id,
                "bundle": deepcopy(bundle),
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
            artifact = self.store.artifacts.get((job_id, artifact_id))
            if artifact is not None:
                references = list(artifact["references"])
                evidence_references = [
                    item
                    for item in references
                    if item["role"] in _EVIDENCE_ROLES
                ]
                non_evidence_references = [
                    item
                    for item in references
                    if item["role"] not in _EVIDENCE_ROLES
                ]
                if evidence_references and role == "reviewer" and purpose == "review":
                    job = self._job(job_id)
                    if artifact["data"] is None:
                        raise JobApiError(
                            "artifact_expired",
                            "Artifact bytes are unavailable.",
                            http_status=410,
                        )
                    selected = evidence_references[0]
                    self._append_event(
                        job,
                        "ARTIFACT_ACCESSED",
                        actor,
                        {
                            "artifactId": artifact_id,
                            "artifactRoles": sorted(
                                {item["role"] for item in references}
                            ),
                            "accessKind": "review_evidence",
                        },
                        selected["attemptId"],
                    )
                    return (
                        self._artifact_metadata(
                            artifact,
                            reference=selected,
                        ),
                        bytes(artifact["data"]),
                    )
                if evidence_references and not non_evidence_references:
                    raise JobApiError(
                        "artifact_access_forbidden",
                        "Review evidence artifacts require reviewer access and review purpose.",
                        http_status=403,
                    )
        return super().get_artifact(
            job_id,
            artifact_id,
            role=role,
            purpose=purpose,
            actor=actor,
        )

    def _validate_current_bundle(
        self,
        page: dict[str, Any],
        bundle_id: str,
        bundle: Mapping[str, Any],
    ) -> None:
        parents = bundle.get("parents") or {}
        if (
            bundle.get("status") != "completed"
            or bundle.get("automaticApproval") is not False
            or bundle.get("pageNumber") != page["pageNumber"]
            or bundle.get("attemptId") != page["currentAttemptId"]
            or parents.get("sourceArtifactId") != page["sourceArtifactId"]
            or parents.get("candidateArtifactId")
            != page["currentCandidateArtifactId"]
            or parents.get("safetyReportArtifactId")
            != page["currentSafetyReportArtifactId"]
            or page.get("currentEvidenceBundleArtifactId") != bundle_id
        ):
            raise JobApiError(
                "stale_review_evidence",
                "The review evidence bundle does not match the current page attempt.",
                http_status=409,
                details={"pageNumber": page["pageNumber"]},
            )
