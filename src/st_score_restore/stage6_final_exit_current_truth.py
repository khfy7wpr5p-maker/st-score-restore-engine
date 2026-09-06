"""Production-effective current truth after Stage 6 S6-09 final exit."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .stage6_final_exit import EXPECTED_ACCEPTANCE_SHA256, NEXT_SAFE_BOUNDARY, validate_stage6_final_exit

SCHEMA_VERSION = "1.0.0"
CHECKPOINT_TYPE = "stage6_final_exit_current_truth_overlay"
RECORDED_ON = "2026-09-06"
PROJECT = "ST Score Restore API / ST Score Restore Engine"
REPOSITORY = "khfy7wpr5p-maker/st-score-restore-engine"
GATE_MAIN_SHA = "ed5cd2657466e171165d99dba0955e57a0c3a306"
GATE_MERGE_PR = 174
GATE_PR_TITLE = "Stage 6: complete S6-09 final exit"
GATE_EXACT_HEAD_SHA = "151a3a1e0fccddc701201625e302b5696531d278"


class Stage6FinalExitCurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage6FinalExitCurrentTruthError(message)


def validate_stage6_final_exit_current_truth(
    raw: Mapping[str, Any],
    acceptance_raw: Mapping[str, Any],
    s6_08_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    final_summary = validate_stage6_final_exit(s6_08_current_truth_raw, acceptance_raw)
    _require(final_summary["stage6State"] == "COMPLETE_PASS_PROVIDER_NEUTRAL", "final-exit acceptance did not PASS")
    _require(final_summary["acceptanceDigest"] == EXPECTED_ACCEPTANCE_SHA256, "final-exit digest drifted")

    historical_stage6 = s6_08_current_truth_raw.get("stage6") or {}
    _require(
        historical_stage6.get("state") == "ACTIVE_INTEGRATION_SECURITY_REGRESSION_COMPLETE_PROVIDER_UNSELECTED",
        "historical S6-08 state drifted",
    )
    _require(historical_stage6.get("s6_09_final_exit_authorized") is False, "historical S6-08 final-exit boundary drifted")
    _require(
        s6_08_current_truth_raw.get("provider", {}).get("selection_status") == "UNSELECTED",
        "historical S6-08 provider state drifted",
    )
    _require(
        s6_08_current_truth_raw.get("deployment", {}).get("production_deployment_authorized") is False,
        "historical S6-08 deployment boundary drifted",
    )

    _require(isinstance(raw, Mapping), "Stage 6 final current truth must be an object")
    value = deepcopy(dict(raw))
    expected_top = {
        "schema_version", "project", "repository", "checkpoint_type", "recorded_on",
        "production_checkpoint", "stage5", "stage6_final_exit", "identity",
        "secrets_kms_iam", "network", "storage_queue_recovery", "provider",
        "deployment", "stage6", "stage7", "assertions", "compatibility_note",
    }
    _require(set(value) == expected_top, "Stage 6 final current-truth fields drifted")
    _require(value["schema_version"] == SCHEMA_VERSION, "schema drifted")
    _require(value["project"] == PROJECT and value["repository"] == REPOSITORY, "project/repository drifted")
    _require(value["checkpoint_type"] == CHECKPOINT_TYPE and value["recorded_on"] == RECORDED_ON, "checkpoint metadata drifted")

    _require(value["production_checkpoint"] == {
        "main_sha": GATE_MAIN_SHA,
        "merge_pr": GATE_MERGE_PR,
        "merge_pr_title": GATE_PR_TITLE,
        "pr_exact_head_sha": GATE_EXACT_HEAD_SHA,
        "exact_head_repository_validation_run_id": 34052211039,
        "exact_head_repository_validation_run_number": 482,
        "exact_head_stage4_governance_run_id": 34052211047,
        "exact_head_stage4_governance_run_number": 93,
        "exact_head_stage5_governance_run_id": 34052211070,
        "exact_head_stage5_governance_run_number": 85,
        "exact_head_stage6_governance_run_id": 34052211112,
        "exact_head_stage6_governance_run_number": 44,
        "postmerge_repository_validation_run_id": 34052287804,
        "postmerge_repository_validation_run_number": 483,
        "postmerge_stage4_governance_run_id": 34052287846,
        "postmerge_stage4_governance_run_number": 94,
        "postmerge_stage5_governance_run_id": 34052287797,
        "postmerge_stage5_governance_run_number": 86,
        "postmerge_stage6_governance_run_id": 34052287904,
        "postmerge_stage6_governance_run_number": 45,
        "ci_status": "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows",
    }, "Stage 6 final production checkpoint drifted")

    _require(value["stage5"] == {
        "state": "COMPLETE_PASS",
        "exit_pass": True,
        "final_acceptance_digest": "467eaf11c451d114d3ef41afd44c87cf2dce5cb68f89a5d6cfc45a81e1eed9fc",
        "color_management_validated": False,
        "color_fidelity_certified": False,
    }, "Stage 5 truth drifted")
    _require(value["stage6_final_exit"] == {
        "acceptance_id": "stage6.final-exit-acceptance.v1",
        "decision": "PASS",
        "acceptance_digest": EXPECTED_ACCEPTANCE_SHA256,
        "accepted_purpose": "stage7-entry-eligibility-only",
    }, "Stage 6 final-exit binding drifted")

    _require(value["identity"] == {
        "production_identity_contract_implemented": True,
        "provider_specific_identity_adapter_activated": False,
    }, "identity truth drifted")
    _require(value["secrets_kms_iam"] == {
        "production_secrets_kms_iam_contract_implemented": True,
        "provider_specific_secrets_kms_iam_activated": False,
        "live_secret_key_or_iam_resource_created": False,
    }, "secrets/KMS/IAM truth drifted")
    _require(value["network"] == {
        "production_network_security_contract_implemented": True,
        "provider_specific_network_adapter_activated": False,
        "live_network_resources_created": False,
        "provider_specific_request_smuggling_certified": False,
        "independent_production_security_signoff_complete": False,
    }, "network truth drifted")

    storage = value["storage_queue_recovery"]
    for key in (
        "production_storage_deployment_contracts_implemented",
        "synthetic_operational_drills_complete",
        "bounded_synthetic_concurrency_stress_complete",
        "integration_security_regression_complete",
    ):
        _require(storage.get(key) is True, f"storage_queue_recovery.{key} must be true")
    for key in (
        "provider_specific_storage_queue_adapter_activated",
        "live_storage_queue_resources_created",
        "production_distributed_stress_validation_complete",
        "production_load_or_soak_validated",
        "production_concurrency_targets_or_failure_budgets_validated",
    ):
        _require(storage.get(key) is False, f"storage_queue_recovery.{key} must be false")

    _require(value["provider"] == {
        "selection_status": "UNSELECTED",
        "provider_specific_evaluation_authorized": True,
        "provider_specific_activation_authorized": False,
        "live_resource_creation_authorized": False,
    }, "provider truth drifted")
    _require(value["deployment"] == {
        "production_deployment_authorized": False,
        "production_deployment_performed": False,
    }, "deployment truth drifted")

    stage6 = value["stage6"]
    expected_stage6_true = (
        "exit_pass", "entry_eligible", "entry_authorized", "started",
        "production_identity_contract_implemented",
        "production_secrets_kms_iam_contract_implemented",
        "production_network_security_contract_implemented",
        "production_storage_deployment_contracts_implemented",
        "synthetic_operational_drills_complete",
        "integration_security_regression_complete",
        "provider_neutral_stage6_deliverable_complete",
    )
    expected_stage6_false = (
        "provider_specific_identity_adapter_activated",
        "provider_specific_secrets_kms_iam_activated",
        "provider_specific_network_adapter_activated",
        "provider_specific_storage_deployment_adapter_activated",
        "production_distributed_stress_validation_complete",
        "production_load_or_soak_validated",
        "independent_penetration_test_or_security_signoff_complete",
        "production_operational_drills_authorized",
        "production_deployment_authorized",
    )
    _require(stage6.get("state") == "COMPLETE_PASS_PROVIDER_NEUTRAL", "Stage 6 final state drifted")
    for key in expected_stage6_true:
        _require(stage6.get(key) is True, f"stage6.{key} must be true")
    for key in expected_stage6_false:
        _require(stage6.get(key) is False, f"stage6.{key} must be false")
    _require(stage6.get("next_safe_boundary") == NEXT_SAFE_BOUNDARY, "Stage 6 next-safe-boundary drifted")

    _require(value["stage7"] == {
        "entry_eligible": True,
        "entry_authorized": False,
        "preview_release_authorized": False,
        "started": False,
    }, "Stage 7 was prematurely authorized or started")

    assertions = value["assertions"]
    _require(assertions.get("historical_evidence_immutable") is True, "historical evidence must remain immutable")
    for key in (
        "historical_s6_08_checkpoint_rewritten",
        "real_or_derivative_bytes_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "raw_secrets_or_key_material_in_ordinary_git",
        "provider_selection_finalized",
        "live_resource_creation_authorized",
        "production_state_mutation_authorized",
        "production_operational_drills_authorized",
        "production_deployment_authorized",
        "production_load_or_soak_tests_authorized",
        "production_penetration_test_authorized",
        "production_concurrency_targets_or_failure_budgets_established",
        "threshold_changes_authorized",
        "resource_limit_changes_authorized",
        "held_out_retuning_authorized",
        "model_training_authorized",
        "publication_authorized",
        "stage7_entry_authorized",
        "preview_release_authorized",
        "color_management_validated",
        "color_fidelity_certified",
        "temporary_pr154_merge_authorized",
        "omr_correctness_established",
        "restoration_effectiveness_established",
        "production_availability_or_scalability_established",
        "provider_specific_security_certified",
    ):
        _require(assertions.get(key) is False, f"assertions.{key} must remain false")

    note = value["compatibility_note"]
    _require(isinstance(note, str) and "COMPLETE/PASS" in note, "compatibility note lost final state")
    _require("Provider selection remains UNSELECTED" in note, "compatibility note lost provider boundary")
    _require("Stage 7 entry" in note, "compatibility note lost Stage 7 boundary")
    return value


def summarize_stage6_final_exit_current_truth(
    raw: Mapping[str, Any],
    acceptance_raw: Mapping[str, Any],
    s6_08_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_final_exit_current_truth(raw, acceptance_raw, s6_08_current_truth_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "stage5State": "COMPLETE_PASS",
        "stage6State": "COMPLETE_PASS_PROVIDER_NEUTRAL",
        "stage6ExitPass": True,
        "providerSelectionStatus": "UNSELECTED",
        "productionDeploymentAuthorized": False,
        "stage7EntryEligible": True,
        "stage7EntryAuthorized": False,
        "stage7Started": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "CHECKPOINT_TYPE", "GATE_EXACT_HEAD_SHA", "GATE_MAIN_SHA", "GATE_MERGE_PR",
    "RECORDED_ON", "SCHEMA_VERSION", "Stage6FinalExitCurrentTruthError",
    "summarize_stage6_final_exit_current_truth", "validate_stage6_final_exit_current_truth",
]
