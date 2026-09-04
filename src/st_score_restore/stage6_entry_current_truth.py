"""Production-effective current truth after Stage 6 entry authorization.

This overlay records the later Stage 6 entry/governance-start decision without
rewriting the historical Stage 5 final-exit checkpoint. It permits only
provider-neutral governance, architecture and contract work. Provider-specific
trust-boundary decisions, production implementation/deployment, Stage 7,
threshold/resource changes, held-out retuning, training and publication remain
separately unauthorized.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .stage6_entry_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    AUTHORIZATION_DECISION,
    AUTHORIZATION_ID,
    NEXT_SAFE_BOUNDARY,
    STAGE5_FINAL_ACCEPTANCE_DIGEST,
    STAGE6_PURPOSE,
    validate_stage6_entry_authorization,
)

SCHEMA_VERSION = "1.0.0"
CHECKPOINT_TYPE = "stage6_entry_governance_authorization_current_truth_overlay"
RECORDED_ON = "2026-09-04"
PROJECT = "ST Score Restore API / ST Score Restore Engine"
REPOSITORY = "khfy7wpr5p-maker/st-score-restore-engine"

GATE_MAIN_SHA = "cb3e5189d79992a06df594cdb60af5c658932719"
GATE_MERGE_PR = 157
GATE_PR_TITLE = "Stage 6: authorize entry and governance start"
GATE_EXACT_HEAD_SHA = "467282cbf7c55c1f493212e63fac8c43b11423d8"

EXACT_REPOSITORY_RUN_ID = 33900390609
EXACT_REPOSITORY_RUN_NUMBER = 439
EXACT_STAGE4_RUN_ID = 33900390565
EXACT_STAGE4_RUN_NUMBER = 50
EXACT_STAGE5_RUN_ID = 33900390632
EXACT_STAGE5_RUN_NUMBER = 42
EXACT_STAGE6_RUN_ID = 33900391497
EXACT_STAGE6_RUN_NUMBER = 1
POSTMERGE_REPOSITORY_RUN_ID = 33900500539
POSTMERGE_REPOSITORY_RUN_NUMBER = 440
POSTMERGE_STAGE4_RUN_ID = 33900500642
POSTMERGE_STAGE4_RUN_NUMBER = 51
POSTMERGE_STAGE5_RUN_ID = 33900500551
POSTMERGE_STAGE5_RUN_NUMBER = 43
POSTMERGE_STAGE6_RUN_ID = 33900500584
POSTMERGE_STAGE6_RUN_NUMBER = 2


class Stage6EntryCurrentTruthError(ValueError):
    """Stage 6 post-entry current truth is malformed, stale, or unsafe."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage6EntryCurrentTruthError(message)


