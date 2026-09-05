"""Production-effective current truth after Stage 6 S6-04 secrets/KMS/IAM implementation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .stage6_s6_04_authorization import (
    AUTHORIZATION_DECISION,
    AUTHORIZATION_ID,
    EXPECTED_CANONICAL_SHA256 as S6_04_AUTHORIZATION_DIGEST,
    NEXT_SAFE_BOUNDARY,
    validate_stage6_s6_04_authorization,
)

SCHEMA_VERSION = "1.0.0"
CHECKPOINT_TYPE = "stage6_s6_04_secrets_kms_iam_current_truth_overlay"
RECORDED_ON = "2026-09-05"
PROJECT = "ST Score Restore API / ST Score Restore Engine"
REPOSITORY = "khfy7wpr5p-maker/st-score-restore-engine"
GATE_MAIN_SHA = "911fb8b228be64a66ba0a70405ef2c6f77a51dce"
GATE_MERGE_PR = 163
GATE_PR_TITLE = "Stage 6: implement S6-04 secrets KMS IAM boundary"
GATE_EXACT_HEAD_SHA = "38f4d099e09af21dad43742a4fcda5423b0c7644"
STAGE5_FINAL_ACCEPTANCE_DIGEST = "467eaf11c451d114d3ef41afd44c87cf2dce5cb68f89a5d6cfc45a81e1eed9fc"
STAGE6_ENTRY_AUTHORIZATION_DIGEST = "58d781f3c6b22ac8350f2f94a6902f76b6310fdf62486aa90c18382566a9e9b3"
S6_02_DECISION_DIGEST = "9485e51f1398c6cff2d9be9264eb8acdf47f8c4ca0fc750062fd9e80298e3865"
S6_03_AUTHORIZATION_DIGEST = "f82421eca0ed90defd04609054f47d1972b5327f71a7f35d644ac84c5f57ce39"


class Stage6S604CurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage6S604CurrentTruthError(message)


def validate_stage6_s6_04_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    s6_03_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_s6_04_authorization(authorization_raw)

    previous = s6_03_current_truth_raw.get("stage6", {})
    _require(
        previous.get("state") == "ACTIVE_IDENTITY_AUTHZ_IMPLEMENTED_PROVIDER_UNSELECTED",
        "historical S6-03 state drifted",
    )
    _require(previous.get("production_secrets_kms_iam_implementation_authorized") is False, "historical S6-03 was broadened")
    _require(s6_03_current_truth_raw.get("provider", {}).get("selection_status") == "UNSELECTED", "historical provider state drifted")

    _require(isinstance(raw, Mapping), "S6-04 current truth must be an object")
    value = deepcopy(dict(raw))
    expected_top = {
        "schema_version", "project", "repository", "checkpoint_type", "recorded_on",
        "production_checkpoint", "stage5", "stage6_entry_authorization", "s6_02_decision",
        "s6_03_authorization", "s6_04_authorization", "identity", "secrets", "kms", "iam",
        "audit", "provider", "stage6", "stage7", "assertions", "compatibility_note",
    }
    _require(set(value) == expected_top, "S6-04 current-truth fields drifted")
    _require(value["schema_version"] == SCHEMA_VERSION, "schema drifted")
    _require(value["project"] == PROJECT and value["repository"] == REPOSITORY, "project/repository drifted")
    _require(value["checkpoint_type"] == CHECKPOINT_TYPE and value["recorded_on"] == RECORDED_ON, "checkpoint metadata drifted")

    _require(value["production_checkpoint"] == {
        "main_sha": GATE_MAIN_SHA,
        "merge_pr": GATE_MERGE_PR,
        "merge_pr_title": GATE_PR_TITLE,
        "pr_exact_head_sha": GATE_EXACT_HEAD_SHA,
        "exact_head_repository_validation_run_id": 33960569854,
        "exact_head_repository_validation_run_number": 456,
        "exact_head_stage4_governance_run_id": 33960569858,
        "exact_head_stage4_governance_run_number": 67,
        "exact_head_stage5_governance_run_id": 33960569886,
        "exact_head_stage5_governance_run_number": 59,
        "exact_head_stage6_governance_run_id": 33960569871,
        "exact_head_stage6_governance_run_number": 18,
        "postmerge_repository_validation_run_id": 33960629792,
        "postmerge_repository_validation_run_number": 457,
        "postmerge_stage4_governance_run_id": 33960629826,
        "postmerge_stage4_governance_run_number": 68,
        "postmerge_stage5_governance_run_id": 33960629810,
        "postmerge_stage5_governance_run_number": 60,
        "postmerge_stage6_governance_run_id": 33960629845,
        "postmerge_stage6_governance_run_number": 19,
        "ci_status": "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows",
    }, "S6-04 production checkpoint drifted")

    _require(value["stage5"] == {
        "state": "COMPLETE_PASS",
        "exit_pass": True,
        "final_acceptance_digest": STAGE5_FINAL_ACCEPTANCE_DIGEST,
        "color_management_validated": False,
        "color_fidelity_certified": False,
    }, "Stage 5 truth drifted")
    _require(value["stage6_entry_authorization"] == {
        "authorization_id": "stage6.entry-governance-authorization.v1",
        "authorization_digest": STAGE6_ENTRY_AUTHORIZATION_DIGEST,
    }, "Stage 6 entry authorization binding drifted")
    _require(value["s6_02_decision"] == {
        "decision_id": "stage6.s6-02.production-trust-boundary-decision.v1",
        "decision_digest": S6_02_DECISION_DIGEST,
    }, "S6-02 decision binding drifted")
    _require(value["s6_03_authorization"] == {
        "authorization_id": "stage6.s6-03.identity-authz-implementation-authorization.v1",
        "authorization_digest": S6_03_AUTHORIZATION_DIGEST,
    }, "S6-03 authorization binding drifted")
    _require(value["s6_04_authorization"] == {
        "authorization_id": AUTHORIZATION_ID,
        "decision": AUTHORIZATION_DECISION,
        "authorization_digest": S6_04_AUTHORIZATION_DIGEST,
    }, "S6-04 authorization binding drifted")

    _require(value["identity"] == {
        "production_identity_contract_implemented": True,
        "provider_specific_identity_adapter_activated": False,
    }, "identity truth drifted")
    _require(value["secrets"] == {
        "provider_neutral_secret_boundary_implemented": True,
        "no_cache_rotation_aware_resolution": True,
        "redacted_secret_material_contract": True,
        "revocation_fail_closed": True,
        "provider_specific_secret_manager_activated": False,
        "live_secret_resource_created": False,
    }, "secret boundary truth drifted")
    _require(value["kms"] == {
        "provider_neutral_envelope_boundary_implemented": True,
        "key_state_revocation_fail_closed": True,
        "encryption_context_binding": True,
        "custom_production_cipher_implemented": False,
        "provider_specific_kms_activated": False,
        "live_key_created": False,
    }, "KMS boundary truth drifted")
    _require(value["iam"] == {
        "workload_identity_contract_implemented": True,
        "least_privilege_deny_by_default": True,
        "exact_no_wildcard_grants": True,
        "environment_separation_enforced": True,
        "separation_of_duties_enforced": True,
        "provider_specific_iam_bindings_activated": False,
        "live_iam_roles_or_policies_created": False,
    }, "IAM boundary truth drifted")
    _require(value["audit"] == {
        "privacy_safe_security_audit_contract_implemented": True,
        "audit_dependency_fail_closed": True,
        "durable_append_only_tamper_evident_audit_store_implemented": False,
    }, "audit boundary truth drifted")
    _require(value["provider"] == {
        "selection_status": "UNSELECTED",
        "provider_specific_evaluation_authorized": True,
        "provider_specific_secrets_kms_iam_activation_authorized": False,
        "live_security_resource_creation_authorized": False,
    }, "provider truth drifted")
    _require(value["stage6"] == {
        "state": "ACTIVE_SECRETS_KMS_IAM_IMPLEMENTED_PROVIDER_UNSELECTED",
        "entry_eligible": True,
        "entry_authorized": True,
        "started": True,
        "production_identity_implementation_authorized": True,
        "production_identity_contract_implemented": True,
        "production_secrets_kms_iam_implementation_authorized": True,
        "production_secrets_kms_iam_contract_implemented": True,
        "provider_specific_identity_adapter_activated": False,
        "provider_specific_secrets_kms_iam_activated": False,
        "production_network_implementation_authorized": False,
        "production_storage_deployment_implementation_authorized": False,
        "production_operational_drills_authorized": False,
        "production_deployment_authorized": False,
        "next_safe_boundary": NEXT_SAFE_BOUNDARY,
    }, "Stage 6 S6-04 state drifted or over-authorized")
    _require(value["stage7"] == {"entry_authorized": False, "preview_release_authorized": False, "started": False}, "Stage 7 was prematurely authorized")

    assertions = value["assertions"]
    _require(isinstance(assertions, Mapping), "assertions must be an object")
    _require(assertions.get("historical_evidence_immutable") is True, "historical evidence must remain immutable")
    for key in (
        "historical_stage5_final_checkpoint_rewritten",
        "historical_stage6_entry_checkpoint_rewritten",
        "historical_s6_02_checkpoint_rewritten",
        "historical_s6_03_checkpoint_rewritten",
        "real_or_derivative_bytes_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "raw_secrets_in_ordinary_git",
        "cryptographic_key_material_in_ordinary_git",
        "provider_selection_finalized",
        "live_resource_creation_authorized",
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
    _require("No provider-specific secret manager" in note, "compatibility note lost live-resource boundary")
    return value


def summarize_stage6_s6_04_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    s6_03_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_s6_04_current_truth(raw, authorization_raw, s6_03_current_truth_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "stage5State": "COMPLETE_PASS",
        "stage6State": "ACTIVE_SECRETS_KMS_IAM_IMPLEMENTED_PROVIDER_UNSELECTED",
        "providerSelectionStatus": "UNSELECTED",
        "secretsKmsIamContractImplemented": True,
        "providerSpecificSecretsKmsIamActivated": False,
        "liveSecurityResourcesCreated": False,
        "productionNetworkImplementationAuthorized": False,
        "productionDeploymentAuthorized": False,
        "stage7EntryAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "CHECKPOINT_TYPE", "GATE_EXACT_HEAD_SHA", "GATE_MAIN_SHA", "GATE_MERGE_PR",
    "RECORDED_ON", "SCHEMA_VERSION", "Stage6S604CurrentTruthError",
    "summarize_stage6_s6_04_current_truth", "validate_stage6_s6_04_current_truth",
]
