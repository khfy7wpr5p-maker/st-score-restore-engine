"""Immutable Stage 4 safety-calibration purpose-grant overlay.

The historical Stage 1 catalog is not rewritten. This module validates the exact
Beethoven/Barley development grants approved for Stage 4 safety calibration and
preserves Chopin as held-out evaluation only. A purpose grant does not accept a
reference-label bundle and does not by itself authorize calibration execution.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any, Mapping

from .dataset_contract_common import _permission, _permission_valid_on, canonical_sha256
from .dataset_contract_constants import DatasetManifestError, EVIDENCE_ID, PURPOSE_ACTOR_ID, SHA

SCHEMA_VERSION = "1.0.0"
GRANT_SET_ID = "stage4.purpose-grants.beethoven-barley-safety-calibration.v1"
APPROVED_GRANT_CANONICAL_SHA256 = "4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc"
APPROVED_AUTHORIZATION_REFERENCE = "evidence:opq_f673f32fbfee9cf66c4b3493bda17de5"
APPROVED_AUTHORIZED_BY = "actor.purpose:opq_f23b22682eed27cfea6a0ca05080f10f"
APPROVED_AUTHORIZED_ON = "2026-09-02"
APPROVED_SOURCE_CODE = "explicit_user_authorization"
APPROVED_PURPOSE = "safety_calibration"
APPROVED_ITEMS = {
    "dataset.item.imslp799143-beethoven-op48-no3.v1": "c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c",
    "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1": "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e",
}
HELD_OUT_ITEM = "dataset.item.imslp82860-chopin-op69.v2"
HELD_OUT_SHA256 = "b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3"


class Stage4PurposeGrantError(ValueError):
    """Stage 4 purpose grants are absent, malformed, or outside approved scope."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4PurposeGrantError(message)


def _validate_restrictions(permission: Mapping[str, Any]) -> None:
    restrictions = permission["restrictions"]
    by_type = {item["type"]: item for item in restrictions}
    _require(
        set(by_type) == {"split_allowlist", "storage_class_allowlist", "environment_allowlist", "external_export"},
        "Stage 4 purpose grant restriction set drifted.",
    )
    _require(by_type["split_allowlist"]["values"] == ["development"], "Stage 4 grant must be development-only.")
    _require(by_type["storage_class_allowlist"]["values"] == ["managed_standard"], "Stage 4 grant requires managed_standard custody.")
    _require(by_type["environment_allowlist"]["values"] == ["stage1_offline"], "Stage 4 grant requires stage1_offline execution.")
    _require(by_type["external_export"]["allowed"] is False, "Stage 4 grant must block external export.")


