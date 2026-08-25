"""Validate C10 compatibility between risk-tiered custody and legacy C4 evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_contract_constants import (  # noqa: E402
    LEGACY_STORAGE_CLASS,
    PROFILE_BY_ELIGIBILITY,
)
from tools.validate_stage1c_vault_verification import (  # noqa: E402
    CONTROL_NAMES as C4_CONTROL_NAMES,
    DEFAULT_RECORD_PATH as C4_ZERO_STATE_PATH,
    validate_file as validate_c4_file,
    validate_repository_contract as validate_c4_repository_contract,
)

SCHEMA_PATH = ROOT / "schemas" / "stage1c-high-assurance-compatibility.schema.json"
DEFAULT_RECORD_PATH = ROOT / "examples" / "stage1c-high-assurance-compatibility.v1.json"
CONTRACT_PATH = ROOT / "docs" / "stage-1c-high-assurance-compatibility-contract.md"
DATASET_SCHEMA_PATH = ROOT / "schemas" / "dataset-catalog.schema.json"
C4_CONTRACT_PATH = ROOT / "docs" / "stage-1c-vault-verification-evidence-contract.md"
POLICY_PATH = ROOT / "docs" / "stage-1c-storage-profile-policy.md"

CLAIM_NAMES = (
    "legacyRecordDowngraded",
    "legacyEvidenceReusedForManagedStandard",
    "legacyEvidenceReusedForManagedRestricted",
    "realVaultVerified",
    "providerApprovedByBrand",
    "artifactOnboardingAuthorized",
    "artifactPermissionGranted",
    "stage2Authorized",
)


class HighAssuranceCompatibilityError(ValueError):
    """Raised when C10 high-assurance compatibility drifts or is invalid."""


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Validate structural compatibility between the Stage 1C risk-tiered "
            "high-assurance profile and the legacy C4 vault evidence contract."
        )
    )
    result.add_argument("record", nargs="?", type=Path, default=DEFAULT_RECORD_PATH)
    return result


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as error:
        raise HighAssuranceCompatibilityError(
            f"invalid JSON at line {error.lineno}, column {error.colno}"
        ) from error
    if not isinstance(data, dict):
        raise HighAssuranceCompatibilityError("JSON root must be an object")
    return data


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    schema = load_json_object(path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        raise HighAssuranceCompatibilityError(
            "high-assurance compatibility schema is invalid"
        ) from error
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
    validator = Draft202012Validator(active_schema)
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        first = errors[0]
        raise HighAssuranceCompatibilityError(
            "schema validation failed at "
            f"{_schema_error_path(first)} ({first.validator})"
        )


def validate_compatibility(
    record: dict[str, Any],
    *,
    c4_schema: dict[str, Any],
    dataset_schema: dict[str, Any],
) -> None:
    eligibility = record["eligibilityClass"]
    profile = record["storageProfile"]

    if PROFILE_BY_ELIGIBILITY.get(eligibility) != profile:
        raise HighAssuranceCompatibilityError(
            "risk-tiered eligibility/profile mapping no longer matches C10"
        )
    mapped_to_high_assurance = {
        key for key, value in PROFILE_BY_ELIGIBILITY.items() if value == profile
    }
    if mapped_to_high_assurance != {"sensitive_custody"}:
        raise HighAssuranceCompatibilityError(
            "high-assurance profile is no longer exclusive to sensitive_custody"
        )
    if LEGACY_STORAGE_CLASS != record["legacyC4StorageClass"]:
        raise HighAssuranceCompatibilityError("legacy storage class binding drifted")

    item_properties = dataset_schema.get("$defs", {}).get("item", {}).get("properties", {})
    eligibility_values = item_properties.get("eligibilityClass", {}).get("enum", [])
    storage_values = (
        item_properties.get("retention", {})
        .get("properties", {})
        .get("storageClass", {})
        .get("enum", [])
    )
    if eligibility not in eligibility_values:
        raise HighAssuranceCompatibilityError(
            "dataset schema no longer admits sensitive_custody"
        )
    if profile not in storage_values:
        raise HighAssuranceCompatibilityError(
            "dataset schema no longer admits high_assurance_vault"
        )

    c4_properties = c4_schema.get("properties", {})
    expected_c4 = {
        "schemaVersion": record["legacyC4SchemaVersion"],
        "contractRef": record["legacyC4ContractRef"],
        "environment": record["legacyC4Environment"],
        "storageClass": record["legacyC4StorageClass"],
    }
    for name, expected in expected_c4.items():
        if c4_properties.get(name, {}).get("const") != expected:
            raise HighAssuranceCompatibilityError(
                f"legacy C4 binding drifted for {name}"
            )

    c4_controls = tuple(
        c4_properties.get("controls", {}).get("required", ())
    )
    if c4_controls != tuple(record["requiredC4Controls"]):
        raise HighAssuranceCompatibilityError("legacy C4 control set drifted")
    if c4_controls != C4_CONTROL_NAMES:
        raise HighAssuranceCompatibilityError(
            "C4 validator and C10 compatibility control sets disagree"
        )

    c4_claims = c4_properties.get("claims", {}).get("properties", {})
    for claim_name, claim_schema in c4_claims.items():
        if claim_schema.get("const") is not False:
            raise HighAssuranceCompatibilityError(
                f"legacy C4 authorization claim must remain false: {claim_name}"
            )
    for name in CLAIM_NAMES:
        if record["claims"][name] is not False:
            raise HighAssuranceCompatibilityError(
                f"C10 compatibility claim must remain false: {name}"
            )


def validate_repository_contract() -> tuple[dict[str, Any], dict[str, Any]]:
    required = (
        SCHEMA_PATH,
        DEFAULT_RECORD_PATH,
        CONTRACT_PATH,
        DATASET_SCHEMA_PATH,
        C4_CONTRACT_PATH,
        POLICY_PATH,
    )
    for path in required:
        if not path.is_file():
            raise HighAssuranceCompatibilityError(
                f"missing C10 contract file: {path.relative_to(ROOT)}"
            )

    schema = load_schema()
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise HighAssuranceCompatibilityError(
            "C10 schema must use JSON Schema Draft 2020-12"
        )
    record = load_json_object(DEFAULT_RECORD_PATH)
    validate_record(record, schema=schema)

    c4_schema = validate_c4_repository_contract()
    dataset_schema = load_json_object(DATASET_SCHEMA_PATH)
    validate_compatibility(record, c4_schema=c4_schema, dataset_schema=dataset_schema)

    c4_zero_state = validate_c4_file(C4_ZERO_STATE_PATH, schema=c4_schema)
    if c4_zero_state["overallState"] != "incomplete":
        raise HighAssuranceCompatibilityError(
            "repository C4 zero-state must remain incomplete"
        )
    return schema, record


def validate_file(path: Path, *, schema: dict[str, Any] | None = None) -> dict[str, Any]:
    active_schema = schema if schema is not None else load_schema()
    record = load_json_object(path)
    validate_record(record, schema=active_schema)
    c4_schema = validate_c4_repository_contract()
    dataset_schema = load_json_object(DATASET_SCHEMA_PATH)
    validate_compatibility(record, c4_schema=c4_schema, dataset_schema=dataset_schema)
    return record


def main() -> None:
    args = parser().parse_args()
    try:
        schema, _ = validate_repository_contract()
        record = validate_file(args.record, schema=schema)
    except (OSError, HighAssuranceCompatibilityError) as error:
        print(
            f"ERROR: Stage 1C high-assurance compatibility failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error

    print(
        "Stage 1C high-assurance compatibility passed: "
        f"{record['eligibilityClass']} -> {record['storageProfile']}; "
        "legacy C4 remains non-downgraded and artifact authorization remains false."
    )


if __name__ == "__main__":
    main()
