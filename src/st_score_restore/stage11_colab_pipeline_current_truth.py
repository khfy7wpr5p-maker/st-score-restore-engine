"""Fail-closed validator for the active Stage 11 Colab training checkpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED_STATE = "DEEPSCORESV2_DENSE_RIGHTS_APPROVED_DRIVE_ARCHIVE_PRESENT_COLAB_READY_AWAITING_CHECKSUM_AND_FIRST_GPU_RUN"


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
        "deepscoresv2_dense_rights_review_complete",
        "deepscoresv2_dense_commercial_training_admitted",
        "deepscoresv2_dense_drive_archive_present",
        "synthetic_degradation_pipeline_ready",
        "colab_pipeline_ready",
        "residual_unet_baseline_implemented",
        "high_resolution_patch_training_enabled",
        "checkpoint_resume_implemented",
        "official_test_preserved_as_held_out",
        "source_family_leakage_guard_enabled",
        "held_out_tuning_forbidden",
    ):
        _require(stage11.get(key) is True, f"{key} must be true")

    for key in (
        "deepscoresv2_dense_archive_checksum_verified",
        "training_executable",
        "training_started",
        "training_executed_on_gpu",
        "model_weights_established",
        "camera_primus_commercial_training_admitted",
        "production_inference_authorized",
        "automatic_final_selection_authorized",
        "model_publication_authorized",
    ):
        _require(stage11.get(key) is False, f"{key} must remain false before first verified GPU run")

    _require(stage11.get("external_pretrained_weight_download_required") is False, "external pretrained download must not be required")

    source = payload.get("training_source") or {}
    _require(source.get("dataset_id") == "deepscoresv2.dense.v2", "training dataset id mismatch")
    _require(source.get("license") == "CC-BY-4.0", "training dataset license mismatch")
    _require(source.get("attribution_required") is True, "CC BY attribution must be recorded")
    _require(source.get("dense_image_count") == 1714, "dense image count mismatch")
    _require(source.get("official_train_images") == 1362, "official train count mismatch")
    _require(source.get("official_test_images") == 352, "official test count mismatch")
    _require(source.get("drive_folder_id") == "1Ov_cUo6O1guuegX1GiqrRlHvTtCjHpvy", "Drive folder id mismatch")
    _require(source.get("drive_file_id") == "1QjvmZSpWgnc8wdfcwfmcXTdibXQnriJS", "Drive file id mismatch")
    _require(source.get("archive_file_name") == "ds2_dense.tar.gz", "archive filename mismatch")
    _require(source.get("archive_size_bytes_observed") == 741814529, "archive size mismatch")
    _require(source.get("archive_md5_expected") == "7237318e381e6e0848ec30eb82decb83", "archive MD5 mismatch")
    _require(source.get("archive_md5_verified") is False, "archive MD5 cannot be claimed before Colab verification")
    _require(source.get("ordinary_git_real_bytes") is False, "real training bytes must remain outside ordinary Git")

    synthetic = payload.get("synthetic_restoration_pairs") or {}
    _require(synthetic.get("clean_role") == "target", "clean image must be target")
    _require(synthetic.get("degraded_role") == "source", "degraded image must be source")
    _require(synthetic.get("recipe_version") == "stage11.synthetic-camera.v1", "synthetic recipe mismatch")
    _require(synthetic.get("thin_symbol_preservation_required") is True, "thin-symbol preservation must remain required")

    colab = payload.get("colab") or {}
    _require(colab.get("notebook") == "notebooks/stage11_deepscoresv2_dense_residual_unet_colab.ipynb", "notebook path mismatch")
    _require(colab.get("archive_checksum_gate_required") is True, "checksum gate must be enabled")
    _require(colab.get("safe_tar_extraction_required") is True, "safe extraction must be enabled")
    _require(colab.get("resume_from_last_checkpoint") is True, "checkpoint resume must be enabled")
    _require(colab.get("held_out_final_eval_default") is False, "held-out final evaluation must default off")

    blockers = set(payload.get("blocking_reason_codes") or [])
    _require("DEEPSCORESV2_DENSE_ARCHIVE_MD5_NOT_YET_VERIFIED_IN_COLAB" in blockers, "checksum blocker must be recorded")
    _require("FIRST_COLAB_GPU_RUN_NOT_EXECUTED" in blockers, "first-run blocker must be recorded")

    assertions = payload.get("assertions") or {}
    for key in (
        "historical_evidence_immutable",
        "source_artifacts_immutable",
        "ordinary_git_artifact_bytes_forbidden",
        "cc_by_attribution_must_be_preserved",
        "source_family_leakage_forbidden",
        "held_out_never_train_or_tune",
        "private_user_student_data_not_authorized",
        "training_cannot_be_claimed_before_execution",
        "camera_primus_not_trainable_under_current_rights_decision",
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
        "rightsApproved": True,
        "archivePresent": True,
        "checksumVerified": False,
        "trainingStarted": False,
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_stage11_colab_pipeline_current_truth(payload)
