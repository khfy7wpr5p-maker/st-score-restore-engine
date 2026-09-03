from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage4_metric_acceptance_target_policy_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    Stage4MetricPolicyAcceptanceError,
    summarize_metric_acceptance_target_policy_acceptance,
    validate_metric_acceptance_target_policy_acceptance,
)

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "evidence/stage4/calibration/metric-acceptance-target-policy-acceptance.v1.json"
CANDIDATE = ROOT / "evidence/stage4/calibration/metric-acceptance-target-policy-candidate.v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Stage4MetricPolicyAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.acceptance = load(ACCEPTANCE)
        self.candidate = load(CANDIDATE)

    def test_exact_acceptance_is_valid_and_keeps_downstream_gates_closed(self) -> None:
        value = validate_metric_acceptance_target_policy_acceptance(self.acceptance, self.candidate)
        self.assertTrue(value["assertions"]["metricAcceptanceTargetPolicyAccepted"])
        self.assertFalse(value["assertions"]["heldOutEvaluationAuthorized"])
        self.assertFalse(value["assertions"]["candidateThresholdsAccepted"])
        self.assertFalse(value["assertions"]["stage4ExitPass"])
        self.assertFalse(value["assertions"]["stage5EntryAuthorized"])
        summary = summarize_metric_acceptance_target_policy_acceptance(self.acceptance, self.candidate)
        self.assertEqual(summary["acceptanceDigest"]["value"], ACCEPTANCE_CANONICAL_SHA256)
        self.assertEqual(summary["remainingReadinessBlockers"], ["no_real_held_out_evaluation_evidence_is_accepted"])

    def test_cannot_authorize_held_out_or_threshold_changes(self) -> None:
        for key in ("heldOutEvaluationAuthorized", "candidateThresholdsAccepted", "productionThresholdChangeAuthorized", "stage4ExitPass", "stage5EntryAuthorized"):
            mutated = copy.deepcopy(self.acceptance)
            mutated["assertions"][key] = True
            with self.assertRaises(Stage4MetricPolicyAcceptanceError):
                validate_metric_acceptance_target_policy_acceptance(mutated, self.candidate)

    def test_future_candidate_mode_stays_fail_closed(self) -> None:
        mutated = copy.deepcopy(self.acceptance)
        mutated["futureCandidatePolicy"]["numericTargetAddendumRequired"] = False
        with self.assertRaises(Stage4MetricPolicyAcceptanceError):
            validate_metric_acceptance_target_policy_acceptance(mutated, self.candidate)

    def test_historical_candidate_cannot_be_rewritten_as_accepted(self) -> None:
        mutated_candidate = copy.deepcopy(self.candidate)
        mutated_candidate["assertions"]["metricAcceptanceTargetPolicyAccepted"] = True
        with self.assertRaises(Exception):
            validate_metric_acceptance_target_policy_acceptance(self.acceptance, mutated_candidate)


if __name__ == "__main__":
    unittest.main()
