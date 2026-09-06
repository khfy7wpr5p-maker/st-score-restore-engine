from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage8_entry_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    Stage8EntryAuthorizationError,
    summarize_stage8_entry_authorization,
    validate_stage8_entry_authorization,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage8EntryAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authorization = load("evidence/stage8/stage8-entry-authorization.v1.json")
        self.stage7_truth = load("docs/live/ST_SCORE_RESTORE_STAGE7_FINAL_EXIT_CURRENT_TRUTH.json")

    def test_authorization_is_valid_and_bounded(self):
        summary = summarize_stage8_entry_authorization(self.authorization, self.stage7_truth)
        self.assertEqual(AUTHORIZATION_CANONICAL_SHA256, summary["authorizationDigest"]["value"])
        self.assertTrue(summary["stage7ExitPass"])
        self.assertTrue(summary["stage8EntryEligible"])
        self.assertTrue(summary["stage8EntryAuthorized"])
        self.assertTrue(summary["stage8Started"])
        self.assertFalse(summary["docresRuntimeDependencyApproved"])
        self.assertFalse(summary["liveDocresRuntimeActivationAuthorized"])
        self.assertFalse(summary["stage9EntryAuthorized"])

    def test_runtime_and_model_scope_cannot_be_silently_broadened(self):
        for field in (
            "externalPackageInstallationAuthorized",
            "docresRuntimeDependencyApproved",
            "modelArtifactDownloadAuthorized",
            "modelWeightsUseAuthorized",
            "networkFetchAuthorized",
            "liveDocresRuntimeActivationAuthorized",
            "realUserDocresCohortAuthorized",
            "productionDeploymentAuthorized",
            "modelTrainingAuthorized",
            "modelPublicationAuthorized",
            "stage9EntryAuthorized",
        ):
            with self.subTest(field=field):
                changed = deepcopy(self.authorization)
                changed["scope"][field] = True
                with self.assertRaises(Stage8EntryAuthorizationError):
                    validate_stage8_entry_authorization(changed, self.stage7_truth)

    def test_historical_stage7_truth_cannot_be_rewritten(self):
        changed = deepcopy(self.stage7_truth)
        changed["stage8"]["entry_authorized"] = True
        with self.assertRaises(Stage8EntryAuthorizationError):
            validate_stage8_entry_authorization(self.authorization, changed)

    def test_stage7_must_remain_complete_pass(self):
        changed = deepcopy(self.stage7_truth)
        changed["stage7"]["state"] = "ACTIVE"
        with self.assertRaises(Stage8EntryAuthorizationError):
            validate_stage8_entry_authorization(self.authorization, changed)

    def test_source_and_claim_boundaries_remain_intact(self):
        for field in (
            "source_artifact_immutable",
            "historical_evidence_immutable",
        ):
            with self.subTest(field=field):
                changed = deepcopy(self.stage7_truth)
                changed["assertions"][field] = False
                with self.assertRaises(Stage8EntryAuthorizationError):
                    validate_stage8_entry_authorization(self.authorization, changed)
        for field in ("omr_correctness_established", "musical_truth_established"):
            with self.subTest(field=field):
                changed = deepcopy(self.stage7_truth)
                changed["assertions"][field] = True
                with self.assertRaises(Stage8EntryAuthorizationError):
                    validate_stage8_entry_authorization(self.authorization, changed)


if __name__ == "__main__":
    unittest.main()
