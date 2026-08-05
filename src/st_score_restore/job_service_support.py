"""Shared constants and pure helpers for the M4 job service."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import PurePath, PureWindowsPath
from typing import Any

_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "UPLOADED": {"ANALYZING", "CANCELLED", "EXPIRED"},
    "ANALYZING": {"READY_FOR_PROCESSING", "FAILED", "CANCELLED", "EXPIRED"},
    "READY_FOR_PROCESSING": {"ANALYZING", "PROCESSING", "CANCELLED", "FAILED", "EXPIRED"},
    "PROCESSING": {"COMPARING", "FAILED", "CANCELLED", "EXPIRED"},
    "COMPARING": {"VALIDATING", "FAILED", "CANCELLED", "EXPIRED"},
    "VALIDATING": {"AWAITING_REVIEW", "FAILED", "CANCELLED", "EXPIRED"},
    "AWAITING_REVIEW": {"READY_FOR_PROCESSING", "APPROVED", "REJECTED", "CANCELLED", "EXPIRED"},
    "APPROVED": {"EXPORTING", "READY_FOR_PROCESSING", "EXPIRED"},
    "EXPORTING": {"COMPLETED", "FAILED", "EXPIRED"},
    "COMPLETED": {"READY_FOR_PROCESSING", "EXPIRED"},
    "REJECTED": {"READY_FOR_PROCESSING", "EXPIRED"},
    "FAILED": {"READY_FOR_PROCESSING", "EXPIRED"},
    "CANCELLED": {"READY_FOR_PROCESSING", "EXPIRED"},
    "EXPIRED": set(),
}


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _artifact_id(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _digest_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _safe_name(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    normalized = value.replace("\\", "/")
    name = PureWindowsPath(normalized).name
    name = PurePath(name).name
    if name in {"", ".", ".."}:
        return fallback
    return name[:255]
