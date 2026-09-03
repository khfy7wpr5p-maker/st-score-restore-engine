from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

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
VALIDATOR = ROOT / "tools/validate_stage4_held_out_evaluation_evidence_acceptance.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Stage4HeldOutEvaluationEvidenceAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.acceptance = load(ACCEPTANCE)
        self.candidate = load(CANDIDATE)
        self.authorization = load(AUTHORIZATION)
        self.stage3 = load(STAGE3_EXECUTION)
        self.stage3_exit = load(STAGE3_EXIT_ACCEPTANCE)
        self.development = load(DEVELOPMENT_ACCEPTANCE)
        self.metric_policy = load(METRIC_POLICY_ACCEPTANCE)

    def validate(self, acceptance: dict | None = None, candidate: dict | None = None) -> dict:
        return validate_held_out_evaluation_evidence_acceptance(
            acceptance or self.acceptance,
            candidate or self.candidate,
            self.authorization,
            self.stage3,
            self.stage3_exit,
            self.development,
            self.metric_policy,
        )

    def test_exact_acceptance_is_valid(self) -> None:
        value = self.validate()
        self.assertTrue(value["assertions"]["heldOutEvaluationEvidenceAccepted"])
        self.assertFalse(value["assertions"]["stage4ExitPass"])
        self.assertFalse(value["assertions"]["stage5EntryAuthorized"])
        self.assertEqual(len(ACCEPTANCE_CANONICAL_SHA256), 64)
        self.assertEqual(len(POST_ACCEPTANCE_READINESS_DIGEST), 64)

    def test_summary_reaches_review_ready_with_zero_blockers_only(self) -> None:
        summary = summarize_held_out_evaluation_evidence_acceptance(
            self.acceptance,
            self.candidate,
            self.authorization,
            self.stage3,
            self.stage3_exit,
            self.development,
            self.metric_policy,
        )
        self.assertEqual(summary["readinessDecision"], "READY_FOR_FINAL_ACCEPTANCE_REVIEW")
        self.assertEqual(summary["remainingReadinessBlockers"], [])
        self.assertTrue(summary["finalGovernanceAcceptanceStillRequired"])
        self.assertFalse(summary["stage4ExitPass"])
        self.assertFalse(summary["stage5EntryAuthorized"])

    def test_acceptance_cannot_grant_stage4_pass(self) -> None:
        tampered = deepcopy(self.acceptance)
        tampered["assertions"]["stage4ExitPass"] = True
        with self.assertRaises(Stage4HeldOutEvaluationEvidenceAcceptanceError):
            self.validate(acceptance=tampered)

    def test_acceptance_cannot_grant_stage5(self) -> None:
        tampered = deepcopy(self.acceptance)
        tampered["assertions"]["stage5EntryAuthorized"] = True
        with self.assertRaises(Stage4HeldOutEvaluationEvidenceAcceptanceError):
            self.validate(acceptance=tampered)

    def test_candidate_tuning_tamper_is_rejected(self) -> None:
        tampered = deepcopy(self.candidate)
        tampered["evaluationSummary"]["heldOutThresholdTuningUsed"] = True
        with self.assertRaises(Exception):
            self.validate(candidate=tampered)

    def test_zero_assessed_rates_remain_not_applicable(self) -> None:
        value = self.validate()
        scope = value["scope"]
        self.assertEqual(scope["assessedCandidateCount"], 0)
        self.assertEqual(scope["coverageRate"], 0.0)
        for key in ("notAssessedRate", "exactMatchRate", "falseNegativeRate", "falsePositiveRate"):
            self.assertEqual(scope[key], "not_applicable")

    def test_standalone_validator_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("READY_FOR_FINAL_ACCEPTANCE_REVIEW", completed.stdout)
        self.assertIn("Stage 4 PASS: false", completed.stdout)


if __name__ == "__main__":
    unittest.main()
