from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "docs/live/ST_SCORE_RESTORE_METRIC_POLICY_CANDIDATE_CURRENT_TRUTH.json"


class PostMetricPolicyCandidateCurrentTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.value = json.loads(OVERLAY.read_text(encoding="utf-8"))

    def test_candidate_is_production_effective_but_not_accepted(self) -> None:
        self.assertTrue(self.value["assertions"]["policy_candidate_production_effective"])
        self.assertFalse(self.value["policy_candidate"]["metric_acceptance_target_policy_accepted"])
        self.assertTrue(self.value["assertions"]["policy_acceptance_requires_separate_explicit_governance_decision"])

    def test_two_blockers_remain(self) -> None:
        readiness = self.value["readiness"]
        self.assertEqual(readiness["decision"], "NOT_READY")
        self.assertEqual(readiness["remaining_blocker_count"], 2)
        self.assertEqual(
            set(readiness["remaining_blocker_codes"]),
            {
                "no_real_held_out_evaluation_evidence_is_accepted",
                "no_stage4_metric_acceptance_target_policy_is_accepted",
            },
        )

    def test_held_out_and_stage_exit_remain_closed(self) -> None:
        self.assertFalse(self.value["held_out"]["evaluation_authorized"])
        self.assertFalse(self.value["held_out"]["tuning_used"])
        self.assertFalse(self.value["assertions"]["stage4_exit_pass"])
        self.assertFalse(self.value["assertions"]["stage5_entry_authorized"])

    def test_numeric_target_fabrication_remains_forbidden(self) -> None:
        self.assertFalse(self.value["safety_targets"]["invented_numeric_performance_targets_allowed"])
        self.assertTrue(self.value["policy_candidate"]["future_candidate_requires_numeric_target_addendum"])


if __name__ == "__main__":
    unittest.main()
