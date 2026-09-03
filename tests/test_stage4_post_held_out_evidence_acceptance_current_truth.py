from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "docs/live/ST_SCORE_RESTORE_HELD_OUT_EVIDENCE_ACCEPTANCE_CURRENT_TRUTH.json"
VALIDATOR = ROOT / "tools/validate_stage4_post_held_out_evidence_acceptance_current_truth.py"


class Stage4PostHeldOutAcceptanceCurrentTruthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))

    def test_overlay_records_zero_blockers_without_pass(self) -> None:
        readiness = self.overlay["stage4_readiness"]
        assertions = self.overlay["assertions"]
        self.assertEqual(readiness["decision"], "READY_FOR_FINAL_ACCEPTANCE_REVIEW")
        self.assertEqual(readiness["blocker_count"], 0)
        self.assertEqual(readiness["blocker_codes"], [])
        self.assertTrue(readiness["final_governance_acceptance_still_required"])
        self.assertFalse(assertions["stage4_exit_pass"])
        self.assertFalse(assertions["stage5_entry_authorized"])

    def test_overlay_preserves_zero_candidate_held_out_boundary(self) -> None:
        held_out = self.overlay["held_out_scope"]
        self.assertEqual(held_out["candidate_derived_count"], 0)
        self.assertEqual(held_out["assessed_candidate_count"], 0)
        self.assertEqual(held_out["coverage_rate"], 0.0)
        self.assertFalse(held_out["new_held_out_execution_performed"])
        self.assertFalse(held_out["held_out_threshold_tuning_used"])
        self.assertFalse(held_out["evaluation_fed_back_into_candidate"])
        for key in ("not_assessed_rate", "exact_match_rate", "false_negative_rate", "false_positive_rate"):
            self.assertEqual(held_out[key], "not_applicable")

    def test_standalone_current_truth_validator_passes(self) -> None:
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
