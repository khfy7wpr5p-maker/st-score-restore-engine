"""Production-effective current truth after Stage 6 S6-05 network implementation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .stage6_s6_05_authorization import (
    AUTHORIZATION_DECISION,
    AUTHORIZATION_ID,
    EXPECTED_CANONICAL_SHA256 as S6_05_AUTHORIZATION_DIGEST,
    NEXT_SAFE_BOUNDARY,
    validate_stage6_s6_05_authorization,
)

SCHEMA_VERSION = "1.0.0"
CHECKPOINT_TYPE = "stage6_s6_05_production_network_current_truth_overlay"
RECORDED_ON = "2026-09-05"
PROJECT = "ST Score Restore API / ST Score Restore Engine"
REPOSITORY = "khfy7wpr5p-maker/st-score-restore-engine"
GATE_MAIN_SHA = "7e7b772663f59d9a00413a87c73b84509834cfa6"
GATE_MERGE_PR = 165
GATE_PR_TITLE = "Stage 6: implement S6-05 production network boundary"
GATE_EXACT_HEAD_SHA = "efd3ac7fc49f1068488547bb595c7ecd196c0168"

STAGE6_ENTRY_DIGEST = "58d781f3c6b22ac8350f2f94a6902f76b6310fdf62486aa90c18382566a9e9b3"
S6_02_DECISION_DIGEST = "9485e51f1398c6cff2d9be9264eb8acdf47f8c4ca0fc750062fd9e80298e3865"
S6_03_AUTHORIZATION_DIGEST = "f82421eca0ed90defd04609054f47d1972b5327f71a7f35d644ac84c5f57ce39"
S6_04_AUTHORIZATION_DIGEST = "a14b4f6dfd8b7a32b3fd9acf9f5a79ecdf6d90cff40e0e842d5e33837d1c0cef"


class Stage6S605CurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage6S605CurrentTruthError(message)


def validate_stage6_s6_05_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    s6_04_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_s6_05_authorization(authorization_raw)

    previous = s6_04_current_truth_raw.get("stage6", {})
    _require(
        previous.get("state") == "ACTIVE_SECRETS_KMS_IAM_IMPLEMENTED_PROVIDER_UNSELECTED",
        "historical S6-04 state drifted",
    )
    _require(
        previous.get("production_network_implementation_authorized") is False,
        "historical S6-04 network authorization was broadened",
    )
    _require(
        s6_04_current_truth_raw.get("provider", {}).get("selection_status") == "UNSELECTED",
        "historical S6-04 provider state drifted",
    )
    _require(
        s6_04_current_truth_raw.get("assertions", {}).get("live_resource_creation_authorized") is False,
        "historical S6-04 live-resource boundary drifted",
    )

    _require(isinstance(raw, Mapping), "S6-05 current truth must be an object")
    value = deepcopy(dict(raw))
    expected_top = {
        "schema_version", "project", "repository", "checkpoint_type", "recorded_on",
        "production_checkpoint", "stage5", "stage6_entry_authorization", "s6_02_decision",
        "s6_03_authorization", "s6_04_authorization", "s6_05_authorization", "identity",
        "secrets_kms_iam", "network", "audit", "provider", "stage6", "stage7",
        "assertions", "compatibility_note",
    }
    _require(set(value) == expected_top, "S6-05 current-truth fields drifted")
    _require(value["schema_version"] == SCHEMA_VERSION, "schema drifted")
    _require(value["project"] == PROJECT and value["repository"] == REPOSITORY, "project/repository drifted")
    _require(value["checkpoint_type"] == CHECKPOINT_TYPE and value["recorded_on"] == RECORDED_ON, "checkpoint metadata drifted")

    _require(value["production_checkpoint"] == {
        "main_sha": GATE_MAIN_SHA,
        "merge_pr": GATE_MERGE_PR,
        "merge_pr_title": GATE_PR_TITLE,
        "pr_exact_head_sha": GATE_EXACT_HEAD_SHA,
        "exact_head_repository_validation_run_id": 33966509577,
        "exact_head_repository_validation_run_number": 460,
        "exact_head_stage4_governance_run_id": 33966509553,
        "exact_head_stage4_governance_run_number": 71,
        "exact_head_stage5_governance_run_id": 33966509580,
        "exact_head_stage5_governance_run_number": 63,
        "exact_head_stage6_governance_run_id": 33966509539,
        "exact_head_stage6_governance_run_number": 22,
        "postmerge_repository_validation_run_id": 33966581756,
        "postmerge_repository_validation_run_number": 461,
        "postmerge_stage4_governance_run_id": 33966581828,
        "postmerge_stage4_governance_run_number": 72,
        "postmerge_stage5_governance_run_id": 33966581873,
        "postmerge_stage5_governance_run_number": 64,
        "postmerge_stage6_governance_run_id": 33966581791,
        "postmerge_stage6_governance_run_number": 23,
        "ci_status": "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows",
    }, "S6-05 production checkpoint drifted")

    _require(value["stage5"] == {
        "state": "COMPLETE_PASS",
        "exit_pass": True,
        "final_acceptance_digest": "467eaf11c451d114d3ef41afd44c87cf2dce5cb68f89a5d6cfc45a81e1eed9fc",
        "color_management_validated": False,
        "color_fidelity_certified": False,
    }, "Stage 5 truth drifted")
    _require(value["stage6_entry_authorization"] == {
        "authorization_id": "stage6.entry-governance-authorization.v1",
        "authorization_digest": STAGE6_ENTRY_DIGEST,
    }, "Stage 6 entry binding drifted")
    _require(value["s6_02_decision"] == {
        "decision_id": "stage6.s6-02.production-trust-boundary-decision.v1",
        "decision_digest": S6_02_DECISION_DIGEST,
    }, "S6-02 binding drifted")
    _require(value["s6_03_authorization"] == {
        "authorization_id": "stage6.s6-03.identity-authz-implementation-authorization.v1",
        "authorization_digest": S6_03_AUTHORIZATION_DIGEST,
    }, "S6-03 binding drifted")
    _require(value["s6_04_authorization"] == {
        "authorization_id": "stage6.s6-04.secrets-kms-iam-implementation-authorization.v1",
        "authorization_digest": S6_04_AUTHORIZATION_DIGEST,
    }, "S6-04 binding drifted")
    _require(value["s6_05_authorization"] == {
        "authorization_id": AUTHORIZATION_ID,
        "decision": AUTHORIZATION_DECISION,
        "authorization_digest": S6_05_AUTHORIZATION_DIGEST,
    }, "S6-05 authorization binding drifted")

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
        "provider_neutral_public_edge_contract_implemented": True,
        "managed_tls_evidence_required": True,
        "trusted_proxy_chain_validation": True,
        "forwarded_headers_fail_closed": True,
        "request_smuggling_normalization_required": True,
        "multipart_boundary_evidence_required": True,
        "waf_rate_quota_connection_evidence_required": True,
        "bounded_request_and_slow_client_evidence_required": True,
        "private_topology_deny_by_default": True,
        "quarantine_outbound_allowed": False,
        "egress_allowlist_ssrf_guard_implemented": True,
        "network_audit_dependency_fail_closed": True,
        "built_in_stdlib_public_edge_allowed": False,
        "provider_specific_network_adapter_activated": False,
        "live_network_resources_created": False,
        "provider_specific_request_smuggling_certified": False,
        "independent_production_security_signoff_complete": False,
    }, "network truth drifted")
    _require(value["audit"] == {
        "privacy_safe_security_audit_contract_implemented": True,
        "audit_dependency_fail_closed": True,
        "durable_append_only_tamper_evident_audit_store_implemented": False,
    }, "audit truth drifted")
    _require(value["provider"] == {
        "selection_status": "UNSELECTED",
        "provider_specific_evaluation_authorized": True,
        "provider_specific_network_activation_authorized": False,
        "live_network_resource_creation_authorized": False,
    }, "provider truth drifted")
    _require(value["stage6"] == {
        "state": "ACTIVE_NETWORK_SECURITY_IMPLEMENTED_PROVIDER_UNSELECTED",
        "entry_eligible": True,
        "entry_authorized": True,
        "started": True,
        "production_identity_implementation_authorized": True,
        "production_identity_contract_implemented": True,
        "production_secrets_kms_iam_implementation_authorized": True,
        "production_secrets_kms_iam_contract_implemented": True,
        "production_network_implementation_authorized": True,
        "production_network_security_contract_implemented": True,
        "provider_specific_identity_adapter_activated": False,
        "provider_specific_secrets_kms_iam_activated": False,
        "provider_specific_network_adapter_activated": False,
        "production_storage_deployment_implementation_authorized": False,
        "production_operational_drills_authorized": False,
        "production_deployment_authorized": False,
        "next_safe_boundary": NEXT_SAFE_BOUNDARY,
    }, "Stage 6 S6-05 state drifted or over-authorized")
    _require(value["stage7"] == {
        "entry_authorized": False,
        "preview_release_authorized": False,
        "started": False,
    }, "Stage 7 was prematurely authorized")

    assertions = value["assertions"]
    _require(isinstance(assertions, Mapping), "assertions must be an object")
    _require(assertions.get("historical_evidence_immutable") is True, "historical evidence must remain immutable")
    for key in (
        "historical_stage5_final_checkpoint_rewritten",
        "historical_stage6_entry_checkpoint_rewritten",
        "historical_s6_02_checkpoint_rewritten",
        "historical_s6_03_checkpoint_rewritten",
        "historical_s6_04_checkpoint_rewritten",
        "real_or_derivative_bytes_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "raw_secrets_or_key_material_in_ordinary_git",
        "provider_selection_finalized",
        "live_network_resource_creation_authorized",
        "provider_specific_network_certification_claimed",
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
    _require("No provider-specific network adapter" in note, "compatibility note lost live-network boundary")
    _require("Provider-specific request-smuggling certification" in note, "compatibility note lost certification caveat")
    return value


def summarize_stage6_s6_05_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    s6_04_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_s6_05_current_truth(raw, authorization_raw, s6_04_current_truth_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "stage5State": "COMPLETE_PASS",
        "stage6State": "ACTIVE_NETWORK_SECURITY_IMPLEMENTED_PROVIDER_UNSELECTED",
        "providerSelectionStatus": "UNSELECTED",
        "networkSecurityContractImplemented": True,
        "providerSpecificNetworkActivated": False,
        "liveNetworkResourcesCreated": False,
        "providerSpecificRequestSmugglingCertified": False,
        "productionStorageDeploymentAuthorized": False,
        "productionDeploymentAuthorized": False,
        "stage7EntryAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "CHECKPOINT_TYPE", "GATE_EXACT_HEAD_SHA", "GATE_MAIN_SHA", "GATE_MERGE_PR",
    "RECORDED_ON", "SCHEMA_VERSION", "Stage6S605CurrentTruthError",
    "summarize_stage6_s6_05_current_truth", "validate_stage6_s6_05_current_truth",
]
