"""Validate Stage 1C vault-verification metadata without reading artifact bytes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "stage1c-vault-verification.schema.json"
DEFAULT_RECORD_PATH = ROOT / "examples" / "stage1c-vault-verification.zero-state.v1.json"

CONTROL_NAMES = (
    "supported_host",
    "encryption_at_rest",
    "offline_boundary",
    "private_by_default",
    "least_privilege_access",
    "separation_of_duties",
    "quarantine_isolation",
    "audit_integrity_and_anti_rollback",
    "retention_enforcement",
    "immediate_revocation",
    "deletion_receipts",
    "backup_anti_resurrection",
    "git_and_sync_separation",
)


class VaultVerificationError(ValueError):
    """Raised when Stage 1C vault-verification metadata is invalid."""


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Validate repository-visible Stage 1C vault-verification metadata. "
            "This tool never reads document artifacts or external custody evidence."
        )
    )
    result.add_argument(
        "record",
        nargs="?",
        type=Path,
        default=DEFAULT_RECORD_PATH,
    )
    return result


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as error:
        raise VaultVerificationError(
            f"invalid JSON at line {error.lineno}, column {error.colno}"
        ) from error
    if not isinstance(data, dict):
        raise VaultVerificationError("JSON root must be an object")
    return data


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    schema = load_json_object(path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        raise VaultVerificationError("vault verification schema is invalid") from error
    return schema


def _schema_error_path(error: Any) -> str:
    parts = [str(part) for part in error.absolute_path]
    return ".".join(parts) if parts else "<root>"


def validate_record(
    record: dict[str, Any],
    *,
    schema: dict[str, Any] | None = None,
) -> None:
    active_schema = schema if schema is not None else load_schema()
    validator = Draft202012Validator(
        active_schema,
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        first = errors[0]
        # Do not echo the rejected instance value: it may be a local path, URL,
        # identity, or other locator that must not leak into CI logs.
        raise VaultVerificationError(
            "schema validation failed at "
            f"{_schema_error_path(first)} ({first.validator})"
        )

    controls = record["controls"]
    results = {name: controls[name]["result"] for name in CONTROL_NAMES}

    for name in CONTROL_NAMES:
        result = results[name]
        evidence_ref = controls[name]["evidenceRef"]
        if result in {"pass", "fail"} and evidence_ref is None:
            raise VaultVerificationError(
                f"control {name} requires opaque evidence for result {result}"
            )
        if result == "not_verified" and evidence_ref is not None:
            raise VaultVerificationError(
                f"control {name} must not carry evidence while not_verified"
            )

    if any(result == "fail" for result in results.values()):
        expected_state = "fail"
    elif any(result == "not_verified" for result in results.values()):
        expected_state = "incomplete"
    else:
        expected_state = "pass"

    if record["overallState"] != expected_state:
        raise VaultVerificationError(
            "overallState contradicts the fail-closed control aggregate"
        )


def validate_file(path: Path) -> dict[str, Any]:
    schema = load_schema()
    record = load_json_object(path)
    validate_record(record, schema=schema)
    return record


def main() -> None:
    args = parser().parse_args()
    try:
        record = validate_file(args.record)
    except (OSError, VaultVerificationError) as error:
        print(
            f"ERROR: Stage 1C vault verification metadata failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error

    print(
        "Stage 1C vault verification metadata passed: "
        f"overallState={record['overallState']}; "
        "artifact onboarding authorization remains false."
    )


if __name__ == "__main__":
    main()
