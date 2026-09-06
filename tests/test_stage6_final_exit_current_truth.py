from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from st_score_restore.stage6_final_exit_current_truth import (
    Stage6FinalExitCurrentTruthError,
    summarize_stage6_final_exit_current_truth,
    validate_stage6_final_exit_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage6FinalExitCurrentTruthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.current = load("docs/live/ST_SCORE_RESTORE_STAGE6_FINAL_EXIT_CURRENT_TRUTH.json")
        self.acceptance = load("evidence/stage6/final-exit/stage6-final-exit-acceptance.v1.json")
        self.s6_08 = load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_08_CURRENT_TRUTH.json")

    def test_current_truth_records_provider_neutral_stage6_pass(self) -> None:
        summary = summarize_stage6_final_exit_current_truth(self.current, self.acceptance, self.s6_08)
        self.assertEqual(summary["stage6State"], "COMPLETE_PASS_PROVIDER_NEUTRAL")
        self.assertTrue(summary["stage6ExitPass"])
        self.assertEqual(summary["providerSelectionStatus"], "UNSELECTED")
        self.assertFalse(summary["productionDeploymentAuthorized"])
        self.assertTrue(summary["stage7EntryEligible"])
        self.assertFalse(summary["stage7EntryAuthorized"])
        self.assertFalse(summary["stage7Started"])

    def test_stage7_auto_authorization_fails_closed(self) -> None:
        value = copy.deepcopy(self.current)
        value["stage7"]["entry_authorized"] = True
        with self.assertRaises(Stage6FinalExitCurrentTruthError):
            validate_stage6_final_exit_current_truth(value, self.acceptance, self.s6_08)

    def test_provider_selection_drift_fails_closed(self) -> None:
        value = copy.deepcopy(self.current)
        value["provider"]["selection_status"] = "SELECTED"
        with self.assertRaises(Stage6FinalExitCurrentTruthError):
            validate_stage6_final_exit_current_truth(value, self.acceptance, self.s6_08)

    def test_production_deployment_overclaim_fails_closed(self) -> None:
        value = copy.deepcopy(self.current)
        value["deployment"]["production_deployment_authorized"] = True
        with self.assertRaises(Stage6FinalExitCurrentTruthError):
            validate_stage6_final_exit_current_truth(value, self.acceptance, self.s6_08)

    def test_historical_s6_08_must_remain_pre_final_exit(self) -> None:
        historical = copy.deepcopy(self.s6_08)
        historical["stage6"]["s6_09_final_exit_authorized"] = True
        with self.assertRaises(Exception):
            validate_stage6_final_exit_current_truth(self.current, self.acceptance, historical)

    def test_final_exit_acceptance_must_remain_exact(self) -> None:
        acceptance = copy.deepcopy(self.acceptance)
        acceptance["claims"]["stage7EntryAuthorized"] = True
        with self.assertRaises(Exception):
            validate_stage6_final_exit_current_truth(self.current, acceptance, self.s6_08)


if __name__ == "__main__":
    unittest.main()