def validate_stage4_purpose_grants(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise Stage4PurposeGrantError("Stage 4 purpose-grant overlay must be an object.")
    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schemaVersion", "grantSetId", "authorizedOn", "authorizationReference", "authorizedBy",
            "authorizationSourceCode", "grants", "heldOutBinding", "assertions"
        },
        "Stage 4 purpose-grant overlay fields drifted.",
    )
    _require(value["schemaVersion"] == SCHEMA_VERSION, "Stage 4 purpose-grant schema drifted.")
    _require(value["grantSetId"] == GRANT_SET_ID, "Stage 4 grant-set id drifted.")
    _require(value["authorizedOn"] == APPROVED_AUTHORIZED_ON, "Stage 4 authorization date drifted.")
    _require(value["authorizationReference"] == APPROVED_AUTHORIZATION_REFERENCE, "Stage 4 authorization reference drifted.")
    _require(value["authorizedBy"] == APPROVED_AUTHORIZED_BY, "Stage 4 authorizer drifted.")
    _require(value["authorizationSourceCode"] == APPROVED_SOURCE_CODE, "Stage 4 authorization source drifted.")
    _require(EVIDENCE_ID.fullmatch(value["authorizationReference"]) is not None, "Stage 4 evidence reference is invalid.")
    _require(PURPOSE_ACTOR_ID.fullmatch(value["authorizedBy"]) is not None, "Stage 4 purpose actor is invalid.")

    grants = value["grants"]
    _require(isinstance(grants, list) and len(grants) == 2, "Stage 4 must contain exactly two development grants.")
    seen: set[str] = set()
    for index, grant in enumerate(grants):
        _require(isinstance(grant, dict), f"Stage 4 grant {index} must be an object.")
        _require(set(grant) == {"datasetItemId", "artifactSha256", "purpose", "permission"}, f"Stage 4 grant {index} fields drifted.")
        item_id = grant["datasetItemId"]
        _require(item_id in APPROVED_ITEMS and item_id not in seen, f"Unapproved or duplicate Stage 4 item: {item_id}")
        seen.add(item_id)
        _require(grant["artifactSha256"] == APPROVED_ITEMS[item_id], f"Stage 4 artifact SHA drifted for {item_id}.")
        _require(SHA.fullmatch(grant["artifactSha256"]) is not None, f"Stage 4 artifact SHA is invalid for {item_id}.")
        _require(grant["purpose"] == APPROVED_PURPOSE, f"Stage 4 purpose drifted for {item_id}.")
        try:
            permission = _permission(grant["permission"], f"grants[{index}].permission")
        except DatasetManifestError as exc:
            raise Stage4PurposeGrantError(f"Invalid Stage 4 permission for {item_id}.") from exc
        _require(permission["status"] == "granted", f"Stage 4 purpose is not granted for {item_id}.")
        _require(permission["authorizationReference"] == APPROVED_AUTHORIZATION_REFERENCE, f"Stage 4 evidence reference drifted for {item_id}.")
        _require(permission["authorizedBy"] == APPROVED_AUTHORIZED_BY, f"Stage 4 actor drifted for {item_id}.")
        _require(permission["authorizedOn"] == date.fromisoformat(APPROVED_AUTHORIZED_ON), f"Stage 4 date drifted for {item_id}.")
        _require(permission["expiresOn"] is None, f"Stage 4 grant unexpectedly expires for {item_id}.")
        _validate_restrictions(permission)
    _require(seen == set(APPROVED_ITEMS), "Stage 4 approved development item set drifted.")

    held_out = value["heldOutBinding"]
    _require(
        held_out == {
            "datasetItemId": HELD_OUT_ITEM,
            "artifactSha256": HELD_OUT_SHA256,
            "split": "held_out",
            "purpose": "held_out_evaluation",
            "existingAuthorizationPreserved": True,
            "candidateDerivationAuthorized": False,
        },
        "Stage 4 Chopin held-out binding drifted.",
    )
    _require(
        value["assertions"] == {
            "historicalCatalogModified": False,
            "safetyCalibrationPurposeAuthorized": True,
            "realDataCalibrationExecutionAuthorized": False,
            "referenceLabelBundleAccepted": False,
            "trainingAuthorized": False,
            "publicationAuthorized": False,
            "demonstrationAuthorized": False,
            "externalExportAuthorized": False,
            "heldOutAuthorizationChanged": False,
            "heldOutTuningAuthorized": False,
        },
        "Stage 4 purpose-grant assertions drifted.",
    )
    _require(canonical_sha256(value) == APPROVED_GRANT_CANONICAL_SHA256, "Stage 4 purpose-grant canonical digest drifted.")
    return value


def purpose_permission_granted_for(
    overlay: Mapping[str, Any], *, dataset_item_id: str, artifact_sha256: str, execution_date: date | str,
    environment: str = "stage1_offline",
) -> bool:
    """Return True only for an exact approved development artifact-purpose tuple."""
    validated = validate_stage4_purpose_grants(overlay)
    when = execution_date if isinstance(execution_date, date) else date.fromisoformat(execution_date)
    for grant in validated["grants"]:
        if grant["datasetItemId"] != dataset_item_id or grant["artifactSha256"] != artifact_sha256:
            continue
        permission = _permission(grant["permission"], "grant.permission")
        if environment != "stage1_offline" or not _permission_valid_on(permission, when):
            return False
        return True
    return False


__all__ = [
    "APPROVED_GRANT_CANONICAL_SHA256", "APPROVED_ITEMS", "APPROVED_PURPOSE", "GRANT_SET_ID",
    "HELD_OUT_ITEM", "HELD_OUT_SHA256", "Stage4PurposeGrantError", "purpose_permission_granted_for",
    "validate_stage4_purpose_grants",
]
