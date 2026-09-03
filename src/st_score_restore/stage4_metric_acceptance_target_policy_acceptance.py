"""Fail-closed acceptance for the Stage 4 metric acceptance-target policy candidate.

This gate accepts only the exact zero-candidate safe-abstention policy candidate.
It resolves the metric-policy readiness prerequisite, but it does not authorize
held-out evaluation/tuning, accept threshold candidates, calibrate thresholds or
resources, grant Stage 4 PASS, or open Stage 5.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Mapping

from .stage4_metric_acceptance_target_policy import (
    HELD_OUT_DATASET_ITEM_ID,
    POLICY_CANDIDATE_CANONICAL_SHA256,
    POLICY_ID,
    POLICY_VERSION,
    validate_metric_acceptance_target_policy_candidate,
)

SCHEMA_VERSION = "1.0.0"
ACCEPTANCE_ID = "stage4.metric-acceptance-target-policy-acceptance.v1"
ACCEPTANCE_DECISION = "ACCEPT_STAGE4_METRIC_ACCEPTANCE_TARGET_POLICY"
ACCEPTED_ON = "2026-09-03"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260903-05"
ACCEPTANCE_SOURCE_CODE = "explicit_user_authorization"
ACCEPTANCE_CANONICAL_SHA256 = "bf62d308f70ca44db617cf2968485e422627abfce70643c78b4da20d58d04801"


class Stage4MetricPolicyAcceptanceError(ValueError):
    pass


def _canonical_digest(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4MetricPolicyAcceptanceError(message)


def validate_metric_acceptance_target_policy_acceptance(
    raw: Mapping[str, Any], policy_candidate_raw: Mapping[str, Any]
) -> dict[str, Any]:
    _require(isinstance(raw, Mapping), "metric-policy acceptance must be an object")
    candidate = validate_metric_acceptance_target_policy_candidate(policy_candidate_raw)
    _require(candidate.get("status") == "policy_candidate_pending_separate_acceptance", "historical candidate status drifted")
    _require(candidate.get("assertions", {}).get("metricAcceptanceTargetPolicyAccepted") is False, "historical candidate was retroactively accepted")

    value = deepcopy(dict(raw))
    _require(_canonical_digest(value) == ACCEPTANCE_CANONICAL_SHA256, "acceptance canonical digest drifted")
    _require(value.get("schemaVersion") == SCHEMA_VERSION, "acceptance schema drifted")
    _require(value.get("acceptanceId") == ACCEPTANCE_ID, "acceptance id drifted")
    _require(value.get("decision") == ACCEPTANCE_DECISION, "policy candidate is not explicitly accepted")
    _require(value.get("acceptedOn") == ACCEPTED_ON, "acceptance date drifted")
    _require(value.get("decisionAuthorityReference") == DECISION_AUTHORITY_REFERENCE, "decision authority drifted")
    _require(value.get("acceptanceSourceCode") == ACCEPTANCE_SOURCE_CODE, "acceptance source drifted")
    _require(
        value.get("policyCandidateDigest") == {"algorithm": "sha256", "value": POLICY_CANDIDATE_CANONICAL_SHA256},
        "policy candidate digest binding drifted",
    )
    _require(value.get("policyId") == POLICY_ID and value.get("policyVersion") == POLICY_VERSION, "policy identity drifted")

    _require(
        value.get("scope") == {
            "stage": 4,
            "purpose": "safety_calibration",
            "appliesTo": "held_out_evaluation_acceptance_review",
            "heldOutDatasetItemId": HELD_OUT_DATASET_ITEM_ID,
            "currentMode": "zero_candidate_safe_abstention",
            "numericCandidateThresholdAcceptanceAuthorized": False,
        },
        "policy acceptance scope drifted or over-authorized",
    )
    _require(
        value.get("acceptedTargets") == {
            "sourceFamilyLeakageCount": 0,
            "heldOutThresholdTuningUsed": False,
            "evaluationFedBackIntoCandidate": False,
            "productionThresholdChangeAuthorized": False,
            "productionResourceLimitChangeAuthorized": False,
            "zeroCandidateCoverageMayBeZero": True,
            "rateMetricsNotApplicableWhenAssessedCountZero": True,
        },
        "accepted safety targets drifted",
    )
    _require(
        value.get("futureCandidatePolicy") == {
            "whenCandidateDerivedCountGreaterThan": 0,
            "decision": "BLOCK_PENDING_SEPARATE_NUMERIC_TARGET_ADDENDUM",
            "numericTargetAddendumRequired": True,
            "automaticThresholdAcceptanceAuthorized": False,
        },
        "future candidate fail-closed boundary drifted",
    )
    _require(
        value.get("assertions") == {
            "metricAcceptanceTargetPolicyAccepted": True,
            "zeroCandidateSafeAbstentionPolicyAccepted": True,
            "inventedNumericPerformanceTargetsAllowed": False,
            "heldOutEvaluationAuthorized": False,
            "heldOutEvaluationUsed": False,
            "heldOutThresholdTuningAuthorized": False,
            "heldOutThresholdTuningUsed": False,
            "candidateThresholdsAccepted": False,
            "thresholdsCalibrated": False,
            "resourceLimitsCalibrated": False,
            "productionThresholdChangeAuthorized": False,
            "productionResourceLimitChangeAuthorized": False,
            "stage4ExitPass": False,
            "stage5EntryAuthorized": False,
        },
        "acceptance assertions drifted or opened a downstream gate",
    )
    return value


def summarize_metric_acceptance_target_policy_acceptance(
    raw: Mapping[str, Any], policy_candidate_raw: Mapping[str, Any]
) -> dict[str, Any]:
    validate_metric_acceptance_target_policy_acceptance(raw, policy_candidate_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "decision": ACCEPTANCE_DECISION,
        "acceptanceDigest": {"algorithm": "sha256", "value": ACCEPTANCE_CANONICAL_SHA256},
        "policyCandidateDigest": {"algorithm": "sha256", "value": POLICY_CANDIDATE_CANONICAL_SHA256},
        "metricAcceptanceTargetPolicyAccepted": True,
        "remainingReadinessBlockers": ["no_real_held_out_evaluation_evidence_is_accepted"],
        "heldOutEvaluationAuthorized": False,
        "stage4ExitPass": False,
        "stage5EntryAuthorized": False,
    }


__all__ = [
    "ACCEPTANCE_CANONICAL_SHA256",
    "ACCEPTANCE_DECISION",
    "ACCEPTANCE_ID",
    "ACCEPTED_ON",
    "DECISION_AUTHORITY_REFERENCE",
    "Stage4MetricPolicyAcceptanceError",
    "summarize_metric_acceptance_target_policy_acceptance",
    "validate_metric_acceptance_target_policy_acceptance",
]
