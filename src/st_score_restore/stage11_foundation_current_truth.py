"""Validation for the Stage 11 foundation current-truth checkpoint."""

from __future__ import annotations

from typing import Any, Mapping

STATE = "FOUNDATION_COMPLETE_AWAITING_SEPARATE_TRAINING_AUTHORIZATION"
NEXT_SAFE_BOUNDARY = "separate_stage11_training_and_dataset_authorization"


class Stage11CurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11CurrentTruthError(message)


def validate_stage11_foundation_current_truth(truth: Mapping[str, Any]) -> dict[str, Any]:
    stage10 = truth.get("stage10")
    _require(isinstance(stage10, Mapping), "Stage 10 truth missing")
    _require(stage10.get("state") == "COMPLETE_PASS_PROVIDER_NEUTRAL_ST_RESTORE_SELECTOR_FOUNDATION", "Stage 10 state drifted")
    _require(stage10.get("exit_pass") is True, "Stage 10 exit must remain pass")

    stage11 = truth.get("stage11")
    _require(isinstance(stage11, Mapping), "Stage 11 truth missing")
    _require(stage11.get("state") == STATE, "Stage 11 foundation state mismatch")
    _require(stage11.get("exit_pass") is False, "Stage 11 must not claim final exit before training/evaluation")
    for key in (
        "entry_eligible",
        "entry_authorized",
        "started",
        "provider_neutral_image_model_foundation_complete",
        "model_interface_contract_complete",
        "training_readiness_manifest_contract_complete",
        "release_manifest_validation_complete",
        "selector_capability_descriptor_complete",
        "synthetic_research_adapter_complete",
        "synthetic_drills_required",
    ):
        _require(stage11.get(key) is True, f"Stage 11 foundation capability missing: {key}")
    _require(stage11.get("architecture_family") == "UNSELECTED", "architecture family must remain unselected")
    for key in (
        "dataset_collection_authorized",
        "user_document_training_use_authorized",
        "model_training_authorized",
        "held_out_retuning_authorized",
        "model_weights_established",
        "model_artifact_download_authorized",
        "network_fetch_authorized",
        "model_publication_authorized",
        "production_inference_authorized",
        "real_user_cohort_authorized",
    ):
        _require(stage11.get(key) is False, f"unauthorized Stage 11 activation: {key}")
    _require(stage11.get("next_safe_boundary") == NEXT_SAFE_BOUNDARY, "Stage 11 next boundary drifted")

    descriptor = truth.get("stage11_selector_descriptor")
    _require(isinstance(descriptor, Mapping), "selector descriptor missing")
    _require(descriptor.get("engineId") == "st_restore_image_model", "selector engine id mismatch")
    _require(descriptor.get("approvalState") == "unapproved", "untrained model cannot be approved")
    _require(descriptor.get("availabilityState") == "unavailable", "untrained model cannot be available")
    _require(descriptor.get("enabled") is False, "untrained model cannot be enabled")
    _require(descriptor.get("expected_stage10_action") == "skip", "Stage 10 must skip untrained model")

    stage12 = truth.get("stage12")
    _require(isinstance(stage12, Mapping), "Stage 12 boundary missing")
    _require(stage12.get("entry_eligible") is False, "Stage 12 cannot be eligible before accepted Stage 11 exit")
    _require(stage12.get("entry_authorized") is False, "Stage 12 unauthorized")
    _require(stage12.get("started") is False, "Stage 12 must not start")

    assertions = truth.get("assertions")
    _require(isinstance(assertions, Mapping), "assertions missing")
    for key, value in assertions.items():
        if key == "production_behavior_changed":
            _require(value is False, "production behavior must remain unchanged")
        else:
            _require(value is True, f"assertion must remain true: {key}")

    continuation = truth.get("continuation_state")
    _require(isinstance(continuation, Mapping), "continuation state missing")
    _require(continuation.get("first_incomplete_boundary") == NEXT_SAFE_BOUNDARY, "continuation boundary drifted")
    _require(continuation.get("stage11_exit_pass") is False, "Stage 11 exit cannot pass yet")
    _require(continuation.get("stage11_training_started") is False, "training must not start")
    _require(continuation.get("stage12_started") is False, "Stage 12 must not start")

    return {
        "valid": True,
        "state": STATE,
        "stage11ExitPass": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }
