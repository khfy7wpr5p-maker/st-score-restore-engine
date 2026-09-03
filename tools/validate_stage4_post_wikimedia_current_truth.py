from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

CURRENT_BASELINE_MAIN = "9d2326931707f65c7eb5f5b22680e8fa85665a60"
CURRENT_BASELINE_PR = 125
CURRENT_BASELINE_RUN_ID = 33728459668
CURRENT_BASELINE_RUN_NUMBER = 324
WIKIMEDIA_GRANT_DIGEST = "603e3dc7669e6259ab061a8241d76206e7bd2bf76b170fc6dbc8c1d0b9d6be07"
ITEM_ID = "dataset.item.wikimedia-guitar-technical-exercise-no1.v1"
SOURCE_FAMILY_ID = "source.family.wikimedia-guitar-technical-exercise-no1.v1"
HELD_OUT_ID = "dataset.item.imslp82860-chopin-op69.v2"
FINDINGS = {"skew", "blur", "glare", "shadow", "uneven_lighting", "noise", "compression"}
LABELS = {"clear", "possible", "probable", "not_assessed"}
READINESS_BLOCKERS = {
    "no_real_development_calibration_evidence_is_accepted",
    "no_real_held_out_evaluation_evidence_is_accepted",
    "no_stage4_metric_acceptance_target_policy_is_accepted",
}
DOC_PATHS = (
    "README.md",
    "docs/roadmap.md",
    "docs/stage-4-current-status.md",
    "docs/technical-specification.md",
    "docs/architecture-consistency-audit.md",
)
HANDOFF_PATH = "docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json"
WORK_PACKAGE_PATH = "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load(path: str) -> dict:
    return json.loads(read(path))


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    for path in (*DOC_PATHS, HANDOFF_PATH, WORK_PACKAGE_PATH):
        require((ROOT / path).exists(), f"required post-Wikimedia current-truth input missing: {path}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    docs = {path: read(path) for path in DOC_PATHS}
    for path, text in docs.items():
        lower = text.lower()
        require(CURRENT_BASELINE_MAIN in text, f"{path} lost PR #125 production baseline main")
        require("pr #125" in lower, f"{path} lost PR #125 binding")
        require("wikimedia" in lower, f"{path} lost Wikimedia development expansion")
        require("stage 4" in lower and "active" in lower, f"{path} lost Stage 4 ACTIVE state")
        require("not_ready" in lower or "not ready" in lower, f"{path} lost Stage 4 NOT_READY state")
        require("stage 5" in lower and "blocked" in lower, f"{path} lost Stage 5 block")
        require(WIKIMEDIA_GRANT_DIGEST in text, f"{path} lost Wikimedia purpose-grant digest")
        for blocker in READINESS_BLOCKERS:
            require(blocker in text, f"{path} lost readiness blocker {blocker}")

    handoff = load(HANDOFF_PATH)
    repo_truth = handoff.get("repository_current_truth", {})
    require(repo_truth.get("main_sha") == CURRENT_BASELINE_MAIN, "live handoff repository current baseline main drifted")
    require(repo_truth.get("latest_merged_pr") == CURRENT_BASELINE_PR, "live handoff latest merged PR drifted")
    require(repo_truth.get("postmerge_ci_run_id") == CURRENT_BASELINE_RUN_ID, "live handoff PR #125 post-merge run ID drifted")
    require(repo_truth.get("postmerge_ci_run_number") == CURRENT_BASELINE_RUN_NUMBER, "live handoff PR #125 post-merge run number drifted")
    require(repo_truth.get("postmerge_ci_status") == "success_python_3_11_and_3_12", "live handoff PR #125 post-merge CI is not green")
    require(repo_truth.get("stage4_state") == "ACTIVE_NOT_READY", "live handoff repository Stage 4 state drifted")
    require(repo_truth.get("stage5_state") == "BLOCKED_PENDING_STAGE4_FINAL_EXIT_PASS", "live handoff repository Stage 5 state drifted")

    execution = handoff.get("current_execution_truth", {})
    require(execution.get("real_data_calibration_executed") is True, "live handoff lost executed Beethoven+Barley truth")
    require(execution.get("execution_evidence_accepted") is False, "live handoff prematurely accepted Beethoven+Barley execution evidence")
    require(execution.get("private_metric_record_count") == 42, "live handoff private observation identity count drifted")
    require(execution.get("measured_record_count") == 24, "live handoff measured count drifted")
    require(execution.get("not_applicable_record_count") == 18, "live handoff not-applicable count drifted")
    require(execution.get("measured_source_family_count") == 1, "live handoff measured source-family count drifted")
    require(execution.get("candidate_derived_count") == 0, "live handoff falsely claims threshold candidates")
    require(execution.get("thresholds_calibrated") is False, "live handoff falsely claims calibrated thresholds")
    require(execution.get("resource_limits_calibrated") is False, "live handoff falsely claims calibrated resource limits")
    require(execution.get("held_out_tuning_used") is False, "live handoff crossed held-out tuning boundary")
    require(execution.get("held_out_evaluation_used") is False, "live handoff prematurely claims held-out evaluation")

    stage4 = handoff.get("stage4", {})
    require(set(stage4.get("readiness_blocker_codes", [])) == READINESS_BLOCKERS, "live handoff readiness blocker set drifted")
    wiki = stage4.get("wikimedia_expansion", {})
    require(wiki.get("merge_pr") == CURRENT_BASELINE_PR, "live handoff Wikimedia merge PR drifted")
    require(wiki.get("merge_commit_sha") == CURRENT_BASELINE_MAIN, "live handoff Wikimedia merge SHA drifted")
    require(wiki.get("postmerge_ci_run_id") == CURRENT_BASELINE_RUN_ID, "live handoff Wikimedia post-merge CI run ID drifted")
    require(wiki.get("postmerge_ci_run_number") == CURRENT_BASELINE_RUN_NUMBER, "live handoff Wikimedia post-merge CI run number drifted")
    require(wiki.get("dataset_item_id") == ITEM_ID, "live handoff Wikimedia dataset item drifted")
    require(wiki.get("source_family_id") == SOURCE_FAMILY_ID, "live handoff Wikimedia source family drifted")
    require(wiki.get("purpose_grant_canonical_sha256") == WIKIMEDIA_GRANT_DIGEST, "live handoff Wikimedia grant digest drifted")
    require(wiki.get("finding_slot_count") == 7, "live handoff Wikimedia finding slot count drifted")
    require(set(wiki.get("finding_types", [])) == FINDINGS, "live handoff Wikimedia finding taxonomy drifted")
    require(set(wiki.get("allowed_labels", [])) == LABELS, "live handoff Wikimedia label vocabulary drifted")
    for key in (
        "human_labels_present",
        "reference_bundle_accepted",
        "calibration_execution_authorized",
        "calibration_executed",
        "model_predictions_allowed_as_reference",
        "held_out_included",
        "production_threshold_changes_authorized",
        "production_resource_limit_changes_authorized",
        "stage4_exit_pass",
        "stage5_entry_authorized",
    ):
        require(wiki.get(key) is False, f"unsafe Wikimedia current-truth flag became true: {key}")
    require(wiki.get("external_evidence_gate") == "awaiting_actual_human_expert_review", "live handoff Wikimedia external evidence gate drifted")

    package = load(WORK_PACKAGE_PATH)
    require(package.get("state") == "awaiting_human_labels", "Wikimedia work package is not awaiting human labels")
    require(package.get("purposeGrantDigest") == WIKIMEDIA_GRANT_DIGEST, "Wikimedia work package grant binding drifted")
    require(set(package.get("labelVocabulary", [])) == LABELS, "Wikimedia work package label vocabulary drifted")
    require(set(package.get("findingTypes", [])) == FINDINGS, "Wikimedia work package finding taxonomy drifted")
    pages = package.get("item", {}).get("pages", [])
    reviews = pages[0].get("reviews", []) if len(pages) == 1 else []
    require(len(reviews) == 7, "Wikimedia work package does not contain exactly seven review slots")
    require({row.get("findingType") for row in reviews} == FINDINGS, "Wikimedia work package review slots drifted")
    for row in reviews:
        require(
            all(row.get(field) is None for field in ("referenceLabel", "reviewerReference", "provenanceReference", "reviewedOn")),
            f"Wikimedia review slot {row.get('findingType')} was populated without the external human evidence gate",
        )
    exclusions = package.get("heldOutExclusions", [])
    require(len(exclusions) == 1 and exclusions[0].get("datasetItemId") == HELD_OUT_ID, "Wikimedia work package lost Chopin exclusion")
    require(exclusions[0].get("includedInDevelopmentReview") is False, "Wikimedia work package included held-out data")
    require(exclusions[0].get("candidateDerivationAuthorized") is False, "Wikimedia work package authorized held-out candidate derivation")

    if failures:
        print("Stage 4 post-Wikimedia current-truth validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 post-Wikimedia current-truth validation: PASS")
    print(f"- production baseline: PR #{CURRENT_BASELINE_PR} / main {CURRENT_BASELINE_MAIN} / Run #{CURRENT_BASELINE_RUN_NUMBER}")
    print("- Beethoven+Barley: executed / abstained / 24 measured + 18 not_applicable / 0 candidates")
    print("- Wikimedia: purpose granted / 7 review slots / human labels absent / acceptance false / execution authorization false")
    print("- Chopin held-out boundary intact / Stage 4 NOT_READY / Stage 5 BLOCKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())