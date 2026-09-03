"""Fail-closed Stage 4 final-exit governance acceptance.

This module converts the already production-effective zero-blocker readiness
state into Stage 4 PASS only when the exact accepted development evidence,
metric policy, held-out evidence, and readiness digest are unchanged. Stage 5
becomes eligible only; entry authorization and start remain separate gates.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256

SCHEMA_VERSION = "1.0.0"
ACCEPTANCE_ID = "stage4.final-exit-acceptance.v1"
ACCEPTANCE_DECISION = "PASS"
ACCEPTED_ON = "2026-09-03"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260903-08"
ACCEPTANCE_SOURCE_CODE = "explicit_user_authorization"
READINESS_DIGEST = "8b31b0dc92d931fa9e7b56a7912ecd1127e74ad0672d03d50526160936a32d0b"
DEVELOPMENT_ACCEPTANCE_DIGEST = "4b891f3263c542c59d5632732c8010ef1bc6aeba17dfd71ffbde9ee6ed7be396"
METRIC_POLICY_ACCEPTANCE_DIGEST = "bf62d308f70ca44db617cf2968485e422627abfce70643c78b4da20d58d04801"
HELD_OUT_ACCEPTANCE_DIGEST = "ff0bdcb8820ba774cebc46265eb36ee0278b591a316ca619d2540d06d3a45164"
ACCEPTANCE_CANONICAL_SHA256 = "41923c6c05c7ea015841fd77da7377aad30261a569d287246eb832f856ad599c"

ACCEPTED_LIMITATIONS = [
    "Stage 4 completed through zero-candidate safe abstention; no numerical candidate threshold was accepted.",
    "Thresholds and resource limits remain uncalibrated_engineering_defaults; Stage 4 PASS does not authorize production threshold or resource-limit changes.",
    "The held-out evaluation assessed zero candidates, so not-assessed, exact-match, false-negative, and false-positive rates remain not_applicable; held-out data was not used for tuning or feedback into candidate derivation.",
    "Real and derivative artifact bytes remain outside ordinary Git; detailed private metrics remain custody-only.",
    "Stage 4 PASS establishes that the accepted safety-calibration governance gates were satisfied; it does not establish corpus representativeness, absence of bias, OMR correctness, restoration effectiveness, or model quality.",
]


class Stage4FinalExitAcceptanceError(ValueError):
    """Final exit acceptance is malformed, stale, or over-authorizing."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4FinalExitAcceptanceError(message)


def _digest(value: Mapping[str, Any], expected: str, name: str) -> None:
    _require(canonical_sha256(value) == expected, f"{name} canonical digest drifted")


