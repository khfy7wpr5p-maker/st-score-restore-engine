"""Fail-closed Stage 3 purpose-grant overlays for immutable Stage 1 corpus catalogs."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import hashlib
import json
from typing import Any, Mapping

from .dataset_catalog_validation import validate_dataset_catalog
from .dataset_contract_common import _permission, _restriction_by_type, canonical_sha256
from .dataset_contract_constants import DatasetManifestError, STAGE1_ENVIRONMENT
from .stage3_custody_execution import (
    Stage3CustodyExecutionResult,
    run_authorized_pdf_pipeline_execution,
)

SCHEMA_VERSION = "1.0.0"
GRANT_SET_ID = "stage3-purpose-grants-pdf-pipeline-2026-09-02-v1"
CATALOG_ID = "dataset.catalog.stage1c-expanded-corpus.v2"
CATALOG_CANONICAL_SHA256 = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"
PURPOSE = "pdf_pipeline_evaluation"
AUTHORIZED_ON = "2026-09-02"
AUTHORIZED_DATASET_ITEMS = frozenset({
    "dataset.item.imslp799143-beethoven-op48-no3.v1",
    "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1",
})


class Stage3PurposeGrantError(ValueError):
    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})


def _fail(code: str, message: str, **details: Any) -> None:
    raise Stage3PurposeGrantError(code, message, details=details)


def _when(value: date | str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise Stage3PurposeGrantError("invalid_execution_date", "Execution date must use YYYY-MM-DD.") from exc


def _digest_without_field(value: Mapping[str, Any], field: str) -> str:
    payload = deepcopy(dict(value))
    payload.pop(field, None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _fixed_restrictions(permission: Mapping[str, Any]) -> bool:
    wanted = {
        "split_allowlist": {"type": "split_allowlist", "values": ["development"]},
        "storage_class_allowlist": {"type": "storage_class_allowlist", "values": ["managed_standard"]},
        "environment_allowlist": {"type": "environment_allowlist", "values": [STAGE1_ENVIRONMENT]},
        "external_export": {"type": "external_export", "allowed": False},
    }
    return (
        len(permission["restrictions"]) == len(wanted)
        and all(_restriction_by_type(dict(permission), key) == expected for key, expected in wanted.items())
    )


def validate_stage3_purpose_grants(
    catalog: Mapping[str, Any],
    grants: Mapping[str, Any],
    *,
    execution_date: date | str,
) -> dict[str, Any]:
    """Validate the exact Beethoven/Barley Stage 3 grant set without mutating catalog."""

    when = _when(execution_date)
    try:
        validated_catalog = validate_dataset_catalog(deepcopy(dict(catalog)))
    except (DatasetManifestError, TypeError, KeyError) as exc:
        raise Stage3PurposeGrantError("catalog_invalid", "Catalog failed canonical validation.") from exc

    expected_fields = {
        "schemaVersion", "grantSetId", "catalogId", "catalogCanonicalSha256", "purpose",
        "authorizationBasis", "authorizedOn", "grants", "assertions", "grantSetDigest",
    }
    if not isinstance(grants, Mapping) or set(grants) != expected_fields:
        _fail("grant_invalid", "Grant-set fields do not match the Stage 3 contract.")
    if grants["schemaVersion"] != SCHEMA_VERSION or grants["grantSetId"] != GRANT_SET_ID:
        _fail("grant_identity_mismatch", "Unexpected Stage 3 grant-set identity.")
    if grants["catalogId"] != CATALOG_ID or grants["catalogCanonicalSha256"] != CATALOG_CANONICAL_SHA256:
        _fail("grant_catalog_binding_mismatch", "Grant set is not bound to accepted expanded-v2 catalog.")
    if canonical_sha256(catalog) != CATALOG_CANONICAL_SHA256:
        _fail("catalog_digest_mismatch", "Runtime catalog differs from immutable expanded-v2 catalog.")
    if grants["purpose"] != PURPOSE or grants["authorizationBasis"] != "explicit_user_authorization":
        _fail("grant_scope_mismatch", "Grant scope must be explicit user authorization for pdf_pipeline_evaluation.")
    if grants["authorizedOn"] != AUTHORIZED_ON or when < date.fromisoformat(AUTHORIZED_ON):
        _fail("grant_date_mismatch", "Grant date is invalid for this execution.")

    expected_assertions = {
        "historicalCatalogsModified": False,
        "trainingAuthorized": False,
        "calibrationAuthorized": False,
        "publicationAuthorized": False,
        "demonstrationAuthorized": False,
        "externalExportAuthorized": False,
    }
    if grants["assertions"] != expected_assertions:
        _fail("grant_assertion_mismatch", "Grant set broadens authorization beyond Stage 3 evaluation.")

    rows = grants["grants"]
    if not isinstance(rows, list) or {row.get("datasetItemId") for row in rows if isinstance(row, Mapping)} != set(AUTHORIZED_DATASET_ITEMS):
        _fail("grant_item_set_mismatch", "Grant set must contain exactly Beethoven and Barley.")
    if len(rows) != 2:
        _fail("grant_item_set_mismatch", "Grant set must contain exactly two unique items.")

    by_id = {item["datasetItemId"]: item for item in validated_catalog["items"]}
    for index, grant in enumerate(rows):
        if not isinstance(grant, Mapping) or set(grant) != {"datasetItemId", "artifactSha256", "byteSize", "split", "permission"}:
            _fail("grant_invalid", f"Grant row {index} has invalid fields.")
        item_id = grant["datasetItemId"]
        item = by_id.get(item_id)
        if item is None:
            _fail("grant_item_not_found", "Grant item is absent from accepted catalog.", datasetItemId=item_id)
        if item["split"] != "development" or grant["split"] != "development":
            _fail("grant_split_mismatch", "pdf_pipeline_evaluation grant is development-only.", datasetItemId=item_id)
        if item["retention"]["storageClass"] != "managed_standard":
            _fail("grant_storage_mismatch", "Grant item must remain in managed_standard custody.", datasetItemId=item_id)
        if item["permissions"][PURPOSE]["status"] != "not_requested":
            _fail("grant_baseline_changed", "Historical permission baseline is no longer not_requested.", datasetItemId=item_id)
        if grant["artifactSha256"] != item["artifact"]["sha256"] or grant["byteSize"] != item["artifact"]["byteSize"]:
            _fail("grant_artifact_mismatch", "Grant is not bound to exact admitted bytes.", datasetItemId=item_id)
        try:
            permission = _permission(grant["permission"], f"grant[{index}].permission")
        except DatasetManifestError as exc:
            raise Stage3PurposeGrantError("grant_permission_invalid", "Grant permission failed canonical validation.") from exc
        if permission["status"] != "granted" or permission["authorizedOn"] != date.fromisoformat(AUTHORIZED_ON):
            _fail("grant_permission_not_valid", "Grant permission is not active from the explicit authorization date.", datasetItemId=item_id)
        if permission["expiresOn"] is not None or permission["revokedOn"] is not None or not _fixed_restrictions(permission):
            _fail("grant_restriction_mismatch", "Grant permission restrictions drifted.", datasetItemId=item_id)

    digest = grants["grantSetDigest"]
    if digest != {"algorithm": "sha256", "value": _digest_without_field(grants, "grantSetDigest")}:
        _fail("grant_set_digest_mismatch", "Grant-set digest is invalid.")
    return deepcopy(dict(grants))


def apply_stage3_purpose_grants(
    catalog: Mapping[str, Any],
    grants: Mapping[str, Any],
    *,
    execution_date: date | str,
) -> dict[str, Any]:
    validated = validate_stage3_purpose_grants(catalog, grants, execution_date=execution_date)
    result = deepcopy(dict(catalog))
    by_id = {item["datasetItemId"]: item for item in result["items"]}
    for grant in validated["grants"]:
        by_id[grant["datasetItemId"]]["permissions"][PURPOSE] = deepcopy(grant["permission"])
    return result


def run_authorized_pdf_pipeline_execution_with_grants(
    catalog: Mapping[str, Any],
    grants: Mapping[str, Any],
    *,
    dataset_item_id: str,
    data: bytes,
    execution_date: date | str,
    **kwargs: Any,
) -> Stage3CustodyExecutionResult:
    overlaid = apply_stage3_purpose_grants(catalog, grants, execution_date=execution_date)
    return run_authorized_pdf_pipeline_execution(
        overlaid,
        dataset_item_id=dataset_item_id,
        data=data,
        purpose=PURPOSE,
        execution_date=execution_date,
        **kwargs,
    )


__all__ = [
    "AUTHORIZED_DATASET_ITEMS", "AUTHORIZED_ON", "CATALOG_CANONICAL_SHA256", "CATALOG_ID",
    "GRANT_SET_ID", "PURPOSE", "SCHEMA_VERSION", "Stage3PurposeGrantError",
    "apply_stage3_purpose_grants", "run_authorized_pdf_pipeline_execution_with_grants",
    "validate_stage3_purpose_grants",
]
