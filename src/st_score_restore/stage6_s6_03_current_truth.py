"""Production-effective current truth after Stage 6 S6-03 identity/authz implementation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .stage6_s6_03_authorization import (
    AUTHORIZATION_DECISION,
    AUTHORIZATION_ID,
    EXPECTED_CANONICAL_SHA256 as S6_03_AUTHORIZATION_DIGEST,
    validate_stage6_s6_03_authorization,
)

SCHEMA_VERSION = "1.0.0"
CHECKPOINT_TYPE = "stage6_s6_03_identity_authz_current_truth_overlay"
RECORDED_ON = "2026-09-04"
PROJECT = "ST Score Restore API / ST Score Restore Engine"
REPOSITORY = "khfy7wpr5p-maker/st-score-restore-engine"
STAGE5_FINAL_ACCEPTANCE_DIGEST = "467eaf11c451d114d3ef41afd44c87cf2dce5cb68f89a5d6cfc45a81e1eed9fc"
STAGE6_ENTRY_AUTHORIZATION_DIGEST = "58d781f3c6b22ac8350f2f94a6902f76b6310fdf62486aa90c18382566a9e9b3"
S6_02_DECISION_DIGEST = "9485e51f1398c6cff2d9be9264eb8acdf47f8c4ca0fc750062fd9e80298e3865"

GATE_MAIN_SHA = "098691022ec613e271ebcc3d8b535c1d50abc554"
GATE_MERGE_PR = 161
GATE_PR_TITLE = "Stage 6: implement S6-03 production identity and authorization"
GATE_EXACT_HEAD_SHA = "d36e69f77234c38d60a9396285a11a3aef84395c"

EXACT_REPOSITORY_RUN_ID = 33918307959
EXACT_REPOSITORY_RUN_NUMBER = 452
EXACT_STAGE4_RUN_ID = 33918307957
EXACT_STAGE4_RUN_NUMBER = 63
EXACT_STAGE5_RUN_ID = 33918307961
EXACT_STAGE5_RUN_NUMBER = 55
EXACT_STAGE6_RUN_ID = 33918308064
EXACT_STAGE6_RUN_NUMBER = 14
POSTMERGE_REPOSITORY_RUN_ID = 33918444370
POSTMERGE_REPOSITORY_RUN_NUMBER = 453
POSTMERGE_STAGE4_RUN_ID = 33918444378
POSTMERGE_STAGE4_RUN_NUMBER = 64
POSTMERGE_STAGE5_RUN_ID = 33918444380
POSTMERGE_STAGE5_RUN_NUMBER = 56
POSTMERGE_STAGE6_RUN_ID = 33918444367
POSTMERGE_STAGE6_RUN_NUMBER = 15
NEXT_SAFE_BOUNDARY = "separate_explicit_s6_04_secrets_kms_iam_implementation_authorization"


class Stage6S603CurrentTruthError(ValueError):
    """S6-03 production-effective current truth is malformed or over-broad."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage6S603CurrentTruthError(message)


