from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from st_score_restore.stage6_entry_authorization import (
    Stage6EntryAuthorizationError,
    validate_stage6_entry_authorization,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage6EntryAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authorization = load("evidence/stage6/governance/stage6-entry-authorization.v1.json")
        self.stage5_final = load("evidence/stage5/final-exit/stage5-final-exit-acceptance.v1.json")
        self.stage5_truth = load("docs/live/ST_SCORE_RESTORE_STAGE5_FINAL_EXIT_CURRENT_TRUTH.json")

    def validate(self, raw: dict | None = None) -> dict:
        return validate_stage6_entry_authorization(
            self.authorization if raw is None else raw,
            self.stage5_final,
            self.stage5_truth,
        )

    def test_exact_authorization_is_valid(self) -> None:
        value = self.validate()
        self.assertTrue(value["scope"]["stage6EntryAuthorized"])
        self.assertTrue(value["scope"]["stage6Started"])
        self.assertTrue(value["scope"]["providerNeutralArchitectureAndContractWorkAuthorized"])
        self.assertFalse(value["scope"]["providerSpecificTrustBoundaryDecisionPackageAuthorized"])

    def test_provider_specific_work_cannot_be_authorized(self) -> None:
        raw = deepcopy(self.authorization)
        raw["scope"]["providerSpecificTrustBoundaryDecisionPackageAuthorized"] = True
        with self.assertRaises(Stage6EntryAuthorizationError):
            self.validate(raw)

    def test_production_deployment_cannot_be_authorized(self) -> None:
        raw = deepcopy(self.authorization)
        raw["scope"]["productionDeploymentAuthorized"] = True
        with self.assertRaises(Stage6EntryAuthorizationError):
            self.validate(raw)

    def test_stage7_cannot_be_authorized(self) -> None:
        raw = deepcopy(self.authorization)
        raw["safetyBoundaries"]["stage7EntryAuthorized"] = True
        with self.assertRaises(Stage6EntryAuthorizationError):
            self.validate(raw)

    def test_training_cannot_be_authorized(self) -> None:
        raw = deepcopy(self.authorization)
        raw["scope"]["modelTrainingAuthorized"] = True
        with self.assertRaises(Stage6EntryAuthorizationError):
            self.validate(raw)


if __name__ == "__main__":
    unittest.main()
