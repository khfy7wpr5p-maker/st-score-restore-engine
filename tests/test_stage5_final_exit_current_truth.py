from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage5_final_exit_current_truth import validate_stage5_final_exit_current_truth


ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage5FinalExitCurrentTruthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.overlay = load("docs/live/ST_SCORE_RESTORE_STAGE5_FINAL_EXIT_CURRENT_TRUTH.json")
        self.qa = load("evidence/stage5/qa/stage5-accessibility-display-qa.v1.json")
        self.acceptance = load("evidence/stage5/final-exit/stage5-final-exit-acceptance.v1.json")
        self.historical = load("docs/live/ST_SCORE_RESTORE_STAGE5_ENTRY_AUTHORIZATION_CURRENT_TRUTH.json")

    def validate(self, overlay=None, qa=None, acceptance=None, historical=None):
        return validate_stage5_final_exit_current_truth(
            overlay or self.overlay,
            qa or self.qa,
            acceptance or self.acceptance,
            historical or self.historical,
        )

    def test_accepts_exact_final_current_truth(self) -> None:
        summary = self.validate()
        self.assertEqual(summary["stage5State"], "COMPLETE_PASS")
        self.assertTrue(summary["stage5ExitPass"])
        self.assertTrue(summary["stage6EntryEligible"])
        self.assertFalse(summary["stage6EntryAuthorized"])
        self.assertFalse(summary["stage6Started"])

    def test_rejects_stage6_auto_authorization(self) -> None:
        overlay = copy.deepcopy(self.overlay)
        overlay["stage6"]["entry_authorized"] = True
        with self.assertRaises(ValueError):
            self.validate(overlay=overlay)

    def test_rejects_color_certification_upgrade(self) -> None:
        overlay = copy.deepcopy(self.overlay)
        overlay["stage5"]["color_fidelity_certified"] = True
        with self.assertRaises(ValueError):
            self.validate(overlay=overlay)

    def test_rejects_screen_reader_probe_as_merged(self) -> None:
        overlay = copy.deepcopy(self.overlay)
        overlay["screen_reader_evidence"]["temporary_probe_merged"] = True
        with self.assertRaises(ValueError):
            self.validate(overlay=overlay)

    def test_rejects_historical_checkpoint_rewrite(self) -> None:
        historical = copy.deepcopy(self.historical)
        historical["stage5"]["state"] = "COMPLETE_PASS"
        historical["stage5"]["started"] = True
        with self.assertRaises(ValueError):
            self.validate(historical=historical)


if __name__ == "__main__":
    unittest.main()
