from __future__ import annotations

from dataclasses import replace
import unittest

from st_score_restore.stage6_integration_security_regression import (
    IntegrationSecurityRegressionError,
    run_integration_security_regression,
    validate_integration_security_regression_report,
)


class Stage6IntegrationSecurityRegressionTests(unittest.TestCase):
    def test_full_synthetic_integration_security_regression_passes(self) -> None:
        report = run_integration_security_regression()
        self.assertTrue(report.passed)
        self.assertTrue(report.synthetic_only)
        self.assertFalse(report.provider_calls_performed)
        self.assertFalse(report.live_resources_created)
        self.assertFalse(report.production_state_mutated)
        self.assertFalse(report.production_deployment_performed)
        self.assertEqual(
            tuple(result.name for result in report.results),
            (
                "trusted_edge_identity_iam_kms_storage_chain",
                "legacy_identity_header_bypass_denied",
                "cross_tenant_job_access_denied",
                "identity_conflict_revocation_signature_denied",
                "cross_environment_secret_kms_denied",
                "security_audit_dependency_fail_closed",
                "edge_and_private_topology_bypass_denied",
                "storage_queue_deployment_fail_closed",
                "s6_07_operational_regression_replay",
            ),
        )

    def test_report_cannot_claim_provider_calls(self) -> None:
        report = run_integration_security_regression()
        with self.assertRaises(IntegrationSecurityRegressionError):
            validate_integration_security_regression_report(replace(report, provider_calls_performed=True))

    def test_report_cannot_claim_live_resources(self) -> None:
        report = run_integration_security_regression()
        with self.assertRaises(IntegrationSecurityRegressionError):
            validate_integration_security_regression_report(replace(report, live_resources_created=True))

    def test_report_cannot_claim_production_deployment(self) -> None:
        report = run_integration_security_regression()
        with self.assertRaises(IntegrationSecurityRegressionError):
            validate_integration_security_regression_report(replace(report, production_deployment_performed=True))

    def test_all_regressions_must_pass(self) -> None:
        report = run_integration_security_regression()
        bad = replace(report.results[0], passed=False)
        with self.assertRaises(IntegrationSecurityRegressionError):
            validate_integration_security_regression_report(replace(report, results=(bad,) + report.results[1:]))


if __name__ == "__main__":
    unittest.main()
