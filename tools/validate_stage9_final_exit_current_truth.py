from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "docs/live/ST_SCORE_RESTORE_STAGE9_FINAL_EXIT_CURRENT_TRUTH.json"
ACCEPTANCE = ROOT / "evidence/stage9/final-exit/stage9-final-exit-acceptance.v1.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"BLOCKED: {message}")


def main() -> None:
    truth = json.loads(TRUTH.read_text(encoding="utf-8"))
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    require(truth.get("artifact_type") == "stage9_final_exit_current_truth", "artifact type drifted")
    checkpoint = truth.get("production_checkpoint", {})
    require(checkpoint.get("main_sha") == "4eff94927e0af935e802605598dee331e228dd40", "production checkpoint SHA drifted")
    require(checkpoint.get("merge_pr") == 182, "merge PR drifted")
    require(checkpoint.get("final_exit_acceptance_git_blob_sha1") == "5b749cf110b86aaa2d804e38e1288356dc6bea69", "acceptance blob binding drifted")
    require(acceptance.get("decision") == "PASS", "acceptance no longer PASS")
    stage9 = truth.get("stage9", {})
    require(stage9.get("state") == "COMPLETE_PASS_PROVIDER_NEUTRAL_MULTI_ENGINE_COMPARATOR_FOUNDATION", "Stage 9 state drifted")
    require(stage9.get("exit_pass") is True, "Stage 9 exit is not PASS")
    require(stage9.get("comparator_contract_complete") is True, "comparator contract incomplete")
    require(stage9.get("provider_neutral_foundation_complete") is True, "provider-neutral foundation incomplete")
    require(stage9.get("automatic_final_selection_authorized") is False, "automatic final selection widened")
    require(stage9.get("production_comparator_activation_authorized") is False, "production comparator activation widened")
    stage9a = truth.get("stage9a", {})
    require(stage9a.get("entry_eligible") is True, "Stage 9A should be next eligible boundary")
    for key in ("entry_authorized", "started", "dataset_collection_authorized", "training_authorized", "model_publication_authorized", "production_inference_authorized"):
        require(stage9a.get(key) is False, f"Stage 9A boundary widened: {key}")
    stage10 = truth.get("stage10", {})
    require(stage10.get("entry_eligible") is False, "Stage 10 must remain blocked pending Stage 9A")
    require(stage10.get("entry_authorized") is False and stage10.get("started") is False, "Stage 10 boundary widened")
    require(stage10.get("blocked_pending") == "accepted_stage9a_exit", "Stage 10 prerequisite drifted")
    assertions = truth.get("assertions", {})
    for key in (
        "historical_evidence_immutable",
        "source_artifact_immutable",
        "derived_artifacts_provenance_bound",
        "safety_validation_precedes_comparator_eligibility",
        "hard_deterministic_veto_non_overridable",
        "hard_semantic_veto_non_overridable_when_present",
        "original_always_selectable",
        "review_required_cannot_be_automatic_winner",
        "unknown_evidence_fails_safe",
        "opaque_universal_quality_score_forbidden",
        "positive_improvement_required_to_prefer_derivative",
    ):
        require(assertions.get(key) is True, f"Stage 9 assertion missing: {key}")
    for key in (
        "external_package_installation_authorized",
        "docres_runtime_dependency_approved",
        "model_artifact_download_authorized",
        "model_weights_use_authorized",
        "network_fetch_authorized",
        "live_docres_runtime_activation_authorized",
        "real_user_docres_cohort_authorized",
        "automatic_final_selection_authorized",
        "stage9a_entry_authorized",
        "stage9a_training_authorized",
        "stage10_entry_authorized",
        "stage10_selector_activation_authorized",
        "live_resource_creation_authorized",
        "production_deployment_authorized",
        "threshold_changes_authorized",
        "resource_limit_changes_authorized",
        "held_out_retuning_authorized",
        "model_training_authorized",
        "model_publication_authorized",
    ):
        require(assertions.get(key) is False, f"unauthorized assertion widened: {key}")
    continuation = truth.get("continuation_state", {})
    require(continuation.get("last_completed_stage") == "Stage 9", "continuation stage drifted")
    require(continuation.get("first_incomplete_boundary") == "separate_stage9a_entry_authorization", "continuation boundary drifted")
    require(stage9.get("next_safe_boundary") == "separate_stage9a_entry_authorization", "Stage 9 next boundary drifted")
    print("PASS: Stage 9 final current truth is internally consistent and fail-closed")


if __name__ == "__main__":
    main()
