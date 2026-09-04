from __future__ import annotations

from typing import Any

from .stage5_final_exit import canonical_sha256


EXPECTED_MAIN_SHA = "19aaa35ac212b2a1698cd23b622bfd59c1e721b4"
EXPECTED_QA_DIGEST = "0e7ae71251db637ee9ba99cdcd5e2216fdfd3d655dc5eda23b676ea9ec5699fe"
EXPECTED_ACCEPTANCE_DIGEST = "467eaf11c451d114d3ef41afd44c87cf2dce5cb68f89a5d6cfc45a81e1eed9fc"


def validate_stage5_final_exit_current_truth(
    overlay: dict[str, Any],
    qa_evidence: dict[str, Any],
    acceptance: dict[str, Any],
    historical_entry_overlay: dict[str, Any],
) -> dict[str, Any]:
    if overlay.get("checkpoint_type") != "stage5_final_exit_current_truth_overlay":
        raise ValueError("unexpected Stage 5 final current-truth checkpoint type")
    if overlay.get("recorded_on") != "2026-09-04":
        raise ValueError("unexpected Stage 5 final current-truth date")

    production = overlay.get("production_checkpoint") or {}
    expected_production = {
        "main_sha": EXPECTED_MAIN_SHA,
        "merge_pr": 155,
        "merge_pr_title": "Stage 5: add bounded display-integrity final-exit QA",
        "pr_exact_head_sha": "781535f159aa99a9143de5e54b030faaf3c9d95e",
        "exact_head_repository_validation_run_id": 33844125058,
        "exact_head_repository_validation_run_number": 431,
        "exact_head_stage5_governance_run_id": 33844125100,
        "exact_head_stage5_governance_run_number": 34,
        "postmerge_repository_validation_run_id": 33844242345,
        "postmerge_repository_validation_run_number": 432,
        "postmerge_stage5_governance_run_id": 33844242264,
        "postmerge_stage5_governance_run_number": 35,
        "postmerge_stage4_governance_run_id": 33844242271,
        "postmerge_stage4_governance_run_number": 43,
        "ci_status": "success_python_3_11_and_3_12_for_repository_stage5_and_stage4_workflows",
    }
    if production != expected_production:
        raise ValueError("Stage 5 production checkpoint mismatch")

    if canonical_sha256(qa_evidence) != EXPECTED_QA_DIGEST:
        raise ValueError("Stage 5 QA evidence digest mismatch")
    if canonical_sha256(acceptance) != EXPECTED_ACCEPTANCE_DIGEST:
        raise ValueError("Stage 5 final acceptance digest mismatch")

    stage4 = overlay.get("stage4") or {}
    if stage4.get("state") != "COMPLETE_PASS" or stage4.get("exit_pass") is not True:
        raise ValueError("Stage 4 must remain COMPLETE/PASS")

    stage5 = overlay.get("stage5") or {}
    if stage5.get("state") != "COMPLETE_PASS" or stage5.get("exit_pass") is not True:
        raise ValueError("Stage 5 must be COMPLETE/PASS")
    if stage5.get("qa_evidence_digest") != EXPECTED_QA_DIGEST:
        raise ValueError("Stage 5 overlay QA digest mismatch")
    if stage5.get("final_acceptance_digest") != EXPECTED_ACCEPTANCE_DIGEST:
        raise ValueError("Stage 5 overlay acceptance digest mismatch")
    for key in (
        "accessible_teacher_review_interface_implemented",
        "real_browser_qa_passed",
        "screen_reader_qa_passed",
        "bounded_display_integrity_qa_passed",
        "stale_screen_fail_closed_verified",
        "evidence_bound_review_decision_verified",
    ):
        if stage5.get(key) is not True:
            raise ValueError(f"missing Stage 5 final assertion: {key}")
    if stage5.get("color_management_validated") is not False:
        raise ValueError("Stage 5 must not claim color-management validation")
    if stage5.get("color_fidelity_certified") is not False:
        raise ValueError("Stage 5 must not claim color-fidelity certification")

    screen_reader = overlay.get("screen_reader_evidence") or {}
    if screen_reader.get("temporary_probe_pr") != 154 or screen_reader.get("temporary_probe_merged") is not False:
        raise ValueError("temporary screen-reader probe must remain unmerged")
    if screen_reader.get("workflow_run_id") != 33843450746 or screen_reader.get("job_id") != 100930256714:
        raise ValueError("screen-reader evidence checkpoint mismatch")
    if screen_reader.get("result") != "PASS" or screen_reader.get("real_speech_output_observed") is not True:
        raise ValueError("screen-reader evidence must record real speech PASS")

    display = overlay.get("display_integrity_boundary") or {}
    expected_display = {
        "crop_encoding": "png_grayscale_8bit",
        "input_color_profiles": "not_inspected",
        "color_management_validated": False,
        "grayscale_browser_decode_verified": True,
        "actual_pixels_at_one_x_verified": True,
        "color_fidelity_claimed": False,
    }
    if display != expected_display:
        raise ValueError("Stage 5 bounded display-integrity boundary mismatch")

    stage6 = overlay.get("stage6") or {}
    if stage6 != {
        "entry_eligible": True,
        "entry_authorized": False,
        "started": False,
        "next_safe_boundary": "separate_explicit_stage6_entry_authorization",
    }:
        raise ValueError("Stage 6 must remain eligible-only and separately unauthorized")

    historical_stage5 = historical_entry_overlay.get("stage5") or {}
    if historical_stage5.get("state") != "ENTRY_AUTHORIZED_NOT_STARTED":
        raise ValueError("historical Stage 5 entry checkpoint was unexpectedly rewritten")
    if historical_stage5.get("started") is not False:
        raise ValueError("historical Stage 5 entry checkpoint must remain immutable")

    assertions = overlay.get("assertions") or {}
    required_false = (
        "historical_stage5_entry_checkpoint_rewritten",
        "real_or_derivative_bytes_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "production_deployment_authorized",
        "production_threshold_changes_authorized",
        "production_resource_limit_changes_authorized",
        "held_out_retuning_authorized",
        "model_training_authorized",
        "publication_authorized",
        "preview_release_authorized",
        "color_management_validated",
        "color_fidelity_certified",
        "representativeness_established",
        "absence_of_bias_established",
        "omr_correctness_established",
        "restoration_effectiveness_established",
    )
    if assertions.get("historical_evidence_immutable") is not True:
        raise ValueError("historical evidence immutability must remain asserted")
    if any(assertions.get(key) is not False for key in required_false):
        raise ValueError("Stage 5 final current truth contains an unauthorized claim")

    return {
        "stage5State": "COMPLETE_PASS",
        "stage5ExitPass": True,
        "stage6EntryEligible": True,
        "stage6EntryAuthorized": False,
        "stage6Started": False,
        "qaEvidenceDigest": EXPECTED_QA_DIGEST,
        "acceptanceDigest": EXPECTED_ACCEPTANCE_DIGEST,
        "colorManagementValidated": False,
        "colorFidelityCertified": False,
    }


__all__ = ["validate_stage5_final_exit_current_truth"]
