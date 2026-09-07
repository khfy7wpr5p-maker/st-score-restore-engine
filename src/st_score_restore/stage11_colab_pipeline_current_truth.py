"""Fail-closed validator for the Stage 11 CameraPrIMuS Colab pipeline checkpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED_STATE = "CAMERAPRIMUS_RIGHTS_REVIEW_COMPLETE_NOT_ADMITTED_COLAB_PIPELINE_READY_AWAITING_RIGHTS_CLEARED_DATA_AND_FIRST_GPU_RUN"


class Stage11ColabPipelineTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11ColabPipelineTruthError(message)


def validate_stage11_colab_pipeline_current_truth(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifact_type") == "stage11_colab_pipeline_current_truth", "artifact type mismatch")
    stage11 = payload.get("stage11") or {}
    _require(stage11.get("state") == EXPECTED_STATE, "unexpected Stage 11 state")
    for key in (
        "training_authorized",
        "dataset_admission_authorized",
        "camera_primus_drive_source_confirmed",
        "paired_restoration_structure_confirmed",
        "colab_pipeline_ready",
        "residual_unet_baseline_implemented",
        "checkpoint_resume_implemented",
        "deterministic_source_family_split_implemented",
        "held_out_tuning_forbidden",
        "camera_primus_rights_review_complete",
    ):
        _require(stage11.get(key) is True, f"{key} must be true")
    for key in (
        "training_started",
        "training_executed_on_gpu",
        "model_weights_established",
        "camera_primus_commercial_training_admitted",
        "rights_cleared_training_pairs_admitted",
        "production_inference_authorized",
        "automatic_final_selection_authorized",
        "model_publication_authorized",
    ):
        _require(stage11.get(key) is False, f"{key} must remain false")
    _require(stage11.get("external_pretrained_weight_download_required") is False, "external pretrained download must not be required")

    drive = payload.get("drive_source") or {}
    _require(drive.get("path") == "TEST/CameraPrIMuS/Corpus", "Drive dataset path mismatch")
    _require(drive.get("folder_id") == "1qIwmGQbcJHox00tMEteojaeU1N3UvNgO", "Drive folder id mismatch")
    _require(drive.get("ordinary_git_real_bytes") is False, "real dataset bytes must stay out of ordinary Git")
    _require(drive.get("commercial_training_admission") == "denied_under_current_rights_evidence", "CameraPrIMuS commercial admission must remain denied")

    rights = payload.get("rights_resolution") or {}
    _require(rights.get("decision") == "COMPLETE_NOT_ADMITTED_FOR_COMMERCIAL_MODEL_TRAINING", "rights decision mismatch")
    for key in (
        "official_dataset_page_has_explicit_commercial_training_license",
        "ismir_2018_paper_license_is_dataset_license",
        "rism_cc_by_3_underlying_data_license_is_camera_primus_package_license",
        "secondary_public_label_is_sufficient_license_grant",
    ):
        _require(rights.get(key) is False, f"rights claim {key} must remain false")

    colab = payload.get("colab") or {}
    _require(colab.get("notebook") == "notebooks/stage11_cameraprimus_residual_unet_colab.ipynb", "notebook path mismatch")
    _require(colab.get("resume_from_last_checkpoint") is True, "checkpoint resume must be enabled")
    _require(colab.get("held_out_final_eval_default") is False, "held-out final evaluation must default off")

    blockers = set(payload.get("blocking_reason_codes") or [])
    _require("CAMERAPRIMUS_COMMERCIAL_TRAINING_RIGHTS_INSUFFICIENT" in blockers, "CameraPrIMuS rights blocker must be recorded")
    _require("RIGHTS_CLEARED_TRAINING_PAIRS_NOT_YET_ADMITTED" in blockers, "rights-cleared data blocker must be recorded")
    _require("FIRST_COLAB_GPU_RUN_NOT_EXECUTED" in blockers, "first-run blocker must be recorded")

    assertions = payload.get("assertions") or {}
    for key in (
        "historical_evidence_immutable",
        "source_artifacts_immutable",
        "ordinary_git_artifact_bytes_forbidden",
        "source_family_leakage_forbidden",
        "held_out_never_train_or_tune",
        "private_user_student_data_not_authorized",
        "training_cannot_be_claimed_before_execution",
        "camera_primus_not_trainable_under_current_rights_decision",
        "rights_cleared_synthetic_or_explicitly_licensed_data_route_required",
        "model_output_not_omr_truth",
        "stage9a_preservation_evidence_required_before_release",
        "stage9_comparator_required_before_release",
        "stage10_selector_required_before_release",
    ):
        _require(assertions.get(key) is True, f"assertion {key} must be true")
    _require(assertions.get("stage12_entry_authorized") is False, "Stage 12 must remain unauthorized")
    _require(assertions.get("production_behavior_changed") is False, "production behavior must remain unchanged")
    return {
        "state": stage11["state"],
        "colabPipelineReady": True,
        "cameraPrIMuSRightsReviewComplete": True,
        "cameraPrIMuSCommercialTrainingAdmitted": False,
        "trainingStarted": False,
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_stage11_colab_pipeline_current_truth(payload)
