"""Fail-closed validation for the Stage 9A final current-truth overlay."""

from __future__ import annotations

from typing import Any, Mapping

from .stage9a_final_exit import FINAL_STATE, validate_stage9a_final_exit

TRUTH_TYPE = "stage9a_final_exit_current_truth"
CHECKPOINT_SHA = "45dfd78c6abbed1f48428fac1359bd54fb74e75a"
ACCEPTANCE_PATH = "evidence/stage9a/final-exit/stage9a-final-exit-acceptance.v1.json"
ACCEPTANCE_BLOB_SHA = "8f27d3949ac3e69e141d2e0e36d5e1441faef1d3"
NEXT_BOUNDARY = "separate_stage10_entry_authorization"


class Stage9AFinalTruthError(ValueError):
    """Raised when Stage 9A current truth overclaims or loses its checkpoint binding."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage9AFinalTruthError(message)


def validate_stage9a_final_exit_current_truth(
    truth: Mapping[str, Any],
    acceptance: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage9a_final_exit(acceptance)
    _require(isinstance(truth, Mapping), "Stage 9A current truth must be an object")
    _require(truth.get("artifact_type") == TRUTH_TYPE, "unexpected Stage 9A current truth type")

    checkpoint = truth.get("production_checkpoint")
    _require(isinstance(checkpoint, Mapping), "production checkpoint missing")
    _require(checkpoint.get("main_sha") == CHECKPOINT_SHA, "production checkpoint SHA mismatch")
    _require(checkpoint.get("merge_pr") == 184, "production checkpoint PR mismatch")
    _require(checkpoint.get("final_exit_acceptance_path") == ACCEPTANCE_PATH, "final-exit path mismatch")
    _require(checkpoint.get("final_exit_acceptance_git_blob_sha1") == ACCEPTANCE_BLOB_SHA, "final-exit blob mismatch")
    _require(checkpoint.get("python_matrix") == ["3.11", "3.12"], "Python matrix mismatch")

    stage9a = truth.get("stage9a")
    _require(isinstance(stage9a, Mapping), "Stage 9A state missing")
    _require(stage9a.get("state") == FINAL_STATE, "Stage 9A state mismatch")
    _require(stage9a.get("exit_pass") is True, "Stage 9A exit must pass")
    for field in (
        "entry_eligible",
        "entry_authorized",
        "started",
        "mspm_evidence_contract_complete",
        "extensible_music_tab_taxonomy_foundation_complete",
        "source_candidate_provenance_binding_complete",
        "semantic_hard_veto_routing_complete",
        "uncertainty_review_original_fallback_complete",
        "stage9_comparator_handoff_complete",
        "synthetic_preservation_drills_pass",
    ):
        _require(stage9a.get(field) is True, f"Stage 9A completed capability missing: {field}")
    for field in (
        "trained_semantic_model_complete",
        "learned_component_training_authorized",
        "production_inference_authorized",
        "automatic_final_selection_authorized",
    ):
        _require(stage9a.get(field) is False, f"unsupported Stage 9A claim: {field}")
    _require(stage9a.get("next_safe_boundary") == NEXT_BOUNDARY, "Stage 9A next boundary mismatch")

    stage10 = truth.get("stage10")
    _require(isinstance(stage10, Mapping), "Stage 10 boundary missing")
    _require(stage10.get("entry_eligible") is True, "Stage 10 should be entry eligible")
    for field in ("entry_authorized", "started", "selector_activation_authorized"):
        _require(stage10.get(field) is False, f"Stage 10 started without explicit authorization: {field}")

    training = truth.get("training")
    _require(isinstance(training, Mapping), "training boundary missing")
    for field, value in training.items():
        _require(value is False, f"training/network scope expanded: {field}")

    deployment = truth.get("deployment")
    _require(isinstance(deployment, Mapping), "deployment boundary missing")
    for field, value in deployment.items():
        _require(value is False, f"deployment scope expanded: {field}")

    assertions = truth.get("assertions")
    _require(isinstance(assertions, Mapping), "assertions missing")
    required_true = (
        "historical_evidence_immutable",
        "source_artifact_immutable",
        "derived_artifacts_provenance_bound",
        "deterministic_safety_remains_independent",
        "hard_deterministic_veto_non_overridable",
        "hard_semantic_veto_non_overridable",
        "original_always_selectable",
        "uncertain_or_unavailable_semantic_evidence_fails_safe",
        "semantic_evidence_cannot_approve_candidate_by_itself",
        "no_opaque_universal_preservation_score",
        "mspm_evidence_is_not_omr_truth",
        "mspm_evidence_is_not_human_musical_truth",
    )
    for field in required_true:
        _require(assertions.get(field) is True, f"truth safety assertion missing: {field}")
    required_false = (
        "trained_mspm_model_established",
        "automatic_final_selection_authorized",
        "stage10_entry_authorized",
        "stage10_selector_activation_authorized",
        "live_resource_creation_authorized",
        "production_deployment_authorized",
        "production_load_or_soak_validated",
        "independent_production_security_signoff_complete",
        "threshold_changes_authorized",
        "resource_limit_changes_authorized",
        "held_out_retuning_authorized",
        "omr_correctness_established",
        "musical_truth_established",
        "universal_restoration_effectiveness_established",
        "production_availability_or_scalability_established",
        "color_management_validated",
        "color_fidelity_certified",
    )
    for field in required_false:
        _require(assertions.get(field) is False, f"unsupported truth assertion: {field}")

    continuation = truth.get("continuation_state")
    _require(isinstance(continuation, Mapping), "continuation state missing")
    _require(continuation.get("last_completed_stage") == "Stage 9A", "last completed stage mismatch")
    _require(continuation.get("last_completed_state") == FINAL_STATE, "last completed state mismatch")
    _require(continuation.get("first_incomplete_boundary") == NEXT_BOUNDARY, "continuation boundary mismatch")
    _require(continuation.get("stage9a_exit_pass") is True, "Stage 9A continuation exit must pass")
    _require(continuation.get("stage10_started") is False, "Stage 10 must remain unstarted")

    return {
        "result": "PASS",
        "state": FINAL_STATE,
        "firstIncompleteBoundary": NEXT_BOUNDARY,
        "stage10EntryEligible": True,
        "stage10EntryAuthorized": False,
        "trainedMspmModelEstablished": False,
    }


__all__ = ["Stage9AFinalTruthError", "validate_stage9a_final_exit_current_truth"]
