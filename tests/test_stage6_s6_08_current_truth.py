from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage6_s6_08_current_truth import (
    Stage6S608CurrentTruthError,
    summarize_stage6_s6_08_current_truth,
    validate_stage6_s6_08_current_truth,
)


class Stage6S608CurrentTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.current = json.loads(Path("docs/live/ST_SCORE_RESTORE_STAGE6_S6_08_CURRENT_TRUTH.json").read_text(encoding="utf-8"))
        cls.authorization = json.loads(Path("evidence/stage6/governance/stage6-s6-08-integration-security-regression-authorization.v1.json").read_text(encoding="utf-8"))
        cls.previous = json.loads(Path("docs/live/ST_SCORE_RESTORE_STAGE6_S6_07_CURRENT_TRUTH.json").read_text(encoding="utf-8"))

    def test_current_truth_validates(self) -> None:
        validated = validate_stage6_s6_08_current_truth(self.current, self.authorization, self.previous)
        self.assertEqual(validated["stage6"]["state"], "ACTIVE_INTEGRATION_SECURITY_REGRESSION_COMPLETE_PROVIDER_UNSELECTED")

    def test_summary_preserves_next_gate(self) -> None:
        summary = summarize_stage6_s6_08_current_truth(self.current, self.authorization, self.previous)
        self.assertTrue(summary["integrationSecurityRegressionComplete"])
        self.assertFalse(summary["productionDeploymentAuthorized"])
        self.assertFalse(summary["stage7EntryAuthorized"])
        self.assertEqual(summary["nextSafeBoundary"], "separate_explicit_s6_09_final_exit_authorization")

    def test_provider_cannot_be_silently_selected(self) -> None:
        current = deepcopy(self.current)
        current["provider"]["selection_status"] = "SELECTED"
        with self.assertRaises(Stage6S608CurrentTruthError):
            validate_stage6_s6_08_current_truth(current, self.authorization, self.previous)

    def test_production_deployment_cannot_be_silently_authorized(self) -> None:
        current = deepcopy(self.current)
        current["deployment"]["production_deployment_authorized"] = True
        with self.assertRaises(Stage6S608CurrentTruthError):
            validate_stage6_s6_08_current_truth(current, self.authorization, self.previous)

    def test_provider_security_certification_cannot_be_claimed(self) -> None:
        current = deepcopy(self.current)
        current["integration_security_regression"]["provider_specific_security_certification_complete"] = True
        with self.assertRaises(Stage6S608CurrentTruthError):
            validate_stage6_s6_08_current_truth(current, self.authorization, self.previous)

    def test_stage7_cannot_be_silently_authorized(self) -> None:
        current = deepcopy(self.current)
        current["stage7"]["entry_authorized"] = True
        with self.assertRaises(Stage6S608CurrentTruthError):
            validate_stage6_s6_08_current_truth(current, self.authorization, self.previous)

    def test_historical_s6_07_gate_must_remain_immutable(self) -> None:
        previous = deepcopy(self.previous)
        previous["stage6"]["s6_08_integration_security_regression_authorized"] = True
        with self.assertRaises(Stage6S608CurrentTruthError):
            validate_stage6_s6_08_current_truth(self.current, self.authorization, previous)


if __name__ == "__main__":
    unittest.main()
