from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from st_score_restore.stage6_entry_current_truth import (
    Stage6EntryCurrentTruthError,
    validate_stage6_entry_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage6EntryCurrentTruthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.overlay = load("docs/live/ST_SCORE_RESTORE_STAGE6_ENTRY_AUTHORIZATION_CURRENT_TRUTH.json")
        self.authorization = load("evidence/stage6/governance/stage6-entry-authorization.v1.json")
        self.stage5_final = load("evidence/stage5/final-exit/stage5-final-exit-acceptance.v1.json")
        self.stage5_truth = load("docs/live/ST_SCORE_RESTORE_STAGE5_FINAL_EXIT_CURRENT_TRUTH.json")

    def validate(self, raw: dict | None = None) -> dict:
        return validate_stage6_entry_current_truth(
            self.overlay if raw is None else raw,
            self.authorization,
            self.stage5_final,
            self.stage5_truth,
        )

    def test_exact_overlay_is_valid(self) -> None:
        value = self.validate()
        self.assertEqual(value["stage6"]["state"], "ACTIVE_GOVERNANCE_PROVIDER_NEUTRAL_ONLY")
        self.assertTrue(value["stage6"]["entry_authorized"])
        self.assertTrue(value["stage6"]["started"])
        self.assertFalse(value["stage6"]["provider_specific_trust_boundary_decision_package_authorized"])

    def test_historical_stage5_truth_is_not_rewritten(self) -> None:
        self.assertFalse(self.stage5_truth["stage6"]["entry_authorized"])
        self.assertFalse(self.stage5_truth["stage6"]["started"])
        self.validate()

    def test_provider_specific_work_cannot_be_enabled(self) -> None:
        raw = deepcopy(self.overlay)
        raw["stage6"]["provider_specific_trust_boundary_decision_package_authorized"] = True
        with self.assertRaises(Stage6EntryCurrentTruthError):
            self.validate(raw)

    def test_production_deployment_cannot_be_enabled(self) -> None:
        raw = deepcopy(self.overlay)
        raw["stage6"]["production_deployment_authorized"] = True
        with self.assertRaises(Stage6EntryCurrentTruthError):
            self.validate(raw)

    def test_stage7_cannot_be_enabled(self) -> None:
        raw = deepcopy(self.overlay)
        raw["stage7"]["entry_authorized"] = True
        with self.assertRaises(Stage6EntryCurrentTruthError):
            self.validate(raw)

    def test_color_management_cannot_be_broadened(self) -> None:
        raw = deepcopy(self.overlay)
        raw["stage5"]["color_management_validated"] = True
        with self.assertRaises(Stage6EntryCurrentTruthError):
            self.validate(raw)


if __name__ == "__main__":
    unittest.main()
