"""Approved Stage 3 purpose-grant overlay for immutable historical catalogs."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any, Mapping

from .dataset_contract_common import _permission, _permission_valid_on, canonical_sha256
from .dataset_contract_constants import DatasetManifestError, EVIDENCE_ID, PURPOSE_ACTOR_ID, SHA
from .stage3_custody_execution import (
    Stage3CustodyExecutionError,
    Stage3CustodyExecutionResult,
    run_authorized_pdf_pipeline_execution,
)

SCHEMA_VERSION = "1.0.0"
GRANT_SET_ID = "stage3.purpose-grants.beethoven-barley.v1"
APPROVED_GRANT_CANONICAL_SHA256 = "3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8"
APPROVED_AUTHORIZATION_REFERENCE = "evidence:opq_dd8bd76ebeb30b1ca0b7d701c0afe5cd"
APPROVED_AUTHORIZED_BY = "actor.purpose:opq_4fc475d3757d6951267d0d05a132dac7"
APPROVED_AUTHORIZED_ON = "2026-09-02"
APPROVED_SOURCE_CODE = "explicit_user_authorization"
APPROVED_ITEMS = {
    "dataset.item.imslp799143-beethoven-op48-no3.v1": "c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c",
    "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1": "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e",
}
APPROVED_PURPOSE = "pdf_pipeline_evaluation"


class Stage3PurposeGrantError(ValueError):
    """The Stage 3 purpose-grant overlay is absent, malformed, or not approved."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage3PurposeGrantError(message)


def _validate_restrictions(permission: Mapping[str, Any]) -> None:
    restrictions = permission["restrictions"]
    by_type = {item["type"]: item for item in restrictions}
    _require(
        set(by_type) == {
            "split_allowlist",
            "storage_class_allowlist",
            "environment_allowlist",
            "external_export",
        },
        "Stage 3 purpose grant must carry the exact approved restriction set.",
    )
    _require(
        by_type["split_allowlist"]["values"] == ["development"],
        "Stage 3 purpose grant is limited to the development split.",
    )
    _require(
        by_type["storage_class_allowlist"]["values"] == ["managed_standard"],
        "Stage 3 purpose grant is limited to managed_standard custody.",
    )
    _require(
        by_type["environment_allowlist"]["values"] == ["stage1_offline"],
        "Stage 3 purpose grant is limited to stage1_offline execution.",
    )
    _require(
        by_type["external_export"]["allowed"] is False,
        "Stage 3 purpose grant must not authorize external export.",
    )


