from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from st_score_restore.stage6_trust_boundary_decision import (
    Stage6TrustBoundaryDecisionError,
    validate_stage6_trust_boundary_decision,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage6TrustBoundaryDecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.decision = load("evidence/stage6/governance/stage6-production-trust-boundary-decision.v1.json")
        self.entry_truth = load("docs/live/ST_SCORE_RESTORE_STAGE6_ENTRY_AUTHORIZATION_CURRENT_TRUTH.json")
        self.entry_authorization = load("evidence/stage6/governance/stage6-entry-authorization.v1.json")
        self.stage5_final = load("evidence/stage5/final-exit/stage5-final-exit-acceptance.v1.json")
        self.historical_stage5_truth = load("docs/live/ST_SCORE_RESTORE_STAGE5_FINAL_EXIT_CURRENT_TRUTH.json")

    def validate(self, raw: dict | None = None) -> dict:
        return validate_stage6_trust_boundary_decision(
            self.decision if raw is None else raw,
            self.entry_truth,
            self.entry_authorization,
            self.stage5_final,
            self.historical_stage5_truth,
        )

    def test_exact_decision_is_valid(self) -> None:
        value = self.validate()
        self.assertEqual(value["providerDecision"]["providerSelectionStatus"], "UNSELECTED")
        self.assertEqual(value["identityStrategy"]["initialRelyingParties"], ["st-score-restore"])
        self.assertFalse(value["scope"]["productionIdentityImplementationAuthorized"])

    def test_provider_cannot_be_silently_selected(self) -> None:
        raw = deepcopy(self.decision)
        raw["providerDecision"]["providerSelectionStatus"] = "SELECTED"
        with self.assertRaises(Stage6TrustBoundaryDecisionError):
            self.validate(raw)

    def test_live_deployment_cannot_be_authorized(self) -> None:
        raw = deepcopy(self.decision)
        raw["productionTrustBoundary"]["deployment"]["liveProductionDeploymentAuthorizedByThisDecision"] = True
        with self.assertRaises(Stage6TrustBoundaryDecisionError):
            self.validate(raw)

    def test_static_api_key_cannot_become_production_identity(self) -> None:
        raw = deepcopy(self.decision)
        raw["identityStrategy"]["productionStaticApiKeysAllowed"] = True
        with self.assertRaises(Stage6TrustBoundaryDecisionError):
            self.validate(raw)

    def test_builtin_server_cannot_be_public_edge(self) -> None:
        raw = deepcopy(self.decision)
        raw["productionTrustBoundary"]["edge"]["builtInStdlibServerPublicExposureAllowed"] = True
        with self.assertRaises(Stage6TrustBoundaryDecisionError):
            self.validate(raw)

    def test_stage7_cannot_be_authorized(self) -> None:
        raw = deepcopy(self.decision)
        raw["scope"]["stage7EntryAuthorized"] = True
        with self.assertRaises(Stage6TrustBoundaryDecisionError):
            self.validate(raw)


if __name__ == "__main__":
    unittest.main()
