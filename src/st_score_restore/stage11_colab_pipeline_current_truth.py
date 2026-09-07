"""Fail-closed validator for the active Stage 11 Colab/training checkpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED_STATE = "FIRST_RESIDUAL_UNET_GPU_RUN_COMPLETE_AWAITING_HELD_OUT_AND_STAGE9A_EVALUATION"
EXPECTED_MD5 = "7237318e381e6e0848ec30eb82decb83"
EXPECTED_CONFIG = "deff0f1270009839e234608dd9967038e1228a6b2b034e26059ac2f8cbfd0f80"
EXPECTED_BEST_SHA256 = "08b279161a9e8c4bd37376da221ecb4e07130724254ccf7d9591c8d32f368683"


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
        "deepscoresv2_dense_archive_checksum_verified",
        "synthetic_degradation_pipeline_ready",
        "colab_pipeline_ready",
        "residual_unet_baseline_implemented",
        "high_resolution_patch_training_enabled",
        "checkpoint_resume_implemented",
        "official_test_preserved_as_held_out",
        "source_family_leakage_guard_enabled",
        "held_out_tuning_forbidden",
        "training_executable",
        "training_started",
        "training_completed",
        "training_executed_on_gpu",
        "first_gpu_training_run_pass",
        "model_weights_established",
        "candidate_model_established",
    ):
        _require(stage11.get(key) is True, f"{key} must be true after the verified GPU run")

    for key in (
        "exit_pass",
        "held_out_evaluation_completed",
        "stage9a_preservation_evaluation_completed",
        "final_model_selected",
        "camera_primus_commercial_training_admitted",
        "production_inference_authorized",
        "automatic_final_selection_authorized",
        "model_publication_authorized",
    ):
        _require(stage11.get(key) is False, f"{key} must remain false at this boundary")

    _require(stage11.get("external_pretrained_weight_download_required") is False, "external pretrained download must not be required")
    _require(stage11.get("next_safe_boundary") == "evaluate_best_checkpoint_on_official_held_out_without_tuning_then_run_stage9a_preservation_checks", "next safe boundary mismatch")

    source = payload.get("training_source") or {}
    _require(source.get("dataset_id") == "deepscoresv2.dense.v2", "training dataset id mismatch")
    _require(source.get("license") == "CC-BY-4.0", "training dataset license mismatch")
    _require(source.get("attribution_required") is True, "CC BY attribution must be recorded")
    _require(source.get("dense_image_count") == 1714, "dense image count mismatch")
    _require(source.get("official_train_images") == 1362, "official train count mismatch")
    _require(source.get("official_test_images") == 352, "official test count mismatch")
    _require(source.get("archive_md5_expected") == EXPECTED_MD5, "archive MD5 mismatch")
    _require(source.get("archive_md5_verified") is True, "archive MD5 must now be verified")
    _require(source.get("ordinary_git_real_bytes") is False, "real training bytes must remain outside ordinary Git")

    run = payload.get("first_gpu_run") or {}
    _require(run.get("gpu") == "Tesla T4", "GPU evidence mismatch")
    _require(run.get("epochs_completed") == 20, "epoch count mismatch")
    _require(run.get("best_epoch") == 19, "best epoch mismatch")
    _require(run.get("config_sha256") == EXPECTED_CONFIG, "config hash mismatch")
    _require(run.get("held_out_used_for_tuning") is False, "held-out tuning is forbidden")
    _require(run.get("epoch19_development_loss") < run.get("epoch0_development_loss"), "development loss did not improve")
    _require(run.get("epoch19_development_pixel_l1") < run.get("epoch0_development_pixel_l1"), "pixel L1 did not improve")
    _require(run.get("epoch19_development_edge_loss") < run.get("epoch0_development_edge_loss"), "edge loss did not improve")
    _require(run.get("epoch19_development_psnr_db") > run.get("epoch0_development_psnr_db"), "development PSNR did not improve")

    artifacts = payload.get("model_artifacts") or {}
    _require(artifacts.get("storage") == "google_drive_only", "model weight storage must remain Drive-only")
    _require(artifacts.get("ordinary_git_model_bytes") is False, "model bytes must not enter ordinary Git")
    _require((artifacts.get("best_checkpoint") or {}).get("sha256") == EXPECTED_BEST_SHA256, "best checkpoint SHA256 mismatch")
    _require((artifacts.get("best_checkpoint") or {}).get("size_bytes") == 23449829, "best checkpoint size mismatch")

    blockers = set(payload.get("blocking_reason_codes") or [])
    for required in (
        "OFFICIAL_HELD_OUT_EVALUATION_NOT_YET_EXECUTED",
        "STAGE9A_PRESERVATION_EVALUATION_NOT_YET_EXECUTED",
        "FINAL_STAGE11_MODEL_SELECTION_NOT_YET_ESTABLISHED",
    ):
        _require(required in blockers, f"missing blocker: {required}")
    _require("DEEPSCORESV2_DENSE_ARCHIVE_MD5_NOT_YET_VERIFIED_IN_COLAB" not in blockers, "obsolete checksum blocker present")
    _require("FIRST_COLAB_GPU_RUN_NOT_EXECUTED" not in blockers, "obsolete first-run blocker present")

    assertions = payload.get("assertions") or {}
    for key in (
        "historical_evidence_immutable",
        "source_artifacts_immutable",
        "ordinary_git_artifact_bytes_forbidden",
        "cc_by_attribution_must_be_preserved",
        "source_family_leakage_forbidden",
        "held_out_never_train_or_tune",
        "private_user_student_data_not_authorized",
        "first_gpu_training_claim_supported_by_evidence",
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
        "checksumVerified": True,
        "trainingStarted": True,
        "trainingCompleted": True,
        "modelWeightsEstablished": True,
        "firstGpuTrainingRunPass": True,
        "finalStage11Pass": False,
        "nextSafeBoundary": stage11["next_safe_boundary"],
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_stage11_colab_pipeline_current_truth(payload)