def validate_stage4_final_exit_acceptance(
    raw: Mapping[str, Any],
    development_acceptance_raw: Mapping[str, Any],
    metric_policy_acceptance_raw: Mapping[str, Any],
    held_out_acceptance_raw: Mapping[str, Any],
    current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    _digest(development_acceptance_raw, DEVELOPMENT_ACCEPTANCE_DIGEST, "development evidence acceptance")
    _digest(metric_policy_acceptance_raw, METRIC_POLICY_ACCEPTANCE_DIGEST, "metric-policy acceptance")
    _digest(held_out_acceptance_raw, HELD_OUT_ACCEPTANCE_DIGEST, "held-out evidence acceptance")

    _require(development_acceptance_raw.get("assertions", {}).get("executionEvidenceAccepted") is True, "development evidence is not accepted")
    _require(metric_policy_acceptance_raw.get("assertions", {}).get("metricAcceptanceTargetPolicyAccepted") is True, "metric policy is not accepted")
    _require(held_out_acceptance_raw.get("assertions", {}).get("heldOutEvaluationEvidenceAccepted") is True, "held-out evidence is not accepted")
    _require(held_out_acceptance_raw.get("assertions", {}).get("heldOutThresholdTuningUsed") is None or held_out_acceptance_raw.get("scope", {}).get("heldOutThresholdTuningUsed") is False, "held-out tuning detected")
    _require(held_out_acceptance_raw.get("scope", {}).get("sourceFamilyLeakageCount") == 0, "source-family leakage detected")
    _require(held_out_acceptance_raw.get("assertions", {}).get("historicalEvidenceRewritten") is False, "historical evidence was rewritten")

    readiness = current_truth_raw.get("stage4_readiness", {})
    assertions = current_truth_raw.get("assertions", {})
    _require(readiness.get("decision") == "READY_FOR_FINAL_ACCEPTANCE_REVIEW", "current truth is not ready for final acceptance")
    _require(readiness.get("readiness_digest") == READINESS_DIGEST, "readiness digest drifted")
    _require(readiness.get("readiness_prerequisites_satisfied") is True, "readiness prerequisites are not satisfied")
    _require(readiness.get("blocker_count") == 0 and readiness.get("blocker_codes") == [], "readiness blockers remain")
    _require(readiness.get("final_governance_acceptance_still_required") is True, "historical current truth was rewritten after final acceptance")
    _require(assertions.get("historical_evidence_immutable") is True, "historical evidence immutability is not satisfied")
    _require(assertions.get("real_or_derivative_bytes_in_ordinary_git") is False, "real or derivative bytes entered ordinary Git")
    _require(assertions.get("held_out_tuning_used") is False, "current truth reports held-out tuning")
    _require(assertions.get("stage4_exit_pass") is False, "historical current truth was retroactively rewritten to PASS")
    _require(assertions.get("stage5_entry_authorized") is False, "historical current truth was retroactively rewritten to authorize Stage 5")

    _require(isinstance(raw, Mapping), "Stage 4 final exit acceptance must be an object")
    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schemaVersion",
            "acceptanceId",
            "decision",
            "acceptedOn",
            "decisionAuthorityReference",
            "acceptanceSourceCode",
            "readinessDigest",
            "developmentEvidenceAcceptanceDigest",
            "metricPolicyAcceptanceDigest",
            "heldOutEvidenceAcceptanceDigest",
            "acceptedReadinessState",
            "acceptedLimitations",
            "acceptedPurpose",
            "stage4ExitPass",
            "stage5EntryEligible",
            "stage5EntryAuthorized",
            "stage5Started",
            "claims",
        },
        "Stage 4 final exit acceptance top-level fields drifted",
    )
    _require(value["schemaVersion"] == SCHEMA_VERSION, "acceptance schema drifted")
    _require(value["acceptanceId"] == ACCEPTANCE_ID, "acceptance id drifted")
    _require(value["decision"] == ACCEPTANCE_DECISION, "Stage 4 final decision is not PASS")
    _require(value["acceptedOn"] == ACCEPTED_ON, "acceptance date drifted")
    _require(value["decisionAuthorityReference"] == DECISION_AUTHORITY_REFERENCE, "decision authority drifted")
    _require(value["acceptanceSourceCode"] == ACCEPTANCE_SOURCE_CODE, "acceptance source drifted")
    _require(value["readinessDigest"] == {"algorithm": "sha256", "value": READINESS_DIGEST}, "readiness binding drifted")
    _require(value["developmentEvidenceAcceptanceDigest"] == {"algorithm": "sha256", "value": DEVELOPMENT_ACCEPTANCE_DIGEST}, "development acceptance binding drifted")
    _require(value["metricPolicyAcceptanceDigest"] == {"algorithm": "sha256", "value": METRIC_POLICY_ACCEPTANCE_DIGEST}, "metric-policy acceptance binding drifted")
    _require(value["heldOutEvidenceAcceptanceDigest"] == {"algorithm": "sha256", "value": HELD_OUT_ACCEPTANCE_DIGEST}, "held-out acceptance binding drifted")

    expected_readiness = {
        "decision": "READY_FOR_FINAL_ACCEPTANCE_REVIEW",
        "readinessPrerequisitesSatisfied": True,
        "blockerCount": 0,
        "blockerCodes": [],
        "heldOutTuningUsed": False,
        "sourceFamilyLeakageCount": 0,
        "historicalEvidenceImmutable": True,
        "realOrDerivativeBytesInOrdinaryGit": False,
        "productionThresholdChangeAuthorized": False,
        "productionResourceLimitChangeAuthorized": False,
    }
    _require(value["acceptedReadinessState"] == expected_readiness, "accepted readiness state drifted or became unsafe")
    _require(value["acceptedLimitations"] == ACCEPTED_LIMITATIONS, "accepted limitations drifted")
    _require(value["acceptedPurpose"] == "stage5-entry-eligibility-only", "accepted purpose drifted")
    _require(value["stage4ExitPass"] is True, "Stage 4 PASS flag missing")
    _require(value["stage5EntryEligible"] is True, "Stage 5 eligibility missing")
    _require(value["stage5EntryAuthorized"] is False, "Stage 5 entry was prematurely authorized")
    _require(value["stage5Started"] is False, "Stage 5 started prematurely")
    _require(value["claims"] and all(claim is False for claim in value["claims"].values()), "unsupported positive downstream claim detected")
    _require(canonical_sha256(value) == ACCEPTANCE_CANONICAL_SHA256, "Stage 4 final exit acceptance canonical digest drifted")
    return value


def summarize_stage4_final_exit_acceptance(
    raw: Mapping[str, Any],
    development_acceptance_raw: Mapping[str, Any],
    metric_policy_acceptance_raw: Mapping[str, Any],
    held_out_acceptance_raw: Mapping[str, Any],
    current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage4_final_exit_acceptance(
        raw,
        development_acceptance_raw,
        metric_policy_acceptance_raw,
        held_out_acceptance_raw,
        current_truth_raw,
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "decision": ACCEPTANCE_DECISION,
        "acceptanceDigest": {"algorithm": "sha256", "value": ACCEPTANCE_CANONICAL_SHA256},
        "readinessDigest": {"algorithm": "sha256", "value": READINESS_DIGEST},
        "stage4ExitPass": True,
        "stage5EntryEligible": True,
        "stage5EntryAuthorized": False,
        "stage5Started": False,
    }


__all__ = [
    "ACCEPTANCE_CANONICAL_SHA256",
    "ACCEPTANCE_DECISION",
    "ACCEPTANCE_ID",
    "ACCEPTED_LIMITATIONS",
    "ACCEPTED_ON",
    "DECISION_AUTHORITY_REFERENCE",
    "READINESS_DIGEST",
    "SCHEMA_VERSION",
    "Stage4FinalExitAcceptanceError",
    "summarize_stage4_final_exit_acceptance",
    "validate_stage4_final_exit_acceptance",
]
