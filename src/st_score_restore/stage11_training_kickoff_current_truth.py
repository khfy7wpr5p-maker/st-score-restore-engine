"""Validation for Stage 11 training-kickoff current truth."""

from __future__ import annotations

from typing import Any, Mapping

STATE = "TRAINING_AUTHORIZED_AWAITING_ACCESSIBLE_ADMITTED_DATA"
NEXT = "admit_accessible_training_bytes_then_execute_reproducible_experiments"


class Stage11TrainingKickoffTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11TrainingKickoffTruthError(message)


def validate_stage11_training_kickoff_current_truth(truth: Mapping[str, Any]) -> dict[str, Any]:
    stage11 = truth.get("stage11") or {}
    _require(stage11.get("state") == STATE, "training kickoff state mismatch")
    _require(stage11.get("exit_pass") is False, "Stage 11 exit cannot pass before training/evaluation")
    for key in ("training_authorized", "dataset_admission_authorized", "architecture_experiment_selection_authorized", "model_weight_creation_authorized"):
        _require(stage11.get(key) is True, f"authorized kickoff capability missing: {key}")
    for key in ("training_started", "training_executable", "model_weights_established", "user_document_training_use_authorized", "student_document_training_use_authorized", "private_document_training_use_authorized", "network_fetch_authorized", "production_inference_authorized", "model_publication_authorized"):
        _require(stage11.get(key) is False, f"premature Stage 11 state: {key}")
    _require(stage11.get("initial_public_development_candidates") == 3, "development candidate count drifted")
    _require(stage11.get("held_out_items_excluded_from_training") == 2, "held-out exclusion count drifted")
    _require(stage11.get("next_safe_boundary") == NEXT, "next boundary drifted")
    policy = truth.get("experiment_policy") or {}
    _require(policy.get("baseline_architecture") == "residual_unet", "baseline architecture drifted")
    _require(policy.get("challenger_architecture") == "hybrid_cnn_transformer", "challenger architecture drifted")
    _require(policy.get("final_architecture_selected") is False, "final architecture cannot be selected before experiments")
    for key in ("independent_stage9a_evidence_required", "stage9_comparator_required", "stage10_selector_required"):
        _require(policy.get(key) is True, f"safety dependency missing: {key}")
    stage12 = truth.get("stage12") or {}
    _require(stage12.get("entry_eligible") is False and stage12.get("entry_authorized") is False and stage12.get("started") is False, "Stage 12 must remain closed")
    assertions = truth.get("assertions") or {}
    for key, value in assertions.items():
        if key == "production_behavior_changed":
            _require(value is False, "production behavior must remain unchanged")
        else:
            _require(value is True, f"assertion must remain true: {key}")
    return {"valid": True, "state": STATE, "trainingAuthorized": True, "trainingStarted": False, "nextSafeBoundary": NEXT}
