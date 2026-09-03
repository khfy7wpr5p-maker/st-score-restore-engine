"""Dependency-free `/api/v1` HTTP router for restoration jobs and teacher review."""

from __future__ import annotations

from dataclasses import dataclass
import hmac
import json
import re
from typing import Any, Mapping
from urllib.parse import parse_qs, urlsplit

from .http_security import (
    parse_json_object,
    parse_multipart_form_data,
    parse_parameterized_header,
    safe_upload_name,
    validate_router_request,
)
from .job_api_types import API_SCHEMA_VERSION, API_VERSION, JobApiConfig, JobApiError, UploadedPage
from .job_service import RestorationJobService
from .review_ui import review_ui_asset


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
        request_id = "request-unassigned"
        try:
            validate_router_request(method, target, headers, body, self.config)
            request_id = _header(headers, "x-request-id") or request_id
            split = urlsplit(target)
            path = split.path.rstrip("/") or "/"
            try:
                query = parse_qs(
                    split.query,
                    keep_blank_values=True,
                    max_num_fields=self.config.max_query_fields,
                )
            except ValueError as error:
                raise JobApiError(
                    "invalid_query_string",
                    "The request query exceeds the configured field limit.",
                ) from error
            normalized_method = method.upper()
            if normalized_method not in {"GET", "POST", "DELETE"}:
                raise JobApiError(
                    "method_not_allowed",
                    "The API accepts only GET, POST, and DELETE.",
                    http_status=405,
                )
            if path == "/health" and normalized_method == "GET":
                return _json_response(
                    200,
                    {
                        "status": "ok",
                        "apiVersion": API_VERSION,
                        "storage": "non_production",
                    },
                    request_id=request_id,
                )
            if normalized_method == "GET":
                asset = review_ui_asset(path)
                if asset is not None:
                    media_type, data = asset
                    return _static_response(media_type, data, request_id=request_id)
            role, actor = self._authenticate(headers)
            if path == "/api/v1/restoration-jobs" and normalized_method == "POST":
                self._require_role(role, {"client", "reviewer"})
                idempotency_key = _header(headers, "idempotency-key")
                if not idempotency_key:
                    raise JobApiError("missing_idempotency_key", "Idempotency-Key is required.")
                pages, restoration_config = self._parse_upload(headers, body)
                snapshot, replay = self.service.create_job(
                    pages,
                    idempotency_key=idempotency_key,
                    actor=actor,
                    restoration_config=restoration_config,
                )
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
                return _json_response(
                    200,
                    {
                        "schemaVersion": API_SCHEMA_VERSION,
                        "apiVersion": API_VERSION,
                        "jobId": snapshot["jobId"],
                        "state": snapshot["state"],
                        "currentAttemptId": snapshot["currentAttemptId"],
                        "updatedAt": snapshot["updatedAt"],
                    },
                    request_id=request_id,
                )
            pages_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/pages", path)
            if pages_match and normalized_method == "GET":
                self._require_role(role, {"client", "reviewer"})
                return _json_response(
                    200,
                    {"jobId": pages_match.group(1), "pages": self.service.get_pages(pages_match.group(1))},
                    request_id=request_id,
                )
            candidates_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/pages/(\d+)/candidates", path)
            if candidates_match and normalized_method == "GET":
                self._require_role(role, {"client", "reviewer"})
                job_id, page = candidates_match.group(1), int(candidates_match.group(2))
                return _json_response(
                    200,
                    {"jobId": job_id, "pageNumber": page, "candidates": self.service.get_candidates(job_id, page)},
                    request_id=request_id,
                )
            safety_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/pages/(\d+)/safety-report", path)
            if safety_match and normalized_method == "GET":
                self._require_role(role, {"client", "reviewer"})
                return _json_response(
                    200,
                    self.service.get_safety_report(safety_match.group(1), int(safety_match.group(2))),
                    request_id=request_id,
                )
            evidence_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/pages/(\d+)/review-bundle", path)
            if evidence_match and normalized_method == "GET":
                self._require_role(role, {"reviewer"})
                return _json_response(
                    200,
                    self.service.get_review_bundle(
                        evidence_match.group(1),
                        int(evidence_match.group(2)),
                        actor=actor,
                    ),
                    request_id=request_id,
                )
            review_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/review", path)
            if review_match and normalized_method == "POST":
                self._require_role(role, {"reviewer"})
                payload = self._json_request(headers, body)
                decisions = payload.get("decisions", [])
                if not isinstance(decisions, list):
                    raise JobApiError("invalid_review_decisions", "decisions must be an array.")
                for index, decision in enumerate(decisions):
                    if not isinstance(decision, Mapping):
                        raise JobApiError(
                            "invalid_review_decision",
                            "Every review decision must be an object.",
                            details={"decisionIndex": index},
                        )
                    evidence_id = decision.get("evidenceBundleArtifactId")
                    if not isinstance(evidence_id, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", evidence_id):
                        raise JobApiError(
                            "missing_review_evidence",
                            "Every API review decision must include the current evidenceBundleArtifactId.",
                            http_status=409,
                            details={"decisionIndex": index},
                        )
                supplied_reviewer = str(payload.get("reviewerId", actor))
                if supplied_reviewer != actor:
                    raise JobApiError(
                        "reviewer_identity_mismatch",
                        "reviewerId must match the authenticated actor identity.",
                        http_status=403,
                    )
                return _json_response(
                    200,
                    self.service.review_job(
                        review_match.group(1),
                        decisions,
                        reviewer_id=actor,
                        notes=str(payload.get("notes", "")),
                    ),
                    request_id=request_id,
                )
            attempt_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/attempts", path)
            if attempt_match and normalized_method == "POST":
                self._require_role(role, {"reviewer"})
                payload = self._json_request(headers, body)
                target_pages = payload.get("targetPages")
                restoration_config = payload.get("restorationConfig") or {}
                if target_pages is not None and not isinstance(target_pages, list):
                    raise JobApiError("invalid_target_pages", "targetPages must be an array.")
                if not isinstance(restoration_config, dict):
                    raise JobApiError("invalid_restoration_config", "restorationConfig must be an object.")
                return _json_response(
                    202,
                    self.service.create_attempt(
                        attempt_match.group(1),
                        target_pages=target_pages,
                        actor=actor,
                        restoration_config=restoration_config,
                        reason=str(payload.get("reason", "manual_retry")),
                    ),
                    request_id=request_id,
                )
            cancel_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/cancel", path)
            if cancel_match and normalized_method == "POST":
                self._require_role(role, {"client", "reviewer"})
                return _json_response(
                    202,
                    self.service.cancel_job(cancel_match.group(1), actor=actor),
                    request_id=request_id,
                )
            consent_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/training-consent", path)
            if consent_match and normalized_method == "POST":
                self._require_role(role, {"reviewer"})
                payload = self._json_request(headers, body)
                supplied_reviewer = str(payload.get("reviewerId", actor))
                if supplied_reviewer != actor:
                    raise JobApiError(
                        "reviewer_identity_mismatch",
                        "reviewerId must match the authenticated actor identity.",
                        http_status=403,
                    )
                return _json_response(
                    200,
                    self.service.record_training_consent(
                        consent_match.group(1),
                        consent=str(payload.get("consent", "")),
                        reviewer_id=actor,
                        scope=str(payload.get("scope", "")),
                        terms_version=str(payload.get("termsVersion", "")),
                        notes=str(payload.get("notes", "")),
                    ),
                    request_id=request_id,
                )
            audit_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/audit", path)
            if audit_match and normalized_method == "GET":
                self._require_role(role, {"client", "reviewer"})
                return _json_response(200, self.service.get_audit(audit_match.group(1)), request_id=request_id)
            artifact_match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)/artifacts/(sha256:[0-9a-f]{64})", path)
            if artifact_match and normalized_method == "GET":
                self._require_role(role, {"client", "reviewer"})
                purpose_values = query.get("purpose") or []
                if len(purpose_values) > 1:
                    raise JobApiError(
                        "ambiguous_query_parameter",
                        "purpose may be supplied at most once.",
                    )
                metadata, data = self.service.get_artifact(
                    artifact_match.group(1),
                    artifact_match.group(2),
                    role=role,
                    purpose=purpose_values[0] if purpose_values else None,
                    actor=actor,
                )
                return ApiResponse(
                    200,
                    {
                        "Content-Type": metadata["mediaType"],
                        "Content-Length": str(len(data)),
                        "Cache-Control": "no-store",
                        "X-Content-Type-Options": "nosniff",
                        "X-Artifact-Id": metadata["artifactId"],
                        "X-Request-Id": request_id,
                    },
                    data,
                )
            raise JobApiError("route_not_found", "API route not found.", http_status=404)
        except JobApiError as error:
            return _json_response(error.http_status, error.to_dict(), request_id=request_id)
        except (json.JSONDecodeError, UnicodeDecodeError):
            wrapped = JobApiError(
                "invalid_json",
                "The JSON request body is invalid.",
            )
            return _json_response(wrapped.http_status, wrapped.to_dict(), request_id=request_id)
        except Exception:  # pragma: no cover - fail-safe transport boundary
            wrapped = JobApiError(
                "internal_api_failure",
                "The request failed safely at the API boundary.",
                http_status=500,
            )
            return _json_response(wrapped.http_status, wrapped.to_dict(), request_id=request_id)

    def _authenticate(self, headers: Mapping[str, str]) -> tuple[str, str]:
        authorization = _header(headers, "authorization") or ""
        api_key = _header(headers, "x-api-key") or ""
        if authorization and api_key:
            raise JobApiError(
                "ambiguous_authentication",
                "Use exactly one authentication credential header.",
                http_status=400,
            )
        supplied = authorization[7:] if authorization.lower().startswith("bearer ") else api_key
        if supplied and hmac.compare_digest(supplied, self.config.reviewer_api_key):
            return "reviewer", _header(headers, "x-actor-id") or "reviewer"
        if supplied and hmac.compare_digest(supplied, self.config.client_api_key):
            return "client", _header(headers, "x-actor-id") or "client"
        raise JobApiError("authentication_required", "A valid API credential is required.", http_status=401)

    @staticmethod
    def _require_role(role: str, allowed: set[str]) -> None:
        if role not in allowed:
            raise JobApiError(
                "insufficient_role",
                "The authenticated role cannot perform this action.",
                http_status=403,
            )

    def _parse_upload(self, headers: Mapping[str, str], body: bytes) -> tuple[list[UploadedPage], dict[str, Any]]:
        content_type = _header(headers, "content-type") or ""
        media_type, parameters = parse_parameterized_header(content_type, "Content-Type")
        if media_type == "multipart/form-data":
            result = parse_multipart_form_data(content_type, body, self.config)
            return result.pages, result.restoration_config
        if parameters:
            raise JobApiError(
                "ambiguous_upload_content_type",
                "Raw document uploads do not accept Content-Type parameters.",
                http_status=415,
            )
        if media_type in self.config.allowed_content_types:
            filename = safe_upload_name(
                _header(headers, "x-filename") or "upload",
                self.config.max_filename_bytes,
            )
            return [UploadedPage(filename, media_type, body)], {}
        raise JobApiError(
            "unsupported_upload_content_type",
            "Use multipart/form-data or an accepted document media type.",
            http_status=415,
        )

    def _json_request(self, headers: Mapping[str, str], body: bytes) -> dict[str, Any]:
        content_type = _header(headers, "content-type")
        if content_type:
            media_type, parameters = parse_parameterized_header(content_type, "Content-Type")
            if media_type != "application/json":
                raise JobApiError(
                    "unsupported_json_content_type",
                    "JSON endpoints require application/json when Content-Type is supplied.",
                    http_status=415,
                )
            charset = parameters.get("charset", "utf-8").lower()
            if charset not in {"utf-8", "utf8"} or set(parameters) - {"charset"}:
                raise JobApiError(
                    "ambiguous_json_content_type",
                    "JSON Content-Type may specify only UTF-8 charset.",
                    http_status=415,
                )
        return parse_json_object(body, self.config)


def _header(headers: Mapping[str, str], name: str) -> str | None:
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value.strip()
    return None


def _static_response(media_type: str, body: bytes, *, request_id: str) -> ApiResponse:
    return ApiResponse(
        200,
        {
            "Content-Type": media_type,
            "Content-Length": str(len(body)),
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
            "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' blob:; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
            "X-Request-Id": request_id,
        },
        body,
    )


def _json_response(status: int, value: Any, *, request_id: str) -> ApiResponse:
    body = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return ApiResponse(
        status,
        {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(body)),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Request-Id": request_id,
        },
        body,
    )
