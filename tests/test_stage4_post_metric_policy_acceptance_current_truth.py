from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "docs/live/ST_SCORE_RESTORE_METRIC_POLICY_ACCEPTANCE_CURRENT_TRUTH.json"


class Stage4PostMetricPolicyAcceptanceCurrentTruthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))

    def test_exact_checkpoint_and_policy_acceptance(self) -> None:
        checkpoint = self.overlay["production_checkpoint"]
        self.assertEqual(checkpoint["main_sha"], "2b0eff6b9ef340a2b697b9965c3a88cb5b78e2ce")
        self.assertEqual(checkpoint["merge_pr"], 142)
        self.assertEqual(checkpoint["postmerge_ci_run_number"], 378)
        policy = self.overlay["accepted_metric_policy"]
        self.assertTrue(policy["metric_acceptance_target_policy_accepted"])
        self.assertEqual(policy["current_mode"], "zero_candidate_safe_abstention")

    def test_exact_single_blocker_remains(self) -> None:
        readiness = self.overlay["readiness"]
        self.assertEqual(readiness["decision"], "NOT_READY")
        self.assertEqual(readiness["remaining_blocker_count"], 1)
        self.assertEqual(readiness["remaining_blocker_codes"], ["no_real_held_out_evaluation_evidence_is_accepted"])

    def test_downstream_state_stays_closed(self) -> None:
        self.assertFalse(self.overlay["held_out"]["evaluation_authorized"])
        self.assertFalse(self.overlay["held_out"]["evaluation_used"])
        assertions = self.overlay["assertions"]
        self.assertFalse(assertions["candidate_thresholds_accepted"])
        self.assertFalse(assertions["production_threshold_changes_authorized"])
        self.assertFalse(assertions["production_resource_limit_changes_authorized"])
        self.assertFalse(assertions["stage4_exit_pass"])
        self.assertFalse(assertions["stage5_entry_authorized"])


if __name__ == "__main__":
    unittest.main()
