from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

ACCEPTANCE_MAIN = "3353b281a4022f107929fae296368390da45a4fb"
ACCEPTANCE_PR = 130
ACCEPTANCE_RUN_ID = 33748180036
ACCEPTANCE_RUN_NUMBER = 348
ACCEPTANCE_DIGEST = "79771e291768ba4979abc1e44dd0ecebfd95892ff2e5861d77706c1cb4563eb3"
RECEIPT_DIGEST = "036bb31ca2672e443885ed06e213ef6913be7c66609ab5017b6f22ed3f33c801"
BUNDLE_DIGEST = "37af98bbeb04832fc94382f246287da0b738c2520225cdcd9f5ea2028bde71f4"
COMPLETION_MAIN = "2ce6151e7ce37198c5b264ddd577df71f49da8bf"
COMPLETION_PR = 128
HELD_OUT_ID = "dataset.item.imslp82860-chopin-op69.v2"
READINESS_BLOCKERS = {
    "no_real_development_calibration_evidence_is_accepted",
    "no_real_held_out_evaluation_evidence_is_accepted",
    "no_stage4_metric_acceptance_target_policy_is_accepted",
}
DOC_PATHS = (
    "README.md",
    "docs/architecture-consistency-audit.md",
    "docs/roadmap.md",
    "docs/stage-4-current-status.md",
    "docs/technical-specification.md",
    "evidence/stage4/corpus-expansion/wikimedia/README.md",
)
OVERLAY_PATH = "docs/live/ST_SCORE_RESTORE_WIKIMEDIA_ACCEPTANCE_CURRENT_TRUTH.json"
ACCEPTANCE_PATH = "evidence/stage4/corpus-expansion/wikimedia/reference-bundle-acceptance.v1.json"
COMPLETION_PATH = "evidence/stage4/corpus-expansion/wikimedia/human-label-completion.v1.json"
WORK_PACKAGE_PATH = "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"
HISTORICAL_HANDOFF_PATH = "docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load(path: str) -> dict:
    return json.loads(read(path))


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    for path in (*DOC_PATHS, OVERLAY_PATH, ACCEPTANCE_PATH, COMPLETION_PATH, WORK_PACKAGE_PATH, HISTORICAL_HANDOFF_PATH):
        require((ROOT / path).exists(), f"required acceptance current-truth input missing: {path}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    for path in DOC_PATHS:
        text = read(path)
        lower = text.lower()
        require("pr #130" in lower, f"{path} lost PR #130 acceptance checkpoint")
        require(ACCEPTANCE_MAIN in text, f"{path} lost PR #130 acceptance main SHA")
        require("7/7" in text and "clear" in lower, f"{path} lost exact human-label truth")
        require("candidate" in lower and "eligible" in lower, f"{path} lost candidate-derivation eligibility")
        require("execution" in lower and "false" in lower or "not authorized" in lower or "not_authorized" in lower, f"{path} lost separate execution-authorization boundary")
        require("stage 4" in lower and ("not_ready" in lower or "not ready" in lower), f"{path} lost Stage 4 NOT_READY")
        require("stage 5" in lower and "blocked" in lower, f"{path} lost Stage 5 block")
        for blocker in READINESS_BLOCKERS:
            require(blocker in text, f"{path} lost readiness blocker {blocker}")

    overlay = load(OVERLAY_PATH)
    checkpoint = overlay.get("production_checkpoint", {})
    require(checkpoint.get("main_sha") == ACCEPTANCE_MAIN, "acceptance overlay main SHA drifted")
    require(checkpoint.get("merge_pr") == ACCEPTANCE_PR, "acceptance overlay PR drifted")
    require(checkpoint.get("postmerge_ci_run_id") == ACCEPTANCE_RUN_ID, "acceptance overlay Run ID drifted")
    require(checkpoint.get("postmerge_ci_run_number") == ACCEPTANCE_RUN_NUMBER, "acceptance overlay Run number drifted")
    require(checkpoint.get("postmerge_ci_status") == "success_python_3_11_and_3_12", "acceptance overlay CI is not green")

    completion_checkpoint = overlay.get("completion_checkpoint", {})
    require(completion_checkpoint.get("main_sha") == COMPLETION_MAIN, "acceptance overlay completion main drifted")
    require(completion_checkpoint.get("merge_pr") == COMPLETION_PR, "acceptance overlay completion PR drifted")
    require(completion_checkpoint.get("immutable_completion_state") == "human_labels_complete_pending_separate_acceptance", "acceptance overlay lost immutable completion snapshot state")
    require(completion_checkpoint.get("human_label_record_count") == 7, "acceptance overlay human-label count drifted")
    require(completion_checkpoint.get("human_label_counts") == {"clear": 7, "possible": 0, "probable": 0, "not_assessed": 0}, "acceptance overlay label distribution drifted")
    require(completion_checkpoint.get("bundle_digest") == BUNDLE_DIGEST, "acceptance overlay bundle binding drifted")

    acceptance = overlay.get("acceptance", {})
    require(acceptance.get("decision") == "ACCEPT_REAL_REFERENCE_BUNDLE", "acceptance overlay decision drifted")
    require(acceptance.get("acceptance_digest") == ACCEPTANCE_DIGEST, "acceptance overlay acceptance digest drifted")
    require(acceptance.get("accepted_reference_receipt_digest") == RECEIPT_DIGEST, "acceptance overlay receipt digest drifted")
    require(acceptance.get("reference_bundle_accepted") is True, "acceptance overlay did not accept reference bundle")
    require(acceptance.get("candidate_derivation_eligible") is True, "acceptance overlay did not enable candidate derivation")

    assertions = overlay.get("assertions", {})
    require(assertions.get("human_labels_present") is True, "acceptance overlay lost human labels")
    require(assertions.get("reference_bundle_accepted") is True, "acceptance overlay reference bundle not accepted")
    require(assertions.get("candidate_derivation_eligible") is True, "acceptance overlay candidate derivation not eligible")
    for key in (
        "labels_automatically_generated",
        "model_predictions_used_as_reference_labels",
        "calibration_execution_authorized",
        "calibration_executed",
        "production_threshold_changes_authorized",
        "production_resource_limit_changes_authorized",
        "held_out_evaluation_authorized",
        "stage4_exit_pass",
        "stage5_entry_authorized",
    ):
        require(assertions.get(key) is False, f"unsafe acceptance overlay flag became true: {key}")

    scope = overlay.get("scope", {})
    require(scope.get("split") == "development", "acceptance overlay split drifted")
    require(scope.get("purpose") == "safety_calibration", "acceptance overlay purpose drifted")
    require(scope.get("record_count") == 7, "acceptance overlay record count drifted")
    require(scope.get("held_out_item_id") == HELD_OUT_ID, "acceptance overlay held-out identity drifted")
    require(scope.get("held_out_included") is False, "held-out data entered development acceptance")
    require(scope.get("held_out_tuning_authorized") is False, "held-out tuning was authorized")

    stage4 = overlay.get("stage4", {})
    require(stage4.get("state") == "ACTIVE_NOT_READY", "acceptance overlay Stage 4 state drifted")
    require(set(stage4.get("readiness_blocker_codes", [])) == READINESS_BLOCKERS, "acceptance overlay blocker set drifted")
    require(stage4.get("next_dependency") == "separate_exact_wikimedia_expanded_development_calibration_execution_authorization", "acceptance overlay next dependency drifted")

    acceptance_evidence = load(ACCEPTANCE_PATH)
    require(acceptance_evidence.get("decision") == "ACCEPT_REAL_REFERENCE_BUNDLE", "committed acceptance decision drifted")
    require(acceptance_evidence.get("bundleDigest", {}).get("value") == BUNDLE_DIGEST, "committed acceptance bundle digest drifted")
    require(acceptance_evidence.get("assertions", {}).get("referenceBundleAccepted") is True, "committed acceptance lost accepted reference bundle")
    require(acceptance_evidence.get("scope", {}).get("candidateDerivationEligible") is True, "committed acceptance lost candidate derivation eligibility")
    require(acceptance_evidence.get("assertions", {}).get("realDataCalibrationExecutionAuthorized") is False, "committed acceptance improperly authorized execution")
    require(acceptance_evidence.get("assertions", {}).get("stage4ExitPass") is False, "committed acceptance improperly granted Stage 4 PASS")
    require(acceptance_evidence.get("assertions", {}).get("stage5EntryAuthorized") is False, "committed acceptance improperly opened Stage 5")

    completion = load(COMPLETION_PATH)
    require(completion.get("state") == "human_labels_complete_pending_separate_acceptance", "immutable completion snapshot was retroactively mutated")
    require(completion.get("assertions", {}).get("referenceBundleAccepted") is False, "immutable completion snapshot was retroactively accepted")
    require(completion.get("assertions", {}).get("candidateDerivationEligible") is False, "immutable completion snapshot was retroactively made eligible")

    package = load(WORK_PACKAGE_PATH)
    require(package.get("state") == "awaiting_human_labels", "immutable work-package template was retroactively mutated")
    pages = package.get("item", {}).get("pages", [])
    reviews = pages[0].get("reviews", []) if len(pages) == 1 else []
    require(len(reviews) == 7, "immutable work package review count drifted")
    for row in reviews:
        require(all(row.get(field) is None for field in ("referenceLabel", "reviewerReference", "provenanceReference", "reviewedOn")), f"immutable work-package human field populated: {row.get('findingType')}")

    historical_handoff = load(HISTORICAL_HANDOFF_PATH)
    historical_human = historical_handoff.get("human_reference_current_truth", {})
    require(historical_human.get("state") == "human_labels_complete_pending_separate_acceptance", "historical completion handoff anchor drifted")
    require(historical_human.get("reference_bundle_accepted") is False, "historical completion handoff was retroactively rewritten")

    if failures:
        print("Stage 4 post-Wikimedia acceptance current-truth validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 post-Wikimedia acceptance current-truth validation: PASS")
    print(f"- acceptance: PR #{ACCEPTANCE_PR} / main {ACCEPTANCE_MAIN} / Run #{ACCEPTANCE_RUN_NUMBER}")
    print("- 7/7 clear human reference labels remain immutable")
    print("- reference bundle accepted / candidate derivation eligible")
    print("- calibration execution still requires separate exact authorization")
    print("- Chopin held-out / Stage 4 NOT_READY / Stage 5 BLOCKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
