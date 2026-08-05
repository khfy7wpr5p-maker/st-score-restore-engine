"""Shared contracts for the versioned job API and teacher-review workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, Mapping

API_SCHEMA_VERSION = "1.0.0"
API_VERSION = "0.4.0"

JobState = Literal[
    "UPLOADED",
    "ANALYZING",
    "READY_FOR_PROCESSING",
    "PROCESSING",
    "COMPARING",
    "VALIDATING",
    "AWAITING_REVIEW",
    "APPROVED",
    "EXPORTING",
    "COMPLETED",
    "REJECTED",
    "FAILED",
    "CANCELLED",
    "EXPIRED",
]

TERMINAL_STATES = {"REJECTED", "FAILED", "CANCELLED", "EXPIRED"}


class JobApiError(ValueError):
    """Stable API/domain failure that can be serialized without leaking internals."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        http_status: int = 400,
        details: Mapping[str, Any] | None = None,
    ) -> None:
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
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


@dataclass(frozen=True)
class UploadedPage:
    """One immutable source page supplied to a restoration job."""

    name: str
    content_type: str
    data: bytes


@dataclass(frozen=True)
class JobApiConfig:
    """Deployment policy for the non-production in-process API baseline."""

    client_api_key: str
    reviewer_api_key: str
    max_upload_bytes: int = 50_000_000
    max_pages: int = 20
    retention_seconds: int = 86_400
    allowed_content_types: tuple[str, ...] = (
        "image/png",
        "image/jpeg",
        "application/pdf",
    )

    def __post_init__(self) -> None:
        if len(self.client_api_key) < 16 or len(self.reviewer_api_key) < 16:
            raise JobApiError(
                "weak_api_key_configuration",
                "Client and reviewer API keys must contain at least 16 characters.",
                http_status=500,
            )
        if self.client_api_key == self.reviewer_api_key:
            raise JobApiError(
                "invalid_api_key_configuration",
                "Client and reviewer API keys must be distinct.",
                http_status=500,
            )
        if not 1 <= self.max_pages <= 100:
            raise JobApiError(
                "invalid_max_pages",
                "max_pages must be between 1 and 100.",
                http_status=500,
            )
        if not 1 <= self.max_upload_bytes <= 500_000_000:
            raise JobApiError(
                "invalid_max_upload_bytes",
                "max_upload_bytes is outside the supported range.",
                http_status=500,
            )
        if not 60 <= self.retention_seconds <= 31_536_000:
            raise JobApiError(
                "invalid_retention_seconds",
                "retention_seconds must be between one minute and one year.",
                http_status=500,
            )


Clock = Callable[[], Any]
IdFactory = Callable[[str], str]
