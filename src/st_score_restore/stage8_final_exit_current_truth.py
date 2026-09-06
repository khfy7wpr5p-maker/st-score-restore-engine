"""Fail-closed validation for the Stage 8 final-exit current-truth overlay."""

from __future__ import annotations

from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage8_final_exit import ACCEPTANCE_CANONICAL_SHA256, validate_stage8_final_exit

EXPECTED_CURRENT_TRUTH_SHA256 = "a9e8e3028d147025ef43404895fa99d0ea5f741456e1b160f0391e5fd7fca0ed"
NEXT_SAFE_BOUNDARY = "separate_exact_docres_dependency_model_runtime_approval_or_stage9_entry_authorization"


class Stage8FinalExitCurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage8FinalExitCurrentTruthError(message)


def validate_stage8_final_exit_current_truth(
    stage8_authorization: Mapping[str, Any],
    stage7_final_truth: Mapping[str, Any],
    docres_contract: Mapping[str, Any],
    final_acceptance: Mapping[str, Any],
    current_truth: Mapping[str, Any],
) -> dict[str, Any]:
    exit_result = validate_stage8_final_exit(
        final_acceptance,
        stage8_authorization,
        stage7_final_truth,
        docres_contract,
    )
    _require(
        exit_result["acceptanceDigest"]["value"] == ACCEPTANCE_CANONICAL_SHA256,
        "Stage 8 final acceptance binding drifted",
    )
    _require(isinstance(current_truth, Mapping), "Stage 8 current truth must be an object")
    _require(current_truth.get("schema_version") == "1.0.0", "current-truth schema drifted")
    _require(current_truth.get("generated_on") == "2026-09-06", "current-truth date drifted")
    _require(current_truth.get("artifact_type") == "stage8_final_exit_current_truth", "current-truth type drifted")

    checkpoint = current_truth.get("production_checkpoint") or {}
    _require(checkpoint.get("main_sha") == "2cd46bd106d4729fe2878474d8c0cb473194fb5d", "accepted production checkpoint SHA drifted")
    _require(checkpoint.get("merge_pr") == 180, "accepted Stage 8 final-exit PR drifted")
    _require(checkpoint.get("merge_title") == "Stage 8: accept optional-candidate final exit", "accepted Stage 8 merge title drifted")
    _require(checkpoint.get("exact_head_sha") == "4d865fb0004cca9c090fe3cbed7fa957edcfeff0", "accepted exact-head SHA drifted")
    _require(checkpoint.get("final_exit_acceptance_sha256") == ACCEPTANCE_CANONICAL_SHA256, "final acceptance digest drifted")
    _require(checkpoint.get("final_exit_acceptance_git_blob_sha1") == "0331e05c7b92b90c0b56256fff47a7e5ca695bff", "final acceptance blob binding drifted")
    _require(checkpoint.get("final_exit_acceptance_path") == "evidence/stage8/final-exit/stage8-final-exit-acceptance.v1.json", "final acceptance path drifted")
    _require(checkpoint.get("python_matrix") == ["3.11", "3.12"], "validated Python matrix drifted")

    expected_exact = {
        "repository_validation": {"run_id": 34055830209, "run_number": 494, "result": "SUCCESS"},
        "stage4_governance": {"run_id": 34055830226, "run_number": 105, "result": "SUCCESS"},
        "stage5_governance": {"run_id": 34055830195, "run_number": 97, "result": "SUCCESS"},
        "stage6_governance": {"run_id": 34055830330, "run_number": 56, "result": "SUCCESS"},
        "stage7_governance": {"run_id": 34055830232, "run_number": 9, "result": "SUCCESS"},
        "stage8_governance": {"run_id": 34055830197, "run_number": 3, "result": "SUCCESS"},
    }
    expected_postmerge = {
        "repository_validation": {"run_id": 34055889289, "run_number": 495, "result": "SUCCESS"},
        "stage4_governance": {"run_id": 34055889288, "run_number": 106, "result": "SUCCESS"},
        "stage5_governance": {"run_id": 34055889259, "run_number": 98, "result": "SUCCESS"},
        "stage6_governance": {"run_id": 34055889262, "run_number": 57, "result": "SUCCESS"},
        "stage7_governance": {"run_id": 34055889286, "run_number": 10, "result": "SUCCESS"},
        "stage8_governance": {"run_id": 34055889278, "run_number": 4, "result": "SUCCESS"},
    }
    _require(checkpoint.get("exact_head_ci") == expected_exact, "exact-head CI evidence drifted")
    _require(checkpoint.get("postmerge_ci") == expected_postmerge, "post-merge CI evidence drifted")

    stage7 = current_truth.get("stage7") or {}
    _require(stage7 == {"state": "COMPLETE_PASS_PROVIDER_NEUTRAL_PREVIEW_CAPABILITY", "exit_pass": True}, "Stage 7 truth drifted")

    stage8 = current_truth.get("stage8") or {}
    _require(stage8.get("state") == "COMPLETE_PASS_DOCRES_OPTIONAL_CANDIDATE_CONTRACT", "Stage 8 final state drifted")
    for key in ("exit_pass", "entry_eligible", "entry_authorized", "started", "optional_candidate_contract_complete"):
        _require(stage8.get(key) is True, f"Stage 8 completed assertion missing: {key}")
    _require(stage8.get("dependency_status") == "UNAPPROVED", "DocRes dependency status over-claimed")
    _require(stage8.get("model_artifact_status") == "UNAPPROVED", "DocRes model artifact status over-claimed")
    for key in ("live_docres_runtime_activation_authorized", "real_user_docres_cohort_authorized", "stage9_comparator_selection_authorized"):
        _require(stage8.get(key) is False, f"Stage 8 current truth over-authorized: {key}")
    _require(stage8.get("next_safe_boundary") == NEXT_SAFE_BOUNDARY, "Stage 8 next-safe-boundary drifted")

    stage9 = current_truth.get("stage9") or {}
    _require(stage9 == {"entry_eligible": True, "entry_authorized": False, "started": False}, "Stage 9 boundary drifted")

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
        "external_package_installation_authorized",
        "docres_runtime_dependency_approved",
        "model_artifact_download_authorized",
        "model_weights_use_authorized",
        "network_fetch_authorized",
        "live_docres_runtime_activation_authorized",
        "real_user_docres_cohort_authorized",
        "stage9_comparator_selection_authorized",
        "automatic_final_selection_authorized",
        "live_resource_creation_authorized",
        "production_deployment_authorized",
        "production_load_or_soak_validated",
        "independent_production_security_signoff_complete",
        "threshold_changes_authorized",
        "resource_limit_changes_authorized",
        "held_out_retuning_authorized",
        "model_training_authorized",
        "model_publication_authorized",
        "stage9_entry_authorized",
        "omr_correctness_established",
        "musical_truth_established",
        "restoration_effectiveness_established",
        "production_availability_or_scalability_established",
        "color_management_validated",
        "color_fidelity_certified",
    ):
        _require(assertions.get(key) is False, f"unsupported current-truth assertion became true: {key}")

    continuation = current_truth.get("continuation_state") or {}
    _require(continuation.get("last_completed_stage") == "Stage 8", "continuation last-completed stage drifted")
    _require(continuation.get("last_completed_state") == "COMPLETE_PASS_DOCRES_OPTIONAL_CANDIDATE_CONTRACT", "continuation state drifted")
    _require(continuation.get("first_incomplete_boundary") == NEXT_SAFE_BOUNDARY, "continuation safe boundary drifted")
    for key in ("stage8_entry_authorized", "stage8_started", "stage8_exit_pass"):
        _require(continuation.get(key) is True, f"Stage 8 continuation assertion missing: {key}")
    for key in ("stage9_started", "stage9a_training_authorized", "stage10_started", "stage11_training_authorized", "stage12_started"):
        _require(continuation.get(key) is False, f"later-stage boundary was crossed: {key}")

    _require(canonical_sha256(current_truth) == EXPECTED_CURRENT_TRUTH_SHA256, "Stage 8 final current-truth canonical digest changed")
    return {
        "stage8State": stage8["state"],
        "stage8ExitPass": True,
        "stage9EntryEligible": True,
        "stage9EntryAuthorized": False,
        "docresRuntimeDependencyApproved": False,
        "liveDocresRuntimeActivationAuthorized": False,
        "stage9ComparatorSelectionAuthorized": False,
        "productionDeploymentAuthorized": False,
        "currentTruthDigest": EXPECTED_CURRENT_TRUTH_SHA256,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "EXPECTED_CURRENT_TRUTH_SHA256",
    "NEXT_SAFE_BOUNDARY",
    "Stage8FinalExitCurrentTruthError",
    "validate_stage8_final_exit_current_truth",
]
