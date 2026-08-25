from __future__ import annotations

import copy
import json
import unittest

from tools.validate_stage1c_managed_standard_verification import (
    CLAIM_NAMES,
    CONTROL_NAMES,
    DEFAULT_RECORD_PATH,
    ManagedStandardVerificationError,
    load_schema,
    validate_record,
)


class Stage1CManagedStandardVerificationTests(unittest.TestCase):
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
            "schemaVersion": "stage1c-managed-standard-verification-v1",
            "architectureRef": "adr-0016-stage-1c-risk-tiered-custody-v1",
            "verificationId": "stdver:opq_0000000000000001",
            "configurationRef": "storagecfg:opq_0000000000000001",
            "assessorRef": "actor:opq_0000000000000001",
            "assessedAt": "2026-08-25T00:00:00Z",
            "eligibilityClass": "open_corpus",
            "storageProfile": "managed_standard",
            "overallState": overall,
            "controls": controls,
            "claims": {name: False for name in CLAIM_NAMES},
        }

    def assert_invalid(self, record: dict) -> str:
        with self.assertRaises(ManagedStandardVerificationError) as caught:
            validate_record(record, schema=self.schema)
        return str(caught.exception)

    def test_zero_state_example_is_incomplete_and_valid(self) -> None:
        record = json.loads(DEFAULT_RECORD_PATH.read_text(encoding="utf-8"))
        validate_record(record, schema=self.schema)
        self.assertEqual(record["overallState"], "incomplete")
        self.assertFalse(record["claims"]["artifactOnboardingAuthorized"])
        self.assertFalse(record["claims"]["providerApprovedByBrand"])

    def test_complete_synthetic_metadata_record_can_pass(self) -> None:
        validate_record(self.make_record("pass"), schema=self.schema)

    def test_pass_with_not_verified_control_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["controls"]["git_exclusion"] = {
            "result": "not_verified",
            "evidenceRef": None,
        }
        self.assert_invalid(record)

    def test_pass_with_failed_control_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["controls"]["git_exclusion"]["result"] = "fail"
        self.assert_invalid(record)

    def test_fail_without_failed_control_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["overallState"] = "fail"
        self.assert_invalid(record)

    def test_incomplete_with_failed_control_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["overallState"] = "incomplete"
        record["controls"]["git_exclusion"]["result"] = "fail"
        self.assert_invalid(record)

    def test_pass_control_without_evidence_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["controls"]["object_binding_capability"]["evidenceRef"] = None
        self.assert_invalid(record)

    def test_fail_control_without_evidence_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["overallState"] = "fail"
        record["controls"]["project_managed_access"] = {
            "result": "fail",
            "evidenceRef": None,
        }
        self.assert_invalid(record)

    def test_not_verified_control_with_evidence_is_rejected(self) -> None:
        record = self.make_record("not_verified")
        record["controls"]["git_exclusion"]["evidenceRef"] = (
            "evidence:opq_0000000000000001"
        )
        self.assert_invalid(record)

    def test_local_path_configuration_ref_is_rejected_without_echo(self) -> None:
        record = self.make_record("pass")
        sensitive = "C:\\Users\\Example\\ScoreCorpus"
        record["configurationRef"] = sensitive
        message = self.assert_invalid(record)
        self.assertNotIn(sensitive, message)

    def test_provider_url_evidence_ref_is_rejected_without_echo(self) -> None:
        record = self.make_record("pass")
        sensitive = "https://storage.example.invalid/private/folder"
        record["controls"]["git_exclusion"]["evidenceRef"] = sensitive
        message = self.assert_invalid(record)
        self.assertNotIn(sensitive, message)

    def test_human_readable_assessor_identity_is_rejected(self) -> None:
        record = self.make_record("pass")
        record["assessorRef"] = "Teacher Example <teacher@example.invalid>"
        self.assert_invalid(record)

    def test_profile_and_eligibility_bindings_cannot_drift(self) -> None:
        record = self.make_record("pass")
        record["storageProfile"] = "managed_restricted"
        self.assert_invalid(record)
        record = self.make_record("pass")
        record["eligibilityClass"] = "restricted_corpus"
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
