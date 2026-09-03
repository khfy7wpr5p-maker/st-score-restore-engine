from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from st_score_restore.stage4_metric_acceptance_target_policy import (
    POLICY_CANDIDATE_CANONICAL_SHA256,
    Stage4MetricPolicyError,
    summarize_metric_acceptance_target_policy_candidate,
    validate_metric_acceptance_target_policy_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "evidence/stage4/calibration/metric-acceptance-target-policy-candidate.v1.json"


class MetricAcceptanceTargetPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = json.loads(POLICY.read_text(encoding="utf-8"))

    def test_committed_candidate_is_valid_and_pending_acceptance(self) -> None:
        value = validate_metric_acceptance_target_policy_candidate(self.raw)
        self.assertEqual(value["status"], "policy_candidate_pending_separate_acceptance")
        self.assertFalse(value["assertions"]["metricAcceptanceTargetPolicyAccepted"])
        self.assertFalse(value["assertions"]["heldOutEvaluationAuthorized"])
        self.assertFalse(value["assertions"]["stage4ExitPass"])
        self.assertFalse(value["assertions"]["stage5EntryAuthorized"])

    def test_summary_binds_exact_candidate_digest(self) -> None:
        summary = summarize_metric_acceptance_target_policy_candidate(self.raw)
        self.assertEqual(summary["policyCandidateDigest"]["value"], POLICY_CANDIDATE_CANONICAL_SHA256)
        self.assertEqual(summary["candidateDerivedCount"], 0)
        self.assertTrue(summary["numericTargetAddendumRequiredIfCandidateAppears"])

    def test_numeric_false_positive_target_cannot_be_invented(self) -> None:
        mutated = copy.deepcopy(self.raw)
        mutated["metricTargets"]["falsePositiveRate"]["numericMaximum"] = 0.01
        with self.assertRaises(Stage4MetricPolicyError):
            validate_metric_acceptance_target_policy_candidate(mutated)

    def test_candidate_cannot_self_accept_policy(self) -> None:
        mutated = copy.deepcopy(self.raw)
        mutated["assertions"]["metricAcceptanceTargetPolicyAccepted"] = True
        with self.assertRaises(Stage4MetricPolicyError):
            validate_metric_acceptance_target_policy_candidate(mutated)

    def test_candidate_present_mode_requires_separate_numeric_addendum(self) -> None:
        future = self.raw["decisionRules"]["candidatePresent"]
        self.assertEqual(future["decision"], "BLOCK_PENDING_SEPARATE_NUMERIC_TARGET_ADDENDUM")
        self.assertTrue(future["numericTargetAddendumRequired"])
        self.assertFalse(future["automaticThresholdAcceptanceAuthorized"])


if __name__ == "__main__":
    unittest.main()
