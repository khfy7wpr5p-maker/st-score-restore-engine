from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

EXPANSION_BASELINE_MAIN = "9d2326931707f65c7eb5f5b22680e8fa85665a60"
EXPANSION_BASELINE_PR = 125
EXPANSION_BASELINE_RUN_ID = 33728459668
EXPANSION_BASELINE_RUN_NUMBER = 324
COMPLETION_MAIN = "2ce6151e7ce37198c5b264ddd577df71f49da8bf"
COMPLETION_PR = 128
COMPLETION_RUN_ID = 33745945427
COMPLETION_RUN_NUMBER = 340
WIKIMEDIA_GRANT_DIGEST = "603e3dc7669e6259ab061a8241d76206e7bd2bf76b170fc6dbc8c1d0b9d6be07"
COMPLETION_WORK_PACKAGE_DIGEST = "9ccec309f611f8057b8b4a20a1aba732544c1638f2b959656b9503718206337c"
COMPLETION_BUNDLE_DIGEST = "37af98bbeb04832fc94382f246287da0b738c2520225cdcd9f5ea2028bde71f4"
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
COMPLETION_PATH = "evidence/stage4/corpus-expansion/wikimedia/human-label-completion.v1.json"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load(path: str) -> dict:
    return json.loads(read(path))


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    for path in (*DOC_PATHS, HANDOFF_PATH, WORK_PACKAGE_PATH, COMPLETION_PATH):
        require((ROOT / path).exists(), f"required post-Wikimedia current-truth input missing: {path}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    docs = {path: read(path) for path in DOC_PATHS}
    for path, text in docs.items():
        lower = text.lower()
        require(EXPANSION_BASELINE_MAIN in text, f"{path} lost PR #125 production baseline main")
        require("pr #125" in lower, f"{path} lost PR #125 binding")
        require(COMPLETION_MAIN in text, f"{path} lost PR #128 human-completion checkpoint main")
        require("pr #128" in lower, f"{path} lost PR #128 binding")
        require("wikimedia" in lower, f"{path} lost Wikimedia development expansion")
        require("stage 4" in lower and "active" in lower, f"{path} lost Stage 4 ACTIVE state")
        require("not_ready" in lower or "not ready" in lower, f"{path} lost Stage 4 NOT_READY state")
        require("stage 5" in lower and "blocked" in lower, f"{path} lost Stage 5 block")
        require(WIKIMEDIA_GRANT_DIGEST in text, f"{path} lost Wikimedia purpose-grant digest")
        require("7/7" in text and "clear" in lower, f"{path} lost seven-label human completion truth")
        for blocker in READINESS_BLOCKERS:
            require(blocker in text, f"{path} lost readiness blocker {blocker}")

    handoff = load(HANDOFF_PATH)
    repo_truth = handoff.get("repository_current_truth", {})
    require(repo_truth.get("main_sha") == EXPANSION_BASELINE_MAIN, "live handoff expansion baseline main drifted")
    require(repo_truth.get("latest_merged_pr") == EXPANSION_BASELINE_PR, "live handoff expansion baseline PR drifted")
    require(repo_truth.get("postmerge_ci_run_id") == EXPANSION_BASELINE_RUN_ID, "live handoff PR #125 post-merge run ID drifted")
    require(repo_truth.get("postmerge_ci_run_number") == EXPANSION_BASELINE_RUN_NUMBER, "live handoff PR #125 post-merge run number drifted")
    require(repo_truth.get("postmerge_ci_status") == "success_python_3_11_and_3_12", "live handoff PR #125 post-merge CI is not green")
    require(repo_truth.get("stage4_state") == "ACTIVE_NOT_READY", "live handoff repository Stage 4 state drifted")
    require(repo_truth.get("stage5_state") == "BLOCKED_PENDING_STAGE4_FINAL_EXIT_PASS", "live handoff repository Stage 5 state drifted")

    human_truth = handoff.get("human_reference_current_truth", {})
    require(human_truth.get("state") == "human_labels_complete_pending_separate_acceptance", "live handoff human-reference state drifted")
    require(human_truth.get("main_sha") == COMPLETION_MAIN, "live handoff human-completion main drifted")
    require(human_truth.get("merge_pr") == COMPLETION_PR, "live handoff human-completion PR drifted")
    require(human_truth.get("postmerge_ci_run_id") == COMPLETION_RUN_ID, "live handoff human-completion run ID drifted")
    require(human_truth.get("postmerge_ci_run_number") == COMPLETION_RUN_NUMBER, "live handoff human-completion run number drifted")
    require(human_truth.get("postmerge_ci_status") == "success_python_3_11_and_3_12", "live handoff human-completion CI is not green")
    require(human_truth.get("human_label_record_count") == 7, "live handoff human label count drifted")
    require(human_truth.get("human_label_counts") == {"clear": 7, "possible": 0, "probable": 0, "not_assessed": 0}, "live handoff human label distribution drifted")
    require(human_truth.get("work_package_digest") == COMPLETION_WORK_PACKAGE_DIGEST, "live handoff completion work-package digest drifted")
    require(human_truth.get("bundle_digest") == COMPLETION_BUNDLE_DIGEST, "live handoff completion bundle digest drifted")
    for key in ("reference_bundle_accepted", "candidate_derivation_eligible", "calibration_execution_authorized", "calibration_executed", "stage4_exit_pass", "stage5_entry_authorized"):
        require(human_truth.get(key) is False, f"unsafe human-reference current-truth flag became true: {key}")

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
    require(execution.get("next_dependency") == "wikimedia_reference_bundle_governance_acceptance", "live handoff next dependency drifted")

    stage4 = handoff.get("stage4", {})
    require(set(stage4.get("readiness_blocker_codes", [])) == READINESS_BLOCKERS, "live handoff readiness blocker set drifted")
    wiki = stage4.get("wikimedia_expansion", {})
    require(wiki.get("merge_pr") == EXPANSION_BASELINE_PR, "live handoff Wikimedia expansion PR drifted")
    require(wiki.get("merge_commit_sha") == EXPANSION_BASELINE_MAIN, "live handoff Wikimedia expansion SHA drifted")
    require(wiki.get("dataset_item_id") == ITEM_ID, "live handoff Wikimedia dataset item drifted")
    require(wiki.get("source_family_id") == SOURCE_FAMILY_ID, "live handoff Wikimedia source family drifted")
    require(wiki.get("purpose_grant_canonical_sha256") == WIKIMEDIA_GRANT_DIGEST, "live handoff Wikimedia grant digest drifted")
    require(wiki.get("finding_slot_count") == 7, "live handoff Wikimedia finding slot count drifted")
    require(set(wiki.get("finding_types", [])) == FINDINGS, "live handoff Wikimedia finding taxonomy drifted")
    require(set(wiki.get("allowed_labels", [])) == LABELS, "live handoff Wikimedia label vocabulary drifted")
    require(wiki.get("human_labels_present") is True, "live handoff lost completed human labels")
    require(wiki.get("human_label_completion_state") == "human_labels_complete_pending_separate_acceptance", "live handoff Wikimedia completion state drifted")
    require(wiki.get("human_label_completion_merge_pr") == COMPLETION_PR, "live handoff Wikimedia completion PR drifted")
    require(wiki.get("human_label_completion_main_sha") == COMPLETION_MAIN, "live handoff Wikimedia completion main drifted")
    require(wiki.get("human_label_completion_postmerge_ci_run_id") == COMPLETION_RUN_ID, "live handoff Wikimedia completion run ID drifted")
    require(wiki.get("human_label_completion_postmerge_ci_run_number") == COMPLETION_RUN_NUMBER, "live handoff Wikimedia completion run number drifted")
    require(wiki.get("human_label_completion_work_package_digest") == COMPLETION_WORK_PACKAGE_DIGEST, "live handoff Wikimedia completion work-package digest drifted")
    require(wiki.get("human_label_completion_bundle_digest") == COMPLETION_BUNDLE_DIGEST, "live handoff Wikimedia completion bundle digest drifted")
    require(wiki.get("human_label_counts") == {"clear": 7, "possible": 0, "probable": 0, "not_assessed": 0}, "live handoff Wikimedia completion label counts drifted")
    require(wiki.get("work_package_remains_pristine") is True, "live handoff lost pristine work-package boundary")
    for key in (
        "reference_bundle_accepted",
        "candidate_derivation_eligible",
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
    require(wiki.get("external_evidence_gate") == "human_labels_complete_pending_separate_acceptance", "live handoff Wikimedia external/governance gate drifted")

    package = load(WORK_PACKAGE_PATH)
    require(package.get("state") == "awaiting_human_labels", "immutable Wikimedia work package state drifted")
    require(package.get("purposeGrantDigest") == WIKIMEDIA_GRANT_DIGEST, "Wikimedia work package grant binding drifted")
    pages = package.get("item", {}).get("pages", [])
    reviews = pages[0].get("reviews", []) if len(pages) == 1 else []
    require(len(reviews) == 7, "Wikimedia work package does not contain exactly seven review slots")
    for row in reviews:
        require(
            all(row.get(field) is None for field in ("referenceLabel", "reviewerReference", "provenanceReference", "reviewedOn")),
            f"immutable Wikimedia work-package slot was populated: {row.get('findingType')}",
        )
    exclusions = package.get("heldOutExclusions", [])
    require(len(exclusions) == 1 and exclusions[0].get("datasetItemId") == HELD_OUT_ID, "Wikimedia work package lost Chopin exclusion")
    require(exclusions[0].get("includedInDevelopmentReview") is False, "Wikimedia work package included held-out data")
    require(exclusions[0].get("candidateDerivationAuthorized") is False, "Wikimedia work package authorized held-out candidate derivation")

    completion = load(COMPLETION_PATH)
    require(completion.get("state") == "human_labels_complete_pending_separate_acceptance", "Wikimedia completion evidence state drifted")
    require(completion.get("workPackageDigest", {}).get("value") == COMPLETION_WORK_PACKAGE_DIGEST, "Wikimedia completion work-package digest drifted")
    require(completion.get("bundleDigest", {}).get("value") == COMPLETION_BUNDLE_DIGEST, "Wikimedia completion bundle digest drifted")
    require(completion.get("labelCounts") == {"clear": 7, "not_assessed": 0, "possible": 0, "probable": 0}, "Wikimedia completion label counts drifted")
    records = completion.get("bundle", {}).get("records", [])
    require(len(records) == 7, "Wikimedia completion record count drifted")
    require({row.get("findingType") for row in records} == FINDINGS, "Wikimedia completion finding taxonomy drifted")
    require({row.get("referenceLabel") for row in records} == {"clear"}, "Wikimedia completion labels are not exactly the supplied all-clear review")
    assertions = completion.get("assertions", {})
    require(assertions.get("humanLabelsPresent") is True, "Wikimedia completion lost humanLabelsPresent=true")
    for key in (
        "labelsAutomaticallyGenerated",
        "modelPredictionsUsedAsReferenceLabels",
        "referenceBundleAccepted",
        "candidateDerivationEligible",
        "expansionCalibrationExecutionAuthorized",
        "expansionCalibrationExecuted",
        "heldOutIncludedInDevelopmentReview",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        require(assertions.get(key) is False, f"unsafe Wikimedia completion assertion became true: {key}")

    if failures:
        print("Stage 4 post-Wikimedia current-truth validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 post-Wikimedia current-truth validation: PASS")
    print(f"- expansion baseline: PR #{EXPANSION_BASELINE_PR} / main {EXPANSION_BASELINE_MAIN} / Run #{EXPANSION_BASELINE_RUN_NUMBER}")
    print(f"- human completion: PR #{COMPLETION_PR} / main {COMPLETION_MAIN} / Run #{COMPLETION_RUN_NUMBER} / 7 clear")
    print("- immutable work package remains pristine / reference acceptance false / execution authorization false")
    print("- Chopin held-out boundary intact / Stage 4 NOT_READY / Stage 5 BLOCKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
