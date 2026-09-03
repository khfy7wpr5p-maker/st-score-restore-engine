from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage4_final_exit_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    READINESS_DIGEST,
    Stage4FinalExitAcceptanceError,
    summarize_stage4_final_exit_acceptance,
    validate_stage4_final_exit_acceptance,
)

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "evidence/stage4/governance/stage4-final-exit-acceptance.v1.json"
DEVELOPMENT = ROOT / "evidence/stage4/calibration/expanded-real-development-execution-acceptance.v1.json"
METRIC_POLICY = ROOT / "evidence/stage4/calibration/metric-acceptance-target-policy-acceptance.v1.json"
HELD_OUT = ROOT / "evidence/stage4/calibration/held-out-evaluation-evidence-acceptance.v1.json"
CURRENT_TRUTH = ROOT / "docs/live/ST_SCORE_RESTORE_HELD_OUT_EVIDENCE_ACCEPTANCE_CURRENT_TRUTH.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Stage4FinalExitAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.acceptance = load(ACCEPTANCE)
        self.development = load(DEVELOPMENT)
        self.metric_policy = load(METRIC_POLICY)
        self.held_out = load(HELD_OUT)
        self.current_truth = load(CURRENT_TRUTH)

    def validate(self, acceptance: dict | None = None, current_truth: dict | None = None) -> dict:
        return validate_stage4_final_exit_acceptance(
            acceptance or self.acceptance,
            self.development,
            self.metric_policy,
            self.held_out,
            current_truth or self.current_truth,
        )

    def test_exact_final_acceptance_is_valid(self) -> None:
        value = self.validate()
        self.assertTrue(value["stage4ExitPass"])
        self.assertTrue(value["stage5EntryEligible"])
        self.assertFalse(value["stage5EntryAuthorized"])
        self.assertFalse(value["stage5Started"])
        self.assertEqual(len(ACCEPTANCE_CANONICAL_SHA256), 64)
        self.assertEqual(len(READINESS_DIGEST), 64)

    def test_summary_does_not_open_stage5(self) -> None:
        summary = summarize_stage4_final_exit_acceptance(
            self.acceptance,
            self.development,
            self.metric_policy,
            self.held_out,
            self.current_truth,
        )
        self.assertEqual(summary["decision"], "PASS")
        self.assertTrue(summary["stage4ExitPass"])
        self.assertTrue(summary["stage5EntryEligible"])
        self.assertFalse(summary["stage5EntryAuthorized"])
        self.assertFalse(summary["stage5Started"])

    def test_stage5_authorization_tamper_is_rejected(self) -> None:
        tampered = deepcopy(self.acceptance)
        tampered["stage5EntryAuthorized"] = True
        with self.assertRaises(Stage4FinalExitAcceptanceError):
            self.validate(acceptance=tampered)

    def test_stage5_start_tamper_is_rejected(self) -> None:
        tampered = deepcopy(self.acceptance)
        tampered["stage5Started"] = True
        with self.assertRaises(Stage4FinalExitAcceptanceError):
            self.validate(acceptance=tampered)

    def test_blocked_readiness_is_rejected(self) -> None:
        tampered = deepcopy(self.current_truth)
        tampered["stage4_readiness"]["blocker_count"] = 1
        tampered["stage4_readiness"]["blocker_codes"] = ["synthetic_blocker"]
        with self.assertRaises(Stage4FinalExitAcceptanceError):
            self.validate(current_truth=tampered)

    def test_positive_calibration_claim_is_rejected(self) -> None:
        tampered = deepcopy(self.acceptance)
        tampered["claims"]["thresholdsCalibrated"] = True
        with self.assertRaises(Stage4FinalExitAcceptanceError):
            self.validate(acceptance=tampered)


if __name__ == "__main__":
    unittest.main()
