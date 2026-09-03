from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HANDOFF_PATH = ROOT / "docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json"
STATUS_PATH = ROOT / "docs/stage-4-current-status.md"

EXECUTION_EVIDENCE_SHA256 = "0d2ce54066d493e3aa5a8b3c3ef3df407532edb5fa51aee14b8a560678731f1a"
PRIVATE_METRIC_BATCH_SHA256 = "5bb2c2e081e6e72697a2c3acb8aacd7b4159dfabf3400fb9a0570ecb1a148079"
PRODUCTION_EXECUTION_MAIN = "4f0346345eb770628928ba1751b4a1d9d5fb51f1"
PRODUCTION_EXECUTION_RUN = 304


class Stage4RealExecutionCurrentTruthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.handoff = json.loads(HANDOFF_PATH.read_text(encoding="utf-8"))
        self.status = STATUS_PATH.read_text(encoding="utf-8")

    def test_top_level_current_execution_truth_is_bound_to_production_evidence(self) -> None:
        current = self.handoff["current_execution_truth"]
        self.assertEqual(current["production_main_sha"], PRODUCTION_EXECUTION_MAIN)
        self.assertEqual(current["postmerge_ci_run_number"], PRODUCTION_EXECUTION_RUN)
        self.assertEqual(current["execution_evidence_sha256"], EXECUTION_EVIDENCE_SHA256)
        self.assertEqual(current["private_metric_batch_sha256"], PRIVATE_METRIC_BATCH_SHA256)
        self.assertTrue(current["real_data_calibration_executed"])
        self.assertFalse(current["execution_evidence_accepted"])

    def test_execution_counts_and_abstention_state_are_exact(self) -> None:
        current = self.handoff["current_execution_truth"]
        self.assertTrue(current["private_observation_metrics_available_in_custody"])
        self.assertEqual(current["private_metric_record_count"], 42)
        self.assertEqual(current["measured_record_count"], 24)
        self.assertEqual(current["not_applicable_record_count"], 18)
        self.assertEqual(current["measured_source_family_count"], 1)
        self.assertEqual(current["candidate_derived_count"], 0)
        self.assertEqual(current["abstained_finding_count"], 6)
        self.assertEqual(current["not_applicable_finding_count"], 1)
        self.assertFalse(current["thresholds_calibrated"])
        self.assertFalse(current["resource_limits_calibrated"])

    def test_held_out_and_production_boundaries_remain_closed(self) -> None:
        current = self.handoff["current_execution_truth"]
        self.assertFalse(current["held_out_tuning_used"])
        self.assertFalse(current["held_out_evaluation_used"])
        self.assertFalse(current["production_threshold_changes_authorized"])
        self.assertFalse(current["production_resource_limit_changes_authorized"])
        self.assertFalse(current["stage4_exit_pass"])
        self.assertFalse(current["stage5_entry_authorized"])

    def test_historical_snapshot_and_current_overlay_are_explicitly_separate(self) -> None:
        historical = self.handoff["stage4"]
        current = historical["current_execution_truth"]
        self.assertFalse(historical["real_data_calibration_executed"])
        self.assertTrue(current["real_data_calibration_executed"])
        self.assertFalse(current["execution_evidence_accepted"])
        self.assertIn("realDataCalibrationExecuted=false", self.status)
        self.assertIn("realDataCalibrationExecuted=true", self.status)
        self.assertIn("Historical compatibility state", self.status)
        self.assertIn("executionEvidenceAccepted=false", self.status)


if __name__ == "__main__":
    unittest.main()
