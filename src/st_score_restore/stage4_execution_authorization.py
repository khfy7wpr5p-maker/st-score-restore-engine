"""Fail-closed Stage 4 real development calibration execution authorization.

This contract authorizes real-data development calibration only for the exact
Beethoven + Barley artifacts already covered by the Stage 4 safety-calibration
purpose grant and accepted human reference-label bundle. It does not execute
calibration, authorize held-out evaluation/tuning, change production thresholds
or resource limits, train a model, publish evidence, grant Stage 4 PASS, or open
Stage 5.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage4_purpose_grants import (
    APPROVED_GRANT_CANONICAL_SHA256,
    APPROVED_ITEMS,
    validate_stage4_purpose_grants,
)
from .stage4_reference_label_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    REFERENCE_RECEIPT_CANONICAL_SHA256,
    validate_reference_label_acceptance,
)
from .stage4_reference_label_completion import BUNDLE_CANONICAL_SHA256

AUTHORIZATION_SCHEMA_VERSION = "1.0.0"
AUTHORIZATION_ID = "stage4.real-development-calibration-execution-authorization.beethoven-barley.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_REAL_DEVELOPMENT_CALIBRATION_EXECUTION"
AUTHORIZED_ON = "2026-09-03"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260903-01"
AUTHORIZATION_SOURCE_CODE = "explicit_user_authorization"
AUTHORIZATION_CANONICAL_SHA256 = "81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68"

EXPECTED_SOURCE_FAMILIES = {
    "dataset.item.imslp799143-beethoven-op48-no3.v1": "source.family.imslp799143-beethoven-op48-no3.v1",
    "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1": "source.family.barley-mnoah-your-face-your-tongue-your-wit.v1",
}


class Stage4ExecutionAuthorizationError(ValueError):
    """Execution authorization is malformed, unbound, expired, or over-scoped."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4ExecutionAuthorizationError(message)


