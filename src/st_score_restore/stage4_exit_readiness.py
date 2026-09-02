"""Deterministic Stage 4 exit-readiness assessment.

This module never grants Stage 4 PASS or Stage 5 entry. It reports missing
prerequisites and unsafe conditions. Even a fully satisfied input can only
become READY_FOR_FINAL_ACCEPTANCE_REVIEW; a separate evidence-bound governance
acceptance is required for Stage 4 exit.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

READINESS_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0.0"

BLOCK_NO_SAFETY_CALIBRATION_PERMISSION = "no_real_artifact_has_granted_safety_calibration_permission"
BLOCK_NO_REFERENCE_BUNDLE = "no_real_calibration_reference_label_bundle_is_accepted"
BLOCK_NO_DEVELOPMENT_EVIDENCE = "no_real_development_calibration_evidence_is_accepted"
BLOCK_NO_HELDOUT_EVIDENCE = "no_real_held_out_evaluation_evidence_is_accepted"
BLOCK_NO_METRIC_TARGET_POLICY = "no_stage4_metric_acceptance_target_policy_is_accepted"
BLOCK_HELDOUT_TUNING = "held_out_threshold_tuning_detected"
BLOCK_SOURCE_FAMILY_LEAKAGE = "source_family_leakage_detected"
BLOCK_HISTORICAL_EVIDENCE_MUTABLE = "historical_evidence_immutability_not_satisfied"
BLOCK_REAL_BYTES_IN_GIT = "real_or_derivative_bytes_present_in_ordinary_git"
BLOCK_PREMATURE_PRODUCTION_CHANGE = "premature_production_change_authorization_detected"

PREREQUISITE_BLOCKERS = (
    BLOCK_NO_SAFETY_CALIBRATION_PERMISSION,
    BLOCK_NO_REFERENCE_BUNDLE,
    BLOCK_NO_DEVELOPMENT_EVIDENCE,
    BLOCK_NO_HELDOUT_EVIDENCE,
    BLOCK_NO_METRIC_TARGET_POLICY,
)
HARD_SAFETY_BLOCKERS = (
    BLOCK_HELDOUT_TUNING,
    BLOCK_SOURCE_FAMILY_LEAKAGE,
    BLOCK_HISTORICAL_EVIDENCE_MUTABLE,
    BLOCK_REAL_BYTES_IN_GIT,
    BLOCK_PREMATURE_PRODUCTION_CHANGE,
)


class Stage4ExitReadinessError(ValueError):
    """Stable rejection for malformed readiness inputs."""

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


def _count(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise Stage4ExitReadinessError("invalid_readiness_input", f"{name} must be a non-negative integer.")
    return value


def _boolean(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise Stage4ExitReadinessError("invalid_readiness_input", f"{name} must be boolean.")
    return value


@dataclass(frozen=True)
class Stage4ReadinessInput:
    safety_calibration_artifact_count: int
    accepted_real_reference_bundle_count: int
    accepted_real_development_evidence_count: int
    accepted_real_held_out_evaluation_evidence_count: int
    accepted_metric_target_policy: bool
    held_out_tuning_used: bool
    source_family_leakage_count: int
    historical_evidence_immutable: bool
    real_or_derivative_bytes_in_ordinary_git: bool
    production_threshold_change_authorized: bool
    production_resource_limit_change_authorized: bool

    def __post_init__(self) -> None:
        _count("safety_calibration_artifact_count", self.safety_calibration_artifact_count)
        _count("accepted_real_reference_bundle_count", self.accepted_real_reference_bundle_count)
        _count("accepted_real_development_evidence_count", self.accepted_real_development_evidence_count)
        _count(
            "accepted_real_held_out_evaluation_evidence_count",
            self.accepted_real_held_out_evaluation_evidence_count,
        )
        _count("source_family_leakage_count", self.source_family_leakage_count)
        _boolean("accepted_metric_target_policy", self.accepted_metric_target_policy)
        _boolean("held_out_tuning_used", self.held_out_tuning_used)
        _boolean("historical_evidence_immutable", self.historical_evidence_immutable)
        _boolean("real_or_derivative_bytes_in_ordinary_git", self.real_or_derivative_bytes_in_ordinary_git)
        _boolean("production_threshold_change_authorized", self.production_threshold_change_authorized)
        _boolean("production_resource_limit_change_authorized", self.production_resource_limit_change_authorized)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Stage4ReadinessInput":
        if not isinstance(value, Mapping):
            raise Stage4ExitReadinessError("invalid_readiness_input", "Readiness input must be an object.")
        expected = {
            "safetyCalibrationArtifactCount",
            "acceptedRealReferenceBundleCount",
            "acceptedRealDevelopmentEvidenceCount",
            "acceptedRealHeldOutEvaluationEvidenceCount",
            "acceptedMetricTargetPolicy",
            "heldOutTuningUsed",
            "sourceFamilyLeakageCount",
            "historicalEvidenceImmutable",
            "realOrDerivativeBytesInOrdinaryGit",
            "productionThresholdChangeAuthorized",
            "productionResourceLimitChangeAuthorized",
        }
        unknown = sorted(str(key) for key in value if key not in expected)
        missing = sorted(key for key in expected if key not in value)
        if unknown or missing:
            raise Stage4ExitReadinessError(
                "invalid_readiness_input",
                f"Readiness input fields mismatch; unknown={unknown}, missing={missing}.",
            )
        return cls(
            safety_calibration_artifact_count=value["safetyCalibrationArtifactCount"],
            accepted_real_reference_bundle_count=value["acceptedRealReferenceBundleCount"],
            accepted_real_development_evidence_count=value["acceptedRealDevelopmentEvidenceCount"],
            accepted_real_held_out_evaluation_evidence_count=value["acceptedRealHeldOutEvaluationEvidenceCount"],
            accepted_metric_target_policy=value["acceptedMetricTargetPolicy"],
            held_out_tuning_used=value["heldOutTuningUsed"],
            source_family_leakage_count=value["sourceFamilyLeakageCount"],
            historical_evidence_immutable=value["historicalEvidenceImmutable"],
            real_or_derivative_bytes_in_ordinary_git=value["realOrDerivativeBytesInOrdinaryGit"],
            production_threshold_change_authorized=value["productionThresholdChangeAuthorized"],
            production_resource_limit_change_authorized=value["productionResourceLimitChangeAuthorized"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "safetyCalibrationArtifactCount": self.safety_calibration_artifact_count,
            "acceptedRealReferenceBundleCount": self.accepted_real_reference_bundle_count,
            "acceptedRealDevelopmentEvidenceCount": self.accepted_real_development_evidence_count,
            "acceptedRealHeldOutEvaluationEvidenceCount": self.accepted_real_held_out_evaluation_evidence_count,
            "acceptedMetricTargetPolicy": self.accepted_metric_target_policy,
            "heldOutTuningUsed": self.held_out_tuning_used,
            "sourceFamilyLeakageCount": self.source_family_leakage_count,
            "historicalEvidenceImmutable": self.historical_evidence_immutable,
            "realOrDerivativeBytesInOrdinaryGit": self.real_or_derivative_bytes_in_ordinary_git,
            "productionThresholdChangeAuthorized": self.production_threshold_change_authorized,
            "productionResourceLimitChangeAuthorized": self.production_resource_limit_change_authorized,
        }


def evaluate_stage4_exit_readiness(
    value: Stage4ReadinessInput | Mapping[str, Any],
) -> dict[str, Any]:
    """Return NOT_READY or READY_FOR_FINAL_ACCEPTANCE_REVIEW, never PASS."""

    state = value if isinstance(value, Stage4ReadinessInput) else Stage4ReadinessInput.from_mapping(value)
    blockers: list[str] = []

    if state.safety_calibration_artifact_count < 1:
        blockers.append(BLOCK_NO_SAFETY_CALIBRATION_PERMISSION)
    if state.accepted_real_reference_bundle_count < 1:
        blockers.append(BLOCK_NO_REFERENCE_BUNDLE)
    if state.accepted_real_development_evidence_count < 1:
        blockers.append(BLOCK_NO_DEVELOPMENT_EVIDENCE)
    if state.accepted_real_held_out_evaluation_evidence_count < 1:
        blockers.append(BLOCK_NO_HELDOUT_EVIDENCE)
    if not state.accepted_metric_target_policy:
        blockers.append(BLOCK_NO_METRIC_TARGET_POLICY)

    if state.held_out_tuning_used:
        blockers.append(BLOCK_HELDOUT_TUNING)
    if state.source_family_leakage_count > 0:
        blockers.append(BLOCK_SOURCE_FAMILY_LEAKAGE)
    if not state.historical_evidence_immutable:
        blockers.append(BLOCK_HISTORICAL_EVIDENCE_MUTABLE)
    if state.real_or_derivative_bytes_in_ordinary_git:
        blockers.append(BLOCK_REAL_BYTES_IN_GIT)
    if state.production_threshold_change_authorized or state.production_resource_limit_change_authorized:
        blockers.append(BLOCK_PREMATURE_PRODUCTION_CHANGE)

    blockers = sorted(set(blockers))
    review_ready = not blockers
    decision = "READY_FOR_FINAL_ACCEPTANCE_REVIEW" if review_ready else "NOT_READY"
    result = {
        "schemaVersion": SCHEMA_VERSION,
        "readinessVersion": READINESS_VERSION,
        "decision": decision,
        "inputSummary": state.to_dict(),
        "blockerCodes": blockers,
        "blockerCount": len(blockers),
        "assertions": {
            "readinessPrerequisitesSatisfied": review_ready,
            "finalGovernanceAcceptanceStillRequired": True,
            "stage4ExitPass": False,
            "stage5EntryAuthorized": False,
            "productionThresholdChangeAuthorizedByReadiness": False,
            "productionResourceLimitChangeAuthorizedByReadiness": False,
            "modelTrainingAuthorized": False,
            "publicationAuthorized": False,
        },
        "limitations": [
            "Readiness is not Stage 4 final acceptance.",
            "Numerical acceptance targets must come from a separately accepted metric-target policy; this evaluator does not invent them.",
            "A READY_FOR_FINAL_ACCEPTANCE_REVIEW result can only permit a separate governance review, never automatic Stage 4 PASS.",
        ],
    }
    result["readinessDigest"] = {"algorithm": "sha256", "value": _canonical_digest(result)}
    return result
