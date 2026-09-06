from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage7_final_exit_current_truth import (
    EXPECTED_CURRENT_TRUTH_SHA256,
    Stage7FinalExitCurrentTruthError,
    validate_stage7_final_exit_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage7FinalExitCurrentTruthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.args = [
            load("docs/live/ST_SCORE_RESTORE_STAGE6_FINAL_EXIT_CURRENT_TRUTH.json"),
            load("evidence/stage7/governance/stage7-entry-authorization.v1.json"),
            load("api/stage7-preview-contract.v1.json"),
            load("evidence/stage7/final-exit/stage7-final-exit-acceptance.v1.json"),
        ]
        self.truth = load("docs/live/ST_SCORE_RESTORE_STAGE7_FINAL_EXIT_CURRENT_TRUTH.json")

    def test_current_truth_is_valid_and_bounded(self):
        result = validate_stage7_final_exit_current_truth(*self.args, self.truth)
        self.assertEqual("COMPLETE_PASS_PROVIDER_NEUTRAL_PREVIEW_CAPABILITY", result["stage7State"])
        self.assertTrue(result["stage7ExitPass"])
        self.assertTrue(result["stage8EntryEligible"])
        self.assertFalse(result["stage8EntryAuthorized"])
        self.assertFalse(result["previewReleaseActivationAuthorized"])
        self.assertEqual(EXPECTED_CURRENT_TRUTH_SHA256, result["currentTruthDigest"])

    def test_current_truth_cannot_activate_preview(self):
        changed = deepcopy(self.truth)
        changed["stage7"]["preview_release_activation_authorized"] = True
        with self.assertRaises(Stage7FinalExitCurrentTruthError):
            validate_stage7_final_exit_current_truth(*self.args, changed)

    def test_current_truth_cannot_start_stage8(self):
        changed = deepcopy(self.truth)
        changed["stage8"]["entry_authorized"] = True
        with self.assertRaises(Stage7FinalExitCurrentTruthError):
            validate_stage7_final_exit_current_truth(*self.args, changed)

    def test_current_truth_cannot_finalize_provider(self):
        changed = deepcopy(self.truth)
        changed["provider"]["selection_status"] = "SELECTED"
        with self.assertRaises(Stage7FinalExitCurrentTruthError):
            validate_stage7_final_exit_current_truth(*self.args, changed)

    def test_current_truth_cannot_claim_omr_or_restoration_effectiveness(self):
        for field in ("omr_correctness_established", "musical_truth_established", "restoration_effectiveness_established"):
            with self.subTest(field=field):
                changed = deepcopy(self.truth)
                changed["assertions"][field] = True
                with self.assertRaises(Stage7FinalExitCurrentTruthError):
                    validate_stage7_final_exit_current_truth(*self.args, changed)


if __name__ == "__main__":
    unittest.main()
