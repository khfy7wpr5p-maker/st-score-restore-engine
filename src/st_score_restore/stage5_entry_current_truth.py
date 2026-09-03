"""Production-effective current truth after Stage 5 entry authorization.

This overlay records the later Stage 5 entry governance authorization without
rewriting the historical Stage 4 final-exit checkpoint. Entry authorization is
not a Stage 5 start decision and does not authorize implementation, execution,
deployment, Stage 6, threshold/resource changes, held-out retuning, training,
or publication.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .stage5_entry_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    AUTHORIZATION_DECISION,
    AUTHORIZATION_ID,
    NEXT_SAFE_BOUNDARY,
    STAGE4_FINAL_ACCEPTANCE_DIGEST,
    STAGE5_PURPOSE,
    validate_stage5_entry_authorization,
)

SCHEMA_VERSION = "1.0.0"
CHECKPOINT_TYPE = "stage5_entry_governance_authorization_current_truth_overlay"
RECORDED_ON = "2026-09-03"
PROJECT = "ST Score Restore API / ST Score Restore Engine"
REPOSITORY = "khfy7wpr5p-maker/st-score-restore-engine"

GATE_MAIN_SHA = "49d2c054da4e159b33cf97238b7deb078110a879"
GATE_MERGE_PR = 150
GATE_PR_TITLE = "Stage 5: authorize entry governance gate"
GATE_EXACT_HEAD_SHA = "0836e8fffa4c8074a8c733c282319b082dd6794d"

EXACT_REPOSITORY_RUN_ID = 33797070010
EXACT_REPOSITORY_RUN_NUMBER = 398
EXACT_STAGE4_RUN_ID = 33797070236
EXACT_STAGE4_RUN_NUMBER = 9
EXACT_STAGE5_RUN_ID = 33797070307
EXACT_STAGE5_RUN_NUMBER = 1
POSTMERGE_REPOSITORY_RUN_ID = 33797217664
POSTMERGE_REPOSITORY_RUN_NUMBER = 399
POSTMERGE_STAGE4_RUN_ID = 33797217598
POSTMERGE_STAGE4_RUN_NUMBER = 10
POSTMERGE_STAGE5_RUN_ID = 33797217701
POSTMERGE_STAGE5_RUN_NUMBER = 2


class Stage5EntryCurrentTruthError(ValueError):
    """Post-entry current-truth overlay is stale, malformed, or unsafe."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage5EntryCurrentTruthError(message)


def validate_stage5_entry_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    stage4_final_acceptance_raw: Mapping[str, Any],
    historical_stage4_final_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage5_entry_authorization(
        authorization_raw,
        stage4_final_acceptance_raw,
        historical_stage4_final_truth_raw,
    )

    historical_stage5 = historical_stage4_final_truth_raw.get("stage5", {})
    _require(historical_stage5.get("entry_eligible") is True, "historical Stage 5 eligibility drifted")
    _require(historical_stage5.get("entry_authorized") is False, "historical Stage 4 final checkpoint was retroactively rewritten")
    _require(historical_stage5.get("started") is False, "historical Stage 4 final checkpoint was retroactively rewritten to start Stage 5")

    _require(isinstance(raw, Mapping), "Stage 5 current-truth overlay must be an object")
    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schema_version",
            "project",
            "repository",
            "checkpoint_type",
            "recorded_on",
            "production_checkpoint",
            "stage4",
            "stage5_entry_authorization",
            "stage5",
            "stage6",
            "assertions",
            "compatibility_note",
        },
        "Stage 5 current-truth top-level fields drifted",
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
        "postmerge_repository_validation_run_id": POSTMERGE_REPOSITORY_RUN_ID,
        "postmerge_repository_validation_run_number": POSTMERGE_REPOSITORY_RUN_NUMBER,
        "postmerge_stage4_governance_run_id": POSTMERGE_STAGE4_RUN_ID,
        "postmerge_stage4_governance_run_number": POSTMERGE_STAGE4_RUN_NUMBER,
        "postmerge_stage5_governance_run_id": POSTMERGE_STAGE5_RUN_ID,
        "postmerge_stage5_governance_run_number": POSTMERGE_STAGE5_RUN_NUMBER,
        "ci_status": "success_python_3_11_and_3_12_for_all_three_workflows",
    }
    _require(value["production_checkpoint"] == expected_checkpoint, "production checkpoint drifted")

    _require(
        value["stage4"] == {
            "state": "COMPLETE_PASS",
            "exit_pass": True,
            "final_acceptance_digest": STAGE4_FINAL_ACCEPTANCE_DIGEST,
        },
        "Stage 4 final truth drifted",
    )
    _require(
        value["stage5_entry_authorization"] == {
            "authorization_id": AUTHORIZATION_ID,
            "decision": AUTHORIZATION_DECISION,
            "authorization_digest": AUTHORIZATION_CANONICAL_SHA256,
            "purpose": STAGE5_PURPOSE,
        },
        "Stage 5 entry authorization truth drifted",
    )
    _require(
        value["stage5"] == {
            "state": "ENTRY_AUTHORIZED_NOT_STARTED",
            "entry_eligible": True,
            "entry_authorized": True,
            "started": False,
            "teacher_review_interface_implementation_authorized": False,
            "teacher_review_interface_execution_authorized": False,
            "production_deployment_authorized": False,
            "next_safe_boundary": NEXT_SAFE_BOUNDARY,
        },
        "Stage 5 current state drifted or over-authorized",
    )
    _require(
        value["stage6"] == {
            "entry_authorized": False,
            "started": False,
        },
        "Stage 6 was prematurely authorized or started",
    )

    expected_assertions = {
        "historical_evidence_immutable": True,
        "historical_stage4_final_checkpoint_rewritten": False,
        "real_or_derivative_bytes_in_ordinary_git": False,
        "raw_private_metrics_in_ordinary_git": False,
        "production_threshold_changes_authorized": False,
        "production_resource_limit_changes_authorized": False,
        "held_out_retuning_authorized": False,
        "model_training_authorized": False,
        "publication_authorized": False,
        "preview_release_authorized": False,
        "representativeness_established": False,
        "absence_of_bias_established": False,
        "omr_correctness_established": False,
        "restoration_effectiveness_established": False,
    }
    _require(value["assertions"] == expected_assertions, "Stage 5 safety assertions drifted")
    _require(
        value["compatibility_note"]
        == "This later overlay records production-effective Stage 5 entry authorization from PR #150. The historical Stage 4 final-exit checkpoint remains immutable with Stage 5 entry authorization=false. Stage 5 entry is now authorized but Stage 5 is not started; teacher-review interface implementation/execution, deployment, Stage 6, threshold/resource changes, held-out retuning, training, publication, and preview release remain separately unauthorized.",
        "compatibility note drifted",
    )
    return value


def summarize_stage5_entry_current_truth(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    stage4_final_acceptance_raw: Mapping[str, Any],
    historical_stage4_final_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage5_entry_current_truth(
        raw,
        authorization_raw,
        stage4_final_acceptance_raw,
        historical_stage4_final_truth_raw,
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "stage4State": "COMPLETE_PASS",
        "stage5EntryEligible": True,
        "stage5EntryAuthorized": True,
        "stage5Started": False,
        "stage6EntryAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "CHECKPOINT_TYPE",
    "GATE_MAIN_SHA",
    "GATE_MERGE_PR",
    "GATE_EXACT_HEAD_SHA",
    "RECORDED_ON",
    "SCHEMA_VERSION",
    "Stage5EntryCurrentTruthError",
    "summarize_stage5_entry_current_truth",
    "validate_stage5_entry_current_truth",
]
