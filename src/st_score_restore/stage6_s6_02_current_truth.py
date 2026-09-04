"""Production-effective current truth after Stage 6 S6-02 approval.

This overlay records the S6-02 trust-boundary decision without rewriting the
historical Stage 5 final checkpoint or the earlier Stage 6 entry checkpoint.
Provider selection remains UNSELECTED and all production implementation/resource
creation remains separately unauthorized.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .stage6_trust_boundary_decision import (
    DECISION,
    DECISION_CANONICAL_SHA256,
    DECISION_ID,
    NEXT_SAFE_BOUNDARY,
    validate_stage6_trust_boundary_decision,
)

SCHEMA_VERSION = "1.0.0"
CHECKPOINT_TYPE = "stage6_s6_02_trust_boundary_current_truth_overlay"
RECORDED_ON = "2026-09-04"
PROJECT = "ST Score Restore API / ST Score Restore Engine"
REPOSITORY = "khfy7wpr5p-maker/st-score-restore-engine"
STAGE5_FINAL_ACCEPTANCE_DIGEST = "467eaf11c451d114d3ef41afd44c87cf2dce5cb68f89a5d6cfc45a81e1eed9fc"
STAGE6_ENTRY_AUTHORIZATION_DIGEST = "58d781f3c6b22ac8350f2f94a6902f76b6310fdf62486aa90c18382566a9e9b3"

GATE_MAIN_SHA = "a2a329381d8ad61f4652e136d84298bbee709868"
GATE_MERGE_PR = 159
GATE_PR_TITLE = "Stage 6: approve S6-02 production trust boundary"
GATE_EXACT_HEAD_SHA = "6da86c094b81593baf12c49112bef29ba15efc47"

EXACT_REPOSITORY_RUN_ID = 33902013269
EXACT_REPOSITORY_RUN_NUMBER = 443
EXACT_STAGE4_RUN_ID = 33902013339
EXACT_STAGE4_RUN_NUMBER = 54
EXACT_STAGE5_RUN_ID = 33902013405
EXACT_STAGE5_RUN_NUMBER = 46
EXACT_STAGE6_RUN_ID = 33902013295
EXACT_STAGE6_RUN_NUMBER = 5
POSTMERGE_REPOSITORY_RUN_ID = 33902106239
POSTMERGE_REPOSITORY_RUN_NUMBER = 444
POSTMERGE_STAGE4_RUN_ID = 33902106404
POSTMERGE_STAGE4_RUN_NUMBER = 55
POSTMERGE_STAGE5_RUN_ID = 33902106493
POSTMERGE_STAGE5_RUN_NUMBER = 47
POSTMERGE_STAGE6_RUN_ID = 33902106335
POSTMERGE_STAGE6_RUN_NUMBER = 6


class Stage6S602CurrentTruthError(ValueError):
    """S6-02 production-effective current truth is malformed or over-broad."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage6S602CurrentTruthError(message)


