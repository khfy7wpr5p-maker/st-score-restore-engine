"""Fail-closed Stage 4 expanded real development calibration authorization.

This contract authorizes development-only calibration execution for the exact
Beethoven + Barley + Wikimedia source set after both immutable real reference
bundles have been governance-accepted. It does not execute calibration, expose
private metrics, authorize held-out evaluation/tuning, change production
thresholds/resources, train or publish a model, grant Stage 4 PASS, or open
Stage 5.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage4_execution_authorization import EXPECTED_SOURCE_FAMILIES
from .stage4_purpose_grants import (
    APPROVED_GRANT_CANONICAL_SHA256,
    APPROVED_ITEMS,
    validate_stage4_purpose_grants,
)
from .stage4_reference_label_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256 as BEETHOVEN_BARLEY_ACCEPTANCE_SHA256,
    REFERENCE_RECEIPT_CANONICAL_SHA256 as BEETHOVEN_BARLEY_RECEIPT_SHA256,
    validate_reference_label_acceptance,
)
from .stage4_reference_label_completion import BUNDLE_CANONICAL_SHA256 as BEETHOVEN_BARLEY_BUNDLE_SHA256
from .stage4_wikimedia_reference_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256 as WIKIMEDIA_ACCEPTANCE_SHA256,
    REFERENCE_RECEIPT_CANONICAL_SHA256 as WIKIMEDIA_RECEIPT_SHA256,
    WIKIMEDIA_BUNDLE_CANONICAL_SHA256,
    validate_wikimedia_reference_acceptance,
)
from .stage4_wikimedia_reference_gate import (
    HELD_OUT_ITEM_ID,
    WIKIMEDIA_GRANT_DIGEST,
    WIKIMEDIA_ITEM_ID,
    WIKIMEDIA_SOURCE_FAMILY_ID,
)

AUTHORIZATION_SCHEMA_VERSION = "1.0.0"
AUTHORIZATION_ID = "stage4.real-development-calibration-execution-authorization.beethoven-barley-wikimedia.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_EXPANDED_REAL_DEVELOPMENT_CALIBRATION_EXECUTION"
AUTHORIZED_ON = "2026-09-03"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260903-03"
AUTHORIZATION_SOURCE_CODE = "explicit_user_authorization"
AUTHORIZATION_CANONICAL_SHA256 = "47027774b8f8258bcbe9ff633d58f9eb3e85edb4e83abf549facd778d6ecdad9"

WIKIMEDIA_ARTIFACT_SHA256 = "36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb"
EXPECTED_ITEMS = {
    **{
        item_id: {
            "artifactSha256": artifact_sha,
            "sourceFamilyId": EXPECTED_SOURCE_FAMILIES[item_id],
        }
        for item_id, artifact_sha in APPROVED_ITEMS.items()
    },
    WIKIMEDIA_ITEM_ID: {
        "artifactSha256": WIKIMEDIA_ARTIFACT_SHA256,
        "sourceFamilyId": WIKIMEDIA_SOURCE_FAMILY_ID,
    },
}


class Stage4WikimediaExpandedExecutionAuthorizationError(ValueError):
    """Expanded execution authorization is malformed, unbound, or over-scoped."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4WikimediaExpandedExecutionAuthorizationError(message)


