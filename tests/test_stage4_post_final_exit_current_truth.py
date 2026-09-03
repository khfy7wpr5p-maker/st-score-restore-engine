from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools.validate_stage4_post_final_exit_current_truth import (
    EXPECTED_ACCEPTANCE_DIGEST,
    EXPECTED_MAIN_SHA,
    OVERLAY,
    FINAL_ACCEPTANCE,
    PRE_FINAL_TRUTH,
    load,
    validate_overlay,
)


class Stage4PostFinalExitCurrentTruthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.overlay = load(OVERLAY)
        self.final_acceptance = load(FINAL_ACCEPTANCE)
        self.pre_final_truth = load(PRE_FINAL_TRUTH)

    def failures(self, overlay: dict | None = None) -> list[str]:
        return validate_overlay(
            overlay or self.overlay,
            self.final_acceptance,
            self.pre_final_truth,
        )

    def test_exact_overlay_is_valid(self) -> None:
        self.assertEqual(self.failures(), [])
        self.assertEqual(self.overlay["production_checkpoint"]["main_sha"], EXPECTED_MAIN_SHA)
        self.assertEqual(
            self.overlay["stage4_final_acceptance"]["acceptance_digest"],
            EXPECTED_ACCEPTANCE_DIGEST,
        )

    def test_stage4_is_complete_pass(self) -> None:
        self.assertEqual(self.overlay["stage4"]["state"], "COMPLETE_PASS")
        self.assertTrue(self.overlay["stage4"]["exit_pass"])
        self.assertEqual(self.overlay["stage4"]["readiness_blocker_count_at_acceptance"], 0)
        self.assertEqual(self.overlay["stage4"]["readiness_blocker_codes_at_acceptance"], [])

    def test_stage5_is_only_eligible(self) -> None:
        stage5 = self.overlay["stage5"]
        self.assertTrue(stage5["entry_eligible"])
        self.assertFalse(stage5["entry_authorized"])
        self.assertFalse(stage5["started"])

    def test_stage5_authorization_tamper_is_detected(self) -> None:
        tampered = deepcopy(self.overlay)
        tampered["stage5"]["entry_authorized"] = True
        self.assertTrue(self.failures(tampered))

    def test_threshold_calibration_tamper_is_detected(self) -> None:
        tampered = deepcopy(self.overlay)
        tampered["stage4"]["thresholds_calibrated"] = True
        self.assertTrue(self.failures(tampered))

    def test_historical_pre_final_checkpoint_remains_pre_final(self) -> None:
        readiness = self.pre_final_truth["stage4_readiness"]
        assertions = self.pre_final_truth["assertions"]
        self.assertTrue(readiness["final_governance_acceptance_still_required"])
        self.assertFalse(assertions["stage4_exit_pass"])
        self.assertFalse(assertions["stage5_entry_authorized"])


if __name__ == "__main__":
    unittest.main()
