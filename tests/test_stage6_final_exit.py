from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from st_score_restore.stage6_final_exit import (
    EXPECTED_ACCEPTANCE_SHA256,
    Stage6FinalExitError,
    canonical_sha256,
    validate_stage6_final_exit,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage6FinalExitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.current = load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_08_CURRENT_TRUTH.json")
        self.acceptance = load("evidence/stage6/final-exit/stage6-final-exit-acceptance.v1.json")

    def test_final_exit_passes_and_remains_provider_neutral(self) -> None:
        result = validate_stage6_final_exit(self.current, self.acceptance)
        self.assertEqual(result["stage6State"], "COMPLETE_PASS_PROVIDER_NEUTRAL")
        self.assertTrue(result["stage6ExitPass"])
        self.assertTrue(result["stage7EntryEligible"])
        self.assertFalse(result["stage7EntryAuthorized"])
        self.assertEqual(result["providerSelectionStatus"], "UNSELECTED")
        self.assertFalse(result["productionDeploymentAuthorized"])
        self.assertEqual(result["acceptanceDigest"], EXPECTED_ACCEPTANCE_SHA256)
        self.assertEqual(canonical_sha256(self.acceptance), EXPECTED_ACCEPTANCE_SHA256)

    def test_provider_selection_drift_fails_closed(self) -> None:
        current = copy.deepcopy(self.current)
        current["provider"]["selection_status"] = "SELECTED"
        with self.assertRaises(Stage6FinalExitError):
            validate_stage6_final_exit(current, self.acceptance)

    def test_live_deployment_claim_fails_closed(self) -> None:
        current = copy.deepcopy(self.current)
        current["deployment"]["production_deployment_authorized"] = True
        with self.assertRaises(Stage6FinalExitError):
            validate_stage6_final_exit(current, self.acceptance)

    def test_stage7_cannot_be_auto_authorized(self) -> None:
        acceptance = copy.deepcopy(self.acceptance)
        acceptance["stage7EntryAuthorized"] = True
        with self.assertRaises(Stage6FinalExitError):
            validate_stage6_final_exit(self.current, acceptance)

    def test_production_certification_cannot_be_overclaimed(self) -> None:
        acceptance = copy.deepcopy(self.acceptance)
        acceptance["claims"]["providerSpecificSecurityCertified"] = True
        with self.assertRaises(Stage6FinalExitError):
            validate_stage6_final_exit(self.current, acceptance)

    def test_acceptance_digest_is_immutable(self) -> None:
        acceptance = copy.deepcopy(self.acceptance)
        acceptance["acceptedLimitations"][0] += " drift"
        with self.assertRaises(Stage6FinalExitError):
            validate_stage6_final_exit(self.current, acceptance)


if __name__ == "__main__":
    unittest.main()
