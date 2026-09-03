from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

from st_score_restore.stage4_held_out_evaluation_evidence_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    POST_ACCEPTANCE_READINESS_DIGEST,
    Stage4HeldOutEvaluationEvidenceAcceptanceError,
    summarize_held_out_evaluation_evidence_acceptance,
    validate_held_out_evaluation_evidence_acceptance,
)

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "evidence/stage4/calibration/held-out-evaluation-evidence-acceptance.v1.json"
CANDIDATE = ROOT / "evidence/stage4/calibration/held-out-evaluation-evidence-candidate.v1.json"
AUTHORIZATION = ROOT / "evidence/stage4/governance/held-out-evaluation-evidence-review-authorization.v1.json"
STAGE3_EXECUTION = ROOT / "evidence/stage3/corpus/execution-evidence.v1.json"
STAGE3_EXIT_ACCEPTANCE = ROOT / "evidence/stage3/corpus/stage3-exit-acceptance.v1.json"
DEVELOPMENT_ACCEPTANCE = ROOT / "evidence/stage4/calibration/expanded-real-development-execution-acceptance.v1.json"
METRIC_POLICY_ACCEPTANCE = ROOT / "evidence/stage4/calibration/metric-acceptance-target-policy-acceptance.v1.json"
WORKFLOW = ROOT / ".github/workflows/repository-validation.yml"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def inputs() -> tuple[dict, dict, dict, dict, dict, dict, dict]:
    return (
        load(ACCEPTANCE),
        load(CANDIDATE),
        load(AUTHORIZATION),
        load(STAGE3_EXECUTION),
        load(STAGE3_EXIT_ACCEPTANCE),
        load(DEVELOPMENT_ACCEPTANCE),
        load(METRIC_POLICY_ACCEPTANCE),
    )


def main() -> int:
    failures: list[str] = []
    for path in (
        ACCEPTANCE,
        CANDIDATE,
        AUTHORIZATION,
        STAGE3_EXECUTION,
        STAGE3_EXIT_ACCEPTANCE,
        DEVELOPMENT_ACCEPTANCE,
        METRIC_POLICY_ACCEPTANCE,
        WORKFLOW,
    ):
        if not path.exists():
            failures.append(f"required held-out acceptance input missing: {path.relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    try:
        acceptance, candidate, authorization, stage3, stage3_exit, development, metric_policy = inputs()
        value = validate_held_out_evaluation_evidence_acceptance(
            acceptance,
            candidate,
            authorization,
            stage3,
            stage3_exit,
            development,
            metric_policy,
        )
        summary = summarize_held_out_evaluation_evidence_acceptance(
            acceptance,
            candidate,
            authorization,
            stage3,
            stage3_exit,
            development,
            metric_policy,
        )
        if value["assertions"]["heldOutEvaluationEvidenceAccepted"] is not True:
            failures.append("held-out evaluation evidence acceptance is not effective")
        if summary["readinessDecision"] != "READY_FOR_FINAL_ACCEPTANCE_REVIEW":
            failures.append("post-acceptance readiness did not reach final-acceptance review")
        if summary["remainingReadinessBlockers"] != []:
            failures.append("post-acceptance readiness still has blockers")
        if summary["stage4ExitPass"] is not False or summary["stage5EntryAuthorized"] is not False:
            failures.append("held-out evidence acceptance over-authorized Stage 4 PASS or Stage 5")

        tampered = deepcopy(acceptance)
        tampered["assertions"]["stage4ExitPass"] = True
        try:
            validate_held_out_evaluation_evidence_acceptance(
                tampered,
                candidate,
                authorization,
                stage3,
                stage3_exit,
                development,
                metric_policy,
            )
            failures.append("tampered Stage 4 PASS acceptance was not rejected")
        except Stage4HeldOutEvaluationEvidenceAcceptanceError:
            pass

        tampered_candidate = deepcopy(candidate)
        tampered_candidate["evaluationSummary"]["heldOutThresholdTuningUsed"] = True
        try:
            validate_held_out_evaluation_evidence_acceptance(
                acceptance,
                tampered_candidate,
                authorization,
                stage3,
                stage3_exit,
                development,
                metric_policy,
            )
            failures.append("tampered held-out tuning candidate was not rejected")
        except Exception:
            pass
    except Exception as exc:
        failures.append(f"held-out evidence acceptance validation raised: {exc}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    validator_command = "python tools/validate_stage4_held_out_evaluation_evidence_acceptance.py"
    if validator_command not in workflow:
        failures.append("repository validation workflow does not run held-out evidence acceptance validator")

    if failures:
        print("Stage 4 held-out evaluation evidence acceptance: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 held-out evaluation evidence acceptance: PASS")
    print(f"- acceptance digest: {ACCEPTANCE_CANONICAL_SHA256}")
    print(f"- post-acceptance readiness digest: {POST_ACCEPTANCE_READINESS_DIGEST}")
    print("- held-out evidence accepted: true")
    print("- remaining readiness blockers: 0")
    print("- readiness: READY_FOR_FINAL_ACCEPTANCE_REVIEW")
    print("- held-out tuning: false")
    print("- Stage 4 PASS: false / Stage 5 entry: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
