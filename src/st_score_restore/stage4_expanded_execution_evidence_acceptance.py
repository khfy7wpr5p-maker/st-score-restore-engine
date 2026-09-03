"""Fail-closed acceptance for real expanded Stage 4 development execution evidence.

This module accepts the exact already-executed Beethoven + Barley + Wikimedia
public-safe development execution evidence. Acceptance validates the execution
and its abstention outcome as real development evidence. It does not calibrate
thresholds/resources, accept candidate thresholds, authorize or use held-out
evaluation/tuning, apply a metric acceptance target policy, grant Stage 4 PASS,
or open Stage 5.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage4_expanded_real_development_execution_evidence import (
    EVIDENCE_CANONICAL_SHA256,
    PRIVATE_METRIC_BATCH_SHA256,
    validate_expanded_real_development_execution_evidence,
)
from .stage4_wikimedia_expanded_execution_authorization import AUTHORIZATION_CANONICAL_SHA256

ACCEPTANCE_SCHEMA_VERSION = "1.0.0"
ACCEPTANCE_ID = "stage4.expanded-real-development-execution-evidence-acceptance.v1"
ACCEPTANCE_DECISION = "ACCEPT_EXPANDED_REAL_DEVELOPMENT_EXECUTION_EVIDENCE"
ACCEPTED_ON = "2026-09-03"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260903-04"
ACCEPTANCE_SOURCE_CODE = "explicit_user_authorization"
ACCEPTANCE_CANONICAL_SHA256 = "4b891f3263c542c59d5632732c8010ef1bc6aeba17dfd71ffbde9ee6ed7be396"


class Stage4ExpandedExecutionEvidenceAcceptanceError(ValueError):
    """Expanded execution-evidence acceptance is malformed or over-authorizing."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4ExpandedExecutionEvidenceAcceptanceError(message)


def validate_expanded_execution_evidence_acceptance(
    raw: Mapping[str, Any], execution_evidence_raw: Mapping[str, Any]
) -> dict[str, Any]:
    _require(isinstance(raw, Mapping), "expanded execution acceptance must be an object")
    evidence = validate_expanded_real_development_execution_evidence(execution_evidence_raw)
    _require(
        evidence.get("evidenceDigest") == {"algorithm": "sha256", "value": EVIDENCE_CANONICAL_SHA256},
        "expanded execution evidence digest drifted",
    )
    _require(
        evidence.get("assertions", {}).get("executionEvidenceAccepted") is False,
        "historical execution evidence must remain immutable and unaccepted",
    )
    _require(evidence.get("summary", {}).get("candidateDerivedCount") == 0, "execution candidate count drifted")
    _require(evidence.get("summary", {}).get("thresholdsCalibrated") is False, "execution evidence unexpectedly calibrated thresholds")

    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schemaVersion",
            "acceptanceId",
            "decision",
            "acceptedOn",
            "decisionAuthorityReference",
            "acceptanceSourceCode",
            "executionEvidenceDigest",
            "privateMetricBatchDigest",
            "executionAuthorizationDigest",
            "scope",
            "assertions",
        },
        "expanded execution acceptance top-level fields drifted",
    )
    _require(value["schemaVersion"] == ACCEPTANCE_SCHEMA_VERSION, "acceptance schema drifted")
    _require(value["acceptanceId"] == ACCEPTANCE_ID, "acceptance id drifted")
    _require(value["decision"] == ACCEPTANCE_DECISION, "expanded execution evidence is not explicitly accepted")
    _require(value["acceptedOn"] == ACCEPTED_ON, "acceptance date drifted")
    _require(value["decisionAuthorityReference"] == DECISION_AUTHORITY_REFERENCE, "decision authority drifted")
    _require(value["acceptanceSourceCode"] == ACCEPTANCE_SOURCE_CODE, "acceptance source drifted")
    _require(
        value["executionEvidenceDigest"] == {"algorithm": "sha256", "value": EVIDENCE_CANONICAL_SHA256},
        "execution evidence binding drifted",
    )
    _require(
        value["privateMetricBatchDigest"] == {"algorithm": "sha256", "value": PRIVATE_METRIC_BATCH_SHA256},
        "private metric batch binding drifted",
    )
    _require(
        value["executionAuthorizationDigest"] == {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "execution authorization binding drifted",
    )

    _require(
        value["scope"] == {
            "purpose": "safety_calibration",
            "split": "development",
            "dataClass": "real",
            "executionState": "executed_abstained",
            "referenceRecordCount": 49,
            "privateMetricRecordCount": 49,
            "measuredRecordCount": 30,
            "notApplicableRecordCount": 19,
            "measuredSourceFamilyCount": 2,
            "candidateDerivedCount": 0,
            "abstainedFindingCount": 6,
            "notApplicableFindingCount": 1,
            "heldOutIncluded": False,
        },
        "acceptance scope drifted or became unsafe",
    )
    _require(
        value["assertions"] == {
            "executionEvidenceAccepted": True,
            "realDataCalibrationExecuted": True,
            "developmentEvidenceOnly": True,
            "thresholdsCalibrated": False,
            "resourceLimitsCalibrated": False,
            "candidateThresholdsAccepted": False,
            "heldOutEvaluationAuthorized": False,
            "heldOutEvaluationUsed": False,
            "heldOutThresholdTuningUsed": False,
            "metricAcceptanceTargetPolicyApplied": False,
            "productionThresholdChangeAuthorized": False,
            "productionResourceLimitChangeAuthorized": False,
            "modelTrainingAuthorized": False,
            "publicationAuthorized": False,
            "stage4ExitPass": False,
            "stage5EntryAuthorized": False,
        },
        "acceptance assertions drifted or over-authorized downstream work",
    )
    _require(canonical_sha256(value) == ACCEPTANCE_CANONICAL_SHA256, "acceptance canonical digest drifted")

    rendered = str(value)
    for forbidden in ("rawValue", "observationId", "possibleThreshold", "probableThreshold", "candidateManifest"):
        _require(forbidden not in rendered, f"acceptance leaked forbidden private/candidate field: {forbidden}")
    return value


def summarize_expanded_execution_evidence_acceptance(
    raw: Mapping[str, Any], execution_evidence_raw: Mapping[str, Any]
) -> dict[str, Any]:
    value = validate_expanded_execution_evidence_acceptance(raw, execution_evidence_raw)
    return {
        "schemaVersion": ACCEPTANCE_SCHEMA_VERSION,
        "decision": ACCEPTANCE_DECISION,
        "acceptanceDigest": {"algorithm": "sha256", "value": ACCEPTANCE_CANONICAL_SHA256},
        "executionEvidenceDigest": value["executionEvidenceDigest"],
        "executionEvidenceAccepted": True,
        "candidateDerivedCount": 0,
        "thresholdsCalibrated": False,
        "heldOutEvaluationAuthorized": False,
        "metricAcceptanceTargetPolicyApplied": False,
        "stage4ExitPass": False,
        "stage5EntryAuthorized": False,
    }


__all__ = [
    "ACCEPTANCE_CANONICAL_SHA256",
    "ACCEPTANCE_DECISION",
    "ACCEPTANCE_ID",
    "ACCEPTANCE_SCHEMA_VERSION",
    "ACCEPTANCE_SOURCE_CODE",
    "ACCEPTED_ON",
    "DECISION_AUTHORITY_REFERENCE",
    "Stage4ExpandedExecutionEvidenceAcceptanceError",
    "summarize_expanded_execution_evidence_acceptance",
    "validate_expanded_execution_evidence_acceptance",
]
