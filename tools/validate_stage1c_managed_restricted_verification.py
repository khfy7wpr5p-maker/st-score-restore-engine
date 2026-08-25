"""Validate Stage 1C managed-restricted verification metadata only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "stage1c-managed-restricted-verification.schema.json"
DEFAULT_RECORD_PATH = ROOT / "examples" / "stage1c-managed-restricted-verification.zero-state.v1.json"
CONTRACT_PATH = ROOT / "docs" / "stage-1c-managed-restricted-verification-contract.md"

CONTROL_NAMES = (
    "git_exclusion",
    "object_binding_capability",
    "project_managed_access",
    "accidental_public_sharing_prevention",
    "encryption_in_transit",
    "encryption_at_rest_private_copies",
    "version_drift_protection",
    "retention_deletion_behavior",
    "opaque_repository_boundary",
    "artifact_terms_compatibility",
    "deny_by_default_membership",
    "public_links_disabled",
    "access_change_history",
    "restriction_compatible_deletion_backup",
    "storage_environment_allowlist_match",
)

CLAIM_NAMES = (
    "artifactOnboardingAuthorized",
    "artifactPermissionGranted",
    "providerApprovedByBrand",
    "artifactBytesIncluded",
    "realArtifactDigestIncluded",
    "modelTrainingAuthorized",
    "publicationAuthorized",
    "stage2Authorized",
)


class ManagedRestrictedVerificationError(ValueError):
    """Raised when Stage 1C managed-restricted evidence is invalid."""


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Validate repository-visible Stage 1C managed-restricted metadata. "
            "This tool never reads artifact bytes or external provider evidence."
        )
    )
    result.add_argument("record", nargs="?", type=Path, default=DEFAULT_RECORD_PATH)
    return result


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as error:
        raise ManagedRestrictedVerificationError(
            f"invalid JSON at line {error.lineno}, column {error.colno}"
        ) from error
    if not isinstance(data, dict):
        raise ManagedRestrictedVerificationError("JSON root must be an object")
    return data


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    schema = load_json_object(path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        raise ManagedRestrictedVerificationError(
            "managed-restricted verification schema is invalid"
        ) from error
    return schema


def validate_repository_contract() -> dict[str, Any]:
    for path in (SCHEMA_PATH, DEFAULT_RECORD_PATH, CONTRACT_PATH):
        if not path.is_file():
            raise ManagedRestrictedVerificationError(
                f"missing C9 contract file: {path.relative_to(ROOT)}"
            )

    schema = load_schema()
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ManagedRestrictedVerificationError(
            "managed-restricted schema must use JSON Schema Draft 2020-12"
        )

    properties = schema.get("properties", {})
    expected_consts = {
        "schemaVersion": "stage1c-managed-restricted-verification-v1",
        "contractRef": "adr-0016-stage-1c-risk-tiered-custody-v1",
        "profile": "managed_restricted",
        "eligibilityClass": "restricted_corpus",
    }
    for name, expected in expected_consts.items():
        if properties.get(name, {}).get("const") != expected:
            raise ManagedRestrictedVerificationError(
                f"unexpected managed-restricted schema binding for {name}"
            )

    controls_schema = properties.get("controls", {})
    if tuple(controls_schema.get("required", ())) != CONTROL_NAMES:
        raise ManagedRestrictedVerificationError(
            "managed-restricted required controls drifted"
        )
    if set(controls_schema.get("properties", {})) != set(CONTROL_NAMES):
        raise ManagedRestrictedVerificationError(
            "managed-restricted control properties drifted"
        )

    claims = properties.get("claims", {}).get("properties", {})
    for name in CLAIM_NAMES:
        if claims.get(name, {}).get("const") is not False:
            raise ManagedRestrictedVerificationError(
                f"managed-restricted authorization claim must remain false: {name}"
            )
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
    validator = Draft202012Validator(active_schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        first = errors[0]
        # Never echo rejected values: they could be a provider URL, path, account,
        # human identity, or other data forbidden from repository-visible logs.
        raise ManagedRestrictedVerificationError(
            "schema validation failed at "
            f"{_schema_error_path(first)} ({first.validator})"
        )

    controls = record["controls"]
    results = {name: controls[name]["result"] for name in CONTROL_NAMES}
    for name in CONTROL_NAMES:
        result = results[name]
        evidence_ref = controls[name]["evidenceRef"]
        if result in {"pass", "fail"} and evidence_ref is None:
            raise ManagedRestrictedVerificationError(
                f"control {name} requires opaque evidence for result {result}"
            )
        if result == "not_verified" and evidence_ref is not None:
            raise ManagedRestrictedVerificationError(
                f"control {name} must not carry evidence while not_verified"
            )

    if any(result == "fail" for result in results.values()):
        expected_state = "fail"
    elif any(result == "not_verified" for result in results.values()):
        expected_state = "incomplete"
    else:
        expected_state = "pass"

    if record["overallState"] != expected_state:
        raise ManagedRestrictedVerificationError(
            "overallState contradicts the fail-closed control aggregate"
        )


def validate_file(
    path: Path, *, schema: dict[str, Any] | None = None
) -> dict[str, Any]:
    active_schema = schema if schema is not None else load_schema()
    record = load_json_object(path)
    validate_record(record, schema=active_schema)
    return record


def main() -> None:
    args = parser().parse_args()
    try:
        schema = validate_repository_contract()
        record = validate_file(args.record, schema=schema)
    except (OSError, ManagedRestrictedVerificationError) as error:
        print(
            f"ERROR: Stage 1C managed-restricted verification failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error

    print(
        "Stage 1C managed-restricted verification metadata passed: "
        f"overallState={record['overallState']}; "
        "artifact onboarding authorization remains false."
    )


if __name__ == "__main__":
    main()
