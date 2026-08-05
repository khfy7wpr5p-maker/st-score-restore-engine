"""Job creation and processing workflow for the M4 API baseline."""

from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
import hashlib
import hmac
import json
from typing import Any, Iterable, Mapping

from .input_inspection import InputInspectionError, inspect_bytes
from .job_api_types import API_SCHEMA_VERSION, API_VERSION, JobApiError, UploadedPage
from .music_safety_validator import MusicSafetyValidationError, validate_candidate
from .restoration_types import RestorationError
from .safe_restoration import restore_bytes
from .job_service_support import _artifact_id, _canonical_json_bytes, _digest_json, _iso, _safe_name


class JobProcessingMixin:
    def create_job(
        self,
        pages: Iterable[UploadedPage],
        *,
        idempotency_key: str,
        actor: str,
        restoration_config: Mapping[str, Any] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        supplied = list(pages)
        self._validate_idempotency_key(idempotency_key)
        if restoration_config is not None and not isinstance(restoration_config, Mapping):
            raise JobApiError(
                "invalid_restoration_config",
                "restoration_config must be an object.",
            )
        if not supplied:
            raise JobApiError("missing_file", "At least one source page is required.")
        if len(supplied) > self.config.max_pages:
            raise JobApiError(
                "too_many_pages",
                "The request exceeds the configured page limit.",
                http_status=413,
                details={"maxPages": self.config.max_pages},
            )

        total = 0
        normalized: list[UploadedPage] = []
        request_pages: list[dict[str, Any]] = []
        for index, page in enumerate(supplied, 1):
            if not isinstance(page, UploadedPage):
                raise JobApiError(
                    "invalid_page_record",
                    "Every page must use the UploadedPage contract.",
                    details={"pageNumber": index},
                )
            if not isinstance(page.data, bytes) or not page.data:
                raise JobApiError(
                    "invalid_page_bytes",
                    "Every uploaded page must contain immutable bytes.",
                    details={"pageNumber": index},
                )
            total += len(page.data)
            if total > self.config.max_upload_bytes:
                raise JobApiError(
                    "oversized_upload",
                    "The upload exceeds the configured byte limit.",
                    http_status=413,
                    details={"maxUploadBytes": self.config.max_upload_bytes},
                )
            content_type = page.content_type.split(";", 1)[0].strip().lower()
            if content_type not in self.config.allowed_content_types:
                raise JobApiError(
                    "unsupported_media_type",
                    "The uploaded page media type is not permitted.",
                    http_status=415,
                    details={"contentType": content_type, "pageNumber": index},
                )
            safe_name = _safe_name(page.name, f"page-{index}")
            normalized_page = UploadedPage(safe_name, content_type, page.data)
            normalized.append(normalized_page)
            request_pages.append(
                {
                    "pageNumber": index,
                    "name": safe_name,
                    "contentType": content_type,
                    "byteSize": len(page.data),
                    "digest": hashlib.sha256(page.data).hexdigest(),
                }
            )

        config_object = dict(restoration_config or {})
        request_digest = _digest_json(
            {"pages": request_pages, "restorationConfig": config_object}
        )
        idempotency_digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
        now = self._now()

        with self.store.lock:
            existing = self.store.idempotency.get(idempotency_digest)
            if existing:
                if not hmac.compare_digest(existing["requestDigest"], request_digest):
                    raise JobApiError(
                        "idempotency_conflict",
                        "The idempotency key was already used with different content.",
                        http_status=409,
                    )
                return self._snapshot(self.store.jobs[existing["jobId"]]), True

            job_id = self._id_factory("job")
            attempt_id = self._id_factory("attempt")
            expires_at = now + timedelta(seconds=self.config.retention_seconds)
            job: dict[str, Any] = {
                "schemaVersion": API_SCHEMA_VERSION,
                "apiVersion": API_VERSION,
                "jobId": job_id,
                "state": "UPLOADED",
                "createdAt": _iso(now),
                "updatedAt": _iso(now),
                "expiresAt": _iso(expires_at),
                "requestDigest": request_digest,
                "idempotencyKeyDigest": idempotency_digest,
                "currentAttemptId": attempt_id,
                "cancelRequested": False,
                "pages": [],
                "attempts": [
                    {
                        "attemptId": attempt_id,
                        "number": 1,
                        "state": "UPLOADED",
                        "targetPages": list(range(1, len(normalized) + 1)),
                        "restorationConfig": config_object,
                        "createdAt": _iso(now),
                        "completedAt": None,
                        "error": None,
                    }
                ],
                "trainingConsentRecords": [],
                "exportArtifactId": None,
                "audit": [],
            }
            for index, page in enumerate(normalized, 1):
                artifact_id = _artifact_id(page.data)
                self._store_artifact(
                    job,
                    artifact_id=artifact_id,
                    attempt_id=None,
                    page_number=index,
                    role="immutable_source",
                    name=page.name,
                    media_type=page.content_type,
                    data=page.data,
                )
                job["pages"].append(
                    {
                        "pageNumber": index,
                        "sourceArtifactId": artifact_id,
                        "sourceName": page.name,
                        "contentType": page.content_type,
                        "analysis": None,
                        "currentCandidateArtifactId": None,
                        "currentSafetyReportArtifactId": None,
                        "currentAttemptId": attempt_id,
                        "reviewDecision": None,
                        "selectedArtifactId": None,
                    }
                )

            self.store.jobs[job_id] = job
            self.store.idempotency[idempotency_digest] = {
                "jobId": job_id,
                "requestDigest": request_digest,
            }
            self._append_event(
                job,
                "JOB_CREATED",
                actor,
                {
                    "pageCount": len(normalized),
                    "requestDigest": request_digest,
                    "sourceArtifactIds": [page["sourceArtifactId"] for page in job["pages"]],
                },
                attempt_id,
            )
            self._append_event(
                job,
                "STATE_TRANSITION",
                actor,
                {"from": None, "to": "UPLOADED"},
                attempt_id,
            )
            return self._snapshot(job), False

    def run_pending(self, *, actor: str = "worker") -> str | None:
        """Process one queued job. A server worker may call this repeatedly."""

        with self.store.lock:
            queued = next(
                (
                    job["jobId"]
                    for job in self.store.jobs.values()
                    if job["state"] in {"UPLOADED", "READY_FOR_PROCESSING"}
                    and not job.get("processingClaimed", False)
                ),
                None,
            )
            if queued is None:
                return None
            self.store.jobs[queued]["processingClaimed"] = True
        try:
            self.process_job(queued, actor=actor)
        finally:
            with self.store.lock:
                if queued in self.store.jobs:
                    self.store.jobs[queued]["processingClaimed"] = False
        return queued

    def process_job(self, job_id: str, *, actor: str = "worker") -> dict[str, Any]:
        with self.store.lock:
            job = self._job(job_id)
            if job["state"] not in {"UPLOADED", "READY_FOR_PROCESSING"}:
                raise JobApiError(
                    "job_not_processable",
                    "The job is not queued for processing.",
                    http_status=409,
                    details={"state": job["state"]},
                )
            attempt = self._current_attempt(job)
            target_pages = list(attempt["targetPages"])
            self._ensure_not_cancelled(job, actor)
            self._transition(job, "ANALYZING", actor)

        try:
            source_inputs: dict[int, tuple[bytes, str]] = {}
            for page_number in target_pages:
                with self.store.lock:
                    job = self._job(job_id)
                    self._ensure_not_cancelled(job, actor)
                    page = self._page(job, page_number)
                    source_artifact = self._artifact(job_id, page["sourceArtifactId"])
                    source_bytes = self._artifact_bytes(source_artifact)
                    source_name = page["sourceName"]
                analysis_bundle = inspect_bytes(
                    source_bytes,
                    source_name=source_name,
                    max_bytes=self.config.max_upload_bytes,
                )
                with self.store.lock:
                    page = self._page(self._job(job_id), page_number)
                    page["analysis"] = analysis_bundle["analysis"]
                    self._append_event(
                        self._job(job_id),
                        "PAGE_ANALYZED",
                        actor,
                        {
                            "pageNumber": page_number,
                            "sourceArtifactId": page["sourceArtifactId"],
                            "analysisDigest": _digest_json(analysis_bundle["analysis"]),
                        },
                        self._job(job_id)["currentAttemptId"],
                    )
                source_inputs[page_number] = (source_bytes, source_name)

            with self.store.lock:
                job = self._job(job_id)
                self._ensure_not_cancelled(job, actor)
                self._transition(job, "READY_FOR_PROCESSING", actor)
                self._transition(job, "PROCESSING", actor)
                attempt_config = dict(self._current_attempt(job)["restorationConfig"])

            candidates: dict[int, tuple[bytes, dict[str, Any], str]] = {}
            for page_number in target_pages:
                source_bytes, source_name = source_inputs[page_number]
                candidate = restore_bytes(
                    source_bytes,
                    source_name=source_name,
                    config=attempt_config,
                    output_format="png",
                    candidate_name=f"page-{page_number}.candidate.png",
                )
                candidate_id = _artifact_id(candidate.output_bytes)
                with self.store.lock:
                    job = self._job(job_id)
                    self._ensure_not_cancelled(job, actor)
                    self._store_artifact(
                        job,
                        artifact_id=candidate_id,
                        attempt_id=job["currentAttemptId"],
                        page_number=page_number,
                        role="restoration_candidate",
                        name=f"page-{page_number}.candidate.png",
                        media_type="image/png",
                        data=candidate.output_bytes,
                    )
                    page = self._page(job, page_number)
                    page["currentCandidateArtifactId"] = candidate_id
                    page["currentAttemptId"] = job["currentAttemptId"]
                    page["reviewDecision"] = None
                    page["selectedArtifactId"] = None
                    self._append_event(
                        job,
                        "CANDIDATE_CREATED",
                        actor,
                        {
                            "pageNumber": page_number,
                            "candidateArtifactId": candidate_id,
                            "candidateManifestDigest": _digest_json(candidate.manifest),
                        },
                        job["currentAttemptId"],
                    )
                candidates[page_number] = (
                    candidate.output_bytes,
                    candidate.manifest,
                    candidate_id,
                )

            with self.store.lock:
                job = self._job(job_id)
                self._ensure_not_cancelled(job, actor)
                self._transition(job, "COMPARING", actor)
                self._append_event(
                    job,
                    "CANDIDATES_COMPARED",
                    actor,
                    {
                        "candidateCount": len(candidates),
                        "comparator": "single_opencv_candidate_per_page",
                    },
                    job["currentAttemptId"],
                )
                self._transition(job, "VALIDATING", actor)

            for page_number in target_pages:
                source_bytes, source_name = source_inputs[page_number]
                candidate_bytes, manifest, candidate_id = candidates[page_number]
                safety_report = validate_candidate(
                    source_bytes,
                    candidate_bytes,
                    source_name=source_name,
                    candidate_name=f"page-{page_number}.candidate.png",
                    candidate_manifest=manifest,
                )
                report_bytes = _canonical_json_bytes(safety_report)
                report_id = _artifact_id(report_bytes)
                with self.store.lock:
                    job = self._job(job_id)
                    self._ensure_not_cancelled(job, actor)
                    self._store_artifact(
                        job,
                        artifact_id=report_id,
                        attempt_id=job["currentAttemptId"],
                        page_number=page_number,
                        role="safety_report",
                        name=f"page-{page_number}.safety.json",
                        media_type="application/json",
                        data=report_bytes,
                    )
                    page = self._page(job, page_number)
                    page["currentSafetyReportArtifactId"] = report_id
                    self._append_event(
                        job,
                        "PAGE_VALIDATED",
                        actor,
                        {
                            "pageNumber": page_number,
                            "candidateArtifactId": candidate_id,
                            "safetyReportArtifactId": report_id,
                            "verdict": safety_report["verdict"],
                            "riskScore": safety_report["metrics"]["riskScore"],
                        },
                        job["currentAttemptId"],
                    )

            with self.store.lock:
                job = self._job(job_id)
                self._ensure_not_cancelled(job, actor)
                attempt = self._current_attempt(job)
                attempt["state"] = "AWAITING_REVIEW"
                attempt["completedAt"] = _iso(self._now())
                self._transition(job, "AWAITING_REVIEW", actor)
                return self._snapshot(job)

        except JobApiError as error:
            if error.code == "job_cancelled":
                with self.store.lock:
                    return self._snapshot(self._job(job_id))
            raise
        except (InputInspectionError, RestorationError, MusicSafetyValidationError) as error:
            return self._fail_processing(job_id, actor, error)
        except Exception as error:  # pragma: no cover - last-resort fail-safe
            wrapped = JobApiError(
                "unexpected_processing_failure",
                "The job failed safely during processing.",
                http_status=500,
                details={"exceptionType": type(error).__name__},
            )
            return self._fail_processing(job_id, actor, wrapped)
