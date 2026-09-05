from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage6_s6_05_current_truth import (
    Stage6S605CurrentTruthError,
    summarize_stage6_s6_05_current_truth,
    validate_stage6_s6_05_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage6S605CurrentTruthTests(unittest.TestCase):
    def setUp(self):
        self.current = load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_05_CURRENT_TRUTH.json")
        self.authorization = load("evidence/stage6/governance/stage6-s6-05-production-network-authorization.v1.json")
        self.previous = load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_04_CURRENT_TRUTH.json")

    def test_committed_current_truth_is_valid(self):
        validated = validate_stage6_s6_05_current_truth(self.current, self.authorization, self.previous)
        summary = summarize_stage6_s6_05_current_truth(validated, self.authorization, self.previous)
        self.assertEqual("ACTIVE_NETWORK_SECURITY_IMPLEMENTED_PROVIDER_UNSELECTED", summary["stage6State"])
        self.assertTrue(summary["networkSecurityContractImplemented"])
        self.assertFalse(summary["liveNetworkResourcesCreated"])
        self.assertFalse(summary["providerSpecificRequestSmugglingCertified"])

    def test_provider_cannot_be_silently_selected(self):
        current = deepcopy(self.current)
        current["provider"]["selection_status"] = "SELECTED"
        with self.assertRaises(Stage6S605CurrentTruthError):
            validate_stage6_s6_05_current_truth(current, self.authorization, self.previous)

    def test_builtin_stdlib_cannot_become_public_edge(self):
        current = deepcopy(self.current)
        current["network"]["built_in_stdlib_public_edge_allowed"] = True
        with self.assertRaises(Stage6S605CurrentTruthError):
            validate_stage6_s6_05_current_truth(current, self.authorization, self.previous)

    def test_live_network_resources_cannot_be_claimed(self):
        current = deepcopy(self.current)
        current["network"]["live_network_resources_created"] = True
        with self.assertRaises(Stage6S605CurrentTruthError):
            validate_stage6_s6_05_current_truth(current, self.authorization, self.previous)

    def test_s6_06_cannot_be_silently_authorized(self):
        current = deepcopy(self.current)
        current["stage6"]["production_storage_deployment_implementation_authorized"] = True
        with self.assertRaises(Stage6S605CurrentTruthError):
            validate_stage6_s6_05_current_truth(current, self.authorization, self.previous)

    def test_provider_specific_certification_cannot_be_claimed(self):
        current = deepcopy(self.current)
        current["network"]["provider_specific_request_smuggling_certified"] = True
        with self.assertRaises(Stage6S605CurrentTruthError):
            validate_stage6_s6_05_current_truth(current, self.authorization, self.previous)

    def test_historical_s6_04_network_boundary_cannot_be_broadened(self):
        previous = deepcopy(self.previous)
        previous["stage6"]["production_network_implementation_authorized"] = True
        with self.assertRaises(Stage6S605CurrentTruthError):
            validate_stage6_s6_05_current_truth(self.current, self.authorization, previous)


if __name__ == "__main__":
    unittest.main()
