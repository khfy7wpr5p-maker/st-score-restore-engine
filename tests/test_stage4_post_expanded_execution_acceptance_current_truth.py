from __future__ import annotations

import json
import unittest
from pathlib import Path

from st_score_restore.stage4_expanded_execution_evidence_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    validate_expanded_execution_evidence_acceptance,
)
from st_score_restore.stage4_exit_readiness import (
    BLOCK_NO_HELDOUT_EVIDENCE,
    BLOCK_NO_METRIC_TARGET_POLICY,
    Stage4ReadinessInput,
    evaluate_stage4_exit_readiness,
)

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "docs/live/ST_SCORE_RESTORE_EXPANDED_EXECUTION_ACCEPTANCE_CURRENT_TRUTH.json"
ACCEPTANCE = ROOT / "evidence/stage4/calibration/expanded-real-development-execution-acceptance.v1.json"
EXECUTION = ROOT / "evidence/stage4/calibration/expanded-real-development-execution.v1.json"


class PostExpandedExecutionAcceptanceCurrentTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))
        cls.acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
        cls.execution = json.loads(EXECUTION.read_text(encoding="utf-8"))

    def test_execution_evidence_is_accepted_without_threshold_candidate(self) -> None:
        accepted = validate_expanded_execution_evidence_acceptance(self.acceptance, self.execution)
        evidence = self.overlay["accepted_execution_evidence"]
        self.assertTrue(accepted["assertions"]["executionEvidenceAccepted"])
        self.assertEqual(evidence["acceptance_digest"], ACCEPTANCE_CANONICAL_SHA256)
        self.assertTrue(evidence["execution_evidence_accepted"])
        self.assertEqual(evidence["candidate_derived_count"], 0)
        self.assertFalse(self.overlay["calibration_state"]["thresholds_calibrated"])

    def test_only_two_readiness_blockers_remain(self) -> None:
        result = evaluate_stage4_exit_readiness(
            Stage4ReadinessInput(
                safety_calibration_artifact_count=3,
                accepted_real_reference_bundle_count=1,
                accepted_real_development_evidence_count=1,
                accepted_real_held_out_evaluation_evidence_count=0,
                accepted_metric_target_policy=False,
                held_out_tuning_used=False,
                source_family_leakage_count=0,
                historical_evidence_immutable=True,
                real_or_derivative_bytes_in_ordinary_git=False,
                production_threshold_change_authorized=False,
                production_resource_limit_change_authorized=False,
            )
        )
        expected = {BLOCK_NO_HELDOUT_EVIDENCE, BLOCK_NO_METRIC_TARGET_POLICY}
        self.assertEqual(result["decision"], "NOT_READY")
        self.assertEqual(set(result["blockerCodes"]), expected)
        self.assertEqual(result["blockerCount"], 2)
        self.assertEqual(set(self.overlay["readiness"]["remaining_blocker_codes"]), expected)
        self.assertEqual(self.overlay["readiness"]["remaining_blocker_count"], 2)
        self.assertEqual(self.overlay["readiness"]["accepted_real_development_evidence_count"], 1)

    def test_downstream_gates_remain_closed(self) -> None:
        self.assertFalse(self.overlay["held_out"]["evaluation_authorized"])
        self.assertFalse(self.overlay["metric_policy"]["acceptance_target_policy_accepted"])
        self.assertFalse(self.overlay["assertions"]["stage4_exit_pass"])
        self.assertFalse(self.overlay["assertions"]["stage5_entry_authorized"])


if __name__ == "__main__":
    unittest.main()
