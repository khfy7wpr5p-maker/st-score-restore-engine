"""Production-effective current truth after Stage 6 S6-07 synthetic operational drills."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .stage6_s6_07_authorization import (
    AUTHORIZATION_DECISION,
    AUTHORIZATION_ID,
    EXPECTED_CANONICAL_SHA256 as S6_07_AUTHORIZATION_DIGEST,
    NEXT_SAFE_BOUNDARY,
    validate_stage6_s6_07_authorization,
)

SCHEMA_VERSION = "1.0.0"
CHECKPOINT_TYPE = "stage6_s6_07_synthetic_operational_drills_current_truth_overlay"
RECORDED_ON = "2026-09-06"
PROJECT = "ST Score Restore API / ST Score Restore Engine"
REPOSITORY = "khfy7wpr5p-maker/st-score-restore-engine"
GATE_MAIN_SHA = "2b51c6fcc4a38a40a64445f9d2ba669971dbac33"
GATE_MERGE_PR = 169
GATE_PR_TITLE = "Stage 6: run S6-07 synthetic operational safety recovery drills"
GATE_EXACT_HEAD_SHA = "00f0442d61983754d694adf69e1a806505d21c38"


class Stage6S607CurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage6S607CurrentTruthError(message)


def validate_stage6_s6_07_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    s6_06_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_s6_07_authorization(authorization_raw)

    previous_stage6 = s6_06_current_truth_raw.get("stage6", {})
    _require(
        previous_stage6.get("state") == "ACTIVE_STORAGE_DEPLOYMENT_CONTRACTS_IMPLEMENTED_PROVIDER_UNSELECTED",
        "historical S6-06 state drifted",
    )
    _require(
        previous_stage6.get("production_operational_drills_authorized") is False,
        "historical S6-06 production operational-drills boundary drifted",
    )
    _require(
        s6_06_current_truth_raw.get("provider", {}).get("selection_status") == "UNSELECTED",
        "historical S6-06 provider state drifted",
    )
    _require(
        s6_06_current_truth_raw.get("deployment", {}).get("production_deployment_authorized") is False,
        "historical S6-06 deployment boundary drifted",
    )

    _require(isinstance(raw, Mapping), "S6-07 current truth must be an object")
    value = deepcopy(dict(raw))
    expected_top = {
        "schema_version", "project", "repository", "checkpoint_type", "recorded_on",
        "production_checkpoint", "stage5", "s6_07_authorization", "identity",
        "secrets_kms_iam", "network", "storage_queue_recovery", "operational_drills",
        "provider", "deployment", "stage6", "stage7", "assertions", "compatibility_note",
    }
    _require(set(value) == expected_top, "S6-07 current-truth fields drifted")
    _require(value["schema_version"] == SCHEMA_VERSION, "schema drifted")
    _require(value["project"] == PROJECT and value["repository"] == REPOSITORY, "project/repository drifted")
    _require(value["checkpoint_type"] == CHECKPOINT_TYPE and value["recorded_on"] == RECORDED_ON, "checkpoint metadata drifted")

    _require(value["production_checkpoint"] == {
        "main_sha": GATE_MAIN_SHA,
        "merge_pr": GATE_MERGE_PR,
        "merge_pr_title": GATE_PR_TITLE,
        "pr_exact_head_sha": GATE_EXACT_HEAD_SHA,
        "exact_head_repository_validation_run_id": 34048992353,
        "exact_head_repository_validation_run_number": 468,
        "exact_head_stage4_governance_run_id": 34048992372,
        "exact_head_stage4_governance_run_number": 79,
        "exact_head_stage5_governance_run_id": 34048992383,
        "exact_head_stage5_governance_run_number": 71,
        "exact_head_stage6_governance_run_id": 34048992386,
        "exact_head_stage6_governance_run_number": 30,
        "postmerge_repository_validation_run_id": 34049098330,
        "postmerge_repository_validation_run_number": 469,
        "postmerge_stage4_governance_run_id": 34049098325,
        "postmerge_stage4_governance_run_number": 80,
        "postmerge_stage5_governance_run_id": 34049098323,
        "postmerge_stage5_governance_run_number": 72,
        "postmerge_stage6_governance_run_id": 34049098386,
        "postmerge_stage6_governance_run_number": 31,
        "ci_status": "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows",
    }, "S6-07 production checkpoint drifted")

    _require(value["stage5"] == {
        "state": "COMPLETE_PASS",
        "exit_pass": True,
        "final_acceptance_digest": "467eaf11c451d114d3ef41afd44c87cf2dce5cb68f89a5d6cfc45a81e1eed9fc",
        "color_management_validated": False,
        "color_fidelity_certified": False,
    }, "Stage 5 truth drifted")
    _require(value["s6_07_authorization"] == {
        "authorization_id": AUTHORIZATION_ID,
        "decision": AUTHORIZATION_DECISION,
        "authorization_digest": S6_07_AUTHORIZATION_DIGEST,
    }, "S6-07 authorization binding drifted")

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
    required_storage_true = (
        "production_storage_deployment_contracts_implemented",
        "synthetic_operational_drills_complete",
        "bounded_synthetic_concurrency_stress_complete",
    )
    required_storage_false = (
        "provider_specific_storage_queue_adapter_activated",
        "live_storage_queue_resources_created",
        "production_distributed_stress_validation_complete",
        "production_load_or_soak_validated",
        "production_concurrency_targets_or_failure_budgets_validated",
    )
    for key in required_storage_true:
        _require(storage.get(key) is True, f"storage_queue_recovery.{key} must be true")
    for key in required_storage_false:
        _require(storage.get(key) is False, f"storage_queue_recovery.{key} must be false")

    drills = value["operational_drills"]
    for key in (
        "synthetic_only",
        "queue_redelivery_and_stale_worker_fencing_passed",
        "crash_recovery_and_idempotent_replay_passed",
        "deletion_restore_anti_resurrection_passed",
        "audit_dependency_fail_closed_passed",
        "deployment_candidate_and_rollback_gate_passed",
        "bounded_concurrency_and_idempotency_stress_passed",
        "synthetic_operational_drills_complete",
    ):
        _require(drills.get(key) is True, f"operational_drills.{key} must be true")
    for key in (
        "provider_calls_performed",
        "production_state_mutated",
        "production_deployment_performed",
        "provider_specific_operational_behavior_certified",
    ):
        _require(drills.get(key) is False, f"operational_drills.{key} must be false")

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

    _require(value["stage6"] == {
        "state": "ACTIVE_SYNTHETIC_OPERATIONAL_DRILLS_COMPLETE_PROVIDER_UNSELECTED",
        "entry_eligible": True,
        "entry_authorized": True,
        "started": True,
        "production_identity_contract_implemented": True,
        "production_secrets_kms_iam_contract_implemented": True,
        "production_network_security_contract_implemented": True,
        "production_storage_deployment_contracts_implemented": True,
        "synthetic_operational_drills_authorized": True,
        "synthetic_operational_drills_complete": True,
        "provider_specific_identity_adapter_activated": False,
        "provider_specific_secrets_kms_iam_activated": False,
        "provider_specific_network_adapter_activated": False,
        "provider_specific_storage_deployment_adapter_activated": False,
        "production_distributed_stress_validation_complete": False,
        "production_operational_drills_authorized": False,
        "production_deployment_authorized": False,
        "s6_08_integration_security_regression_authorized": False,
        "next_safe_boundary": NEXT_SAFE_BOUNDARY,
    }, "Stage 6 S6-07 state drifted or over-authorized")
    _require(value["stage7"] == {
        "entry_authorized": False,
        "preview_release_authorized": False,
        "started": False,
    }, "Stage 7 was prematurely authorized")

    assertions = value["assertions"]
    _require(assertions.get("historical_evidence_immutable") is True, "historical evidence must remain immutable")
    for key in (
        "historical_s6_06_checkpoint_rewritten",
        "real_or_derivative_bytes_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "raw_secrets_or_key_material_in_ordinary_git",
        "provider_selection_finalized",
        "live_resource_creation_authorized",
        "production_state_mutation_authorized",
        "production_operational_drills_authorized",
        "production_deployment_authorized",
        "production_load_or_soak_tests_authorized",
        "production_concurrency_targets_or_failure_budgets_established",
        "threshold_changes_authorized",
        "resource_limit_changes_authorized",
        "held_out_retuning_authorized",
        "model_training_authorized",
        "publication_authorized",
        "color_management_validated",
        "color_fidelity_certified",
        "temporary_pr154_merge_authorized",
    ):
        _require(assertions.get(key) is False, f"assertions.{key} must remain false")

    note = value["compatibility_note"]
    _require(isinstance(note, str) and "synthetic-only" in note, "compatibility note lost synthetic-only boundary")
    _require("Provider selection remains UNSELECTED" in note, "compatibility note lost provider boundary")
    _require("No provider API calls" in note, "compatibility note lost live-provider boundary")
    return value


def summarize_stage6_s6_07_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    s6_06_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_s6_07_current_truth(raw, authorization_raw, s6_06_current_truth_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "stage5State": "COMPLETE_PASS",
        "stage6State": "ACTIVE_SYNTHETIC_OPERATIONAL_DRILLS_COMPLETE_PROVIDER_UNSELECTED",
        "providerSelectionStatus": "UNSELECTED",
        "syntheticOperationalDrillsComplete": True,
        "boundedSyntheticConcurrencyStressComplete": True,
        "productionDistributedStressValidationComplete": False,
        "productionDeploymentAuthorized": False,
        "stage7EntryAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "CHECKPOINT_TYPE", "GATE_EXACT_HEAD_SHA", "GATE_MAIN_SHA", "GATE_MERGE_PR",
    "RECORDED_ON", "SCHEMA_VERSION", "Stage6S607CurrentTruthError",
    "summarize_stage6_s6_07_current_truth", "validate_stage6_s6_07_current_truth",
]
