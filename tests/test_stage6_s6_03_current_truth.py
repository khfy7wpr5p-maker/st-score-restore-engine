from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage6_s6_03_current_truth import (
    Stage6S603CurrentTruthError,
    summarize_stage6_s6_03_current_truth,
    validate_stage6_s6_03_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage6S603CurrentTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_03_CURRENT_TRUTH.json")
        cls.authorization = load("evidence/stage6/governance/stage6-s6-03-identity-authz-authorization.v1.json")
        cls.previous = load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_02_CURRENT_TRUTH.json")

    def test_committed_current_truth_is_valid(self):
        validated = validate_stage6_s6_03_current_truth(
            self.current,
            self.authorization,
            self.previous,
        )
        self.assertEqual("ACTIVE_IDENTITY_AUTHZ_IMPLEMENTED_PROVIDER_UNSELECTED", validated["stage6"]["state"])
        summary = summarize_stage6_s6_03_current_truth(
            self.current,
            self.authorization,
            self.previous,
        )
        self.assertTrue(summary["productionIdentityContractImplemented"])
        self.assertFalse(summary["providerSpecificIdentityAdapterActivated"])
        self.assertFalse(summary["durableProductionAuthorizationStoreImplemented"])

    def test_provider_cannot_be_silently_selected(self):
        changed = deepcopy(self.current)
        changed["provider"]["selection_status"] = "SELECTED"
        with self.assertRaises(Stage6S603CurrentTruthError):
            validate_stage6_s6_03_current_truth(changed, self.authorization, self.previous)

    def test_storage_cannot_be_silently_claimed_complete(self):
        changed = deepcopy(self.current)
        changed["authorization"]["atomic_job_authorization_cocommit_implemented"] = True
        with self.assertRaises(Stage6S603CurrentTruthError):
            validate_stage6_s6_03_current_truth(changed, self.authorization, self.previous)

    def test_historical_s6_02_checkpoint_cannot_be_rewritten(self):
        previous = deepcopy(self.previous)
        previous["stage6"]["production_identity_implementation_authorized"] = True
        with self.assertRaises(Stage6S603CurrentTruthError):
            validate_stage6_s6_03_current_truth(self.current, self.authorization, previous)

    def test_production_deployment_remains_unauthorized(self):
        changed = deepcopy(self.current)
        changed["stage6"]["production_deployment_authorized"] = True
        with self.assertRaises(Stage6S603CurrentTruthError):
            validate_stage6_s6_03_current_truth(changed, self.authorization, self.previous)


if __name__ == "__main__":
    unittest.main()
