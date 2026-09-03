"""Fail-closed Stage 4 metric acceptance-target policy candidate.

The current real development result derived zero threshold candidates. This
module therefore freezes a safety-first zero-candidate policy without inventing
numerical performance thresholds. Any future candidate-present mode requires a
separately versioned numerical-target addendum.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

SCHEMA_VERSION = "1.0.0"
POLICY_ID = "stage4.metric-acceptance-target-policy-candidate.v1"
POLICY_VERSION = "0.1.0"
POLICY_STATUS = "policy_candidate_pending_separate_acceptance"
POLICY_CANDIDATE_CANONICAL_SHA256 = "aed1b8964d2f08dffed34bf48c9339bb88249d6175b77ebe9b923c62595e557f"
PRODUCTION_MAIN_SHA = "7afec26402f0c9bf6fb9f8814089b74657f9ce5f"
DEVELOPMENT_ACCEPTANCE_DIGEST = "4b891f3263c542c59d5632732c8010ef1bc6aeba17dfd71ffbde9ee6ed7be396"
DEVELOPMENT_EXECUTION_DIGEST = "552a85a68dd789bd00dc4cb7ce6db38078a77c45297a7e5f716d008eae908b0c"
HELD_OUT_DATASET_ITEM_ID = "dataset.item.imslp82860-chopin-op69.v2"


class Stage4MetricPolicyError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "rejected",
            "error": {"code": self.code, "message": self.message},
        }


def _canonical_digest(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise Stage4MetricPolicyError(code, message)


def _require_hard_target(targets: Mapping[str, Any], name: str, expected: Any) -> None:
    entry = targets.get(name)
    _require(isinstance(entry, Mapping), "invalid_metric_target", f"{name} target must be an object.")
    _require(entry.get("operator") == "equal", "invalid_metric_target", f"{name} must use equality.")
    _require(entry.get("target") == expected, "invalid_metric_target", f"{name} target drifted.")
    _require(entry.get("hardSafetyRequirement") is True, "invalid_metric_target", f"{name} must be hard safety requirement.")


def validate_metric_acceptance_target_policy_candidate(raw: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(raw, Mapping), "invalid_policy", "Policy candidate must be an object.")
    _require(_canonical_digest(raw) == POLICY_CANDIDATE_CANONICAL_SHA256, "policy_digest_mismatch", "Committed policy candidate digest drifted.")
    _require(raw.get("schemaVersion") == SCHEMA_VERSION, "invalid_policy", "Schema version drifted.")
    _require(raw.get("policyId") == POLICY_ID, "invalid_policy", "Policy id drifted.")
    _require(raw.get("policyVersion") == POLICY_VERSION, "invalid_policy", "Policy version drifted.")
    _require(raw.get("status") == POLICY_STATUS, "invalid_policy", "Policy candidate status drifted.")

    basis = raw.get("basis")
    _require(isinstance(basis, Mapping), "invalid_policy", "basis must be an object.")
    _require(basis.get("productionMainSha") == PRODUCTION_MAIN_SHA, "basis_mismatch", "Production checkpoint drifted.")
    _require(basis.get("expandedDevelopmentExecutionAcceptanceDigest") == DEVELOPMENT_ACCEPTANCE_DIGEST, "basis_mismatch", "Development acceptance digest drifted.")
    _require(basis.get("expandedDevelopmentExecutionEvidenceDigest") == DEVELOPMENT_EXECUTION_DIGEST, "basis_mismatch", "Development execution digest drifted.")
    _require(basis.get("acceptedRealDevelopmentEvidenceCount") == 1, "basis_mismatch", "Exactly one accepted real development evidence bundle is required.")
    _require(basis.get("candidateDerivedCount") == 0, "candidate_state_mismatch", "This policy candidate is only valid for the zero-candidate development state.")
    _require(basis.get("productionConfigurationState") == "uncalibrated_engineering_defaults", "basis_mismatch", "Production configuration state drifted.")

    scope = raw.get("scope")
    _require(isinstance(scope, Mapping), "invalid_policy", "scope must be an object.")
    _require(scope.get("stage") == 4 and scope.get("purpose") == "safety_calibration", "scope_mismatch", "Stage/purpose mismatch.")
    _require(scope.get("appliesTo") == "held_out_evaluation_acceptance_review", "scope_mismatch", "Policy scope drifted.")
    _require(scope.get("heldOutDatasetItemId") == HELD_OUT_DATASET_ITEM_ID, "scope_mismatch", "Held-out identity drifted.")
    _require(scope.get("currentMode") == "zero_candidate_safe_abstention", "scope_mismatch", "Current mode drifted.")
    _require(scope.get("numericCandidateThresholdAcceptanceAuthorized") is False, "unsafe_policy", "Candidate threshold acceptance must remain unauthorized.")

    targets = raw.get("metricTargets")
    _require(isinstance(targets, Mapping), "invalid_policy", "metricTargets must be an object.")
    _require_hard_target(targets, "sourceFamilyLeakageCount", 0)
    _require_hard_target(targets, "heldOutThresholdTuningUsed", False)
    _require_hard_target(targets, "evaluationFedBackIntoCandidate", False)
    _require_hard_target(targets, "productionThresholdChangeAuthorized", False)
    _require_hard_target(targets, "productionResourceLimitChangeAuthorized", False)

    coverage = targets.get("coverageRate")
    not_assessed = targets.get("notAssessedRate")
    _require(isinstance(coverage, Mapping) and coverage.get("mode") == "zero_candidate_abstention_compatible" and coverage.get("numericMinimum") is None, "invented_numeric_target", "Coverage target must remain non-numeric for zero-candidate abstention.")
    _require(isinstance(not_assessed, Mapping) and not_assessed.get("mode") == "zero_candidate_abstention_compatible" and not_assessed.get("numericMaximum") is None, "invented_numeric_target", "notAssessed target must remain non-numeric for zero-candidate abstention.")
    for name, bound in (("exactMatchRate", "numericMinimum"), ("falseNegativeRate", "numericMaximum"), ("falsePositiveRate", "numericMaximum")):
        entry = targets.get(name)
        _require(isinstance(entry, Mapping) and entry.get("mode") == "not_applicable_when_zero_assessed" and entry.get(bound) is None, "invented_numeric_target", f"{name} must remain not-applicable when assessed count is zero.")

    rules = raw.get("decisionRules")
    _require(isinstance(rules, Mapping), "invalid_policy", "decisionRules must be an object.")
    zero = rules.get("zeroCandidateSafeAbstention")
    future = rules.get("candidatePresent")
    _require(isinstance(zero, Mapping), "invalid_policy", "zero-candidate rule missing.")
    _require(zero.get("requiredCurrentCandidateDerivedCount") == 0, "invalid_policy", "zero-candidate rule drifted.")
    _require(zero.get("requiresHeldOutEvaluationEvidence") is True, "invalid_policy", "Held-out evidence must remain required.")
    _require(zero.get("requiresSourceFamilyLeakageCount") == 0, "invalid_policy", "Leakage target drifted.")
    _require(zero.get("requiresHeldOutThresholdTuningUsed") is False and zero.get("requiresEvaluationFedBackIntoCandidate") is False, "unsafe_policy", "Held-out feedback/tuning must remain forbidden.")
    _require(zero.get("allowsZeroCoverage") is True and zero.get("allowsRateMetricsNotApplicableWhenAssessedCountZero") is True, "invalid_policy", "Safe abstention handling drifted.")
    _require(zero.get("decisionIfSatisfied") == "ELIGIBLE_FOR_SEPARATE_HELD_OUT_EVIDENCE_ACCEPTANCE_REVIEW", "unsafe_policy", "Policy must not self-accept held-out evidence.")
    _require(isinstance(future, Mapping), "invalid_policy", "candidate-present rule missing.")
    _require(future.get("whenCandidateDerivedCountGreaterThan") == 0, "invalid_policy", "Candidate-present trigger drifted.")
    _require(future.get("decision") == "BLOCK_PENDING_SEPARATE_NUMERIC_TARGET_ADDENDUM", "unsafe_policy", "Candidate-present mode must fail closed.")
    _require(future.get("numericTargetAddendumRequired") is True and future.get("automaticThresholdAcceptanceAuthorized") is False, "unsafe_policy", "Numerical target addendum boundary drifted.")

    assertions = raw.get("assertions")
    _require(isinstance(assertions, Mapping), "invalid_policy", "assertions must be an object.")
    _require(assertions.get("policyCandidateOnly") is True, "unsafe_policy", "Policy must remain candidate-only.")
    for key in (
        "metricAcceptanceTargetPolicyAccepted",
        "heldOutEvaluationAuthorized",
        "heldOutEvaluationUsed",
        "heldOutThresholdTuningAuthorized",
        "candidateThresholdsAccepted",
        "thresholdsCalibrated",
        "resourceLimitsCalibrated",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        _require(assertions.get(key) is False, "unsafe_policy", f"{key} must remain false in the candidate contract.")
    return dict(raw)


def summarize_metric_acceptance_target_policy_candidate(raw: Mapping[str, Any]) -> dict[str, Any]:
    value = validate_metric_acceptance_target_policy_candidate(raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "policyId": POLICY_ID,
        "policyVersion": POLICY_VERSION,
        "status": value["status"],
        "policyCandidateDigest": {"algorithm": "sha256", "value": POLICY_CANDIDATE_CANONICAL_SHA256},
        "currentMode": value["scope"]["currentMode"],
        "candidateDerivedCount": value["basis"]["candidateDerivedCount"],
        "metricAcceptanceTargetPolicyAccepted": False,
        "heldOutEvaluationAuthorized": False,
        "numericTargetAddendumRequiredIfCandidateAppears": True,
        "stage4ExitPass": False,
        "stage5EntryAuthorized": False,
    }
