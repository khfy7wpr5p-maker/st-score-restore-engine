from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage5_start_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    Stage5StartAuthorizationError,
    summarize_stage5_start_authorization,
    validate_stage5_start_authorization,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage5StartAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authorization = load("evidence/stage5/governance/stage5-framework-start-authorization.v1.json")
        self.entry_authorization = load("evidence/stage5/governance/stage5-entry-authorization.v1.json")
        self.entry_truth = load("docs/live/ST_SCORE_RESTORE_STAGE5_ENTRY_AUTHORIZATION_CURRENT_TRUTH.json")

    def test_accepts_exact_authorized_scope(self) -> None:
        value = validate_stage5_start_authorization(
            self.authorization,
            self.entry_authorization,
            self.entry_truth,
        )
        self.assertTrue(value["scope"]["stage5Started"])
        self.assertTrue(value["scope"]["teacherReviewInterfaceImplementationAuthorized"])
        self.assertTrue(value["scope"]["teacherReviewInterfaceExecutionAuthorized"])
        self.assertTrue(value["scope"]["localAccessibilityVerificationAuthorized"])
        self.assertTrue(value["scope"]["localDisplayQaAuthorized"])
        self.assertFalse(value["scope"]["productionDeploymentAuthorized"])
        self.assertFalse(value["scope"]["stage6EntryAuthorized"] if "stage6EntryAuthorized" in value["scope"] else False)

    def test_summary_is_fail_closed_for_stage6_and_deployment(self) -> None:
        summary = summarize_stage5_start_authorization(
            self.authorization,
            self.entry_authorization,
            self.entry_truth,
        )
        self.assertEqual(summary["authorizationDigest"]["value"], AUTHORIZATION_CANONICAL_SHA256)
        self.assertTrue(summary["stage5Started"])
        self.assertFalse(summary["productionDeploymentAuthorized"])
        self.assertFalse(summary["stage6EntryAuthorized"])

    def test_rejects_production_deployment_escalation(self) -> None:
        mutated = deepcopy(self.authorization)
        mutated["scope"]["productionDeploymentAuthorized"] = True
        with self.assertRaises(Stage5StartAuthorizationError):
            validate_stage5_start_authorization(mutated, self.entry_authorization, self.entry_truth)

    def test_rejects_threshold_change_escalation(self) -> None:
        mutated = deepcopy(self.authorization)
        mutated["scope"]["productionThresholdChangesAuthorized"] = True
        with self.assertRaises(Stage5StartAuthorizationError):
            validate_stage5_start_authorization(mutated, self.entry_authorization, self.entry_truth)

    def test_rejects_held_out_retuning_escalation(self) -> None:
        mutated = deepcopy(self.authorization)
        mutated["scope"]["heldOutRetuningAuthorized"] = True
        with self.assertRaises(Stage5StartAuthorizationError):
            validate_stage5_start_authorization(mutated, self.entry_authorization, self.entry_truth)

    def test_rejects_rewritten_historical_entry_truth(self) -> None:
        mutated_truth = deepcopy(self.entry_truth)
        mutated_truth["stage5"]["started"] = True
        with self.assertRaises(Stage5StartAuthorizationError):
            validate_stage5_start_authorization(self.authorization, self.entry_authorization, mutated_truth)


if __name__ == "__main__":
    unittest.main()