def validate_wikimedia_expanded_execution_authorization(
    raw: Mapping[str, Any],
    beethoven_barley_purpose_raw: Mapping[str, Any],
    beethoven_barley_acceptance_raw: Mapping[str, Any],
    beethoven_barley_completion_raw: Mapping[str, Any],
    wikimedia_purpose_raw: Mapping[str, Any],
    wikimedia_acceptance_raw: Mapping[str, Any],
    wikimedia_completion_raw: Mapping[str, Any],
    wikimedia_work_package_raw: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise Stage4WikimediaExpandedExecutionAuthorizationError("expanded execution authorization must be an object")
    value = deepcopy(dict(raw))

    beethoven_barley_purpose = validate_stage4_purpose_grants(beethoven_barley_purpose_raw)
    _require(
        canonical_sha256(beethoven_barley_purpose) == APPROVED_GRANT_CANONICAL_SHA256,
        "Beethoven+Barley purpose-grant digest drifted",
    )
    beethoven_barley_acceptance = validate_reference_label_acceptance(
        beethoven_barley_acceptance_raw, beethoven_barley_completion_raw
    )
    _require(
        canonical_sha256(beethoven_barley_acceptance) == BEETHOVEN_BARLEY_ACCEPTANCE_SHA256,
        "Beethoven+Barley reference acceptance digest drifted",
    )
    _require(
        beethoven_barley_acceptance.get("assertions", {}).get("referenceBundleAccepted") is True,
        "Beethoven+Barley reference bundle is not accepted",
    )

    _require(isinstance(wikimedia_purpose_raw, Mapping), "Wikimedia purpose grant must be an object")
    _require(
        canonical_sha256(dict(wikimedia_purpose_raw)) == WIKIMEDIA_GRANT_DIGEST,
        "Wikimedia purpose-grant digest drifted",
    )
    wikimedia_acceptance = validate_wikimedia_reference_acceptance(
        wikimedia_acceptance_raw, wikimedia_completion_raw, wikimedia_work_package_raw
    )
    _require(
        canonical_sha256(wikimedia_acceptance) == WIKIMEDIA_ACCEPTANCE_SHA256,
        "Wikimedia reference acceptance digest drifted",
    )
    _require(
        wikimedia_acceptance.get("assertions", {}).get("referenceBundleAccepted") is True,
        "Wikimedia reference bundle is not accepted",
    )
    _require(
        wikimedia_acceptance.get("assertions", {}).get("realDataCalibrationExecutionAuthorized") is False,
        "historical Wikimedia acceptance must remain immutable and non-authorizing",
    )

    _require(
        set(value) == {
            "schemaVersion", "authorizationId", "decision", "authorizedOn",
            "decisionAuthorityReference", "authorizationSourceCode", "purposeGrantDigests",
            "referenceBundleAcceptanceDigests", "acceptedReferenceReceiptDigests",
            "referenceBundleDigests", "scope", "assertions"
        },
        "expanded execution authorization top-level fields drifted",
    )
    _require(value["schemaVersion"] == AUTHORIZATION_SCHEMA_VERSION, "expanded authorization schema drifted")
    _require(value["authorizationId"] == AUTHORIZATION_ID, "expanded authorization id drifted")
    _require(value["decision"] == AUTHORIZATION_DECISION, "expanded development calibration execution is not explicitly authorized")
    _require(value["authorizedOn"] == AUTHORIZED_ON, "expanded authorization date drifted")
    _require(value["decisionAuthorityReference"] == DECISION_AUTHORITY_REFERENCE, "expanded decision authority drifted")
    _require(value["authorizationSourceCode"] == AUTHORIZATION_SOURCE_CODE, "expanded authorization source drifted")

    _require(
        value["purposeGrantDigests"] == {
            "beethovenBarley": {"algorithm": "sha256", "value": APPROVED_GRANT_CANONICAL_SHA256},
            "wikimedia": {"algorithm": "sha256", "value": WIKIMEDIA_GRANT_DIGEST},
        },
        "expanded purpose-grant bindings drifted",
    )
    _require(
        value["referenceBundleAcceptanceDigests"] == {
            "beethovenBarley": {"algorithm": "sha256", "value": BEETHOVEN_BARLEY_ACCEPTANCE_SHA256},
            "wikimedia": {"algorithm": "sha256", "value": WIKIMEDIA_ACCEPTANCE_SHA256},
        },
        "expanded reference-acceptance bindings drifted",
    )
    _require(
        value["acceptedReferenceReceiptDigests"] == {
            "beethovenBarley": {"algorithm": "sha256", "value": BEETHOVEN_BARLEY_RECEIPT_SHA256},
            "wikimedia": {"algorithm": "sha256", "value": WIKIMEDIA_RECEIPT_SHA256},
        },
        "expanded accepted-reference receipt bindings drifted",
    )
    _require(
        value["referenceBundleDigests"] == {
            "beethovenBarley": {"algorithm": "sha256", "value": BEETHOVEN_BARLEY_BUNDLE_SHA256},
            "wikimedia": {"algorithm": "sha256", "value": WIKIMEDIA_BUNDLE_CANONICAL_SHA256},
        },
        "expanded reference-bundle bindings drifted",
    )

    scope = value["scope"]
    _require(isinstance(scope, dict), "expanded execution scope must be an object")
    _require(
        set(scope) == {
            "split", "dataClass", "purpose", "environment", "storageClass",
            "datasetItemCount", "sourceFamilyCount", "referenceRecordCount", "datasetItems",
            "candidateDerivationAuthorized", "developmentEvaluationAuthorized", "heldOutIncluded",
            "heldOutEvaluationAuthorized", "heldOutTuningAuthorized", "privateObservationMetricsRequired",
            "rawObservationMetricsAllowedInOrdinaryGit"
        },
        "expanded execution scope fields drifted",
    )
    _require(scope["split"] == "development", "expanded execution must remain development-only")
    _require(scope["dataClass"] == "real", "expanded execution must remain real-data scoped")
    _require(scope["purpose"] == "safety_calibration", "expanded execution purpose drifted")
    _require(scope["environment"] == "stage1_offline", "expanded execution environment drifted")
    _require(scope["storageClass"] == "managed_standard", "expanded execution storage class drifted")
    _require(scope["datasetItemCount"] == 3, "expanded execution must bind exactly three development items")
    _require(scope["sourceFamilyCount"] == 3, "expanded execution must bind exactly three source families")
    _require(scope["referenceRecordCount"] == 49, "expanded execution must bind exactly 49 human reference records")

    items = scope["datasetItems"]
    _require(isinstance(items, list) and len(items) == 3, "expanded execution item list drifted")
    seen: set[str] = set()
    for item in items:
        _require(isinstance(item, dict), "expanded execution item must be an object")
        _require(set(item) == {"datasetItemId", "artifactSha256", "sourceFamilyId"}, "expanded execution item fields drifted")
        item_id = item["datasetItemId"]
        _require(item_id in EXPECTED_ITEMS and item_id not in seen, f"unapproved or duplicate expanded execution item: {item_id}")
        seen.add(item_id)
        expected = EXPECTED_ITEMS[item_id]
        _require(item["artifactSha256"] == expected["artifactSha256"], f"artifact SHA drifted for {item_id}")
        _require(item["sourceFamilyId"] == expected["sourceFamilyId"], f"source-family binding drifted for {item_id}")
    _require(seen == set(EXPECTED_ITEMS), "expanded execution exact development item set drifted")
    _require(HELD_OUT_ITEM_ID not in seen, "held-out Chopin entered expanded development execution scope")

    _require(scope["candidateDerivationAuthorized"] is True, "expanded candidate derivation is not authorized")
    _require(scope["developmentEvaluationAuthorized"] is True, "expanded development evaluation is not authorized")
    _require(scope["heldOutIncluded"] is False, "held-out data entered expanded development execution scope")
    _require(scope["heldOutEvaluationAuthorized"] is False, "held-out evaluation was prematurely authorized")
    _require(scope["heldOutTuningAuthorized"] is False, "held-out tuning was authorized")
    _require(scope["privateObservationMetricsRequired"] is True, "private observation metrics are not required")
    _require(scope["rawObservationMetricsAllowedInOrdinaryGit"] is False, "raw observation metrics were allowed in ordinary Git")

    _require(
        value["assertions"] == {
            "safetyCalibrationPurposeGranted": True,
            "referenceBundlesAccepted": True,
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
        "expanded authorization assertions drifted or over-authorized downstream work",
    )
    _require(canonical_sha256(value) == AUTHORIZATION_CANONICAL_SHA256, "expanded authorization canonical digest drifted")
    return value


def expanded_execution_authorized_for(
    authorization_raw: Mapping[str, Any],
    beethoven_barley_purpose_raw: Mapping[str, Any],
    beethoven_barley_acceptance_raw: Mapping[str, Any],
    beethoven_barley_completion_raw: Mapping[str, Any],
    wikimedia_purpose_raw: Mapping[str, Any],
    wikimedia_acceptance_raw: Mapping[str, Any],
    wikimedia_completion_raw: Mapping[str, Any],
    wikimedia_work_package_raw: Mapping[str, Any],
    *,
    dataset_item_id: str,
    artifact_sha256: str,
    source_family_id: str,
    execution_date: date | str,
    environment: str = "stage1_offline",
) -> bool:
    value = validate_wikimedia_expanded_execution_authorization(
        authorization_raw,
        beethoven_barley_purpose_raw,
        beethoven_barley_acceptance_raw,
        beethoven_barley_completion_raw,
        wikimedia_purpose_raw,
        wikimedia_acceptance_raw,
        wikimedia_completion_raw,
        wikimedia_work_package_raw,
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


def summarize_wikimedia_expanded_execution_authorization(
    raw: Mapping[str, Any],
    beethoven_barley_purpose_raw: Mapping[str, Any],
    beethoven_barley_acceptance_raw: Mapping[str, Any],
    beethoven_barley_completion_raw: Mapping[str, Any],
    wikimedia_purpose_raw: Mapping[str, Any],
    wikimedia_acceptance_raw: Mapping[str, Any],
    wikimedia_completion_raw: Mapping[str, Any],
    wikimedia_work_package_raw: Mapping[str, Any],
) -> dict[str, Any]:
    value = validate_wikimedia_expanded_execution_authorization(
        raw,
        beethoven_barley_purpose_raw,
        beethoven_barley_acceptance_raw,
        beethoven_barley_completion_raw,
        wikimedia_purpose_raw,
        wikimedia_acceptance_raw,
        wikimedia_completion_raw,
        wikimedia_work_package_raw,
    )
    return {
        "schemaVersion": AUTHORIZATION_SCHEMA_VERSION,
        "decision": AUTHORIZATION_DECISION,
        "authorizationDigest": {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "datasetItemCount": value["scope"]["datasetItemCount"],
        "sourceFamilyCount": value["scope"]["sourceFamilyCount"],
        "referenceRecordCount": value["scope"]["referenceRecordCount"],
        "realDataCalibrationExecutionAuthorized": True,
        "realDataCalibrationExecuted": False,
        "heldOutEvaluationAuthorized": False,
        "heldOutTuningAuthorized": False,
        "productionThresholdChangeAuthorized": False,
        "productionResourceLimitChangeAuthorized": False,
        "stage4ExitPass": False,
        "stage5EntryAuthorized": False,
    }


__all__ = [
    "AUTHORIZATION_CANONICAL_SHA256",
    "AUTHORIZATION_DECISION",
    "AUTHORIZATION_ID",
    "AUTHORIZATION_SCHEMA_VERSION",
    "AUTHORIZATION_SOURCE_CODE",
    "AUTHORIZED_ON",
    "DECISION_AUTHORITY_REFERENCE",
    "EXPECTED_ITEMS",
    "Stage4WikimediaExpandedExecutionAuthorizationError",
    "WIKIMEDIA_ARTIFACT_SHA256",
    "expanded_execution_authorized_for",
    "summarize_wikimedia_expanded_execution_authorization",
    "validate_wikimedia_expanded_execution_authorization",
]
