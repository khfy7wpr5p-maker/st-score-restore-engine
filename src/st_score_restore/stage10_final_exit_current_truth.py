"""Fail-closed authoritative Stage 10 final current-truth validation."""

from __future__ import annotations

from typing import Any, Mapping

from st_score_restore.stage10_final_exit import (
    CAPABILITY_MERGE_SHA,
    EXACT_HEAD_SHA,
    STATE,
    validate_stage10_final_exit,
)

CURRENT_TRUTH_ARTIFACT_TYPE = "stage10_final_exit_current_truth"
ACCEPTANCE_BLOB_SHA = "72f6a664e2ae35e6cb104e28e4835023b83b6b88"


class Stage10CurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage10CurrentTruthError(message)


def _all_false(mapping: Mapping[str, Any], fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        _require(mapping.get(field) is False, f"{label} scope expansion: {field}")


def validate_stage10_final_exit_current_truth(
    truth: Mapping[str, Any],
    acceptance: Mapping[str, Any],
    authorization: Mapping[str, Any],
    stage9a_truth: Mapping[str, Any],
    selector_contract: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage10_final_exit(acceptance, authorization, stage9a_truth, selector_contract)
    _require(isinstance(truth, Mapping), "current truth must be an object")
    _require(truth.get("artifact_type") == CURRENT_TRUTH_ARTIFACT_TYPE, "unexpected current-truth artifact type")

    checkpoint = truth.get("production_checkpoint")
    _require(isinstance(checkpoint, Mapping), "Stage 10 checkpoint missing")
    _require(checkpoint.get("main_sha") == CAPABILITY_MERGE_SHA, "accepted capability checkpoint mismatch")
    _require(checkpoint.get("merge_pr") == 186, "accepted capability PR mismatch")
    _require(checkpoint.get("exact_head_sha") == EXACT_HEAD_SHA, "exact-head checkpoint mismatch")
    _require(checkpoint.get("final_exit_acceptance_path") == "evidence/stage10/final-exit/stage10-final-exit-acceptance.v1.json", "acceptance path mismatch")
    _require(checkpoint.get("final_exit_acceptance_git_blob_sha1") == ACCEPTANCE_BLOB_SHA, "acceptance blob mismatch")
    _require(checkpoint.get("python_matrix") == ["3.11", "3.12"], "Python matrix mismatch")
    for ci_name in ("exact_head_ci", "postmerge_ci"):
        ci = checkpoint.get(ci_name)
        _require(isinstance(ci, Mapping) and len(ci) == 9, f"{ci_name} evidence incomplete")
        for item in ci.values():
            _require(isinstance(item, Mapping) and item.get("result") == "SUCCESS", f"{ci_name} contains non-success")

    stage10 = truth.get("stage10")
    _require(isinstance(stage10, Mapping), "Stage 10 current truth missing")
    _require(stage10.get("state") == STATE, "Stage 10 state mismatch")
    for field in (
        "exit_pass",
        "entry_eligible",
        "entry_authorized",
        "started",
        "provider_neutral_selector_contract_complete",
        "engine_eligibility_planning_complete",
        "original_always_included",
        "stage9_recommendation_consumption_complete",
        "stage9a_evidence_enforcement_complete",
        "original_aware_controlled_selection_complete",
        "fail_safe_review_original_fallback_complete",
        "explainable_reason_codes_complete",
        "synthetic_selector_drills_pass",
    ):
        _require(stage10.get(field) is True, f"Stage 10 current-truth capability missing: {field}")
    _all_false(stage10, ("live_selector_activation_authorized", "automatic_final_selection_authorized", "real_user_selector_cohort_authorized"), "Stage 10")
    _require(stage10.get("next_safe_boundary") == "separate_stage11_entry_authorization", "Stage 10 next boundary mismatch")

    stage11 = truth.get("stage11")
    _require(isinstance(stage11, Mapping), "Stage 11 current truth missing")
    _require(stage11.get("entry_eligible") is True, "Stage 11 must be eligible")
    _all_false(stage11, ("entry_authorized", "started", "image_model_training_authorized"), "Stage 11")

    docres = truth.get("docres")
    _require(isinstance(docres, Mapping), "DocRes boundary missing")
    _require(docres.get("dependency_status") == "UNAPPROVED", "DocRes dependency unexpectedly approved")
    _require(docres.get("model_artifact_status") == "UNAPPROVED", "DocRes model unexpectedly approved")
    _all_false(docres, ("live_runtime_activation_authorized", "real_user_cohort_authorized"), "DocRes")

    provider = truth.get("provider")
    _require(isinstance(provider, Mapping), "provider boundary missing")
    _require(provider.get("selection_status") == "UNSELECTED", "provider unexpectedly selected")
    _all_false(provider, ("provider_specific_activation_authorized", "live_resource_creation_authorized"), "provider")

    deployment = truth.get("deployment")
    _require(isinstance(deployment, Mapping), "deployment boundary missing")
    _all_false(deployment, ("production_deployment_authorized", "production_deployment_performed"), "deployment")

    training = truth.get("training")
    _require(isinstance(training, Mapping), "training boundary missing")
    _all_false(training, tuple(training.keys()), "training")

    assertions = truth.get("assertions")
    _require(isinstance(assertions, Mapping), "assertions missing")
    for field in (
        "historical_evidence_immutable",
        "source_artifact_immutable",
        "derived_artifacts_provenance_bound",
        "original_always_selectable",
        "selector_cannot_bypass_music_tab_safety",
        "selector_cannot_bypass_stage9_comparator",
        "selector_cannot_bypass_stage9a_preservation_evidence",
        "hard_deterministic_veto_non_overridable",
        "hard_semantic_veto_non_overridable",
        "review_required_cannot_become_automatic_variant_selection",
        "unknown_or_malformed_evidence_fails_safe",
        "selector_decision_is_not_teacher_approval",
        "selector_decision_is_not_omr_truth",
        "selector_decision_is_not_human_musical_truth",
    ):
        _require(assertions.get(field) is True, f"required Stage 10 assertion missing: {field}")
    for field in (
        "live_selector_activation_authorized",
        "automatic_final_selection_authorized",
        "real_user_selector_cohort_authorized",
        "stage11_entry_authorized",
        "stage11_image_model_training_authorized",
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
    ):
        _require(assertions.get(field) is False, f"unsupported assertion became true: {field}")

    continuation = truth.get("continuation_state")
    _require(isinstance(continuation, Mapping), "continuation state missing")
    _require(continuation.get("last_completed_stage") == "Stage 10", "last completed stage mismatch")
    _require(continuation.get("last_completed_state") == STATE, "last completed state mismatch")
    _require(continuation.get("first_incomplete_boundary") == "separate_stage11_entry_authorization", "continuation boundary mismatch")
    _require(continuation.get("stage10_exit_pass") is True, "Stage 10 exit must pass")
    _all_false(continuation, ("stage11_started", "stage11_image_model_training_authorized", "stage12_started"), "continuation")

    return {
        "result": "PASS",
        "artifactType": CURRENT_TRUTH_ARTIFACT_TYPE,
        "stage10State": STATE,
        "stage10ExitPass": True,
        "stage11EntryEligible": True,
        "stage11EntryAuthorized": False,
        "stage11Started": False,
        "nextSafeBoundary": "separate_stage11_entry_authorization",
    }


__all__ = ["Stage10CurrentTruthError", "validate_stage10_final_exit_current_truth"]
