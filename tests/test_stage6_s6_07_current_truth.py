from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage6_s6_07_current_truth import (
    Stage6S607CurrentTruthError,
    summarize_stage6_s6_07_current_truth,
    validate_stage6_s6_07_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage6S607CurrentTruthTests(unittest.TestCase):
    def setUp(self):
        self.current = load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_07_CURRENT_TRUTH.json")
        self.authorization = load("evidence/stage6/governance/stage6-s6-07-synthetic-operational-drills-authorization.v1.json")
        self.previous = load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_06_CURRENT_TRUTH.json")

    def test_committed_current_truth_is_valid(self):
        validated = validate_stage6_s6_07_current_truth(self.current, self.authorization, self.previous)
        summary = summarize_stage6_s6_07_current_truth(validated, self.authorization, self.previous)
        self.assertEqual("ACTIVE_SYNTHETIC_OPERATIONAL_DRILLS_COMPLETE_PROVIDER_UNSELECTED", summary["stage6State"])
        self.assertTrue(summary["syntheticOperationalDrillsComplete"])
        self.assertFalse(summary["productionDistributedStressValidationComplete"])
        self.assertFalse(summary["productionDeploymentAuthorized"])

    def test_provider_cannot_be_silently_selected(self):
        current = deepcopy(self.current)
        current["provider"]["selection_status"] = "SELECTED"
        with self.assertRaises(Stage6S607CurrentTruthError):
            validate_stage6_s6_07_current_truth(current, self.authorization, self.previous)

    def test_synthetic_drills_cannot_claim_live_provider_calls(self):
        current = deepcopy(self.current)
        current["operational_drills"]["provider_calls_performed"] = True
        with self.assertRaises(Stage6S607CurrentTruthError):
            validate_stage6_s6_07_current_truth(current, self.authorization, self.previous)

    def test_production_stress_cannot_be_silently_certified(self):
        current = deepcopy(self.current)
        current["storage_queue_recovery"]["production_distributed_stress_validation_complete"] = True
        with self.assertRaises(Stage6S607CurrentTruthError):
            validate_stage6_s6_07_current_truth(current, self.authorization, self.previous)

    def test_production_deployment_cannot_be_silently_authorized(self):
        current = deepcopy(self.current)
        current["deployment"]["production_deployment_authorized"] = True
        with self.assertRaises(Stage6S607CurrentTruthError):
            validate_stage6_s6_07_current_truth(current, self.authorization, self.previous)

    def test_s6_08_cannot_be_silently_authorized(self):
        current = deepcopy(self.current)
        current["stage6"]["s6_08_integration_security_regression_authorized"] = True
        with self.assertRaises(Stage6S607CurrentTruthError):
            validate_stage6_s6_07_current_truth(current, self.authorization, self.previous)

    def test_historical_s6_06_boundary_cannot_be_broadened(self):
        previous = deepcopy(self.previous)
        previous["stage6"]["production_operational_drills_authorized"] = True
        with self.assertRaises(Stage6S607CurrentTruthError):
            validate_stage6_s6_07_current_truth(self.current, self.authorization, previous)


if __name__ == "__main__":
    unittest.main()
