from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.validate_stage1c_vault_verification import (
    CONTROL_NAMES,
    DEFAULT_RECORD_PATH,
    VaultVerificationError,
    load_schema,
    validate_record,
)


class Stage1CVaultVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_schema()

    def make_record(self, result: str = "pass") -> dict:
        controls = {}
        for index, name in enumerate(CONTROL_NAMES, start=1):
            controls[name] = {
                "result": result,
                "evidenceRef": (
                    None
                    if result == "not_verified"
                    else f"evidence:opq_{index:016d}"
                ),
            }
        overall = {
            "pass": "pass",
            "fail": "fail",
            "not_verified": "incomplete",
        }[result]
        return {
            "schemaVersion": "stage1c-vault-verification-v1",
            "contractRef": "adr-0014-stage-1b-custody-operations-v1",
            "g4BindingRef": "stage1c-g4-2026-08-08",
            "verificationId": "vaultver:opq_0000000000000001",
            "vaultRef": "custody:opq_0000000000000001",
            "assessorRef": "actor:opq_0000000000000001",
            "assessedAt": "2026-08-24T00:00:00Z",
            "environment": "stage1_offline",
            "storageClass": "custody_external",
            "overallState": overall,
            "controls": controls,
            "claims": {
                "artifactOnboardingAuthorized": False,
                "artifactPermissionGranted": False,
                "artifactBytesIncluded": False,
                "realArtifactDigestIncluded": False,
                "stage2Authorized": False,
            },
        }

    def assert_invalid(self, record: dict) -> str:
        with self.assertRaises(VaultVerificationError) as caught:
            validate_record(record, schema=self.schema)
        return str(caught.exception)

    def test_zero_state_example_is_incomplete_and_valid(self) -> None:
        record = json.loads(DEFAULT_RECORD_PATH.read_text(encoding="utf-8"))
        validate_record(record, schema=self.schema)
        self.assertEqual(record["overallState"], "incomplete")
        self.assertFalse(record["claims"]["artifactOnboardingAuthorized"])

    def test_complete_synthetic_metadata_record_can_pass(self) -> None:
        record = self.make_record("pass")
        validate_record(record, schema=self.schema)

    def test_pass_with_not_verified_control_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["controls"]["supported_host"] = {
            "result": "not_verified",
            "evidenceRef": None,
        }
        self.assert_invalid(record)

    def test_pass_with_failed_control_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["controls"]["supported_host"]["result"] = "fail"
        self.assert_invalid(record)

    def test_fail_without_failed_control_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["overallState"] = "fail"
        self.assert_invalid(record)

    def test_incomplete_with_failed_control_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["overallState"] = "incomplete"
        record["controls"]["supported_host"]["result"] = "fail"
        self.assert_invalid(record)

    def test_pass_control_without_evidence_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["controls"]["supported_host"]["evidenceRef"] = None
        self.assert_invalid(record)

    def test_fail_control_without_evidence_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["overallState"] = "fail"
        record["controls"]["supported_host"] = {
            "result": "fail",
            "evidenceRef": None,
        }
        self.assert_invalid(record)

    def test_not_verified_control_with_evidence_is_rejected(self) -> None:
        record = self.make_record("not_verified")
        record["controls"]["supported_host"]["evidenceRef"] = (
            "evidence:opq_0000000000000001"
        )
        self.assert_invalid(record)

    def test_local_path_vault_ref_is_rejected_without_echoing_value(self) -> None:
        record = self.make_record("pass")
        sensitive = "C:\\Users\\Example\\Stage1Vault"
        record["vaultRef"] = sensitive
        message = self.assert_invalid(record)
        self.assertNotIn(sensitive, message)

    def test_provider_url_evidence_ref_is_rejected_without_echoing_value(self) -> None:
        record = self.make_record("pass")
        sensitive = "https://storage.example.invalid/private/container"
        record["controls"]["supported_host"]["evidenceRef"] = sensitive
        message = self.assert_invalid(record)
        self.assertNotIn(sensitive, message)

    def test_human_readable_assessor_identity_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["assessorRef"] = "Teacher Example <teacher@example.invalid>"
        self.assert_invalid(record)

    def test_authorization_claims_cannot_be_enabled(self) -> None:
        for claim in (
            "artifactOnboardingAuthorized",
            "artifactPermissionGranted",
            "artifactBytesIncluded",
            "realArtifactDigestIncluded",
            "stage2Authorized",
        ):
            with self.subTest(claim=claim):
                record = self.make_record("pass")
                record["claims"][claim] = True
                self.assert_invalid(record)

    def test_unknown_top_level_field_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["providerName"] = "example"
        self.assert_invalid(record)

    def test_unknown_control_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["controls"]["unapproved_control"] = {
            "result": "pass",
            "evidenceRef": "evidence:opq_0000000000000001",
        }
        self.assert_invalid(record)

    def test_input_record_is_not_mutated(self) -> None:
        record = self.make_record("pass")
        before = copy.deepcopy(record)
        validate_record(record, schema=self.schema)
        self.assertEqual(record, before)


if __name__ == "__main__":
    unittest.main()
