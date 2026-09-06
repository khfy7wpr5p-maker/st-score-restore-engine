"""Production-effective current truth after Stage 6 S6-08 integration/security regression."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .stage6_s6_08_authorization import (
    AUTHORIZATION_DECISION,
    AUTHORIZATION_ID,
    EXPECTED_CANONICAL_SHA256 as S6_08_AUTHORIZATION_DIGEST,
    NEXT_SAFE_BOUNDARY,
    validate_stage6_s6_08_authorization,
)

SCHEMA_VERSION = "1.0.0"
CHECKPOINT_TYPE = "stage6_s6_08_integration_security_regression_current_truth_overlay"
RECORDED_ON = "2026-09-06"
PROJECT = "ST Score Restore API / ST Score Restore Engine"
REPOSITORY = "khfy7wpr5p-maker/st-score-restore-engine"
GATE_MAIN_SHA = "92fb71ea5d2200f709c530a645a1b841421aa4c5"
GATE_MERGE_PR = 172
GATE_PR_TITLE = "Stage 6: run S6-08 integration security regression"
GATE_EXACT_HEAD_SHA = "7f40135725096abba4003fe97d51e384b6b7274c"
S6_07_AUTHORIZATION_DIGEST = "d32fbe896fa718ec76de00c1de3802345c599ff667a85d00790291ec82183b1b"


class Stage6S608CurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage6S608CurrentTruthError(message)


def validate_stage6_s6_08_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    s6_07_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_s6_08_authorization(authorization_raw)

    previous_stage6 = s6_07_current_truth_raw.get("stage6", {})
    _require(
        previous_stage6.get("state") == "ACTIVE_SYNTHETIC_OPERATIONAL_DRILLS_COMPLETE_PROVIDER_UNSELECTED",
        "historical S6-07 state drifted",
    )
    _require(
        previous_stage6.get("synthetic_operational_drills_complete") is True,
        "historical S6-07 operational drill result drifted",
    )
    _require(
        previous_stage6.get("s6_08_integration_security_regression_authorized") is False,
        "historical S6-07 S6-08 authorization boundary drifted",
    )
    _require(
        s6_07_current_truth_raw.get("provider", {}).get("selection_status") == "UNSELECTED",
        "historical S6-07 provider state drifted",
    )
    _require(
        s6_07_current_truth_raw.get("deployment", {}).get("production_deployment_authorized") is False,
        "historical S6-07 deployment boundary drifted",
    )

    _require(isinstance(raw, Mapping), "S6-08 current truth must be an object")
    value = deepcopy(dict(raw))
    expected_top = {
        "schema_version", "project", "repository", "checkpoint_type", "recorded_on",
        "production_checkpoint", "stage5", "s6_07", "s6_08_authorization",
        "integration_security_regression", "identity", "secrets_kms_iam", "network",
        "storage_queue_recovery", "provider", "deployment", "stage6", "stage7",
        "assertions", "compatibility_note",
    }
    _require(set(value) == expected_top, "S6-08 current-truth fields drifted")
    _require(value["schema_version"] == SCHEMA_VERSION, "schema drifted")
    _require(value["project"] == PROJECT and value["repository"] == REPOSITORY, "project/repository drifted")
    _require(value["checkpoint_type"] == CHECKPOINT_TYPE and value["recorded_on"] == RECORDED_ON, "checkpoint metadata drifted")

    _require(value["production_checkpoint"] == {
        "main_sha": GATE_MAIN_SHA,
        "merge_pr": GATE_MERGE_PR,
        "merge_pr_title": GATE_PR_TITLE,
        "pr_exact_head_sha": GATE_EXACT_HEAD_SHA,
        "exact_head_repository_validation_run_id": 34051340029,
        "exact_head_repository_validation_run_number": 478,
        "exact_head_stage4_governance_run_id": 34051340019,
        "exact_head_stage4_governance_run_number": 89,
        "exact_head_stage5_governance_run_id": 34051340032,
        "exact_head_stage5_governance_run_number": 81,
        "exact_head_stage6_governance_run_id": 34051340015,
        "exact_head_stage6_governance_run_number": 40,
        "postmerge_repository_validation_run_id": 34051427805,
        "postmerge_repository_validation_run_number": 479,
        "postmerge_stage4_governance_run_id": 34051427788,
        "postmerge_stage4_governance_run_number": 90,
        "postmerge_stage5_governance_run_id": 34051427804,
        "postmerge_stage5_governance_run_number": 82,
        "postmerge_stage6_governance_run_id": 34051427807,
        "postmerge_stage6_governance_run_number": 41,
        "ci_status": "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows",
    }, "S6-08 production checkpoint drifted")

    _require(value["stage5"] == {
        "state": "COMPLETE_PASS",
        "exit_pass": True,
        "final_acceptance_digest": "467eaf11c451d114d3ef41afd44c87cf2dce5cb68f89a5d6cfc45a81e1eed9fc",
        "color_management_validated": False,
        "color_fidelity_certified": False,
    }, "Stage 5 truth drifted")
    _require(value["s6_07"] == {
        "authorization_digest": S6_07_AUTHORIZATION_DIGEST,
        "synthetic_operational_drills_complete": True,
    }, "S6-07 binding drifted")
    _require(value["s6_08_authorization"] == {
        "authorization_id": AUTHORIZATION_ID,
        "decision": AUTHORIZATION_DECISION,
        "authorization_digest": S6_08_AUTHORIZATION_DIGEST,
    }, "S6-08 authorization binding drifted")

    regression = value["integration_security_regression"]
    for key in (
        "synthetic_only",
        "trusted_edge_identity_iam_kms_storage_chain_passed",
        "legacy_identity_header_bypass_denied",
        "cross_tenant_job_access_denied",
        "identity_conflict_revocation_signature_denied",
        "cross_environment_secret_kms_denied",
        "security_audit_dependency_fail_closed",
        "edge_and_private_topology_bypass_denied",
        "storage_queue_deployment_fail_closed",
        "s6_07_operational_regression_replay_passed",
        "integration_security_regression_complete",
    ):
        _require(regression.get(key) is True, f"integration_security_regression.{key} must be true")
    for key in (
        "provider_calls_performed",
        "live_resources_created",
        "production_state_mutated",
        "production_deployment_performed",
        "provider_specific_security_certification_complete",
        "independent_penetration_test_or_security_signoff_complete",
    ):
        _require(regression.get(key) is False, f"integration_security_regression.{key} must be false")

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

    _require(value["stage6"] == {
        "state": "ACTIVE_INTEGRATION_SECURITY_REGRESSION_COMPLETE_PROVIDER_UNSELECTED",
        "entry_eligible": True,
        "entry_authorized": True,
        "started": True,
        "production_identity_contract_implemented": True,
        "production_secrets_kms_iam_contract_implemented": True,
        "production_network_security_contract_implemented": True,
        "production_storage_deployment_contracts_implemented": True,
        "synthetic_operational_drills_complete": True,
        "integration_security_regression_authorized": True,
        "integration_security_regression_complete": True,
        "provider_specific_identity_adapter_activated": False,
        "provider_specific_secrets_kms_iam_activated": False,
        "provider_specific_network_adapter_activated": False,
        "provider_specific_storage_deployment_adapter_activated": False,
        "production_distributed_stress_validation_complete": False,
        "production_load_or_soak_validated": False,
        "independent_penetration_test_or_security_signoff_complete": False,
        "production_operational_drills_authorized": False,
        "production_deployment_authorized": False,
        "s6_09_final_exit_authorized": False,
        "next_safe_boundary": NEXT_SAFE_BOUNDARY,
    }, "Stage 6 S6-08 state drifted or over-authorized")
    _require(value["stage7"] == {
        "entry_authorized": False,
        "preview_release_authorized": False,
        "started": False,
    }, "Stage 7 was prematurely authorized")

    assertions = value["assertions"]
    _require(assertions.get("historical_evidence_immutable") is True, "historical evidence must remain immutable")
    for key in (
        "historical_s6_07_checkpoint_rewritten",
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
        "color_management_validated",
        "color_fidelity_certified",
        "temporary_pr154_merge_authorized",
    ):
        _require(assertions.get(key) is False, f"assertions.{key} must remain false")

    note = value["compatibility_note"]
    _require(isinstance(note, str) and "provider-neutral synthetic" in note, "compatibility note lost synthetic boundary")
    _require("Provider selection remains UNSELECTED" in note, "compatibility note lost provider boundary")
    _require("No provider API calls" in note, "compatibility note lost provider-call boundary")
    _require("independent penetration test/security sign-off" in note, "compatibility note lost independent-signoff boundary")
    return value


def summarize_stage6_s6_08_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    s6_07_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_s6_08_current_truth(raw, authorization_raw, s6_07_current_truth_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "stage5State": "COMPLETE_PASS",
        "stage6State": "ACTIVE_INTEGRATION_SECURITY_REGRESSION_COMPLETE_PROVIDER_UNSELECTED",
        "providerSelectionStatus": "UNSELECTED",
        "syntheticOperationalDrillsComplete": True,
        "integrationSecurityRegressionComplete": True,
        "productionDistributedStressValidationComplete": False,
        "independentSecuritySignoffComplete": False,
        "productionDeploymentAuthorized": False,
        "stage7EntryAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "CHECKPOINT_TYPE", "GATE_EXACT_HEAD_SHA", "GATE_MAIN_SHA", "GATE_MERGE_PR",
    "RECORDED_ON", "SCHEMA_VERSION", "Stage6S608CurrentTruthError",
    "summarize_stage6_s6_08_current_truth", "validate_stage6_s6_08_current_truth",
]
