from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "evidence/stage9/final-exit/stage9-final-exit-acceptance.v1.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"BLOCKED: {message}")


def main() -> None:
    data = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    require(data.get("decision") == "PASS", "Stage 9 final exit is not PASS")
    require(data.get("accepted_state") == "COMPLETE_PASS_PROVIDER_NEUTRAL_MULTI_ENGINE_COMPARATOR_FOUNDATION", "accepted state drifted")
    evidence = data.get("implementation_evidence", {})
    require(evidence.get("capability_pull_request") == 182, "capability PR drifted")
    require(evidence.get("exact_head_sha") == "58aee3088e8f74a5dc12f199ed3010f8de62a964", "exact head drifted")
    require(evidence.get("merged_main_sha") == "4eff94927e0af935e802605598dee331e228dd40", "merged main drifted")
    accepted = data.get("accepted_capabilities", {})
    for key in (
        "provider_neutral_multi_engine_comparator_foundation",
        "immutable_original_first_class_baseline",
        "provenance_bound_variant_eligibility",
        "safety_validation_precedes_comparator",
        "hard_deterministic_veto_non_overridable",
        "hard_semantic_veto_non_overridable_when_present",
        "review_and_unknown_fail_safe",
        "positive_improvement_required_to_prefer_derivative",
        "explainable_lexicographic_ranking",
        "exact_evidence_tie_routes_to_review",
        "synthetic_comparator_drills_pass",
        "recommendation_only_contract",
    ):
        require(accepted.get(key) is True, f"accepted capability missing: {key}")
    for section_name in ("exact_head_ci", "postmerge_ci"):
        section = data.get(section_name, {})
        require(set(section) == {"repository_validation", "stage4_governance", "stage5_governance", "stage6_governance", "stage7_governance", "stage8_governance", "stage9_governance"}, f"{section_name} workflow set drifted")
        require(all(item.get("result") == "SUCCESS" for item in section.values()), f"{section_name} contains non-success evidence")
    limitations = data.get("limitations_and_non_claims", {})
    for key in (
        "automatic_final_selection_authorized",
        "stage9a_entry_authorized",
        "stage9a_training_authorized",
        "stage10_entry_authorized",
        "stage10_selector_activation_authorized",
        "docres_runtime_dependency_approved",
        "docres_model_artifact_approved",
        "live_docres_runtime_authorized",
        "provider_specific_activation_authorized",
        "live_resource_creation_authorized",
        "production_deployment_authorized",
        "threshold_changes_authorized",
        "resource_limit_changes_authorized",
        "held_out_retuning_authorized",
        "model_training_authorized",
        "model_publication_authorized",
    ):
        require(limitations.get(key) is False, f"unauthorized boundary widened: {key}")
    require(data.get("next_safe_boundary") == "separate_stage9a_entry_authorization", "next safe boundary drifted")
    print("PASS: Stage 9 final-exit acceptance is complete and fail-closed")


if __name__ == "__main__":
    main()
