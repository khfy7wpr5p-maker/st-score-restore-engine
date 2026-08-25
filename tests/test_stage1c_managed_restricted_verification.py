from __future__ import annotations

import copy
import json
import unittest

from tools.validate_stage1c_managed_restricted_verification import (
    CLAIM_NAMES,
    CONTROL_NAMES,
    DEFAULT_RECORD_PATH,
    ManagedRestrictedVerificationError,
    load_schema,
    validate_record,
    validate_repository_contract,
)


class Stage1CManagedRestrictedVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_schema()

    def make_record(self, result: str = "pass") -> dict:
        controls = {}
        for index, name in enumerate(CONTROL_NAMES, start=1):
            controls[name] = {
                "result": result,
                "evidenceRef": (
                    None if result == "not_verified" else f"evidence:opq_{index:016d}"
                ),
            }
        overall = {"pass": "pass", "fail": "fail", "not_verified": "incomplete"}[result]
        return {
            "schemaVersion": "stage1c-managed-restricted-verification-v1",
            "contractRef": "adr-0016-stage-1c-risk-tiered-custody-v1",
            "verificationId": "restrictver:opq_0000000000000001",
            "configurationRef": "storagecfg:opq_0000000000000001",
            "restrictionSetRef": "restrictset:opq_0000000000000001",
            "assessorRef": "actor:opq_0000000000000001",
            "assessedAt": "2026-08-25T00:00:00Z",
            "profile": "managed_restricted",
            "eligibilityClass": "restricted_corpus",
            "overallState": overall,
            "controls": controls,
            "claims": {name: False for name in CLAIM_NAMES},
        }

    def assert_invalid(self, record: dict) -> str:
        with self.assertRaises(ManagedRestrictedVerificationError) as caught:
            validate_record(record, schema=self.schema)
        return str(caught.exception)

    def test_repository_contract_is_valid(self) -> None:
        validate_repository_contract()

    def test_zero_state_is_incomplete_and_valid(self) -> None:
        record = json.loads(DEFAULT_RECORD_PATH.read_text(encoding="utf-8"))
        validate_record(record, schema=self.schema)
        self.assertEqual(record["overallState"], "incomplete")
        self.assertFalse(record["claims"]["artifactOnboardingAuthorized"])

    def test_complete_synthetic_metadata_record_can_pass(self) -> None:
        validate_record(self.make_record("pass"), schema=self.schema)

    def test_pass_with_not_verified_control_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["controls"]["artifact_terms_compatibility"] = {
            "result": "not_verified",
            "evidenceRef": None,
        }
        self.assert_invalid(record)

    def test_pass_with_failed_control_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["controls"]["public_links_disabled"]["result"] = "fail"
        self.assert_invalid(record)

    def test_fail_without_failed_control_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["overallState"] = "fail"
        self.assert_invalid(record)

    def test_incomplete_with_failed_control_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["overallState"] = "incomplete"
        record["controls"]["deny_by_default_membership"]["result"] = "fail"
        self.assert_invalid(record)

    def test_pass_control_without_evidence_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["controls"]["storage_environment_allowlist_match"]["evidenceRef"] = None
        self.assert_invalid(record)

    def test_fail_control_without_evidence_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["overallState"] = "fail"
        record["controls"]["access_change_history"] = {
            "result": "fail",
            "evidenceRef": None,
        }
        self.assert_invalid(record)

    def test_not_verified_control_with_evidence_is_rejected(self) -> None:
        record = self.make_record("not_verified")
        record["controls"]["restriction_compatible_deletion_backup"]["evidenceRef"] = (
            "evidence:opq_0000000000000001"
        )
        self.assert_invalid(record)

    def test_profile_binding_cannot_drift(self) -> None:
        record = self.make_record("pass")
        record["profile"] = "managed_standard"
        self.assert_invalid(record)

    def test_eligibility_binding_cannot_drift(self) -> None:
        record = self.make_record("pass")
        record["eligibilityClass"] = "open_corpus"
        self.assert_invalid(record)

    def test_contract_binding_cannot_drift(self) -> None:
        record = self.make_record("pass")
        record["contractRef"] = "adr-0014-stage-1b-custody-operations-v1"
        self.assert_invalid(record)

    def test_local_path_configuration_ref_is_rejected_without_echo(self) -> None:
        record = self.make_record("pass")
        sensitive = "C:\\Users\\Example\\Restricted"
        record["configurationRef"] = sensitive
        message = self.assert_invalid(record)
        self.assertNotIn(sensitive, message)

    def test_provider_url_restriction_ref_is_rejected_without_echo(self) -> None:
        record = self.make_record("pass")
        sensitive = "https://storage.example.invalid/restricted"
        record["restrictionSetRef"] = sensitive
        message = self.assert_invalid(record)
        self.assertNotIn(sensitive, message)

    def test_human_readable_assessor_identity_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["assessorRef"] = "Reviewer Example <reviewer@example.invalid>"
        self.assert_invalid(record)

    def test_authorization_and_brand_claims_cannot_be_enabled(self) -> None:
        for claim in CLAIM_NAMES:
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