def validate_stage6_entry_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    stage5_final_acceptance_raw: Mapping[str, Any],
    historical_stage5_final_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_entry_authorization(
        authorization_raw,
        stage5_final_acceptance_raw,
        historical_stage5_final_truth_raw,
    )

    historical_stage6 = historical_stage5_final_truth_raw.get("stage6", {})
    _require(historical_stage6.get("entry_eligible") is True, "historical Stage 6 eligibility drifted")
    _require(historical_stage6.get("entry_authorized") is False, "historical Stage 5 final checkpoint was retroactively rewritten")
    _require(historical_stage6.get("started") is False, "historical Stage 5 final checkpoint was retroactively rewritten to start Stage 6")

    _require(isinstance(raw, Mapping), "Stage 6 current-truth overlay must be an object")
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
            "stage6",
            "stage7",
            "assertions",
            "compatibility_note",
        },
        "Stage 6 current-truth top-level fields drifted",
    )
    _require(value["schema_version"] == SCHEMA_VERSION, "current-truth schema drifted")
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
    _require(value["production_checkpoint"] == expected_checkpoint, "production checkpoint drifted")

    _require(
        value["stage5"] == {
            "state": "COMPLETE_PASS",
            "exit_pass": True,
            "final_acceptance_digest": STAGE5_FINAL_ACCEPTANCE_DIGEST,
            "color_management_validated": False,
            "color_fidelity_certified": False,
        },
        "Stage 5 final truth drifted",
    )
    _require(
        value["stage6_entry_authorization"] == {
            "authorization_id": AUTHORIZATION_ID,
            "decision": AUTHORIZATION_DECISION,
            "authorization_digest": AUTHORIZATION_CANONICAL_SHA256,
            "purpose": STAGE6_PURPOSE,
        },
        "Stage 6 entry authorization truth drifted",
    )
    _require(
        value["stage6"] == {
            "state": "ACTIVE_GOVERNANCE_PROVIDER_NEUTRAL_ONLY",
            "entry_eligible": True,
            "entry_authorized": True,
            "started": True,
            "provider_neutral_architecture_and_contract_work_authorized": True,
            "provider_specific_trust_boundary_decision_package_authorized": False,
            "production_identity_implementation_authorized": False,
            "production_secrets_kms_iam_implementation_authorized": False,
            "production_network_implementation_authorized": False,
            "production_storage_deployment_implementation_authorized": False,
            "production_operational_drills_authorized": False,
            "production_deployment_authorized": False,
            "next_safe_boundary": NEXT_SAFE_BOUNDARY,
        },
        "Stage 6 current state drifted or over-authorized",
    )
    _require(
        value["stage7"] == {
            "entry_authorized": False,
            "preview_release_authorized": False,
            "started": False,
        },
        "Stage 7 was prematurely authorized or started",
    )

    expected_assertions = {
        "historical_evidence_immutable": True,
        "historical_stage5_final_checkpoint_rewritten": False,
        "real_or_derivative_bytes_in_ordinary_git": False,
        "raw_private_metrics_in_ordinary_git": False,
        "production_threshold_changes_authorized": False,
        "production_resource_limit_changes_authorized": False,
        "held_out_retuning_authorized": False,
        "model_training_authorized": False,
        "publication_authorized": False,
        "color_management_validated": False,
        "color_fidelity_certified": False,
        "temporary_pr154_merge_authorized": False,
        "representativeness_established": False,
        "absence_of_bias_established": False,
        "omr_correctness_established": False,
        "restoration_effectiveness_established": False,
    }
    _require(value["assertions"] == expected_assertions, "Stage 6 safety assertions drifted")
    _require(
        value["compatibility_note"]
        == "This later overlay records production-effective Stage 6 entry authorization and provider-neutral governance start from PR #157. The historical Stage 5 final-exit checkpoint remains immutable with Stage 6 entry authorization=false. Stage 6 is now active only for provider-neutral governance, architecture and contract work; provider-specific trust-boundary decisions, production identity/network/storage/KMS implementation, operational resource creation, production deployment, Stage 7 preview release, threshold/resource changes, held-out retuning, training and publication remain separately unauthorized.",
        "compatibility note drifted",
    )
    return value


def summarize_stage6_entry_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    stage5_final_acceptance_raw: Mapping[str, Any],
    historical_stage5_final_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_entry_current_truth(
        raw,
        authorization_raw,
        stage5_final_acceptance_raw,
        historical_stage5_final_truth_raw,
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "stage5State": "COMPLETE_PASS",
        "stage6EntryEligible": True,
        "stage6EntryAuthorized": True,
        "stage6Started": True,
        "providerSpecificStage6WorkAuthorized": False,
        "stage7EntryAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "CHECKPOINT_TYPE",
    "GATE_MAIN_SHA",
    "GATE_MERGE_PR",
    "GATE_EXACT_HEAD_SHA",
    "RECORDED_ON",
    "SCHEMA_VERSION",
    "Stage6EntryCurrentTruthError",
    "summarize_stage6_entry_current_truth",
    "validate_stage6_entry_current_truth",
]
