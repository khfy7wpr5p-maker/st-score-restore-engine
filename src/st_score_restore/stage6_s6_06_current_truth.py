"""Production-effective current truth after Stage 6 S6-06 storage/deployment implementation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .stage6_s6_06_authorization import (
    AUTHORIZATION_DECISION,
    AUTHORIZATION_ID,
    EXPECTED_CANONICAL_SHA256 as S6_06_AUTHORIZATION_DIGEST,
    NEXT_SAFE_BOUNDARY,
    validate_stage6_s6_06_authorization,
)

SCHEMA_VERSION = "1.0.0"
CHECKPOINT_TYPE = "stage6_s6_06_storage_deployment_current_truth_overlay"
RECORDED_ON = "2026-09-06"
PROJECT = "ST Score Restore API / ST Score Restore Engine"
REPOSITORY = "khfy7wpr5p-maker/st-score-restore-engine"
GATE_MAIN_SHA = "5b32db9b0f8a9b24421c687c987f107559ac987b"
GATE_MERGE_PR = 167
GATE_PR_TITLE = "Stage 6: implement S6-06 production storage deployment boundary"
GATE_EXACT_HEAD_SHA = "038b0c3b056937a6f7d5869d2946c6bc2dab5728"

STAGE6_ENTRY_DIGEST = "58d781f3c6b22ac8350f2f94a6902f76b6310fdf62486aa90c18382566a9e9b3"
S6_02_DECISION_DIGEST = "9485e51f1398c6cff2d9be9264eb8acdf47f8c4ca0fc750062fd9e80298e3865"
S6_03_AUTHORIZATION_DIGEST = "f82421eca0ed90defd04609054f47d1972b5327f71a7f35d644ac84c5f57ce39"
S6_04_AUTHORIZATION_DIGEST = "a14b4f6dfd8b7a32b3fd9acf9f5a79ecdf6d90cff40e0e842d5e33837d1c0cef"
S6_05_AUTHORIZATION_DIGEST = "6815772f8f393b2bf281c75cb4500035808ec7ee5dc083d822dcefca1db9716c"


class Stage6S606CurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage6S606CurrentTruthError(message)


def validate_stage6_s6_06_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    s6_05_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_s6_06_authorization(authorization_raw)

    previous = s6_05_current_truth_raw.get("stage6", {})
    _require(
        previous.get("state") == "ACTIVE_NETWORK_SECURITY_IMPLEMENTED_PROVIDER_UNSELECTED",
        "historical S6-05 state drifted",
    )
    _require(
        previous.get("production_storage_deployment_implementation_authorized") is False,
        "historical S6-05 storage/deployment authorization was broadened",
    )
    _require(
        s6_05_current_truth_raw.get("provider", {}).get("selection_status") == "UNSELECTED",
        "historical S6-05 provider state drifted",
    )
    _require(
        s6_05_current_truth_raw.get("assertions", {}).get("live_network_resource_creation_authorized") is False,
        "historical S6-05 live-resource boundary drifted",
    )

    _require(isinstance(raw, Mapping), "S6-06 current truth must be an object")
    value = deepcopy(dict(raw))
    expected_top = {
        "schema_version", "project", "repository", "checkpoint_type", "recorded_on",
        "production_checkpoint", "stage5", "stage6_entry_authorization", "s6_02_decision",
        "s6_03_authorization", "s6_04_authorization", "s6_05_authorization",
        "s6_06_authorization", "identity", "secrets_kms_iam", "network",
        "storage_queue_recovery", "audit", "deployment", "provider", "stage6",
        "stage7", "assertions", "compatibility_note",
    }
    _require(set(value) == expected_top, "S6-06 current-truth fields drifted")
    _require(value["schema_version"] == SCHEMA_VERSION, "schema drifted")
    _require(value["project"] == PROJECT and value["repository"] == REPOSITORY, "project/repository drifted")
    _require(value["checkpoint_type"] == CHECKPOINT_TYPE and value["recorded_on"] == RECORDED_ON, "checkpoint metadata drifted")

    _require(value["production_checkpoint"] == {
        "main_sha": GATE_MAIN_SHA,
        "merge_pr": GATE_MERGE_PR,
        "merge_pr_title": GATE_PR_TITLE,
        "pr_exact_head_sha": GATE_EXACT_HEAD_SHA,
        "exact_head_repository_validation_run_id": 34040419880,
        "exact_head_repository_validation_run_number": 464,
        "exact_head_stage4_governance_run_id": 34040419861,
        "exact_head_stage4_governance_run_number": 75,
        "exact_head_stage5_governance_run_id": 34040419896,
        "exact_head_stage5_governance_run_number": 67,
        "exact_head_stage6_governance_run_id": 34040419894,
        "exact_head_stage6_governance_run_number": 26,
        "postmerge_repository_validation_run_id": 34040489560,
        "postmerge_repository_validation_run_number": 465,
        "postmerge_stage4_governance_run_id": 34040489509,
        "postmerge_stage4_governance_run_number": 76,
        "postmerge_stage5_governance_run_id": 34040489491,
        "postmerge_stage5_governance_run_number": 68,
        "postmerge_stage6_governance_run_id": 34040489539,
        "postmerge_stage6_governance_run_number": 27,
        "ci_status": "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows",
    }, "S6-06 production checkpoint drifted")

    bindings = {
        "stage6_entry_authorization": ("authorization_id", "stage6.entry-governance-authorization.v1", "authorization_digest", STAGE6_ENTRY_DIGEST),
        "s6_02_decision": ("decision_id", "stage6.s6-02.production-trust-boundary-decision.v1", "decision_digest", S6_02_DECISION_DIGEST),
        "s6_03_authorization": ("authorization_id", "stage6.s6-03.identity-authz-implementation-authorization.v1", "authorization_digest", S6_03_AUTHORIZATION_DIGEST),
        "s6_04_authorization": ("authorization_id", "stage6.s6-04.secrets-kms-iam-implementation-authorization.v1", "authorization_digest", S6_04_AUTHORIZATION_DIGEST),
        "s6_05_authorization": ("authorization_id", "stage6.s6-05.production-network-implementation-authorization.v1", "authorization_digest", S6_05_AUTHORIZATION_DIGEST),
    }
    for section, (id_key, id_value, digest_key, digest_value) in bindings.items():
        _require(value[section] == {id_key: id_value, digest_key: digest_value}, f"{section} binding drifted")
    _require(value["s6_06_authorization"] == {
        "authorization_id": AUTHORIZATION_ID,
        "decision": AUTHORIZATION_DECISION,
        "authorization_digest": S6_06_AUTHORIZATION_DIGEST,
    }, "S6-06 authorization binding drifted")

    _require(value["stage5"] == {
        "state": "COMPLETE_PASS",
        "exit_pass": True,
        "final_acceptance_digest": "467eaf11c451d114d3ef41afd44c87cf2dce5cb68f89a5d6cfc45a81e1eed9fc",
        "color_management_validated": False,
        "color_fidelity_certified": False,
    }, "Stage 5 truth drifted")

    _require(value["identity"].get("production_identity_contract_implemented") is True, "identity contract missing")
    _require(value["identity"].get("provider_specific_identity_adapter_activated") is False, "identity provider adapter prematurely activated")
    _require(value["secrets_kms_iam"].get("production_secrets_kms_iam_contract_implemented") is True, "secrets/KMS/IAM contract missing")
    _require(value["secrets_kms_iam"].get("provider_specific_secrets_kms_iam_activated") is False, "provider secrets/KMS/IAM prematurely activated")
    _require(value["network"].get("production_network_security_contract_implemented") is True, "network contract missing")
    _require(value["network"].get("provider_specific_network_adapter_activated") is False, "provider network adapter prematurely activated")
    _require(value["network"].get("live_network_resources_created") is False, "live network resources unexpectedly created")

    storage = value["storage_queue_recovery"]
    for key in (
        "metadata_database_contract_implemented",
        "migration_and_rollback_contract_implemented",
        "encrypted_object_storage_contract_implemented",
        "tenant_scoping_contract_implemented",
        "external_durable_queue_contract_implemented",
        "lease_fencing_and_idempotency_contract_implemented",
        "crash_recovery_contract_implemented",
        "retention_two_stage_deletion_contract_implemented",
        "backup_restore_anti_resurrection_contract_implemented",
        "environment_isolation_contract_implemented",
    ):
        _require(storage.get(key) is True, f"storage_queue_recovery.{key} must be true")
    for key in (
        "provider_specific_storage_queue_adapter_activated",
        "live_storage_queue_resources_created",
        "distributed_stress_validation_complete",
        "synthetic_operational_drills_complete",
    ):
        _require(storage.get(key) is False, f"storage_queue_recovery.{key} must be false")

    audit = value["audit"]
    for key in (
        "privacy_safe_security_audit_contract_implemented",
        "provider_neutral_append_only_tamper_evident_contract_implemented",
        "independent_anti_rollback_anchor_required",
    ):
        _require(audit.get(key) is True, f"audit.{key} must be true")
    _require(audit.get("provider_specific_durable_audit_store_activated") is False, "durable provider audit store prematurely activated")
    _require(audit.get("live_audit_resource_created") is False, "live audit resource unexpectedly created")

    deployment = value["deployment"]
    for key in (
        "immutable_artifact_and_signed_provenance_contract_implemented",
        "staging_health_and_migration_preflight_contract_implemented",
        "rollback_contract_implemented",
        "secrets_excluded_from_artifact_contract_implemented",
        "privacy_safe_observability_contract_implemented",
    ):
        _require(deployment.get(key) is True, f"deployment.{key} must be true")
    for key in (
        "provider_specific_deployment_platform_activated",
        "production_deployment_authorized",
        "production_deployment_performed",
    ):
        _require(deployment.get(key) is False, f"deployment.{key} must remain false")

    _require(value["provider"] == {
        "selection_status": "UNSELECTED",
        "provider_specific_evaluation_authorized": True,
        "provider_specific_storage_deployment_activation_authorized": False,
        "live_resource_creation_authorized": False,
    }, "provider truth drifted")
    _require(value["stage6"] == {
        "state": "ACTIVE_STORAGE_DEPLOYMENT_CONTRACTS_IMPLEMENTED_PROVIDER_UNSELECTED",
        "entry_eligible": True,
        "entry_authorized": True,
        "started": True,
        "production_identity_contract_implemented": True,
        "production_secrets_kms_iam_contract_implemented": True,
        "production_network_security_contract_implemented": True,
        "production_storage_deployment_implementation_authorized": True,
        "production_storage_deployment_contracts_implemented": True,
        "provider_specific_identity_adapter_activated": False,
        "provider_specific_secrets_kms_iam_activated": False,
        "provider_specific_network_adapter_activated": False,
        "provider_specific_storage_deployment_adapter_activated": False,
        "production_operational_drills_authorized": False,
        "production_deployment_authorized": False,
        "next_safe_boundary": NEXT_SAFE_BOUNDARY,
    }, "Stage 6 S6-06 state drifted or over-authorized")
    _require(value["stage7"] == {
        "entry_authorized": False,
        "preview_release_authorized": False,
        "started": False,
    }, "Stage 7 was prematurely authorized")

    assertions = value["assertions"]
    _require(assertions.get("historical_evidence_immutable") is True, "historical evidence must remain immutable")
    for key in (
        "historical_stage5_final_checkpoint_rewritten",
        "historical_stage6_entry_checkpoint_rewritten",
        "historical_s6_02_checkpoint_rewritten",
        "historical_s6_03_checkpoint_rewritten",
        "historical_s6_04_checkpoint_rewritten",
        "historical_s6_05_checkpoint_rewritten",
        "local_sqlite_promoted_to_production",
        "real_or_derivative_bytes_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "raw_secrets_or_key_material_in_ordinary_git",
        "provider_selection_finalized",
        "live_resource_creation_authorized",
        "production_deployment_authorized",
        "production_operational_drills_authorized",
        "production_threshold_changes_authorized",
        "production_resource_limit_changes_authorized",
        "held_out_retuning_authorized",
        "model_training_authorized",
        "publication_authorized",
        "color_management_validated",
        "color_fidelity_certified",
        "temporary_pr154_merge_authorized",
    ):
        _require(assertions.get(key) is False, f"assertions.{key} must remain false")

    note = value["compatibility_note"]
    _require(isinstance(note, str) and "Provider selection remains UNSELECTED" in note, "compatibility note lost provider boundary")
    _require("local SQLite/content-addressed baseline remains non-production" in note, "compatibility note lost local-baseline boundary")
    _require("No provider-specific database" in note, "compatibility note lost live-resource boundary")
    return value


def summarize_stage6_s6_06_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    s6_05_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_s6_06_current_truth(raw, authorization_raw, s6_05_current_truth_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "stage5State": "COMPLETE_PASS",
        "stage6State": "ACTIVE_STORAGE_DEPLOYMENT_CONTRACTS_IMPLEMENTED_PROVIDER_UNSELECTED",
        "providerSelectionStatus": "UNSELECTED",
        "storageDeploymentContractsImplemented": True,
        "providerSpecificStorageDeploymentActivated": False,
        "liveResourcesCreated": False,
        "productionOperationalDrillsAuthorized": False,
        "productionDeploymentAuthorized": False,
        "stage7EntryAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "CHECKPOINT_TYPE", "GATE_EXACT_HEAD_SHA", "GATE_MAIN_SHA", "GATE_MERGE_PR",
    "RECORDED_ON", "SCHEMA_VERSION", "Stage6S606CurrentTruthError",
    "summarize_stage6_s6_06_current_truth", "validate_stage6_s6_06_current_truth",
]
