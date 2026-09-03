from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from st_score_restore.stage5_entry_current_truth import (
    Stage5EntryCurrentTruthError,
    validate_stage5_entry_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage5PostEntryAuthorizationCurrentTruthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.overlay = load("docs/live/ST_SCORE_RESTORE_STAGE5_ENTRY_AUTHORIZATION_CURRENT_TRUTH.json")
        self.authorization = load("evidence/stage5/governance/stage5-entry-authorization.v1.json")
        self.stage4_final = load("evidence/stage4/final-exit/stage4-final-exit-acceptance.v1.json")
        self.historical_stage4_truth = load("docs/live/ST_SCORE_RESTORE_STAGE4_FINAL_EXIT_CURRENT_TRUTH.json")

    def validate(self, overlay: dict | None = None) -> dict:
        return validate_stage5_entry_current_truth(
            self.overlay if overlay is None else overlay,
            self.authorization,
            self.stage4_final,
            self.historical_stage4_truth,
        )

    def test_exact_overlay_is_valid(self) -> None:
        value = self.validate()
        self.assertEqual(value["stage4"]["state"], "COMPLETE_PASS")
        self.assertTrue(value["stage5"]["entry_authorized"])
        self.assertFalse(value["stage5"]["started"])
        self.assertFalse(value["stage6"]["entry_authorized"])

    def test_overlay_cannot_start_stage5(self) -> None:
        value = deepcopy(self.overlay)
        value["stage5"]["started"] = True
        with self.assertRaises(Stage5EntryCurrentTruthError):
            self.validate(value)

    def test_overlay_cannot_authorize_interface_implementation(self) -> None:
        value = deepcopy(self.overlay)
        value["stage5"]["teacher_review_interface_implementation_authorized"] = True
        with self.assertRaises(Stage5EntryCurrentTruthError):
            self.validate(value)

    def test_overlay_cannot_authorize_stage6(self) -> None:
        value = deepcopy(self.overlay)
        value["stage6"]["entry_authorized"] = True
        with self.assertRaises(Stage5EntryCurrentTruthError):
            self.validate(value)

    def test_historical_stage4_checkpoint_stays_pre_entry_authorization(self) -> None:
        self.assertTrue(self.historical_stage4_truth["stage5"]["entry_eligible"])
        self.assertFalse(self.historical_stage4_truth["stage5"]["entry_authorized"])
        self.assertFalse(self.historical_stage4_truth["stage5"]["started"])


if __name__ == "__main__":
    unittest.main()
