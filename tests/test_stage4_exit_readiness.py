from __future__ import annotations

import unittest

from st_score_restore.stage4_exit_readiness import (
    BLOCK_HELDOUT_TUNING,
    BLOCK_HISTORICAL_EVIDENCE_MUTABLE,
    BLOCK_NO_DEVELOPMENT_EVIDENCE,
    BLOCK_NO_HELDOUT_EVIDENCE,
    BLOCK_NO_METRIC_TARGET_POLICY,
    BLOCK_NO_REFERENCE_BUNDLE,
    BLOCK_NO_SAFETY_CALIBRATION_PERMISSION,
    BLOCK_PREMATURE_PRODUCTION_CHANGE,
    BLOCK_REAL_BYTES_IN_GIT,
    BLOCK_SOURCE_FAMILY_LEAKAGE,
    Stage4ExitReadinessError,
    Stage4ReadinessInput,
    evaluate_stage4_exit_readiness,
)


def current_zero_state(**overrides) -> Stage4ReadinessInput:
    values = {
        "safety_calibration_artifact_count": 0,
        "accepted_real_reference_bundle_count": 0,
        "accepted_real_development_evidence_count": 0,
        "accepted_real_held_out_evaluation_evidence_count": 0,
        "accepted_metric_target_policy": False,
        "held_out_tuning_used": False,
        "source_family_leakage_count": 0,
        "historical_evidence_immutable": True,
        "real_or_derivative_bytes_in_ordinary_git": False,
        "production_threshold_change_authorized": False,
        "production_resource_limit_change_authorized": False,
    }
    values.update(overrides)
    return Stage4ReadinessInput(**values)


class Stage4ExitReadinessTests(unittest.TestCase):
    def test_current_zero_state_is_not_ready_with_exact_prerequisite_blockers(self):
        result = evaluate_stage4_exit_readiness(current_zero_state())
        self.assertEqual(result["decision"], "NOT_READY")
        self.assertEqual(
            set(result["blockerCodes"]),
            {
                BLOCK_NO_SAFETY_CALIBRATION_PERMISSION,
                BLOCK_NO_REFERENCE_BUNDLE,
                BLOCK_NO_DEVELOPMENT_EVIDENCE,
                BLOCK_NO_HELDOUT_EVIDENCE,
                BLOCK_NO_METRIC_TARGET_POLICY,
            },
        )
        self.assertFalse(result["assertions"]["stage4ExitPass"])
        self.assertFalse(result["assertions"]["stage5EntryAuthorized"])

    def test_hypothetical_complete_state_is_review_ready_but_never_pass(self):
        result = evaluate_stage4_exit_readiness(
            current_zero_state(
                safety_calibration_artifact_count=2,
                accepted_real_reference_bundle_count=2,
                accepted_real_development_evidence_count=1,
                accepted_real_held_out_evaluation_evidence_count=1,
                accepted_metric_target_policy=True,
            )
        )
        self.assertEqual(result["decision"], "READY_FOR_FINAL_ACCEPTANCE_REVIEW")
        self.assertEqual(result["blockerCodes"], [])
        self.assertTrue(result["assertions"]["readinessPrerequisitesSatisfied"])
        self.assertTrue(result["assertions"]["finalGovernanceAcceptanceStillRequired"])
        self.assertFalse(result["assertions"]["stage4ExitPass"])
        self.assertFalse(result["assertions"]["stage5EntryAuthorized"])

    def test_held_out_tuning_is_a_hard_blocker(self):
        result = evaluate_stage4_exit_readiness(
            current_zero_state(
                safety_calibration_artifact_count=1,
                accepted_real_reference_bundle_count=1,
                accepted_real_development_evidence_count=1,
                accepted_real_held_out_evaluation_evidence_count=1,
                accepted_metric_target_policy=True,
                held_out_tuning_used=True,
            )
        )
        self.assertEqual(result["decision"], "NOT_READY")
        self.assertEqual(result["blockerCodes"], [BLOCK_HELDOUT_TUNING])

    def test_source_family_leakage_is_a_hard_blocker(self):
        result = evaluate_stage4_exit_readiness(
            current_zero_state(
                safety_calibration_artifact_count=1,
                accepted_real_reference_bundle_count=1,
                accepted_real_development_evidence_count=1,
                accepted_real_held_out_evaluation_evidence_count=1,
                accepted_metric_target_policy=True,
                source_family_leakage_count=1,
            )
        )
        self.assertEqual(result["blockerCodes"], [BLOCK_SOURCE_FAMILY_LEAKAGE])

    def test_historical_evidence_mutability_blocks_readiness(self):
        result = evaluate_stage4_exit_readiness(
            current_zero_state(
                safety_calibration_artifact_count=1,
                accepted_real_reference_bundle_count=1,
                accepted_real_development_evidence_count=1,
                accepted_real_held_out_evaluation_evidence_count=1,
                accepted_metric_target_policy=True,
                historical_evidence_immutable=False,
            )
        )
        self.assertEqual(result["blockerCodes"], [BLOCK_HISTORICAL_EVIDENCE_MUTABLE])

    def test_real_bytes_in_git_blocks_readiness(self):
        result = evaluate_stage4_exit_readiness(
            current_zero_state(
                safety_calibration_artifact_count=1,
                accepted_real_reference_bundle_count=1,
                accepted_real_development_evidence_count=1,
                accepted_real_held_out_evaluation_evidence_count=1,
                accepted_metric_target_policy=True,
                real_or_derivative_bytes_in_ordinary_git=True,
            )
        )
        self.assertEqual(result["blockerCodes"], [BLOCK_REAL_BYTES_IN_GIT])

    def test_premature_production_change_authorization_blocks_readiness(self):
        result = evaluate_stage4_exit_readiness(
            current_zero_state(
                safety_calibration_artifact_count=1,
                accepted_real_reference_bundle_count=1,
                accepted_real_development_evidence_count=1,
                accepted_real_held_out_evaluation_evidence_count=1,
                accepted_metric_target_policy=True,
                production_threshold_change_authorized=True,
            )
        )
        self.assertEqual(result["blockerCodes"], [BLOCK_PREMATURE_PRODUCTION_CHANGE])
        self.assertFalse(result["assertions"]["productionThresholdChangeAuthorizedByReadiness"])

    def test_digest_is_deterministic(self):
        first = evaluate_stage4_exit_readiness(current_zero_state())
        second = evaluate_stage4_exit_readiness(current_zero_state())
        self.assertEqual(first["readinessDigest"], second["readinessDigest"])

    def test_mapping_requires_exact_schema(self):
        with self.assertRaises(Stage4ExitReadinessError):
            evaluate_stage4_exit_readiness({"safetyCalibrationArtifactCount": 0})

    def test_negative_counts_are_rejected(self):
        with self.assertRaises(Stage4ExitReadinessError):
            current_zero_state(safety_calibration_artifact_count=-1)


if __name__ == "__main__":
    unittest.main()
