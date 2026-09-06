from __future__ import annotations

from dataclasses import replace
import unittest

from st_score_restore.stage6_operational_drills import (
    OperationalDrillError,
    run_synthetic_operational_drills,
    validate_synthetic_operational_drill_report,
)


class Stage6OperationalDrillTests(unittest.TestCase):
    def test_all_synthetic_operational_drills_pass(self):
        report = run_synthetic_operational_drills()
        self.assertTrue(report.passed)
        self.assertTrue(report.synthetic_only)
        self.assertFalse(report.provider_calls_performed)
        self.assertFalse(report.production_state_mutated)
        self.assertFalse(report.production_deployment_performed)
        self.assertEqual(6, len(report.results))

    def test_expected_fail_closed_scenarios_are_exercised(self):
        report = run_synthetic_operational_drills()
        names = {result.name: result for result in report.results}
        self.assertIn("stale_claim_denied", names["queue_redelivery_and_stale_worker_fencing"].assertions)
        self.assertIn("partial_write_fail_closed", names["crash_recovery_and_idempotent_replay"].assertions)
        self.assertIn("resurrection_rejected", names["deletion_restore_anti_resurrection"].assertions)
        self.assertIn("sensitive_operation_blocked_when_audit_unavailable", names["audit_dependency_fail_closed"].assertions)
        self.assertIn("production_activation_blocked", names["deployment_candidate_and_rollback_gate"].assertions)
        self.assertIn("idempotent_commit_once", names["bounded_concurrency_and_idempotency_stress"].assertions)

    def test_concurrency_drill_is_bounded(self):
        report = run_synthetic_operational_drills()
        result = next(item for item in report.results if item.name == "bounded_concurrency_and_idempotency_stress")
        self.assertEqual(64, result.operations)

    def test_report_cannot_claim_live_provider_calls(self):
        report = run_synthetic_operational_drills()
        mutated = replace(report, provider_calls_performed=True)
        with self.assertRaises(OperationalDrillError):
            validate_synthetic_operational_drill_report(mutated)

    def test_report_cannot_claim_production_deployment(self):
        report = run_synthetic_operational_drills()
        mutated = replace(report, production_deployment_performed=True)
        with self.assertRaises(OperationalDrillError):
            validate_synthetic_operational_drill_report(mutated)


if __name__ == "__main__":
    unittest.main()
