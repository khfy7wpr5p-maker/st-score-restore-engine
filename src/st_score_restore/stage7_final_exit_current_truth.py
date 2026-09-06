"""Fail-closed validation for the Stage 7 final-exit current-truth overlay."""

from __future__ import annotations

from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage7_final_exit import EXPECTED_ACCEPTANCE_SHA256, validate_stage7_final_exit

EXPECTED_CURRENT_TRUTH_SHA256 = "616038d34539ceb5ae2876295ae8e4d5ba4b44e3b2e3cafa1add919c1f7ac6c8"
NEXT_SAFE_BOUNDARY = "separate_explicit_preview_release_activation_or_stage8_entry_authorization"


class Stage7FinalExitCurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage7FinalExitCurrentTruthError(message)


def validate_stage7_final_exit_current_truth(
    stage6_final_truth: Mapping[str, Any],
    stage7_authorization: Mapping[str, Any],
    preview_contract: Mapping[str, Any],
    final_acceptance: Mapping[str, Any],
    current_truth: Mapping[str, Any],
) -> dict[str, Any]:
    exit_result = validate_stage7_final_exit(
        stage6_final_truth,
        stage7_authorization,
        preview_contract,
        final_acceptance,
    )
    _require(exit_result["acceptanceDigest"] == EXPECTED_ACCEPTANCE_SHA256, "Stage 7 final acceptance binding drifted")
    _require(isinstance(current_truth, Mapping), "Stage 7 current truth must be an object")
    _require(current_truth.get("schema_version") == "1.0.0", "current-truth schema drifted")
    _require(current_truth.get("generated_on") == "2026-09-06", "current-truth date drifted")
    _require(current_truth.get("artifact_type") == "stage7_final_exit_current_truth", "current-truth type drifted")

    checkpoint = current_truth.get("production_checkpoint") or {}
    _require(checkpoint.get("main_sha") == "14ac1f61bd194af8d5b00727f121521c3607579f", "accepted production checkpoint SHA drifted")
    _require(checkpoint.get("merge_pr") == 177, "accepted Stage 7 final-exit PR drifted")
    _require(checkpoint.get("exact_head_sha") == "f4be745e6099cd09de87867b5f4975323e224ce0", "accepted exact-head SHA drifted")
    _require(checkpoint.get("final_exit_acceptance_sha256") == EXPECTED_ACCEPTANCE_SHA256, "final acceptance digest drifted")
    _require(checkpoint.get("final_exit_acceptance_git_blob_sha1") == "47608910e2f1c3f9ff4aea179a565090eef62da6", "final acceptance blob binding drifted")
    _require(checkpoint.get("python_matrix") == ["3.11", "3.12"], "validated Python matrix drifted")

    expected_exact = {
        "repository_validation": {"run_id": 34053729981, "run_number": 488, "result": "SUCCESS"},
        "stage4_governance": {"run_id": 34053729854, "run_number": 99, "result": "SUCCESS"},
        "stage5_governance": {"run_id": 34053729898, "run_number": 91, "result": "SUCCESS"},
        "stage6_governance": {"run_id": 34053730057, "run_number": 50, "result": "SUCCESS"},
        "stage7_governance": {"run_id": 34053729921, "run_number": 3, "result": "SUCCESS"},
    }
    expected_postmerge = {
        "repository_validation": {"run_id": 34053804973, "run_number": 489, "result": "SUCCESS"},
        "stage4_governance": {"run_id": 34053804992, "run_number": 100, "result": "SUCCESS"},
        "stage5_governance": {"run_id": 34053805044, "run_number": 92, "result": "SUCCESS"},
        "stage6_governance": {"run_id": 34053805090, "run_number": 51, "result": "SUCCESS"},
        "stage7_governance": {"run_id": 34053805052, "run_number": 4, "result": "SUCCESS"},
    }
    _require(checkpoint.get("exact_head_ci") == expected_exact, "exact-head CI evidence drifted")
    _require(checkpoint.get("postmerge_ci") == expected_postmerge, "post-merge CI evidence drifted")

    stage6 = current_truth.get("stage6") or {}
    _require(stage6 == {"state": "COMPLETE_PASS_PROVIDER_NEUTRAL", "exit_pass": True}, "Stage 6 truth drifted")
    stage7 = current_truth.get("stage7") or {}
    _require(stage7.get("state") == "COMPLETE_PASS_PROVIDER_NEUTRAL_PREVIEW_CAPABILITY", "Stage 7 final state drifted")
    for key in ("exit_pass", "entry_eligible", "entry_authorized", "started", "provider_neutral_preview_capability_complete"):
        _require(stage7.get(key) is True, f"Stage 7 completed assertion missing: {key}")
    for key in ("preview_release_activation_authorized", "preview_release_activated", "real_user_cohort_authorized"):
        _require(stage7.get(key) is False, f"Stage 7 current truth over-authorized: {key}")
    _require(stage7.get("next_safe_boundary") == NEXT_SAFE_BOUNDARY, "Stage 7 next-safe-boundary drifted")

    stage8 = current_truth.get("stage8") or {}
    _require(stage8 == {"entry_eligible": True, "entry_authorized": False, "started": False}, "Stage 8 boundary drifted")
    provider = current_truth.get("provider") or {}
    _require(provider == {
        "selection_status": "UNSELECTED",
        "provider_specific_activation_authorized": False,
        "live_resource_creation_authorized": False,
    }, "provider-neutral boundary drifted")
    deployment = current_truth.get("deployment") or {}
    _require(deployment == {"production_deployment_authorized": False, "production_deployment_performed": False}, "production deployment boundary drifted")

    assertions = current_truth.get("assertions") or {}
    for key in ("historical_evidence_immutable", "source_artifact_immutable", "derived_artifacts_provenance_bound"):
        _require(assertions.get(key) is True, f"required invariant missing: {key}")
    for key in (
        "real_or_derivative_bytes_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "raw_secrets_or_key_material_in_ordinary_git",
        "preview_release_activation_authorized",
        "real_user_cohort_authorized",
        "provider_selection_finalized",
        "live_resource_creation_authorized",
        "production_deployment_authorized",
        "production_load_or_soak_validated",
        "independent_production_security_signoff_complete",
        "threshold_changes_authorized",
        "resource_limit_changes_authorized",
        "held_out_retuning_authorized",
        "model_training_authorized",
        "model_publication_authorized",
        "stage8_entry_authorized",
        "omr_correctness_established",
        "musical_truth_established",
        "restoration_effectiveness_established",
        "production_availability_or_scalability_established",
        "color_management_validated",
        "color_fidelity_certified",
    ):
        _require(assertions.get(key) is False, f"unsupported current-truth assertion became true: {key}")

    continuation = current_truth.get("continuation_state") or {}
    _require(continuation.get("last_completed_stage") == "Stage 7", "continuation last-completed stage drifted")
    _require(continuation.get("last_completed_state") == "COMPLETE_PASS_PROVIDER_NEUTRAL_PREVIEW_CAPABILITY", "continuation state drifted")
    _require(continuation.get("first_incomplete_boundary") == NEXT_SAFE_BOUNDARY, "continuation safe boundary drifted")
    for key in ("stage7_entry_authorized", "stage7_started", "stage7_exit_pass"):
        _require(continuation.get(key) is True, f"Stage 7 continuation assertion missing: {key}")
    for key in ("stage8_started", "stage9_started", "stage9a_training_authorized", "stage10_started", "stage11_training_authorized", "stage12_started"):
        _require(continuation.get(key) is False, f"later-stage boundary was crossed: {key}")

    _require(canonical_sha256(current_truth) == EXPECTED_CURRENT_TRUTH_SHA256, "Stage 7 final current-truth canonical digest changed")
    return {
        "stage7State": stage7["state"],
        "stage7ExitPass": True,
        "stage8EntryEligible": True,
        "stage8EntryAuthorized": False,
        "previewReleaseActivationAuthorized": False,
        "providerSelectionStatus": "UNSELECTED",
        "productionDeploymentAuthorized": False,
        "currentTruthDigest": EXPECTED_CURRENT_TRUTH_SHA256,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "EXPECTED_CURRENT_TRUTH_SHA256",
    "NEXT_SAFE_BOUNDARY",
    "Stage7FinalExitCurrentTruthError",
    "validate_stage7_final_exit_current_truth",
]