def validate_stage6_s6_02_current_truth(
    raw: Mapping[str, Any],
    decision_raw: Mapping[str, Any],
    entry_current_truth_raw: Mapping[str, Any],
    entry_authorization_raw: Mapping[str, Any],
    stage5_final_acceptance_raw: Mapping[str, Any],
    historical_stage5_final_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_trust_boundary_decision(
        decision_raw,
        entry_current_truth_raw,
        entry_authorization_raw,
        stage5_final_acceptance_raw,
        historical_stage5_final_truth_raw,
    )

    earlier_stage6 = entry_current_truth_raw.get("stage6", {})
    _require(earlier_stage6.get("state") == "ACTIVE_GOVERNANCE_PROVIDER_NEUTRAL_ONLY", "earlier Stage 6 entry checkpoint drifted")
    _require(earlier_stage6.get("provider_specific_trust_boundary_decision_package_authorized") is False, "earlier Stage 6 checkpoint was retroactively rewritten")
    _require(earlier_stage6.get("production_identity_implementation_authorized") is False, "earlier Stage 6 checkpoint was broadened")

    _require(isinstance(raw, Mapping), "S6-02 current-truth overlay must be an object")
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
            "identity",
            "provider",
            "stage6",
            "stage7",
            "assertions",
            "compatibility_note",
        },
        "S6-02 current-truth top-level fields drifted",
    )
    _require(value["schema_version"] == SCHEMA_VERSION, "S6-02 current-truth schema drifted")
    _require(value["project"] == PROJECT, "project drifted")
    _require(value["repository"] == REPOSITORY, "repository drifted")
    _require(value["checkpoint_type"] == CHECKPOINT_TYPE, "checkpoint type drifted")
    _require(value["recorded_on"] == RECORDED_ON, "recorded date drifted")

    expected_checkpoint = {
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
    }
    _require(value["production_checkpoint"] == expected_checkpoint, "S6-02 production checkpoint drifted")

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
            "decision_id": DECISION_ID,
            "decision": DECISION,
            "decision_digest": DECISION_CANONICAL_SHA256,
        },
        "S6-02 decision binding drifted",
    )
    _require(
        value["identity"] == {
            "architecture": "shared_capable_identity_plane",
            "initial_relying_parties": ["st-score-restore"],
            "future_relying_party_integration_requires_separate_authorization": True,
            "production_caller_supplied_actor_id_allowed": False,
            "production_static_api_keys_allowed": False,
        },
        "identity current truth drifted",
    )
    _require(
        value["provider"] == {
            "selection_status": "UNSELECTED",
            "provider_specific_evaluation_authorized": True,
            "provider_specific_implementation_authorized": False,
        },
        "provider current truth drifted",
    )
    _require(
        value["stage6"] == {
            "state": "ACTIVE_GOVERNANCE_TRUST_BOUNDARY_DECIDED_PROVIDER_UNSELECTED",
            "entry_eligible": True,
            "entry_authorized": True,
            "started": True,
            "provider_neutral_architecture_and_contract_work_authorized": True,
            "provider_specific_trust_boundary_decision_package_authorized": True,
            "production_identity_implementation_authorized": False,
            "production_secrets_kms_iam_implementation_authorized": False,
            "production_network_implementation_authorized": False,
            "production_storage_deployment_implementation_authorized": False,
            "production_operational_drills_authorized": False,
            "production_deployment_authorized": False,
            "next_safe_boundary": NEXT_SAFE_BOUNDARY,
        },
        "Stage 6 S6-02 state drifted or over-authorized",
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
        "S6-02 safety assertions drifted",
    )
    _require(
        value["compatibility_note"]
        == "This overlay records production-effective S6-02 trust-boundary approval from PR #159 without rewriting the historical Stage 5 final checkpoint or the earlier Stage 6 entry checkpoint. The reusable identity plane is architecturally shared-capable but ST Score Restore is the only initial relying party. Provider selection remains UNSELECTED. Production identity, secrets/KMS/IAM, network, storage/deployment implementation, live resource creation, operational drills, production deployment, Stage 7, threshold/resource changes, held-out retuning, training and publication remain separately unauthorized.",
        "S6-02 compatibility note drifted",
    )
    return value


def summarize_stage6_s6_02_current_truth(
    raw: Mapping[str, Any],
    decision_raw: Mapping[str, Any],
    entry_current_truth_raw: Mapping[str, Any],
    entry_authorization_raw: Mapping[str, Any],
    stage5_final_acceptance_raw: Mapping[str, Any],
    historical_stage5_final_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_s6_02_current_truth(
        raw,
        decision_raw,
        entry_current_truth_raw,
        entry_authorization_raw,
        stage5_final_acceptance_raw,
        historical_stage5_final_truth_raw,
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "stage5State": "COMPLETE_PASS",
        "stage6State": "ACTIVE_GOVERNANCE_TRUST_BOUNDARY_DECIDED_PROVIDER_UNSELECTED",
        "identityArchitecture": "shared_capable_identity_plane",
        "initialRelyingParties": ["st-score-restore"],
        "providerSelectionStatus": "UNSELECTED",
        "productionImplementationAuthorized": False,
        "productionDeploymentAuthorized": False,
        "stage7EntryAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "CHECKPOINT_TYPE",
    "GATE_EXACT_HEAD_SHA",
    "GATE_MAIN_SHA",
    "GATE_MERGE_PR",
    "RECORDED_ON",
    "SCHEMA_VERSION",
    "Stage6S602CurrentTruthError",
    "summarize_stage6_s6_02_current_truth",
    "validate_stage6_s6_02_current_truth",
]
