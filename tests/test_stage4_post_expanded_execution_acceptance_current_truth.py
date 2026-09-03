from __future__ import annotations

import json
import unittest
from pathlib import Path

from st_score_restore.stage4_exit_readiness import (
    BLOCK_NO_HELDOUT_EVIDENCE,
    BLOCK_NO_METRIC_TARGET_POLICY,
)

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "docs/live/ST_SCORE_RESTORE_EXPANDED_EXECUTION_ACCEPTANCE_CURRENT_TRUTH.json"


class PostExpandedExecutionAcceptanceCurrentTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))

    def test_execution_evidence_is_accepted_without_threshold_candidate(self) -> None:
        evidence = self.overlay["accepted_execution_evidence"]
        self.assertTrue(evidence["execution_evidence_accepted"])
        self.assertEqual(evidence["candidate_derived_count"], 0)
        self.assertFalse(self.overlay["calibration_state"]["thresholds_calibrated"])

    def test_only_two_readiness_blockers_remain(self) -> None:
        self.assertEqual(
            set(self.overlay["readiness"]["remaining_blocker_codes"]),
            {BLOCK_NO_HELDOUT_EVIDENCE, BLOCK_NO_METRIC_TARGET_POLICY},
        )
        self.assertEqual(self.overlay["readiness"]["remaining_blocker_count"], 2)
        self.assertEqual(self.overlay["readiness"]["accepted_real_development_evidence_count"], 1)

    def test_downstream_gates_remain_closed(self) -> None:
        self.assertFalse(self.overlay["held_out"]["evaluation_authorized"])
        self.assertFalse(self.overlay["metric_policy"]["acceptance_target_policy_accepted"])
        self.assertFalse(self.overlay["assertions"]["stage4_exit_pass"])
        self.assertFalse(self.overlay["assertions"]["stage5_entry_authorized"])


if __name__ == "__main__":
    unittest.main()