def validate_stage6_s6_03_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    s6_02_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_s6_03_authorization(authorization_raw)

    earlier_stage6 = s6_02_current_truth_raw.get("stage6", {})
    _require(
        earlier_stage6.get("state") == "ACTIVE_GOVERNANCE_TRUST_BOUNDARY_DECIDED_PROVIDER_UNSELECTED",
        "historical S6-02 state drifted",
    )
    _require(
        earlier_stage6.get("production_identity_implementation_authorized") is False,
        "historical S6-02 identity authorization was retroactively broadened",
    )
    _require(
        s6_02_current_truth_raw.get("provider", {}).get("selection_status") == "UNSELECTED",
        "historical S6-02 provider state drifted",
    )

    _require(isinstance(raw, Mapping), "S6-03 current-truth overlay must be an object")
    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schema_version",
            "project",
            "repository",
            "checkpoint_type",
            "recorded_on",
            "production_checkpoint",
            "stage5",
            "stage6_entry_authorization",
            "s6_02_decision",
            "s6_03_authorization",
            "identity",
            "authorization",
            "provider",
            "stage6",
            "stage7",
            "assertions",
            "compatibility_note",
        },
        "S6-03 current-truth top-level fields drifted",
    )
    _require(value["schema_version"] == SCHEMA_VERSION, "S6-03 schema drifted")
    _require(value["project"] == PROJECT, "project drifted")
    _require(value["repository"] == REPOSITORY, "repository drifted")
    _require(value["checkpoint_type"] == CHECKPOINT_TYPE, "checkpoint type drifted")
    _require(value["recorded_on"] == RECORDED_ON, "recorded date drifted")

    _require(
        value["production_checkpoint"] == {
            "main_sha": GATE_MAIN_SHA,
            "merge_pr": GATE_MERGE_PR,
            "merge_pr_title": GATE_PR_TITLE,
            "pr_exact_head_sha": GATE_EXACT_HEAD_SHA,
            "exact_head_repository_validation_run_id": EXACT_REPOSITORY_RUN_ID,
            "exact_head_repository_validation_run_number": EXACT_REPOSITORY_RUN_NUMBER,
            "exact_head_stage4_governance_run_id": EXACT_STAGE4_RUN_ID,
            "exact_head_stage4_governance_run_number": EXACT_STAGE4_RUN_NUMBER,
            "exact_head_stage5_governance_run_id": EXACT_STAGE5_RUN_ID,
            "exact_head_stage5_governance_run_number": EXACT_STAGE5_RUN_NUMBER,
            "exact_head_stage6_governance_run_id": EXACT_STAGE6_RUN_ID,
            "exact_head_stage6_governance_run_number": EXACT_STAGE6_RUN_NUMBER,
            "postmerge_repository_validation_run_id": POSTMERGE_REPOSITORY_RUN_ID,
            "postmerge_repository_validation_run_number": POSTMERGE_REPOSITORY_RUN_NUMBER,
            "postmerge_stage4_governance_run_id": POSTMERGE_STAGE4_RUN_ID,
            "postmerge_stage4_governance_run_number": POSTMERGE_STAGE4_RUN_NUMBER,
            "postmerge_stage5_governance_run_id": POSTMERGE_STAGE5_RUN_ID,
            "postmerge_stage5_governance_run_number": POSTMERGE_STAGE5_RUN_NUMBER,
            "postmerge_stage6_governance_run_id": POSTMERGE_STAGE6_RUN_ID,
            "postmerge_stage6_governance_run_number": POSTMERGE_STAGE6_RUN_NUMBER,
            "ci_status": "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows",
        },
        "S6-03 production checkpoint drifted",
    )
    _require(
        value["stage5"] == {
            "state": "COMPLETE_PASS",
            "exit_pass": True,
            "final_acceptance_digest": STAGE5_FINAL_ACCEPTANCE_DIGEST,
            "color_management_validated": False,
            "color_fidelity_certified": False,
        },
        "Stage 5 truth drifted",
    )
    _require(
        value["stage6_entry_authorization"] == {
            "authorization_id": "stage6.entry-governance-authorization.v1",
            "authorization_digest": STAGE6_ENTRY_AUTHORIZATION_DIGEST,
        },
        "Stage 6 entry authorization binding drifted",
    )
    _require(
        value["s6_02_decision"] == {
            "decision_id": "stage6.s6-02.production-trust-boundary-decision.v1",
            "decision_digest": S6_02_DECISION_DIGEST,
        },
        "S6-02 decision binding drifted",
    )
    _require(
        value["s6_03_authorization"] == {
            "authorization_id": AUTHORIZATION_ID,
            "decision": AUTHORIZATION_DECISION,
            "authorization_digest": S6_03_AUTHORIZATION_DIGEST,
        },
        "S6-03 authorization binding drifted",
    )
    _require(
        value["identity"] == {
            "architecture": "shared_capable_identity_plane",
            "initial_relying_parties": ["st-score-restore"],
            "production_identity_contract_implemented": True,
            "provider_specific_signature_backend_activated": False,
            "issuer_audience_expiry_not_before_key_identity_enforced": True,
            "revocation_fail_closed": True,
            "opaque_principal_derivation": True,
            "production_caller_supplied_actor_id_allowed": False,
            "production_static_api_keys_allowed": False,
        },
        "identity current truth drifted",
    )
    _require(
        value["authorization"] == {
            "tenant_isolation_enforced": True,
            "client_job_ownership_enforced": True,
            "role_conflict_enforced": True,
            "principal_scoped_idempotency_enforced": True,
            "missing_security_binding_fails_closed": True,
            "durable_production_authorization_store_implemented": False,
            "atomic_job_authorization_cocommit_implemented": False,
        },
        "authorization current truth drifted",
    )
    _require(
        value["provider"] == {
            "selection_status": "UNSELECTED",
            "provider_specific_evaluation_authorized": True,
            "provider_specific_identity_adapter_activation_authorized": False,
            "live_identity_provider_resource_creation_authorized": False,
        },
        "provider current truth drifted",
    )
    _require(
        value["stage6"] == {
            "state": "ACTIVE_IDENTITY_AUTHZ_IMPLEMENTED_PROVIDER_UNSELECTED",
            "entry_eligible": True,
            "entry_authorized": True,
            "started": True,
            "provider_neutral_architecture_and_contract_work_authorized": True,
            "provider_specific_trust_boundary_decision_package_authorized": True,
            "production_identity_implementation_authorized": True,
            "production_identity_contract_implemented": True,
            "provider_specific_identity_adapter_activated": False,
            "production_secrets_kms_iam_implementation_authorized": False,
            "production_network_implementation_authorized": False,
            "production_storage_deployment_implementation_authorized": False,
            "production_operational_drills_authorized": False,
            "production_deployment_authorized": False,
            "next_safe_boundary": NEXT_SAFE_BOUNDARY,
        },
        "Stage 6 S6-03 state drifted or over-authorized",
    )
    _require(
        value["stage7"] == {
            "entry_authorized": False,
            "preview_release_authorized": False,
            "started": False,
        },
        "Stage 7 was prematurely authorized",
    )
    _require(
        value["assertions"] == {
            "historical_evidence_immutable": True,
            "historical_stage5_final_checkpoint_rewritten": False,
            "historical_stage6_entry_checkpoint_rewritten": False,
            "historical_s6_02_checkpoint_rewritten": False,
            "real_or_derivative_bytes_in_ordinary_git": False,
            "raw_private_metrics_in_ordinary_git": False,
            "provider_selection_finalized": False,
            "live_resource_creation_authorized": False,
            "production_threshold_changes_authorized": False,
            "production_resource_limit_changes_authorized": False,
            "held_out_retuning_authorized": False,
            "model_training_authorized": False,
            "publication_authorized": False,
            "color_management_validated": False,
            "color_fidelity_certified": False,
            "temporary_pr154_merge_authorized": False,
        },
        "S6-03 safety assertions drifted",
    )
    expected_note = (
        "This overlay records production-effective S6-03 provider-neutral identity and authorization implementation from PR #161 without rewriting historical Stage 5, Stage 6 entry or S6-02 checkpoints. The production contract validates signed identity evidence, derives opaque principals, fails closed on revocation and authorization-state uncertainty, enforces tenant isolation and client job ownership, and scopes idempotency to the authenticated principal. Provider selection remains UNSELECTED; no provider-specific identity adapter, live IdP resource, durable production authorization store, atomic job/authz co-commit, secrets/KMS/IAM, network, storage/deployment, operational drill, production deployment, Stage 7, threshold/resource change, held-out retuning, training or publication is activated or authorized by this checkpoint."
    )
    _require(value["compatibility_note"] == expected_note, "S6-03 compatibility note drifted")
    return value


def summarize_stage6_s6_03_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    s6_02_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_s6_03_current_truth(raw, authorization_raw, s6_02_current_truth_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "stage5State": "COMPLETE_PASS",
        "stage6State": "ACTIVE_IDENTITY_AUTHZ_IMPLEMENTED_PROVIDER_UNSELECTED",
        "providerSelectionStatus": "UNSELECTED",
        "productionIdentityContractImplemented": True,
        "providerSpecificIdentityAdapterActivated": False,
        "tenantIsolationEnforced": True,
        "clientJobOwnershipEnforced": True,
        "principalScopedIdempotencyEnforced": True,
        "durableProductionAuthorizationStoreImplemented": False,
        "atomicJobAuthorizationCocommitImplemented": False,
        "productionDeploymentAuthorized": False,
        "stage7EntryAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "CHECKPOINT_TYPE",
    "GATE_EXACT_HEAD_SHA",
    "GATE_MAIN_SHA",
    "GATE_MERGE_PR",
    "NEXT_SAFE_BOUNDARY",
    "RECORDED_ON",
    "SCHEMA_VERSION",
    "Stage6S603CurrentTruthError",
    "summarize_stage6_s6_03_current_truth",
    "validate_stage6_s6_03_current_truth",
]
