"""Internal state, artifact, and audit helpers for the M4 job service."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import json
from typing import Any

from .job_api_types import API_SCHEMA_VERSION, API_VERSION, JobApiError
from .job_service_support import _ALLOWED_TRANSITIONS, _artifact_id, _canonical_json_bytes, _digest_json, _iso, _safe_name


class JobInternalMixin:
    def _create_attempt_locked(
        self,
        job: dict[str, Any],
        *,
        target_pages: list[int],
        actor: str,
        restoration_config: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        if job["state"] == "EXPIRED":
            raise JobApiError("job_expired", "The job has expired.", http_status=410)
        if job["state"] not in {
            "AWAITING_REVIEW",
            "COMPLETED",
            "REJECTED",
            "FAILED",
            "CANCELLED",
        }:
            raise JobApiError(
                "retry_not_allowed",
                "A new attempt cannot be created from the current state.",
                http_status=409,
                details={"state": job["state"]},
            )
        try:
            unique_pages = sorted(set(int(value) for value in target_pages))
        except (TypeError, ValueError) as error:
            raise JobApiError(
                "invalid_target_pages",
                "target pages must contain integers.",
            ) from error
        if not unique_pages:
            raise JobApiError("missing_target_pages", "At least one target page is required.")
        for page_number in unique_pages:
            self._page(job, page_number)
        attempt_id = self._id_factory("attempt")
        now = self._now()
        attempt = {
            "attemptId": attempt_id,
            "number": len(job["attempts"]) + 1,
            "state": "READY_FOR_PROCESSING",
            "targetPages": unique_pages,
            "restorationConfig": restoration_config,
            "createdAt": _iso(now),
            "completedAt": None,
            "error": None,
        }
        job["attempts"].append(attempt)
        job["currentAttemptId"] = attempt_id
        job["cancelRequested"] = False
        job["exportArtifactId"] = None
        for page_number in unique_pages:
            page = self._page(job, page_number)
            page["currentAttemptId"] = attempt_id
            page["currentCandidateArtifactId"] = None
            page["currentSafetyReportArtifactId"] = None
            page["reviewDecision"] = None
            page["selectedArtifactId"] = None
        self._append_event(
            job,
            "ATTEMPT_CREATED",
            actor,
            {
                "attemptNumber": attempt["number"],
                "targetPages": unique_pages,
                "reason": reason,
                "restorationConfigDigest": _digest_json(restoration_config),
            },
            attempt_id,
        )
        self._transition(job, "READY_FOR_PROCESSING", actor)
        return self._snapshot(job)

    def _fail_processing(self, job_id: str, actor: str, error: Exception) -> dict[str, Any]:
        if hasattr(error, "to_dict"):
            structured = error.to_dict()  # type: ignore[attr-defined]
        else:
            structured = {
                "status": "error",
                "error": {"code": "processing_failed", "message": str(error), "details": {}},
            }
        with self.store.lock:
            job = self._job(job_id)
            attempt = self._current_attempt(job)
            attempt["state"] = "FAILED"
            attempt["completedAt"] = _iso(self._now())
            attempt["error"] = structured
            if job["state"] != "FAILED":
                self._transition(job, "FAILED", actor)
            self._append_event(
                job,
                "PROCESSING_FAILED",
                actor,
                {
                    "errorCode": structured.get("error", {}).get("code", "processing_failed"),
                    "safeFallback": "return_original",
                },
                job["currentAttemptId"],
            )
            return self._snapshot(job)

    def _ensure_not_cancelled(self, job: dict[str, Any], actor: str) -> None:
        if job["state"] == "EXPIRED":
            raise JobApiError("job_expired", "The job has expired.", http_status=410)
        if not job.get("cancelRequested"):
            return
        if job["state"] != "CANCELLED":
            self._transition(job, "CANCELLED", actor)
        attempt = self._current_attempt(job)
        attempt["state"] = "CANCELLED"
        attempt["completedAt"] = _iso(self._now())
        raise JobApiError(
            "job_cancelled",
            "The job was cancelled.",
            http_status=409,
        )

    def _transition(self, job: dict[str, Any], target: str, actor: str) -> None:
        source = job["state"]
        if target == source:
            return
        if target not in _ALLOWED_TRANSITIONS.get(source, set()):
            raise JobApiError(
                "invalid_state_transition",
                "The requested job-state transition is not permitted.",
                http_status=409,
                details={"from": source, "to": target},
            )
        job["state"] = target
        job["updatedAt"] = _iso(self._now())
        attempt = self._current_attempt(job)
        attempt["state"] = target
        self._append_event(
            job,
            "STATE_TRANSITION",
            actor,
            {"from": source, "to": target},
            job["currentAttemptId"],
        )

    def _append_event(
        self,
        job: dict[str, Any],
        event_type: str,
        actor: str,
        details: dict[str, Any],
        attempt_id: str | None,
    ) -> None:
        self.store.append_event(
            job,
            event_type=event_type,
            occurred_at=_iso(self._now()),
            actor=actor,
            details=deepcopy(details),
            attempt_id=attempt_id,
        )
        job["updatedAt"] = job["audit"][-1]["occurredAt"]

    def _store_artifact(
        self,
        job: dict[str, Any],
        *,
        artifact_id: str,
        attempt_id: str | None,
        page_number: int | None,
        role: str,
        name: str,
        media_type: str,
        data: bytes,
    ) -> None:
        reference = {
            "attemptId": attempt_id,
            "pageNumber": page_number,
            "role": role,
            "name": _safe_name(name, "artifact"),
            "mediaType": media_type,
        }
        storage_key = (job["jobId"], artifact_id)
        existing = self.store.artifacts.get(storage_key)
        if existing is not None:
            if existing["jobId"] != job["jobId"] or existing["digest"] != artifact_id.split(":", 1)[1]:
                raise JobApiError(
                    "artifact_identity_collision",
                    "Artifact identity collision detected.",
                    http_status=500,
                )
            if existing["data"] is not None and bytes(existing["data"]) != bytes(data):
                raise JobApiError(
                    "artifact_identity_collision",
                    "Artifact digest does not match stored bytes.",
                    http_status=500,
                )
            if reference not in existing["references"]:
                existing["references"].append(reference)
            return
        self.store.artifacts[storage_key] = {
            "artifactId": artifact_id,
            "jobId": job["jobId"],
            "byteSize": len(data),
            "digest": artifact_id.split(":", 1)[1],
            "createdAt": _iso(self._now()),
            "deletedAt": None,
            "references": [reference],
            "data": bytes(data),
        }

    def _safety_report(self, job: dict[str, Any], page: dict[str, Any]) -> dict[str, Any]:
        report_id = page["currentSafetyReportArtifactId"]
        if not report_id:
            raise JobApiError(
                "safety_report_not_ready",
                "The page safety report is not ready.",
                http_status=409,
                details={"pageNumber": page["pageNumber"]},
            )
        artifact = self._artifact(job["jobId"], report_id)
        data = self._artifact_bytes(artifact)
        return json.loads(data.decode("utf-8"))

    def _snapshot(self, job: dict[str, Any]) -> dict[str, Any]:
        pages = []
        for page in job["pages"]:
            report_summary = None
            if page["currentSafetyReportArtifactId"]:
                artifact = self.store.artifacts.get((job["jobId"], page["currentSafetyReportArtifactId"]))
                if artifact and artifact["data"] is not None:
                    report = json.loads(bytes(artifact["data"]).decode("utf-8"))
                    report_summary = {
                        "artifactId": artifact["artifactId"],
                        "verdict": report["verdict"],
                        "riskScore": report["metrics"]["riskScore"],
                    }
            pages.append(
                {
                    "pageNumber": page["pageNumber"],
                    "sourceArtifactId": page["sourceArtifactId"],
                    "sourceName": page["sourceName"],
                    "contentType": page["contentType"],
                    "analysis": deepcopy(page["analysis"]),
                    "currentAttemptId": page["currentAttemptId"],
                    "currentCandidateArtifactId": page["currentCandidateArtifactId"],
                    "safetyReport": report_summary,
                    "reviewDecision": deepcopy(page["reviewDecision"]),
                    "selectedArtifactId": page["selectedArtifactId"],
                }
            )
        return {
            "schemaVersion": API_SCHEMA_VERSION,
            "apiVersion": API_VERSION,
            "jobId": job["jobId"],
            "state": job["state"],
            "createdAt": job["createdAt"],
            "updatedAt": job["updatedAt"],
            "expiresAt": job["expiresAt"],
            "currentAttemptId": job["currentAttemptId"],
            "pages": pages,
            "attempts": deepcopy(job["attempts"]),
            "trainingConsent": self._current_training_consent(job),
            "exportArtifactId": job["exportArtifactId"],
            "auditHeadHash": job["audit"][-1]["eventHash"] if job["audit"] else None,
        }

    @staticmethod
    def _artifact_metadata(
        artifact: dict[str, Any],
        *,
        reference: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata = {
            key: deepcopy(value)
            for key, value in artifact.items()
            if key != "data"
        }
        selected = reference or artifact["references"][0]
        metadata.update(deepcopy(selected))
        metadata["roles"] = sorted({item["role"] for item in artifact["references"]})
        metadata["pageNumbers"] = sorted({item["pageNumber"] for item in artifact["references"] if item["pageNumber"] is not None})
        metadata["attemptIds"] = sorted({item["attemptId"] for item in artifact["references"] if item["attemptId"] is not None})
        return metadata

    @staticmethod
    def _current_training_consent(job: dict[str, Any]) -> dict[str, Any] | None:
        records = job["trainingConsentRecords"]
        return deepcopy(records[-1]) if records else None

    def _job(self, job_id: str) -> dict[str, Any]:
        try:
            return self.store.jobs[job_id]
        except KeyError as error:
            raise JobApiError("job_not_found", "Restoration job not found.", http_status=404) from error

    def _artifact(self, job_id: str, artifact_id: str) -> dict[str, Any]:
        try:
            return self.store.artifacts[(job_id, artifact_id)]
        except KeyError as error:
            raise JobApiError("artifact_not_found", "Artifact not found.", http_status=404) from error

    @staticmethod
    def _artifact_bytes(artifact: dict[str, Any]) -> bytes:
        data = artifact["data"]
        if data is None:
            raise JobApiError("artifact_expired", "Artifact bytes are unavailable.", http_status=410)
        return bytes(data)

    @staticmethod
    def _page(job: dict[str, Any], page_number: int) -> dict[str, Any]:
        for page in job["pages"]:
            if page["pageNumber"] == page_number:
                return page
        raise JobApiError(
            "page_not_found",
            "Page not found.",
            http_status=404,
            details={"pageNumber": page_number},
        )

    @staticmethod
    def _current_attempt(job: dict[str, Any]) -> dict[str, Any]:
        for attempt in reversed(job["attempts"]):
            if attempt["attemptId"] == job["currentAttemptId"]:
                return attempt
        raise JobApiError(
            "attempt_not_found",
            "Current attempt metadata is missing.",
            http_status=500,
        )

    def _now(self) -> datetime:
        value = self._clock()
        if not isinstance(value, datetime):
            raise JobApiError(
                "invalid_clock",
                "Clock must return a datetime.",
                http_status=500,
            )
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)

    @staticmethod
    def _validate_idempotency_key(value: str) -> None:
        if not isinstance(value, str) or not 8 <= len(value) <= 128:
            raise JobApiError(
                "invalid_idempotency_key",
                "Idempotency-Key must contain 8 to 128 characters.",
            )
        if any(character.isspace() for character in value):
            raise JobApiError(
                "invalid_idempotency_key",
                "Idempotency-Key must not contain whitespace.",
            )
