from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

from st_score_restore.dataset_contract_common import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "docs/live/ST_SCORE_RESTORE_STAGE4_FINAL_EXIT_CURRENT_TRUTH.json"
FINAL_ACCEPTANCE = ROOT / "evidence/stage4/final-exit/stage4-final-exit-acceptance.v1.json"
PRE_FINAL_TRUTH = ROOT / "docs/live/ST_SCORE_RESTORE_HELD_OUT_EVIDENCE_ACCEPTANCE_CURRENT_TRUTH.json"
WORKFLOW = ROOT / ".github/workflows/stage4-governance-validation.yml"
EVIDENCE_ROOT = ROOT / "evidence/stage4"

EXPECTED_MAIN_SHA = "4ff1118fe79602b351ad9ab8735937b9e911555d"
EXPECTED_PR_HEAD_SHA = "1518eac6c852f7fdb5478c9a6b15bc3cd2faa365"
EXPECTED_ACCEPTANCE_DIGEST = "41923c6c05c7ea015841fd77da7377aad30261a569d287246eb832f856ad599c"
EXPECTED_READINESS_DIGEST = "8b31b0dc92d931fa9e7b56a7912ecd1127e74ad0672d03d50526160936a32d0b"
EXPECTED_DEVELOPMENT_ACCEPTANCE = "4b891f3263c542c59d5632732c8010ef1bc6aeba17dfd71ffbde9ee6ed7be396"
EXPECTED_METRIC_POLICY_ACCEPTANCE = "bf62d308f70ca44db617cf2968485e422627abfce70643c78b4da20d58d04801"
EXPECTED_HELD_OUT_ACCEPTANCE = "ff0bdcb8820ba774cebc46265eb36ee0278b591a316ca619d2540d06d3a45164"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_overlay(overlay: dict, final_acceptance: dict, pre_final_truth: dict) -> list[str]:
    failures: list[str] = []

    if overlay.get("schema_version") != "1.0.0":
        failures.append("overlay schema_version drifted")
    if overlay.get("checkpoint_type") != "stage4_final_exit_acceptance_current_truth_overlay":
        failures.append("overlay checkpoint_type drifted")

    checkpoint = overlay.get("production_checkpoint", {})
    expected_checkpoint = {
        "main_sha": EXPECTED_MAIN_SHA,
        "merge_pr": 148,
        "merge_pr_title": "Stage 4: final exit governance acceptance",
        "pr_exact_head_sha": EXPECTED_PR_HEAD_SHA,
        "exact_head_repository_validation_run_id": 33776247270,
        "exact_head_repository_validation_run_number": 394,
        "exact_head_stage4_governance_run_id": 33776247258,
        "exact_head_stage4_governance_run_number": 5,
        "postmerge_repository_validation_run_id": 33776404315,
        "postmerge_repository_validation_run_number": 395,
        "postmerge_stage4_governance_run_id": 33776404434,
        "postmerge_stage4_governance_run_number": 6,
        "ci_status": "success_python_3_11_and_3_12_for_both_workflows",
    }
    if checkpoint != expected_checkpoint:
        failures.append("production checkpoint drifted")

    acceptance = overlay.get("stage4_final_acceptance", {})
    expected_acceptance = {
        "acceptance_id": "stage4.final-exit-acceptance.v1",
        "decision": "PASS",
        "acceptance_digest": EXPECTED_ACCEPTANCE_DIGEST,
        "readiness_digest": EXPECTED_READINESS_DIGEST,
        "development_evidence_acceptance_digest": EXPECTED_DEVELOPMENT_ACCEPTANCE,
        "metric_policy_acceptance_digest": EXPECTED_METRIC_POLICY_ACCEPTANCE,
        "held_out_evidence_acceptance_digest": EXPECTED_HELD_OUT_ACCEPTANCE,
    }
    if acceptance != expected_acceptance:
        failures.append("final acceptance binding drifted")

    stage4 = overlay.get("stage4", {})
    expected_stage4 = {
        "state": "COMPLETE_PASS",
        "exit_pass": True,
        "readiness_blocker_count_at_acceptance": 0,
        "readiness_blocker_codes_at_acceptance": [],
        "zero_candidate_safe_abstention_accepted": True,
        "candidate_thresholds_accepted": False,
        "thresholds_calibrated": False,
        "resource_limits_calibrated": False,
        "production_configuration_state": "uncalibrated_engineering_defaults",
    }
    if stage4 != expected_stage4:
        failures.append("Stage 4 final state drifted")

    held_out = overlay.get("held_out", {})
    expected_held_out = {
        "dataset_item_id": "dataset.item.imslp82860-chopin-op69.v2",
        "evaluation_evidence_accepted": True,
        "assessed_candidate_count": 0,
        "held_out_threshold_tuning_used": False,
        "held_out_feedback_into_candidate_derivation": False,
        "zero_assessed_rate_metrics": "not_applicable",
    }
    if held_out != expected_held_out:
        failures.append("held-out final truth drifted")

    stage5 = overlay.get("stage5", {})
    expected_stage5 = {
        "entry_eligible": True,
        "entry_authorized": False,
        "started": False,
        "next_safe_boundary": "separate_explicit_stage5_entry_governance_authorization",
    }
    if stage5 != expected_stage5:
        failures.append("Stage 5 boundary drifted or was over-authorized")

    assertions = overlay.get("assertions", {})
    expected_assertions = {
        "historical_evidence_immutable": True,
        "real_or_derivative_bytes_in_ordinary_git": False,
        "raw_private_metrics_in_ordinary_git": False,
        "production_threshold_changes_authorized": False,
        "production_resource_limit_changes_authorized": False,
        "held_out_retuning_authorized": False,
        "model_training_authorized": False,
        "publication_authorized": False,
        "representativeness_established": False,
        "absence_of_bias_established": False,
        "omr_correctness_established": False,
        "restoration_effectiveness_established": False,
    }
    if assertions != expected_assertions:
        failures.append("post-final safety assertions drifted")

    if canonical_sha256(final_acceptance) != EXPECTED_ACCEPTANCE_DIGEST:
        failures.append("final-exit acceptance evidence digest drifted")
    if final_acceptance.get("stage4ExitPass") is not True:
        failures.append("final-exit evidence does not carry Stage 4 PASS")
    if final_acceptance.get("stage5EntryEligible") is not True:
        failures.append("final-exit evidence does not carry Stage 5 eligibility")
    if final_acceptance.get("stage5EntryAuthorized") is not False:
        failures.append("final-exit evidence prematurely authorizes Stage 5")
    if final_acceptance.get("stage5Started") is not False:
        failures.append("final-exit evidence prematurely starts Stage 5")

    pre_readiness = pre_final_truth.get("stage4_readiness", {})
    pre_assertions = pre_final_truth.get("assertions", {})
    if pre_readiness.get("decision") != "READY_FOR_FINAL_ACCEPTANCE_REVIEW":
        failures.append("historical pre-final current truth was rewritten")
    if pre_readiness.get("readiness_digest") != EXPECTED_READINESS_DIGEST:
        failures.append("historical pre-final readiness digest drifted")
    if pre_readiness.get("final_governance_acceptance_still_required") is not True:
        failures.append("historical pre-final governance boundary was rewritten")
    if pre_assertions.get("stage4_exit_pass") is not False:
        failures.append("historical pre-final Stage 4 PASS was retroactively changed")
    if pre_assertions.get("stage5_entry_authorized") is not False:
        failures.append("historical pre-final Stage 5 authorization was retroactively changed")

    return failures


