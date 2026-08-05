"""Dependency-free `/api/v1` HTTP router for restoration jobs and teacher review."""

from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
import hmac
import json
import re
from typing import Any, Mapping
from urllib.parse import parse_qs, urlsplit

from .job_api_types import API_SCHEMA_VERSION, API_VERSION, JobApiConfig, JobApiError, UploadedPage
from .job_service import RestorationJobService


@dataclass(frozen=True)
class ApiResponse:
    status: int
    headers: dict[str, str]
    body: bytes


class ApiV1:
    """Pure request router; adapters may expose it through any HTTP server."""

    def __init__(self, service: RestorationJobService, config: JobApiConfig) -> None:
        self.service = service
        self.config = config

    def handle(self, method: str, target: str, headers: Mapping[str, str], body: bytes = b"") -> ApiResponse:
        request_id = _header(headers, "x-request-id") or "request-unassigned"
        try:
            if len(body) > self.config.max_upload_bytes + 2_000_000:
                raise JobApiError("request_body_too_large", "The HTTP request body exceeds the configured limit.", http_status=413)
            split = urlsplit(target)
            path = split.path.rstrip("/") or "/"
            query = parse_qs(split.query, keep_blank_values=True)
            normalized_method = method.upper()
            if path == "/health" and normalized_method == "GET":
                return _json_response(200, {"status": "ok", "apiVersion": API_VERSION, "storage": "in_memory_non_production"}, request_id=request_id)
            role, actor = self._authenticate(headers)
            if path == "/api/v1/restoration-jobs" and normalized_method == "POST":
                self._require_role(role, {"client", "reviewer"})
                idempotency_key = _header(headers, "idempotency-key")
                if not idempotency_key:
                    raise JobApiError("missing_idempotency_key", "Idempotency-Key is required.")
                pages, restoration_config = self._parse_upload(headers, body)
                snapshot, replay = self.service.create_job(pages, idempotency_key=idempotency_key, actor=actor, restoration_config=restoration_config)
                response = _json_response(200 if replay else 202, snapshot, request_id=request_id)
                response.headers["Idempotency-Replayed"] = "true" if replay else "false"
                response.headers["Location"] = f"/api/v1/restoration-jobs/{snapshot['jobId']}"
                return response
            job_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)", path)
            if job_match:
                job_id = job_match.group(1)
                if normalized_method == "GET":
                    self._require_role(role, {"client", "reviewer"})
                    return _json_response(200, self.service.get_job(job_id), request_id=request_id)
                if normalized_method == "DELETE":
                    self._require_role(role, {"client", "reviewer"})
                    return _json_response(202, self.service.expire_job(job_id, actor=actor), request_id=request_id)
            status_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/status", path)
            if status_match and normalized_method == "GET":
                self._require_role(role, {"client", "reviewer"})
                snapshot = self.service.get_job(status_match.group(1))
                return _json_response(200, {"schemaVersion": API_SCHEMA_VERSION, "apiVersion": API_VERSION, "jobId": snapshot["jobId"], "state": snapshot["state"], "currentAttemptId": snapshot["currentAttemptId"], "updatedAt": snapshot["updatedAt"]}, request_id=request_id)
            pages_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/pages", path)
            if pages_match and normalized_method == "GET":
                self._require_role(role, {"client", "reviewer"})
                return _json_response(200, {"jobId": pages_match.group(1), "pages": self.service.get_pages(pages_match.group(1))}, request_id=request_id)
            candidates_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/pages/(\d+)/candidates", path)
            if candidates_match and normalized_method == "GET":
                self._require_role(role, {"client", "reviewer"})
                job_id, page = candidates_match.group(1), int(candidates_match.group(2))
                return _json_response(200, {"jobId": job_id, "pageNumber": page, "candidates": self.service.get_candidates(job_id, page)}, request_id=request_id)
            safety_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/pages/(\d+)/safety-report", path)
            if safety_match and normalized_method == "GET":
                self._require_role(role, {"client", "reviewer"})
                return _json_response(200, self.service.get_safety_report(safety_match.group(1), int(safety_match.group(2))), request_id=request_id)
            review_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/review", path)
            if review_match and normalized_method == "POST":
                self._require_role(role, {"reviewer"})
                payload = _json_body(body)
                decisions = payload.get("decisions", [])
                if not isinstance(decisions, list):
                    raise JobApiError("invalid_review_decisions", "decisions must be an array.")
                supplied_reviewer = str(payload.get("reviewerId", actor))
                if supplied_reviewer != actor:
                    raise JobApiError("reviewer_identity_mismatch", "reviewerId must match the authenticated actor identity.", http_status=403)
                return _json_response(200, self.service.review_job(review_match.group(1), decisions, reviewer_id=actor, notes=str(payload.get("notes", ""))), request_id=request_id)
            attempt_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/attempts", path)
            if attempt_match and normalized_method == "POST":
                self._require_role(role, {"reviewer"})
                payload = _json_body(body)
                target_pages = payload.get("targetPages")
                restoration_config = payload.get("restorationConfig") or {}
                if target_pages is not None and not isinstance(target_pages, list):
                    raise JobApiError("invalid_target_pages", "targetPages must be an array.")
                if not isinstance(restoration_config, dict):
                    raise JobApiError("invalid_restoration_config", "restorationConfig must be an object.")
                return _json_response(202, self.service.create_attempt(attempt_match.group(1), target_pages=target_pages, actor=actor, restoration_config=restoration_config, reason=str(payload.get("reason", "manual_retry"))), request_id=request_id)
            cancel_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/cancel", path)
            if cancel_match and normalized_method == "POST":
                self._require_role(role, {"client", "reviewer"})
                return _json_response(202, self.service.cancel_job(cancel_match.group(1), actor=actor), request_id=request_id)
            consent_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/training-consent", path)
            if consent_match and normalized_method == "POST":
                self._require_role(role, {"reviewer"})
                payload = _json_body(body)
                supplied_reviewer = str(payload.get("reviewerId", actor))
                if supplied_reviewer != actor:
                    raise JobApiError("reviewer_identity_mismatch", "reviewerId must match the authenticated actor identity.", http_status=403)
                return _json_response(200, self.service.record_training_consent(consent_match.group(1), consent=str(payload.get("consent", "")), reviewer_id=actor, scope=str(payload.get("scope", "")), terms_version=str(payload.get("termsVersion", "")), notes=str(payload.get("notes", ""))), request_id=request_id)
            audit_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/audit", path)
            if audit_match and normalized_method == "GET":
                self._require_role(role, {"client", "reviewer"})
                return _json_response(200, self.service.get_audit(audit_match.group(1)), request_id=request_id)
            artifact_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/artifacts/(sha256:[0-9a-f]{64})", path)
            if artifact_match and normalized_method == "GET":
                self._require_role(role, {"client", "reviewer"})
                metadata, data = self.service.get_artifact(artifact_match.group(1), artifact_match.group(2), role=role, purpose=(query.get("purpose") or [None])[0], actor=actor)
                return ApiResponse(200, {"Content-Type": metadata["mediaType"], "Content-Length": str(len(data)), "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "X-Artifact-Id": metadata["artifactId"], "X-Request-Id": request_id}, data)
            raise JobApiError("route_not_found", "API route not found.", http_status=404)
        except JobApiError as error:
            return _json_response(error.http_status, error.to_dict(), request_id=request_id)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            wrapped = JobApiError("invalid_json", "The JSON request body is invalid.", details={"error": str(error)})
            return _json_response(wrapped.http_status, wrapped.to_dict(), request_id=request_id)
        except Exception as error:  # pragma: no cover - fail-safe transport boundary
            wrapped = JobApiError("internal_api_failure", "The request failed safely at the API boundary.", http_status=500, details={"exceptionType": type(error).__name__})
            return _json_response(wrapped.http_status, wrapped.to_dict(), request_id=request_id)

    def _authenticate(self, headers: Mapping[str, str]) -> tuple[str, str]:
        authorization = _header(headers, "authorization") or ""
        api_key = _header(headers, "x-api-key") or ""
        supplied = authorization[7:] if authorization.lower().startswith("bearer ") else api_key
        if supplied and hmac.compare_digest(supplied, self.config.reviewer_api_key):
            return "reviewer", _header(headers, "x-actor-id") or "reviewer"
        if supplied and hmac.compare_digest(supplied, self.config.client_api_key):
            return "client", _header(headers, "x-actor-id") or "client"
        raise JobApiError("authentication_required", "A valid API credential is required.", http_status=401)

    @staticmethod
    def _require_role(role: str, allowed: set[str]) -> None:
        if role not in allowed:
            raise JobApiError("insufficient_role", "The authenticated role cannot perform this action.", http_status=403)

    def _parse_upload(self, headers: Mapping[str, str], body: bytes) -> tuple[list[UploadedPage], dict[str, Any]]:
        content_type = _header(headers, "content-type") or ""
        media_type = content_type.split(";", 1)[0].strip().lower()
        if media_type == "multipart/form-data":
            return _parse_multipart(content_type, body)
        if media_type in self.config.allowed_content_types:
            filename = _header(headers, "x-filename") or "upload"
            return [UploadedPage(filename, media_type, body)], {}
        raise JobApiError("unsupported_upload_content_type", "Use multipart/form-data or an accepted document media type.", http_status=415)


def _parse_multipart(content_type: str, body: bytes) -> tuple[list[UploadedPage], dict[str, Any]]:
    envelope = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("ascii") + body
    message = BytesParser(policy=policy.default).parsebytes(envelope)
    if not message.is_multipart():
        raise JobApiError("invalid_multipart", "Multipart request could not be parsed.")
    pages: list[UploadedPage] = []
    restoration_config: dict[str, Any] = {}
    for part in message.iter_parts():
        if part.is_multipart():
            raise JobApiError("nested_multipart_forbidden", "Nested multipart bodies are not supported.")
        field = part.get_param("name", header="content-disposition")
        filename = part.get_filename()
        payload = part.get_payload(decode=True) or b""
        if field == "file":
            if not filename:
                raise JobApiError("missing_filename", "Each file field must include a filename.")
            pages.append(UploadedPage(filename, part.get_content_type().lower(), bytes(payload)))
        elif field == "restorationConfig":
            if restoration_config:
                raise JobApiError("duplicate_restoration_config", "Only one restorationConfig field is permitted.")
            parsed = json.loads(bytes(payload).decode(part.get_content_charset() or "utf-8"))
            if not isinstance(parsed, dict):
                raise JobApiError("invalid_restoration_config", "restorationConfig must be a JSON object.")
            restoration_config = parsed
        elif field not in {None, ""}:
            raise JobApiError("unexpected_multipart_field", "The multipart request contains an unsupported field.", details={"field": field})
    return pages, restoration_config


def _json_body(body: bytes) -> dict[str, Any]:
    if not body:
        return {}
    parsed = json.loads(body.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise JobApiError("invalid_json_root", "JSON request root must be an object.")
    return parsed


def _header(headers: Mapping[str, str], name: str) -> str | None:
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value.strip()
    return None


def _json_response(status: int, value: Any, *, request_id: str) -> ApiResponse:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return ApiResponse(status, {"Content-Type": "application/json; charset=utf-8", "Content-Length": str(len(body)), "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "X-Request-Id": request_id}, body)