def validate_stage4_execution_authorization(
    raw: Mapping[str, Any],
    purpose_raw: Mapping[str, Any],
    acceptance_raw: Mapping[str, Any],
    completion_raw: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise Stage4ExecutionAuthorizationError("execution authorization must be an object")
    value = deepcopy(dict(raw))

    purpose = validate_stage4_purpose_grants(purpose_raw)
    acceptance = validate_reference_label_acceptance(acceptance_raw, completion_raw)
    _require(canonical_sha256(purpose) == APPROVED_GRANT_CANONICAL_SHA256, "purpose-grant digest drifted")
    _require(canonical_sha256(acceptance) == ACCEPTANCE_CANONICAL_SHA256, "reference acceptance digest drifted")
    _require(acceptance.get("assertions", {}).get("referenceBundleAccepted") is True, "accepted reference bundle missing")
    _require(
        acceptance.get("assertions", {}).get("realDataCalibrationExecutionAuthorized") is False,
        "historical reference acceptance must remain immutable and non-authorizing",
    )

    _require(
        set(value) == {
            "schemaVersion", "authorizationId", "decision", "authorizedOn", "decisionAuthorityReference",
            "authorizationSourceCode", "purposeGrantDigest", "referenceBundleAcceptanceDigest",
            "acceptedReferenceReceiptDigest", "referenceBundleDigest", "scope", "assertions"
        },
        "execution authorization top-level fields drifted",
    )
    _require(value["schemaVersion"] == AUTHORIZATION_SCHEMA_VERSION, "execution authorization schema drifted")
    _require(value["authorizationId"] == AUTHORIZATION_ID, "execution authorization id drifted")
    _require(value["decision"] == AUTHORIZATION_DECISION, "real development calibration execution is not explicitly authorized")
    _require(value["authorizedOn"] == AUTHORIZED_ON, "execution authorization date drifted")
    _require(value["decisionAuthorityReference"] == DECISION_AUTHORITY_REFERENCE, "execution decision authority drifted")
    _require(value["authorizationSourceCode"] == AUTHORIZATION_SOURCE_CODE, "execution authorization source drifted")
    _require(
        value["purposeGrantDigest"] == {"algorithm": "sha256", "value": APPROVED_GRANT_CANONICAL_SHA256},
        "purpose-grant binding drifted",
    )
    _require(
        value["referenceBundleAcceptanceDigest"] == {"algorithm": "sha256", "value": ACCEPTANCE_CANONICAL_SHA256},
        "reference-bundle acceptance binding drifted",
    )
    _require(
        value["acceptedReferenceReceiptDigest"] == {"algorithm": "sha256", "value": REFERENCE_RECEIPT_CANONICAL_SHA256},
        "accepted reference receipt binding drifted",
    )
    _require(
        value["referenceBundleDigest"] == {"algorithm": "sha256", "value": BUNDLE_CANONICAL_SHA256},
        "accepted reference-bundle digest binding drifted",
    )

    scope = value["scope"]
    _require(isinstance(scope, dict), "execution authorization scope must be an object")
    _require(
        set(scope) == {
            "split", "dataClass", "purpose", "environment", "storageClass", "datasetItemCount",
            "sourceFamilyCount", "referenceRecordCount", "datasetItems", "candidateDerivationAuthorized",
            "developmentEvaluationAuthorized", "heldOutIncluded", "heldOutEvaluationAuthorized",
            "heldOutTuningAuthorized", "privateObservationMetricsRequired", "rawObservationMetricsAllowedInOrdinaryGit"
        },
        "execution authorization scope fields drifted",
    )
    _require(scope["split"] == "development", "execution authorization must remain development-only")
    _require(scope["dataClass"] == "real", "execution authorization must remain real-data scoped")
    _require(scope["purpose"] == "safety_calibration", "execution authorization purpose drifted")
    _require(scope["environment"] == "stage1_offline", "execution environment drifted")
    _require(scope["storageClass"] == "managed_standard", "execution storage class drifted")
    _require(scope["datasetItemCount"] == 2, "execution authorization must bind exactly two development items")
    _require(scope["sourceFamilyCount"] == 2, "execution authorization must bind exactly two source families")
    _require(scope["referenceRecordCount"] == 42, "execution authorization must bind the accepted 42-label bundle")

    items = scope["datasetItems"]
    _require(isinstance(items, list) and len(items) == 2, "execution authorization item list drifted")
    seen: set[str] = set()
    for item in items:
        _require(isinstance(item, dict), "execution authorization item must be an object")
        _require(set(item) == {"datasetItemId", "artifactSha256", "sourceFamilyId"}, "execution item fields drifted")
        item_id = item["datasetItemId"]
        _require(item_id in APPROVED_ITEMS and item_id not in seen, f"unapproved or duplicate execution item: {item_id}")
        seen.add(item_id)
        _require(item["artifactSha256"] == APPROVED_ITEMS[item_id], f"artifact SHA drifted for {item_id}")
        _require(item["sourceFamilyId"] == EXPECTED_SOURCE_FAMILIES[item_id], f"source-family binding drifted for {item_id}")
    _require(seen == set(APPROVED_ITEMS), "execution authorization exact development item set drifted")

    _require(scope["candidateDerivationAuthorized"] is True, "development candidate derivation is not authorized")
    _require(scope["developmentEvaluationAuthorized"] is True, "development evaluation is not authorized")
    _require(scope["heldOutIncluded"] is False, "held-out data entered development execution scope")
    _require(scope["heldOutEvaluationAuthorized"] is False, "held-out evaluation was prematurely authorized")
    _require(scope["heldOutTuningAuthorized"] is False, "held-out tuning was authorized")
    _require(scope["privateObservationMetricsRequired"] is True, "private observation metrics are not required")
    _require(scope["rawObservationMetricsAllowedInOrdinaryGit"] is False, "raw observation metrics were allowed in ordinary Git")

    _require(
        value["assertions"] == {
            "safetyCalibrationPurposeGranted": True,
            "referenceBundleAccepted": True,
            "realDataCalibrationExecutionAuthorized": True,
            "realDataCalibrationExecuted": False,
            "thresholdsCalibrated": False,
            "resourceLimitsCalibrated": False,
            "productionThresholdChangeAuthorized": False,
            "productionResourceLimitChangeAuthorized": False,
            "heldOutThresholdTuningUsed": False,
            "externalExportAuthorized": False,
            "modelTrainingAuthorized": False,
            "publicationAuthorized": False,
            "stage4ExitPass": False,
            "stage5EntryAuthorized": False,
        },
        "execution authorization assertions drifted or over-authorized downstream work",
    )
    _require(canonical_sha256(value) == AUTHORIZATION_CANONICAL_SHA256, "execution authorization canonical digest drifted")
    return value


def execution_authorized_for(
    authorization_raw: Mapping[str, Any],
    purpose_raw: Mapping[str, Any],
    acceptance_raw: Mapping[str, Any],
    completion_raw: Mapping[str, Any],
    *,
    dataset_item_id: str,
    artifact_sha256: str,
    source_family_id: str,
    execution_date: date | str,
    environment: str = "stage1_offline",
) -> bool:
    """Return True only for an exact item in the accepted development execution scope."""
    value = validate_stage4_execution_authorization(
        authorization_raw, purpose_raw, acceptance_raw, completion_raw
    )
    when = execution_date if isinstance(execution_date, date) else date.fromisoformat(execution_date)
    if when < date.fromisoformat(AUTHORIZED_ON) or environment != value["scope"]["environment"]:
        return False
    return any(
        item["datasetItemId"] == dataset_item_id
        and item["artifactSha256"] == artifact_sha256
        and item["sourceFamilyId"] == source_family_id
        for item in value["scope"]["datasetItems"]
    )


def summarize_stage4_execution_authorization(
    raw: Mapping[str, Any],
    purpose_raw: Mapping[str, Any],
    acceptance_raw: Mapping[str, Any],
    completion_raw: Mapping[str, Any],
) -> dict[str, Any]:
    value = validate_stage4_execution_authorization(raw, purpose_raw, acceptance_raw, completion_raw)
    return {
        "schemaVersion": AUTHORIZATION_SCHEMA_VERSION,
        "decision": AUTHORIZATION_DECISION,
        "authorizationDigest": {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "datasetItemCount": value["scope"]["datasetItemCount"],
        "referenceRecordCount": value["scope"]["referenceRecordCount"],
        "realDataCalibrationExecutionAuthorized": True,
        "heldOutEvaluationAuthorized": False,
        "heldOutTuningAuthorized": False,
        "productionThresholdChangeAuthorized": False,
        "productionResourceLimitChangeAuthorized": False,
        "stage4ExitPass": False,
        "stage5EntryAuthorized": False,
    }


__all__ = [
    "AUTHORIZATION_CANONICAL_SHA256", "AUTHORIZATION_DECISION", "AUTHORIZATION_ID",
    "AUTHORIZATION_SCHEMA_VERSION", "AUTHORIZED_ON", "DECISION_AUTHORITY_REFERENCE",
    "EXPECTED_SOURCE_FAMILIES", "Stage4ExecutionAuthorizationError", "execution_authorized_for",
    "summarize_stage4_execution_authorization", "validate_stage4_execution_authorization",
]
