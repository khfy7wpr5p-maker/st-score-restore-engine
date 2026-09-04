"""Shared contracts for the versioned job API and teacher-review workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, Mapping

API_SCHEMA_VERSION = "1.0.0"
API_VERSION = "0.5.0"

JobState = Literal[
    "UPLOADED", "ANALYZING", "READY_FOR_PROCESSING", "PROCESSING",
    "COMPARING", "VALIDATING", "AWAITING_REVIEW", "APPROVED",
    "EXPORTING", "COMPLETED", "REJECTED", "FAILED", "CANCELLED", "EXPIRED",
]
TERMINAL_STATES = {"REJECTED", "FAILED", "CANCELLED", "EXPIRED"}


class JobApiError(ValueError):
    def __init__(self, code: str, message: str, *, http_status: int = 400,
                 details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = int(http_status)
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": API_SCHEMA_VERSION,
            "apiVersion": API_VERSION,
            "status": "error",
            "error": {"code": self.code, "message": self.message, "details": self.details},
        }


@dataclass(frozen=True)
class UploadedPage:
    name: str
    content_type: str
    data: bytes


@dataclass(frozen=True)
class JobApiConfig:
    """Deployment and transport policy for the API boundary."""

    client_api_key: str
    reviewer_api_key: str
    authentication_mode: Literal["development_static", "production_external"] = "development_static"
    max_upload_bytes: int = 50_000_000
    max_pages: int = 20
    retention_seconds: int = 86_400
    allowed_content_types: tuple[str, ...] = (
        "image/png", "image/jpeg", "application/pdf",
    )
    max_request_overhead_bytes: int = 2_000_000
    max_request_target_bytes: int = 4_096
    max_query_fields: int = 32
    max_header_count: int = 64
    max_header_line_bytes: int = 8_192
    max_header_bytes: int = 32_768
    max_json_bytes: int = 1_000_000
    max_multipart_parts: int = 101
    max_multipart_header_count: int = 16
    max_multipart_header_line_bytes: int = 4_096
    max_multipart_header_bytes: int = 16_384
    max_filename_bytes: int = 255
    connection_timeout_seconds: float = 10.0
    max_concurrent_requests: int = 32

    def __post_init__(self) -> None:
        if self.authentication_mode not in {"development_static", "production_external"}:
            raise JobApiError(
                "invalid_authentication_mode",
                "authentication_mode must be development_static or production_external.",
                http_status=500,
            )
        if len(self.client_api_key) < 16 or len(self.reviewer_api_key) < 16:
            raise JobApiError("weak_api_key_configuration", "Client and reviewer API keys must contain at least 16 characters.", http_status=500)
        if self.client_api_key == self.reviewer_api_key:
            raise JobApiError("invalid_api_key_configuration", "Client and reviewer API keys must be distinct.", http_status=500)
        if not 1 <= self.max_pages <= 100:
            raise JobApiError("invalid_max_pages", "max_pages must be between 1 and 100.", http_status=500)
        if not 1 <= self.max_upload_bytes <= 500_000_000:
            raise JobApiError("invalid_max_upload_bytes", "max_upload_bytes is outside the supported range.", http_status=500)
        if not 60 <= self.retention_seconds <= 31_536_000:
            raise JobApiError("invalid_retention_seconds", "retention_seconds must be between one minute and one year.", http_status=500)
        limits = {
            "max_request_overhead_bytes": (1_024, 20_000_000),
            "max_request_target_bytes": (256, 65_536),
            "max_query_fields": (1, 256),
            "max_header_count": (8, 100),
            "max_header_line_bytes": (256, 65_536),
            "max_header_bytes": (1_024, 1_000_000),
            "max_json_bytes": (2, 20_000_000),
            "max_multipart_parts": (2, 256),
            "max_multipart_header_count": (2, 64),
            "max_multipart_header_line_bytes": (128, 16_384),
            "max_multipart_header_bytes": (512, 131_072),
            "max_filename_bytes": (32, 1_024),
            "max_concurrent_requests": (1, 256),
        }
        for name, (minimum, maximum) in limits.items():
            value = int(getattr(self, name))
            if not minimum <= value <= maximum:
                raise JobApiError("invalid_http_security_configuration", f"{name} is outside the supported range.", http_status=500, details={"field": name})
        if self.max_multipart_parts < self.max_pages + 1:
            raise JobApiError("invalid_http_security_configuration", "max_multipart_parts must allow all pages plus restorationConfig.", http_status=500)
        if self.max_header_line_bytes > self.max_header_bytes:
            raise JobApiError("invalid_http_security_configuration", "max_header_line_bytes cannot exceed max_header_bytes.", http_status=500)
        if self.max_multipart_header_line_bytes > self.max_multipart_header_bytes:
            raise JobApiError("invalid_http_security_configuration", "max_multipart_header_line_bytes cannot exceed max_multipart_header_bytes.", http_status=500)
        if not 0.1 <= float(self.connection_timeout_seconds) <= 300:
            raise JobApiError("invalid_http_security_configuration", "connection_timeout_seconds must be between 0.1 and 300.", http_status=500)

    @property
    def max_request_bytes(self) -> int:
        return self.max_upload_bytes + self.max_request_overhead_bytes


Clock = Callable[[], Any]
IdFactory = Callable[[str], str]