def main() -> int:
    failures: list[str] = []
    for path in (OVERLAY, FINAL_ACCEPTANCE, PRE_FINAL_TRUTH, WORKFLOW):
        if not path.exists():
            failures.append(f"required post-final-exit input missing: {path.relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    overlay = load(OVERLAY)
    final_acceptance = load(FINAL_ACCEPTANCE)
    pre_final_truth = load(PRE_FINAL_TRUTH)
    failures.extend(validate_overlay(overlay, final_acceptance, pre_final_truth))

    tampered = deepcopy(overlay)
    tampered["stage5"]["entry_authorized"] = True
    if not validate_overlay(tampered, final_acceptance, pre_final_truth):
        failures.append("tampered Stage 5 authorization was not rejected")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    command = "python tools/validate_stage4_post_final_exit_current_truth.py"
    if command not in workflow:
        failures.append("Stage 4 governance workflow does not run post-final-exit current-truth validator")

    for path in EVIDENCE_ROOT.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        if '"rawValue"' in text:
            failures.append(f"raw private metric value leaked into ordinary Git: {path.relative_to(ROOT)}")
            break

    if failures:
        print("Stage 4 post-final-exit current truth: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 post-final-exit current truth: PASS")
    print(f"- production main: {EXPECTED_MAIN_SHA}")
    print(f"- final acceptance digest: {EXPECTED_ACCEPTANCE_DIGEST}")
    print("- Stage 4: COMPLETE_PASS")
    print("- Stage 5: eligible=true / authorized=false / started=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
