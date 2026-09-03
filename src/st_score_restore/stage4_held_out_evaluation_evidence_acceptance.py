"""Fail-closed acceptance for the exact Stage 4 Chopin held-out evidence candidate.

This module accepts the already-bridged real held-out evaluation evidence in
zero-candidate safe-abstention mode. It validates all upstream bindings and
then permits only READY_FOR_FINAL_ACCEPTANCE_REVIEW. It never grants Stage 4
PASS, Stage 5 entry, threshold/resource changes, model training, publication,
held-out tuning, or feedback into candidate derivation.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage4_exit_readiness import Stage4ReadinessInput, evaluate_stage4_exit_readiness
from .stage4_held_out_evaluation_evidence import (
    AUTHORIZATION_CANONICAL_SHA256,
    EVIDENCE_CANONICAL_SHA256,
    HELD_OUT_ARTIFACT_SHA256,
    HELD_OUT_DATASET_ITEM_ID,
    HELD_OUT_SOURCE_FAMILY_ID,
    STAGE3_HELD_OUT_RECEIPT_DIGEST,
    DEVELOPMENT_EXECUTION_ACCEPTANCE_DIGEST,
    METRIC_POLICY_ACCEPTANCE_DIGEST,
    validate_held_out_evaluation_evidence_candidate,
)

SCHEMA_VERSION = "1.0.0"
ACCEPTANCE_ID = "stage4.held-out-evaluation-evidence-acceptance.chopin-op69.v1"
ACCEPTANCE_DECISION = "ACCEPT_STAGE4_HELD_OUT_EVALUATION_EVIDENCE"
ACCEPTED_ON = "2026-09-03"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260903-07"
ACCEPTANCE_SOURCE_CODE = "explicit_user_authorization"
ACCEPTANCE_CANONICAL_SHA256 = "ff0bdcb8820ba774cebc46265eb36ee0278b591a316ca619d2540d06d3a45164"
POST_ACCEPTANCE_READINESS_DIGEST = "8b31b0dc92d931fa9e7b56a7912ecd1127e74ad0672d03d50526160936a32d0b"


class Stage4HeldOutEvaluationEvidenceAcceptanceError(ValueError):
    """Held-out evidence acceptance is malformed, stale, or over-authorizing."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4HeldOutEvaluationEvidenceAcceptanceError(message)


def _post_acceptance_readiness() -> dict[str, Any]:
    result = evaluate_stage4_exit_readiness(
        Stage4ReadinessInput(
            safety_calibration_artifact_count=3,
            accepted_real_reference_bundle_count=2,
            accepted_real_development_evidence_count=1,
            accepted_real_held_out_evaluation_evidence_count=1,
            accepted_metric_target_policy=True,
            held_out_tuning_used=False,
            source_family_leakage_count=0,
            historical_evidence_immutable=True,
            real_or_derivative_bytes_in_ordinary_git=False,
            production_threshold_change_authorized=False,
            production_resource_limit_change_authorized=False,
        )
    )
    _require(result.get("decision") == "READY_FOR_FINAL_ACCEPTANCE_REVIEW", "post-acceptance readiness is not review-ready")
    _require(result.get("blockerCodes") == [], "post-acceptance readiness still has blockers")
    _require(result.get("blockerCount") == 0, "post-acceptance blocker count is not zero")
    assertions = result.get("assertions", {})
    _require(assertions.get("readinessPrerequisitesSatisfied") is True, "readiness prerequisites are not satisfied")
    _require(assertions.get("finalGovernanceAcceptanceStillRequired") is True, "final governance acceptance requirement disappeared")
    _require(assertions.get("stage4ExitPass") is False, "readiness self-authorized Stage 4 PASS")
    _require(assertions.get("stage5EntryAuthorized") is False, "readiness self-authorized Stage 5")
    _require(
        result.get("readinessDigest") == {"algorithm": "sha256", "value": POST_ACCEPTANCE_READINESS_DIGEST},
        "post-acceptance readiness digest drifted",
    )
    return result