def validate_stage3_purpose_grants(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the single approved immutable Stage 3 purpose-grant overlay."""

    if not isinstance(raw, Mapping):
        raise Stage3PurposeGrantError("Stage 3 purpose-grant overlay must be an object.")
    value = deepcopy(dict(raw))
    expected_fields = {
        "schemaVersion",
        "grantSetId",
        "authorizedOn",
        "authorizationReference",
        "authorizedBy",
        "authorizationSourceCode",
        "grants",
        "assertions",
    }
    _require(set(value) == expected_fields, "Stage 3 purpose-grant overlay fields drifted.")
    _require(value["schemaVersion"] == SCHEMA_VERSION, "Stage 3 purpose-grant schema version drifted.")
    _require(value["grantSetId"] == GRANT_SET_ID, "Stage 3 purpose-grant set id drifted.")
    _require(value["authorizedOn"] == APPROVED_AUTHORIZED_ON, "Stage 3 purpose-grant authorization date drifted.")
    _require(value["authorizationReference"] == APPROVED_AUTHORIZATION_REFERENCE, "Stage 3 purpose-grant evidence reference drifted.")
    _require(value["authorizedBy"] == APPROVED_AUTHORIZED_BY, "Stage 3 purpose-grant actor drifted.")
    _require(value["authorizationSourceCode"] == APPROVED_SOURCE_CODE, "Stage 3 purpose-grant source code drifted.")
    _require(EVIDENCE_ID.fullmatch(value["authorizationReference"]) is not None, "Stage 3 purpose-grant evidence id is invalid.")
    _require(PURPOSE_ACTOR_ID.fullmatch(value["authorizedBy"]) is not None, "Stage 3 purpose-grant actor id is invalid.")

    grants = value["grants"]
    _require(isinstance(grants, list), "Stage 3 purpose grants must be an array.")
    _require(len(grants) == len(APPROVED_ITEMS), "Stage 3 purpose-grant item count drifted.")
    seen: set[str] = set()
    for index, grant in enumerate(grants):
        _require(isinstance(grant, dict), f"Stage 3 purpose grant {index} must be an object.")
        _require(
            set(grant) == {"datasetItemId", "artifactSha256", "purpose", "permission"},
            f"Stage 3 purpose grant {index} fields drifted.",
        )
        item_id = grant["datasetItemId"]
        _require(item_id in APPROVED_ITEMS, f"Stage 3 purpose grant contains an unapproved item: {item_id}")
        _require(item_id not in seen, f"Stage 3 purpose grant repeats item: {item_id}")
        seen.add(item_id)
        _require(grant["artifactSha256"] == APPROVED_ITEMS[item_id], f"Stage 3 purpose grant artifact digest drifted for {item_id}.")
        _require(SHA.fullmatch(grant["artifactSha256"]) is not None, f"Stage 3 purpose grant artifact digest is invalid for {item_id}.")
        _require(grant["purpose"] == APPROVED_PURPOSE, f"Stage 3 purpose grant purpose drifted for {item_id}.")
        try:
            permission = _permission(grant["permission"], f"grants[{index}].permission")
        except DatasetManifestError as exc:
            raise Stage3PurposeGrantError(f"Stage 3 purpose grant permission is invalid for {item_id}.") from exc
        _require(permission["status"] == "granted", f"Stage 3 purpose grant is not granted for {item_id}.")
        _require(permission["authorizationReference"] == APPROVED_AUTHORIZATION_REFERENCE, f"Stage 3 purpose grant evidence reference drifted for {item_id}.")
        _require(permission["authorizedBy"] == APPROVED_AUTHORIZED_BY, f"Stage 3 purpose grant actor drifted for {item_id}.")
        _require(permission["authorizedOn"] == date.fromisoformat(APPROVED_AUTHORIZED_ON), f"Stage 3 purpose grant date drifted for {item_id}.")
        _require(permission["expiresOn"] is None, f"Stage 3 purpose grant unexpectedly expires for {item_id}.")
        _validate_restrictions(permission)

    _require(seen == set(APPROVED_ITEMS), "Stage 3 purpose-grant item set drifted.")
    assertions = value["assertions"]
    expected_assertions = {
        "historicalCatalogModified": False,
        "trainingAuthorized": False,
        "calibrationAuthorized": False,
        "publicationAuthorized": False,
        "demonstrationAuthorized": False,
        "externalExportAuthorized": False,
        "heldOutAuthorizationChanged": False,
    }
    _require(assertions == expected_assertions, "Stage 3 purpose-grant assertions drifted.")
    _require(
        canonical_sha256(value) == APPROVED_GRANT_CANONICAL_SHA256,
        "Stage 3 purpose-grant canonical digest is not the approved immutable digest.",
    )
    return value


def _grant_for(
    overlay: Mapping[str, Any],
    *,
    dataset_item_id: str,
    artifact_sha256: str,
    purpose: str,
) -> dict[str, Any]:
    validated = validate_stage3_purpose_grants(overlay)
    for grant in validated["grants"]:
        if (
            grant["datasetItemId"] == dataset_item_id
            and grant["artifactSha256"] == artifact_sha256
            and grant["purpose"] == purpose
        ):
            return deepcopy(grant)
    raise Stage3PurposeGrantError("No approved Stage 3 purpose grant matches the requested item/artifact/purpose tuple.")


def run_purpose_granted_pdf_pipeline_execution(
    catalog: Mapping[str, Any],
    purpose_grants: Mapping[str, Any],
    *,
    dataset_item_id: str,
    data: bytes,
    purpose: str,
    execution_date: date | str,
    environment: str = "stage1_offline",
    config: Any = None,
    quality_config: Any = None,
) -> Stage3CustodyExecutionResult:
    """Apply the approved grant in memory, then use the existing fail-closed Stage 3 executor."""

    catalog_copy = deepcopy(dict(catalog))
    item = next(
        (candidate for candidate in catalog_copy.get("items", []) if candidate.get("datasetItemId") == dataset_item_id),
        None,
    )
    if item is None:
        raise Stage3CustodyExecutionError(
            "dataset_item_not_found",
            "Dataset item is not present in the catalog supplied to the purpose-grant wrapper.",
            details={"datasetItemId": dataset_item_id},
        )
    if item.get("split") != "development":
        raise Stage3CustodyExecutionError(
            "purpose_grant_split_not_allowed",
            "The approved Stage 3 purpose-grant overlay may be applied to development items only.",
            details={"split": item.get("split")},
        )
    baseline = item.get("permissions", {}).get(purpose)
    if not isinstance(baseline, dict) or baseline.get("status") != "not_requested":
        raise Stage3CustodyExecutionError(
            "purpose_grant_cannot_override_catalog_state",
            "The Stage 3 purpose-grant overlay may only supplement a historical not_requested catalog permission.",
            details={"catalogPermissionStatus": baseline.get("status") if isinstance(baseline, dict) else None},
        )
    artifact_sha256 = item.get("artifact", {}).get("sha256")
    try:
        grant = _grant_for(
            purpose_grants,
            dataset_item_id=dataset_item_id,
            artifact_sha256=artifact_sha256,
            purpose=purpose,
        )
    except Stage3PurposeGrantError as exc:
        raise Stage3CustodyExecutionError(
            "purpose_grant_not_approved",
            "The supplied Stage 3 purpose-grant overlay is not the approved immutable grant.",
        ) from exc
    permission = _permission(grant["permission"], "grant.permission")
    when = execution_date if isinstance(execution_date, date) else date.fromisoformat(execution_date)
    if not _permission_valid_on(permission, when):
        raise Stage3CustodyExecutionError(
            "purpose_grant_not_valid_on_execution_date",
            "The approved Stage 3 purpose grant is not valid on the execution date.",
        )
    item["permissions"][purpose] = deepcopy(grant["permission"])
    return run_authorized_pdf_pipeline_execution(
        catalog_copy,
        dataset_item_id=dataset_item_id,
        data=data,
        purpose=purpose,
        execution_date=execution_date,
        environment=environment,
        config=config,
        quality_config=quality_config,
    )


__all__ = [
    "APPROVED_GRANT_CANONICAL_SHA256",
    "APPROVED_ITEMS",
    "APPROVED_PURPOSE",
    "GRANT_SET_ID",
    "SCHEMA_VERSION",
    "Stage3PurposeGrantError",
    "run_purpose_granted_pdf_pipeline_execution",
    "validate_stage3_purpose_grants",
]
