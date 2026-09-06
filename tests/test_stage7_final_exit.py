from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage7_final_exit import (
    EXPECTED_ACCEPTANCE_SHA256,
    Stage7FinalExitError,
    validate_stage7_final_exit,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage7FinalExitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.stage6_truth = load("docs/live/ST_SCORE_RESTORE_STAGE6_FINAL_EXIT_CURRENT_TRUTH.json")
        self.authorization = load("evidence/stage7/governance/stage7-entry-authorization.v1.json")
        self.preview_contract = load("api/stage7-preview-contract.v1.json")
        self.acceptance = load("evidence/stage7/final-exit/stage7-final-exit-acceptance.v1.json")

    def test_final_exit_is_valid_and_bounded(self):
        result = validate_stage7_final_exit(
            self.stage6_truth,
            self.authorization,
            self.preview_contract,
            self.acceptance,
        )
        self.assertEqual("COMPLETE_PASS_PROVIDER_NEUTRAL_PREVIEW_CAPABILITY", result["stage7State"])
        self.assertTrue(result["stage7ExitPass"])
        self.assertTrue(result["stage8EntryEligible"])
        self.assertFalse(result["stage8EntryAuthorized"])
        self.assertFalse(result["previewReleaseActivationAuthorized"])
        self.assertEqual(EXPECTED_ACCEPTANCE_SHA256, result["acceptanceDigest"])

    def test_preview_activation_cannot_be_smuggled_into_exit(self):
        changed = deepcopy(self.acceptance)
        changed["claims"]["previewReleaseActivationAuthorized"] = True
        with self.assertRaises(Stage7FinalExitError):
            validate_stage7_final_exit(self.stage6_truth, self.authorization, self.preview_contract, changed)

    def test_stage8_cannot_be_started_by_stage7_exit(self):
        changed = deepcopy(self.acceptance)
        changed["stage8EntryAuthorized"] = True
        with self.assertRaises(Stage7FinalExitError):
            validate_stage7_final_exit(self.stage6_truth, self.authorization, self.preview_contract, changed)

    def test_preview_contract_must_remain_fail_closed(self):
        changed = deepcopy(self.preview_contract)
        changed["routing"]["killSwitchRoute"] = "restored_candidate"
        with self.assertRaises(Stage7FinalExitError):
            validate_stage7_final_exit(self.stage6_truth, self.authorization, changed, self.acceptance)

    def test_provider_must_remain_unselected(self):
        changed = deepcopy(self.acceptance)
        changed["acceptedReadinessState"]["providerSelectionStatus"] = "SELECTED"
        with self.assertRaises(Stage7FinalExitError):
            validate_stage7_final_exit(self.stage6_truth, self.authorization, self.preview_contract, changed)

    def test_unsupported_accuracy_claims_fail_closed(self):
        for field in (
            "omrCorrectnessEstablished",
            "musicalTruthEstablished",
            "restorationEffectivenessEstablished",
            "productionAvailabilityOrScalabilityEstablished",
            "providerSpecificSecurityCertified",
        ):
            with self.subTest(field=field):
                changed = deepcopy(self.acceptance)
                changed["claims"][field] = True
                with self.assertRaises(Stage7FinalExitError):
                    validate_stage7_final_exit(self.stage6_truth, self.authorization, self.preview_contract, changed)


if __name__ == "__main__":
    unittest.main()
