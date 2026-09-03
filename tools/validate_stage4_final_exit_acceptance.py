from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

from st_score_restore.stage4_final_exit_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    READINESS_DIGEST,
    Stage4FinalExitAcceptanceError,
    summarize_stage4_final_exit_acceptance,
    validate_stage4_final_exit_acceptance,
)

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "evidence/stage4/final-exit/stage4-final-exit-acceptance.v1.json"
DEVELOPMENT = ROOT / "evidence/stage4/calibration/expanded-real-development-execution-acceptance.v1.json"
METRIC_POLICY = ROOT / "evidence/stage4/calibration/metric-acceptance-target-policy-acceptance.v1.json"
HELD_OUT = ROOT / "evidence/stage4/calibration/held-out-evaluation-evidence-acceptance.v1.json"
CURRENT_TRUTH = ROOT / "docs/live/ST_SCORE_RESTORE_HELD_OUT_EVIDENCE_ACCEPTANCE_CURRENT_TRUTH.json"
WORKFLOW = ROOT / ".github/workflows/stage4-governance-validation.yml"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []
    for path in (ACCEPTANCE, DEVELOPMENT, METRIC_POLICY, HELD_OUT, CURRENT_TRUTH, WORKFLOW):
        if not path.exists():
            failures.append(f"required Stage 4 final-exit input missing: {path.relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    acceptance = load(ACCEPTANCE)
    development = load(DEVELOPMENT)
    metric_policy = load(METRIC_POLICY)
    held_out = load(HELD_OUT)
    current_truth = load(CURRENT_TRUTH)

    try:
        value = validate_stage4_final_exit_acceptance(
            acceptance, development, metric_policy, held_out, current_truth
        )
        summary = summarize_stage4_final_exit_acceptance(
            acceptance, development, metric_policy, held_out, current_truth
        )
        if value["stage4ExitPass"] is not True:
            failures.append("Stage 4 final-exit PASS is not effective")
        if summary["stage5EntryEligible"] is not True:
            failures.append("Stage 5 eligibility was not recorded")
        if summary["stage5EntryAuthorized"] is not False or summary["stage5Started"] is not False:
            failures.append("Stage 4 final acceptance over-authorized Stage 5")

        tampered = deepcopy(acceptance)
        tampered["stage5EntryAuthorized"] = True
        try:
            validate_stage4_final_exit_acceptance(
                tampered, development, metric_policy, held_out, current_truth
            )
            failures.append("tampered Stage 5 authorization was not rejected")
        except Stage4FinalExitAcceptanceError:
            pass

        tampered_truth = deepcopy(current_truth)
        tampered_truth["stage4_readiness"]["blocker_count"] = 1
        tampered_truth["stage4_readiness"]["blocker_codes"] = ["synthetic_blocker"]
        try:
            validate_stage4_final_exit_acceptance(
                acceptance, development, metric_policy, held_out, tampered_truth
            )
            failures.append("blocked readiness was not rejected")
        except Stage4FinalExitAcceptanceError:
            pass
    except Exception as exc:
        failures.append(f"Stage 4 final-exit validation raised: {exc}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    commands = (
        "python tools/validate_stage4_held_out_evaluation_evidence_acceptance.py",
        "python tools/validate_stage4_post_held_out_evidence_acceptance_current_truth.py",
        "python tools/validate_stage4_final_exit_acceptance.py",
    )
    for command in commands:
        if command not in workflow:
            failures.append(f"Stage 4 governance workflow is missing validator command: {command}")

    if failures:
        print("Stage 4 final exit acceptance: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 final exit acceptance: PASS")
    print(f"- acceptance digest: {ACCEPTANCE_CANONICAL_SHA256}")
    print(f"- readiness digest: {READINESS_DIGEST}")
    print("- Stage 4 exit: PASS")
    print("- Stage 5: eligible=true / authorized=false / started=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