def validate_held_out_evaluation_evidence_acceptance(
    raw: Mapping[str, Any],
    evidence_candidate_raw: Mapping[str, Any],
    review_authorization_raw: Mapping[str, Any],
    stage3_execution_raw: Mapping[str, Any],
    stage3_exit_acceptance_raw: Mapping[str, Any],
    development_acceptance_raw: Mapping[str, Any],
    metric_policy_acceptance_raw: Mapping[str, Any],
) -> dict[str, Any]:
    evidence = validate_held_out_evaluation_evidence_candidate(
        evidence_candidate_raw,
        review_authorization_raw,
        stage3_execution_raw,
        stage3_exit_acceptance_raw,
        development_acceptance_raw,
        metric_policy_acceptance_raw,
    )
    _require(evidence.get("state") == "ready_pending_separate_acceptance", "held-out evidence candidate state drifted")
    _require(evidence.get("assertions", {}).get("heldOutEvaluationEvidenceAccepted") is False, "historical candidate was rewritten as accepted")

    _require(isinstance(raw, Mapping), "held-out evidence acceptance must be an object")
    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schemaVersion",
            "acceptanceId",
            "decision",
            "acceptedOn",
            "decisionAuthorityReference",
            "acceptanceSourceCode",
            "heldOutEvaluationEvidenceDigest",
            "reviewAuthorizationDigest",
            "stage3HeldOutReceiptDigest",
            "stage4ExpandedDevelopmentExecutionAcceptanceDigest",
            "stage4MetricPolicyAcceptanceDigest",
            "scope",
            "assertions",
        },
        "held-out evidence acceptance top-level fields drifted",
    )
    _require(value["schemaVersion"] == SCHEMA_VERSION, "acceptance schema drifted")
    _require(value["acceptanceId"] == ACCEPTANCE_ID, "acceptance id drifted")
    _require(value["decision"] == ACCEPTANCE_DECISION, "held-out evaluation evidence is not explicitly accepted")
    _require(value["acceptedOn"] == ACCEPTED_ON, "acceptance date drifted")
    _require(value["decisionAuthorityReference"] == DECISION_AUTHORITY_REFERENCE, "decision authority drifted")
    _require(value["acceptanceSourceCode"] == ACCEPTANCE_SOURCE_CODE, "acceptance source drifted")
    _require(
        value["heldOutEvaluationEvidenceDigest"] == {"algorithm": "sha256", "value": EVIDENCE_CANONICAL_SHA256},
        "held-out evidence binding drifted",
    )
    _require(
        value["reviewAuthorizationDigest"] == {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "held-out review authorization binding drifted",
    )
    _require(
        value["stage3HeldOutReceiptDigest"] == {"algorithm": "sha256", "value": STAGE3_HELD_OUT_RECEIPT_DIGEST},
        "Stage 3 held-out receipt binding drifted",
    )
    _require(
        value["stage4ExpandedDevelopmentExecutionAcceptanceDigest"]
        == {"algorithm": "sha256", "value": DEVELOPMENT_EXECUTION_ACCEPTANCE_DIGEST},
        "development evidence acceptance binding drifted",
    )
    _require(
        value["stage4MetricPolicyAcceptanceDigest"]
        == {"algorithm": "sha256", "value": METRIC_POLICY_ACCEPTANCE_DIGEST},
        "metric-policy acceptance binding drifted",
    )

    expected_scope = {
        "stage": 4,
        "datasetItemId": HELD_OUT_DATASET_ITEM_ID,
        "sourceFamilyId": HELD_OUT_SOURCE_FAMILY_ID,
        "artifactSha256": HELD_OUT_ARTIFACT_SHA256,
        "split": "held_out",
        "purpose": "held_out_evaluation",
        "mode": "zero_candidate_safe_abstention",
        "realExecutionState": "previously_completed_stage3",
        "candidateDerivedCount": 0,
        "candidateAppliedCount": 0,
        "assessedCandidateCount": 0,
        "coverageRate": 0.0,
        "notAssessedRate": "not_applicable",
        "exactMatchRate": "not_applicable",
        "falseNegativeRate": "not_applicable",
        "falsePositiveRate": "not_applicable",
        "sourceFamilyLeakageCount": 0,
        "heldOutThresholdTuningUsed": False,
        "evaluationFedBackIntoCandidate": False,
    }
    _require(value["scope"] == expected_scope, "held-out acceptance scope drifted or became unsafe")

    expected_assertions = {
        "heldOutEvaluationEvidenceAccepted": True,
        "realHeldOutArtifactPreviouslyExecuted": True,
        "historicalEvidenceRewritten": False,
        "newHeldOutArtifactExecutionPerformed": False,
        "rateMetricsNotApplicableWhenAssessedCountZero": True,
        "candidateThresholdsAccepted": False,
        "thresholdsCalibrated": False,
        "resourceLimitsCalibrated": False,
        "productionThresholdChangeAuthorized": False,
        "productionResourceLimitChangeAuthorized": False,
        "modelTrainingAuthorized": False,
        "publicationAuthorized": False,
        "finalGovernanceAcceptanceStillRequired": True,
        "stage4ExitPass": False,
        "stage5EntryAuthorized": False,
    }
    _require(value["assertions"] == expected_assertions, "held-out acceptance assertions drifted or over-authorized downstream work")
    _require(canonical_sha256(value) == ACCEPTANCE_CANONICAL_SHA256, "held-out acceptance canonical digest drifted")

    _post_acceptance_readiness()
    return value


def summarize_held_out_evaluation_evidence_acceptance(
    raw: Mapping[str, Any],
    evidence_candidate_raw: Mapping[str, Any],
    review_authorization_raw: Mapping[str, Any],
    stage3_execution_raw: Mapping[str, Any],
    stage3_exit_acceptance_raw: Mapping[str, Any],
    development_acceptance_raw: Mapping[str, Any],
    metric_policy_acceptance_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_held_out_evaluation_evidence_acceptance(
        raw,
        evidence_candidate_raw,
        review_authorization_raw,
        stage3_execution_raw,
        stage3_exit_acceptance_raw,
        development_acceptance_raw,
        metric_policy_acceptance_raw,
    )
    readiness = _post_acceptance_readiness()
    return {
        "schemaVersion": SCHEMA_VERSION,
        "decision": ACCEPTANCE_DECISION,
        "acceptanceDigest": {"algorithm": "sha256", "value": ACCEPTANCE_CANONICAL_SHA256},
        "heldOutEvaluationEvidenceDigest": {"algorithm": "sha256", "value": EVIDENCE_CANONICAL_SHA256},
        "heldOutEvaluationEvidenceAccepted": True,
        "readinessDecision": readiness["decision"],
        "remainingReadinessBlockers": readiness["blockerCodes"],
        "finalGovernanceAcceptanceStillRequired": True,
        "stage4ExitPass": False,
        "stage5EntryAuthorized": False,
    }


__all__ = [
    "ACCEPTANCE_CANONICAL_SHA256",
    "ACCEPTANCE_DECISION",
    "ACCEPTANCE_ID",
    "ACCEPTANCE_SOURCE_CODE",
    "ACCEPTED_ON",
    "DECISION_AUTHORITY_REFERENCE",
    "POST_ACCEPTANCE_READINESS_DIGEST",
    "SCHEMA_VERSION",
    "Stage4HeldOutEvaluationEvidenceAcceptanceError",
    "summarize_held_out_evaluation_evidence_acceptance",
    "validate_held_out_evaluation_evidence_acceptance",
]
