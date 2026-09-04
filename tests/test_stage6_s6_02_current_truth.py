from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from st_score_restore.stage6_s6_02_current_truth import (
    Stage6S602CurrentTruthError,
    validate_stage6_s6_02_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage6S602CurrentTruthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.truth = load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_02_CURRENT_TRUTH.json")
        self.decision = load("evidence/stage6/governance/stage6-production-trust-boundary-decision.v1.json")
        self.entry_truth = load("docs/live/ST_SCORE_RESTORE_STAGE6_ENTRY_AUTHORIZATION_CURRENT_TRUTH.json")
        self.entry_authorization = load("evidence/stage6/governance/stage6-entry-authorization.v1.json")
        self.stage5_final = load("evidence/stage5/final-exit/stage5-final-exit-acceptance.v1.json")
        self.historical_stage5_truth = load("docs/live/ST_SCORE_RESTORE_STAGE5_FINAL_EXIT_CURRENT_TRUTH.json")

    def validate(self, raw: dict | None = None) -> dict:
        return validate_stage6_s6_02_current_truth(
            self.truth if raw is None else raw,
            self.decision,
            self.entry_truth,
            self.entry_authorization,
            self.stage5_final,
            self.historical_stage5_truth,
        )

    def test_exact_current_truth_is_valid(self) -> None:
        value = self.validate()
        self.assertEqual(value["provider"]["selection_status"], "UNSELECTED")
        self.assertEqual(value["identity"]["initial_relying_parties"], ["st-score-restore"])
        self.assertTrue(value["stage6"]["provider_specific_trust_boundary_decision_package_authorized"])
        self.assertFalse(value["stage6"]["production_identity_implementation_authorized"])

    def test_provider_selection_cannot_be_claimed(self) -> None:
        raw = deepcopy(self.truth)
        raw["provider"]["selection_status"] = "SELECTED"
        with self.assertRaises(Stage6S602CurrentTruthError):
            self.validate(raw)

    def test_production_identity_cannot_be_claimed_authorized(self) -> None:
        raw = deepcopy(self.truth)
        raw["stage6"]["production_identity_implementation_authorized"] = True
        with self.assertRaises(Stage6S602CurrentTruthError):
            self.validate(raw)

    def test_live_resources_cannot_be_claimed_authorized(self) -> None:
        raw = deepcopy(self.truth)
        raw["assertions"]["live_resource_creation_authorized"] = True
        with self.assertRaises(Stage6S602CurrentTruthError):
            self.validate(raw)

    def test_stage7_cannot_be_claimed_authorized(self) -> None:
        raw = deepcopy(self.truth)
        raw["stage7"]["entry_authorized"] = True
        with self.assertRaises(Stage6S602CurrentTruthError):
            self.validate(raw)


if __name__ == "__main__":
    unittest.main()
