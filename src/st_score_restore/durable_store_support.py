"""Pure helpers and stable errors for durable local job persistence."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import hmac
import json
from typing import Any

STORE_SCHEMA_VERSION = 1
QUEUED_STATES = {"UPLOADED", "READY_FOR_PROCESSING"}


class DurableStoreError(RuntimeError):
    """Fail-closed persistence error with a stable diagnostic code."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "error",
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


def validate_audit_chain(job: dict[str, Any]) -> None:
    """Verify contiguous sequence numbers and every SHA-256 audit link."""

    previous = None
    for expected_sequence, event in enumerate(job.get("audit", []), 1):
        if event.get("sequence") != expected_sequence:
            raise DurableStoreError(
                "audit_sequence_corrupt",
                "Audit event sequence is not contiguous.",
                details={"jobId": job.get("jobId")},
            )
        if event.get("previousEventHash") != previous:
            raise DurableStoreError(
                "audit_chain_corrupt",
                "Audit previous-hash link is invalid.",
                details={"jobId": job.get("jobId")},
            )
        unsigned = {key: value for key, value in event.items() if key != "eventHash"}
        expected = hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()
        actual = str(event.get("eventHash", ""))
        if not hmac.compare_digest(expected, actual):
            raise DurableStoreError(
                "audit_hash_corrupt",
                "Audit event hash is invalid.",
                details={"jobId": job.get("jobId"), "sequence": expected_sequence},
            )
        previous = actual


def load_object(raw: str, code: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise DurableStoreError(code, "Stored JSON metadata is invalid.") from error
    if not isinstance(value, dict):
        raise DurableStoreError(code, "Stored JSON metadata root must be an object.")
    return value


def dump_json(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def aware_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("now must be a datetime")
    return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)


def iso(value: datetime) -> str:
    return aware_utc(value).isoformat().replace("+00:00", "Z")


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
