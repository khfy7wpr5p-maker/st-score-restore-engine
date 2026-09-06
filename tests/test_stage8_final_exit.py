from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage8_final_exit import (
    ACCEPTANCE_CANONICAL_SHA256,
    Stage8FinalExitError,
    summarize_stage8_final_exit,
    validate_stage8_final_exit,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage8FinalExitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.acceptance = load("evidence/stage8/final-exit/stage8-final-exit-acceptance.v1.json")
        self.authorization = load("evidence/stage8/stage8-entry-authorization.v1.json")
        self.stage7_truth = load("docs/live/ST_SCORE_RESTORE_STAGE7_FINAL_EXIT_CURRENT_TRUTH.json")
        self.contract = load("api/stage8-docres-candidate-contract.v1.json")

    def test_final_exit_pass_is_bounded(self):
        summary = summarize_stage8_final_exit(
            self.acceptance, self.authorization, self.stage7_truth, self.contract
        )
        self.assertEqual("PASS", summary["decision"])
        self.assertEqual(ACCEPTANCE_CANONICAL_SHA256, summary["acceptanceDigest"]["value"])
        self.assertTrue(summary["stage8ExitPass"])
        self.assertTrue(summary["stage9EntryEligible"])
        self.assertFalse(summary["stage9EntryAuthorized"])
        self.assertFalse(summary["docresRuntimeDependencyApproved"])
        self.assertFalse(summary["liveDocresRuntimeActivationAuthorized"])
        self.assertFalse(summary["stage9ComparatorSelectionAuthorized"])

    def test_live_docres_scope_cannot_be_silently_claimed(self):
        for field in (
            "externalPackageInstallationAuthorized",
            "modelArtifactDownloadAuthorized",
            "modelWeightsUseAuthorized",
            "networkFetchAuthorized",
            "liveDocresRuntimeActivationAuthorized",
            "realUserDocresCohortAuthorized",
            "productionDeploymentAuthorized",
            "stage9ComparatorSelectionAuthorized",
        ):
            with self.subTest(field=field):
                changed = deepcopy(self.acceptance)
                changed["acceptedReadinessState"][field] = True
                with self.assertRaises(Stage8FinalExitError):
                    validate_stage8_final_exit(changed, self.authorization, self.stage7_truth, self.contract)

    def test_stage9_is_eligible_but_not_authorized_or_started(self):
        for field in ("stage9EntryAuthorized", "stage9Started"):
            changed = deepcopy(self.acceptance)
            changed[field] = True
            with self.assertRaises(Stage8FinalExitError):
                validate_stage8_final_exit(changed, self.authorization, self.stage7_truth, self.contract)

    def test_contract_cannot_enable_live_runtime_or_final_selection(self):
        changed = deepcopy(self.contract)
        changed["runtime"]["liveRuntimeActivationAuthorized"] = True
        with self.assertRaises(Stage8FinalExitError):
            validate_stage8_final_exit(self.acceptance, self.authorization, self.stage7_truth, changed)

        changed = deepcopy(self.contract)
        changed["safetyHandoff"]["automaticFinalSelectionAuthorized"] = True
        with self.assertRaises(Stage8FinalExitError):
            validate_stage8_final_exit(self.acceptance, self.authorization, self.stage7_truth, changed)

    def test_unsupported_claims_remain_false(self):
        for field in (
            "omrCorrectnessEstablished",
            "musicalTruthEstablished",
            "restorationEffectivenessEstablished",
            "productionAvailabilityOrScalabilityEstablished",
        ):
            changed = deepcopy(self.acceptance)
            changed["claims"][field] = True
            with self.assertRaises(Stage8FinalExitError):
                validate_stage8_final_exit(changed, self.authorization, self.stage7_truth, self.contract)


if __name__ == "__main__":
    unittest.main()
