from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools import validate_stage4_post_wikimedia_acceptance_current_truth as validator

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "docs/live/ST_SCORE_RESTORE_WIKIMEDIA_ACCEPTANCE_CURRENT_TRUTH.json"
HISTORICAL_HANDOFF = ROOT / "docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json"
COMPLETION = ROOT / "evidence/stage4/corpus-expansion/wikimedia/human-label-completion.v1.json"
ACCEPTANCE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-bundle-acceptance.v1.json"


class Stage4PostWikimediaAcceptanceCurrentTruthTests(unittest.TestCase):
    def test_acceptance_current_truth_validator_passes(self) -> None:
        self.assertEqual(validator.main(), 0)

    def test_overlay_carries_later_acceptance_without_rewriting_completion(self) -> None:
        overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))
        completion = json.loads(COMPLETION.read_text(encoding="utf-8"))
        historical = json.loads(HISTORICAL_HANDOFF.read_text(encoding="utf-8"))

        self.assertEqual(overlay["production_checkpoint"]["main_sha"], validator.ACCEPTANCE_MAIN)
        self.assertTrue(overlay["assertions"]["reference_bundle_accepted"])
        self.assertTrue(overlay["assertions"]["candidate_derivation_eligible"])
        self.assertFalse(overlay["assertions"]["calibration_execution_authorized"])
        self.assertFalse(overlay["assertions"]["calibration_executed"])
        self.assertFalse(overlay["assertions"]["stage4_exit_pass"])
        self.assertFalse(overlay["assertions"]["stage5_entry_authorized"])

        self.assertEqual(completion["state"], "human_labels_complete_pending_separate_acceptance")
        self.assertFalse(completion["assertions"]["referenceBundleAccepted"])
        self.assertFalse(completion["assertions"]["candidateDerivationEligible"])
        self.assertFalse(historical["human_reference_current_truth"]["reference_bundle_accepted"])

    def test_committed_acceptance_is_separate_and_fail_closed(self) -> None:
        acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
        self.assertEqual(acceptance["decision"], "ACCEPT_REAL_REFERENCE_BUNDLE")
        self.assertTrue(acceptance["assertions"]["referenceBundleAccepted"])
        self.assertTrue(acceptance["scope"]["candidateDerivationEligible"])
        self.assertFalse(acceptance["assertions"]["realDataCalibrationExecutionAuthorized"])
        self.assertFalse(acceptance["assertions"]["realDataCalibrationExecuted"])
        self.assertFalse(acceptance["assertions"]["stage4ExitPass"])
        self.assertFalse(acceptance["assertions"]["stage5EntryAuthorized"])


if __name__ == "__main__":
    unittest.main()
