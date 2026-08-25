"""Evaluate Stage 1C artifact admission without reading artifact bytes."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_contract_common import (  # noqa: E402
    _permission,
    _permission_valid_on,
    _restriction_by_type,
    _utc_datetime,
)
from st_score_restore.dataset_contract_constants import (  # noqa: E402
    DatasetManifestError,
    PROFILE_BY_ELIGIBILITY,
    PURPOSES,
    STAGE1_ENVIRONMENT,
)
from st_score_restore.dataset_manifest import (  # noqa: E402
    load_json_object,
    validate_dataset_catalog,
)
from tools.validate_stage1c_managed_restricted_verification import (  # noqa: E402
    ManagedRestrictedVerificationError,
    validate_record as validate_restricted_record,
)
from tools.validate_stage1c_managed_standard_verification import (  # noqa: E402
    ManagedStandardVerificationError,
    validate_record as validate_standard_record,
)
from tools.validate_stage1c_vault_verification import (  # noqa: E402
    VaultVerificationError,
    validate_record as validate_vault_record,
)

SCHEMA_PATH = ROOT / "schemas" / "stage1c-artifact-admission-request.schema.json"
DEFAULT_REQUEST_PATH = ROOT / "examples" / "stage1c-artifact-admission.zero-state.v1.json"
DEFAULT_CATALOG_PATH = ROOT / "examples" / "dataset-catalog.metadata-only.v1.json"
CONTRACT_PATH = ROOT / "docs" / "stage-1c-artifact-admission-contract.md"

ALLOWED_PURPOSE_TO_SPLIT = {
    "quality_evaluation": "development",
    "held_out_evaluation": "held_out",
}

PROFILE_VERIFICATION_FIELDS = {
    "managed_standard": ("verificationId", "eligibilityClass", "storageProfile"),
    "managed_restricted": ("verificationId", "eligibilityClass", "profile"),
    "high_assurance_vault": ("verificationId", None, None),
}


class ArtifactAdmissionError(ValueError):
    """Raised when the C11 admission request or repository contract is invalid."""


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Evaluate a Stage 1C artifact admission request against the current "
            "dataset catalog and an optional profile-verification record. This "
            "tool never reads artifact bytes or external provider evidence."
        )
    )
    result.add_argument("request", nargs="?", type=Path, default=DEFAULT_REQUEST_PATH)
    result.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG_PATH)
    result.add_argument("--profile-verification", type=Path)
    result.add_argument(
        "--require-eligible",
        action="store_true",
        help="exit non-zero unless the deterministic decision is eligible",
    )
    return result


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    schema = load_json_object(path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        raise ArtifactAdmissionError("artifact-admission schema is invalid") from error
    return schema


def _schema_error_path(error: Any) -> str:
    parts = [str(part) for part in error.absolute_path]
    return ".".join(parts) if parts else "<root>"


def validate_request(
    request: dict[str, Any],
    *,
    schema: dict[str, Any] | None = None,
) -> None:
    active_schema = schema if schema is not None else load_schema()
    validator = Draft202012Validator(active_schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(request),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        first = errors[0]
        raise ArtifactAdmissionError(
            "request schema validation failed at "
            f"{_schema_error_path(first)} ({first.validator})"
        )


def validate_repository_contract() -> dict[str, Any]:
    for path in (SCHEMA_PATH, DEFAULT_REQUEST_PATH, DEFAULT_CATALOG_PATH, CONTRACT_PATH):
        if not path.is_file():
            raise ArtifactAdmissionError(
                f"missing C11 contract file: {path.relative_to(ROOT)}"
            )

    schema = load_schema()
    properties = schema.get("properties", {})
    expected_consts = {
        "schemaVersion": "stage1c-artifact-admission-request-v1",
        "architectureRef": "adr-0016-stage-1c-risk-tiered-custody-v1",
    }
    for field, expected in expected_consts.items():
        if properties.get(field, {}).get("const") != expected:
            raise ArtifactAdmissionError(
                f"unexpected C11 schema binding for {field}"
            )

    claims = properties.get("claims", {}).get("properties", {})
    if not claims or any(value.get("const") is not False for value in claims.values()):
        raise ArtifactAdmissionError("all C11 authorization-expansion claims must stay false")

    zero_state = load_json_object(DEFAULT_REQUEST_PATH)
    validate_request(zero_state, schema=schema)
    return schema


def _add(reasons: set[str], condition: bool, code: str) -> None:
    if condition:
        reasons.add(code)


def _review_after(item: dict[str, Any], when: date) -> bool:
    dates = (
        item["provenance"]["rightsReview"]["verifiedOn"],
        item["privacy"]["reviewedOn"],
        item["review"]["reviewedOn"],
    )
    return any(raw is not None and date.fromisoformat(raw) > when for raw in dates)


def _permission_restrictions_allow(
    permission: dict[str, Any],
    *,
    split: str,
    storage_profile: str,
    retention_expiry: str | None,
) -> bool:
    split_rule = _restriction_by_type(permission, "split_allowlist")
    if split_rule is not None and split not in split_rule["values"]:
        return False

    storage_rule = _restriction_by_type(permission, "storage_class_allowlist")
    if storage_rule is not None and storage_profile not in storage_rule["values"]:
        return False

    environment_rule = _restriction_by_type(permission, "environment_allowlist")
    if environment_rule is not None and STAGE1_ENVIRONMENT not in environment_rule["values"]:
        return False

    retention_rule = _restriction_by_type(permission, "retention_not_after")
    if retention_rule is not None:
        if retention_expiry is None:
            return False
        maximum = date.fromisoformat(retention_rule["date"])
        if date.fromisoformat(retention_expiry) > maximum:
            return False

    return True


def _validate_profile_record(
    storage_profile: str,
    record: dict[str, Any],
) -> None:
    if storage_profile == "managed_standard":
        validate_standard_record(record)
    elif storage_profile == "managed_restricted":
        validate_restricted_record(record)
    elif storage_profile == "high_assurance_vault":
        validate_vault_record(record)
    else:  # pragma: no cover - protected by request/catalog validation
        raise ArtifactAdmissionError("unsupported storage profile")


def evaluate_admission(
    request: dict[str, Any],
    *,
    catalog: dict[str, Any],
    profile_record: dict[str, Any] | None = None,
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a deterministic eligible/blocked decision and stable reason codes."""
    validate_request(request, schema=schema)
    validated_catalog = validate_dataset_catalog(catalog)
    reasons: set[str] = set()

    item = next(
        (
            candidate
            for candidate in validated_catalog["items"]
            if candidate["datasetItemId"] == request["datasetItemId"]
        ),
        None,
    )
    if item is None:
        return {"decision": "blocked", "reasonCodes": ["unknown_dataset_item"]}

    when = _utc_datetime(request["evaluatedAt"], "request.evaluatedAt").date()
    artifact = item["artifact"]
    retention = item["retention"]
    eligibility = item["eligibilityClass"]
    storage_profile = retention["storageClass"]
    requested_purpose = request["requestedPurpose"]

    _add(reasons, artifact["state"] != "external_available", "artifact_not_external_available")
    _add(
        reasons,
        request["acquisitionEvidenceRef"] != item["provenance"]["sourceReference"],
        "acquisition_evidence_mismatch",
    )
    _add(reasons, request["expectedEligibilityClass"] is None, "missing_expected_eligibility")
    _add(reasons, request["expectedStorageProfile"] is None, "missing_expected_storage_profile")
    if request["expectedEligibilityClass"] is not None:
        _add(
            reasons,
            request["expectedEligibilityClass"] != eligibility,
            "eligibility_class_mismatch",
        )
    if request["expectedStorageProfile"] is not None:
        _add(
            reasons,
            request["expectedStorageProfile"] != storage_profile,
            "storage_profile_mismatch",
        )

    expected_profile = PROFILE_BY_ELIGIBILITY.get(eligibility)
    _add(
        reasons,
        expected_profile is None or expected_profile != storage_profile,
        "eligibility_profile_pair_invalid",
    )

    _add(reasons, requested_purpose is None, "missing_requested_purpose")
    _add(
        reasons,
        request["profileVerificationRef"] is None,
        "missing_profile_verification_ref",
    )
    _add(
        reasons,
        request["storageBindingEvidenceRef"] is None,
        "missing_storage_binding_evidence",
    )
    _add(reasons, item["revocation"]["status"] != "not_revoked", "item_revoked_or_deleting")
    _add(reasons, _review_after(item, when), "review_completed_after_evaluation_time")

    retention_expiry = retention["expiresOn"]
    if retention_expiry is not None:
        _add(
            reasons,
            when >= date.fromisoformat(retention_expiry),
            "retention_expired",
        )

    granted_purposes = {
        purpose
        for purpose in PURPOSES
        if item["permissions"][purpose]["status"] == "granted"
    }

    if requested_purpose is not None:
        expected_split = ALLOWED_PURPOSE_TO_SPLIT[requested_purpose]
        _add(reasons, item["split"] != expected_split, "purpose_split_mismatch")
        _add(
            reasons,
            granted_purposes != {requested_purpose},
            "active_purpose_set_not_exact",
        )
        permission = _permission(
            item["permissions"][requested_purpose],
            f"item.permissions.{requested_purpose}",
        )
        _add(
            reasons,
            not _permission_valid_on(permission, when),
            "requested_purpose_not_current",
        )
        _add(
            reasons,
            not _permission_restrictions_allow(
                permission,
                split=item["split"],
                storage_profile=storage_profile,
                retention_expiry=retention_expiry,
            ),
            "requested_purpose_restriction_mismatch",
        )

    if profile_record is None:
        reasons.add("missing_profile_verification_record")
    elif request["expectedStorageProfile"] is not None:
        try:
            _validate_profile_record(request["expectedStorageProfile"], profile_record)
        except (
            ManagedStandardVerificationError,
            ManagedRestrictedVerificationError,
            VaultVerificationError,
        ):
            reasons.add("profile_verification_record_invalid")
        else:
            verification_field, eligibility_field, profile_field = PROFILE_VERIFICATION_FIELDS[
                request["expectedStorageProfile"]
            ]
            _add(
                reasons,
                request["profileVerificationRef"] != profile_record.get(verification_field),
                "profile_verification_ref_mismatch",
            )
            _add(
                reasons,
                profile_record.get("overallState") != "pass",
                "profile_verification_not_pass",
            )
            if eligibility_field is not None:
                _add(
                    reasons,
                    profile_record.get(eligibility_field) != eligibility,
                    "profile_verification_eligibility_mismatch",
                )
            if profile_field is not None:
                _add(
                    reasons,
                    profile_record.get(profile_field) != storage_profile,
                    "profile_verification_storage_mismatch",
                )

    decision = "eligible" if not reasons else "blocked"
    return {"decision": decision, "reasonCodes": sorted(reasons)}


def main() -> None:
    args = parser().parse_args()
    try:
        schema = validate_repository_contract()
        request = load_json_object(args.request)
        catalog = load_json_object(args.catalog)
        profile_record = (
            load_json_object(args.profile_verification)
            if args.profile_verification is not None
            else None
        )
        result = evaluate_admission(
            request,
            catalog=catalog,
            profile_record=profile_record,
            schema=schema,
        )
    except (
        OSError,
        DatasetManifestError,
        ArtifactAdmissionError,
    ) as error:
        print(f"ERROR: Stage 1C artifact admission evaluation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    reasons = ",".join(result["reasonCodes"]) if result["reasonCodes"] else "none"
    print(
        "Stage 1C artifact admission evaluation completed: "
        f"decision={result['decision']}; reasonCodes={reasons}; artifact bytes were not read."
    )
    if args.require_eligible and result["decision"] != "eligible":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
