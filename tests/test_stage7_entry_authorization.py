from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage7_entry_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    Stage7EntryAuthorizationError,
    summarize_stage7_entry_authorization,
    validate_stage7_entry_authorization,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage7EntryAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authorization = load("evidence/stage7/governance/stage7-entry-authorization.v1.json")
        self.stage6_truth = load("docs/live/ST_SCORE_RESTORE_STAGE6_FINAL_EXIT_CURRENT_TRUTH.json")

    def test_authorization_is_valid_and_bounded(self):
        summary = summarize_stage7_entry_authorization(self.authorization, self.stage6_truth)
        self.assertEqual(AUTHORIZATION_CANONICAL_SHA256, summary["authorizationDigest"]["value"])
        self.assertTrue(summary["stage6ExitPass"])
        self.assertTrue(summary["stage7EntryEligible"])
        self.assertTrue(summary["stage7EntryAuthorized"])
        self.assertTrue(summary["stage7Started"])
        self.assertTrue(summary["providerNeutralPreviewReadinessAuthorized"])
        self.assertFalse(summary["previewReleaseActivationAuthorized"])
        self.assertFalse(summary["stage8EntryAuthorized"])

    def test_scope_cannot_silently_authorize_release_activation(self):
        changed = deepcopy(self.authorization)
        changed["scope"]["previewReleaseActivationAuthorized"] = True
        with self.assertRaises(Stage7EntryAuthorizationError):
            validate_stage7_entry_authorization(changed, self.stage6_truth)

    def test_scope_cannot_silently_authorize_provider_or_production(self):
        for field in (
            "providerSelectionAuthorized",
            "providerSpecificAdapterActivationAuthorized",
            "liveResourceCreationAuthorized",
            "productionDeploymentAuthorized",
            "productionLoadSoakAuthorized",
            "productionPenetrationTestAuthorized",
            "modelTrainingAuthorized",
            "modelPublicationAuthorized",
            "stage8EntryAuthorized",
        ):
            with self.subTest(field=field):
                changed = deepcopy(self.authorization)
                changed["scope"][field] = True
                with self.assertRaises(Stage7EntryAuthorizationError):
                    validate_stage7_entry_authorization(changed, self.stage6_truth)

    def test_historical_stage6_truth_cannot_be_rewritten(self):
        changed = deepcopy(self.stage6_truth)
        changed["stage7"]["entry_authorized"] = True
        with self.assertRaises(Stage7EntryAuthorizationError):
            validate_stage7_entry_authorization(self.authorization, changed)

    def test_stage6_must_remain_provider_neutral_pass(self):
        changed = deepcopy(self.stage6_truth)
        changed["stage6"]["state"] = "COMPLETE_PASS_PROVIDER_SELECTED"
        with self.assertRaises(Stage7EntryAuthorizationError):
            validate_stage7_entry_authorization(self.authorization, changed)

    def test_color_and_omr_claim_boundaries_remain_false(self):
        for field in ("color_management_validated", "color_fidelity_certified", "omr_correctness_established"):
            with self.subTest(field=field):
                changed = deepcopy(self.stage6_truth)
                changed["assertions"][field] = True
                with self.assertRaises(Stage7EntryAuthorizationError):
                    validate_stage7_entry_authorization(self.authorization, changed)


if __name__ == "__main__":
    unittest.main()
