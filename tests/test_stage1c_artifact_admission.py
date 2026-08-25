from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from dataset_test_item_helpers import item, opaque, permission  # noqa: E402
from st_score_restore.dataset_manifest import canonical_sha256, load_json_object  # noqa: E402
from tools.evaluate_stage1c_artifact_admission import (  # noqa: E402
    ArtifactAdmissionError,
    evaluate_admission,
    validate_repository_contract,
    validate_request,
)


class Stage1CArtifactAdmissionTests(unittest.TestCase):
    def catalog(self, candidate: dict) -> dict:
        return {
            "schemaVersion": "1.3.0",
            "entryDecisionId": "adr-0013-stage-1-entry-v1",
            "catalogId": "dataset.catalog.c11-admission-test.v1",
            "descriptionCode": "c11-admission-test",
            "items": [candidate],
        }

    def pass_profile(self, filename: str) -> dict:
        record = load_json_object(ROOT / "examples" / filename)
        record = copy.deepcopy(record)
        record["overallState"] = "pass"
        for index, control in enumerate(record["controls"].values(), start=100):
            control["result"] = "pass"
            control["evidenceRef"] = f"evidence:{opaque(index)}"
        return record

    def request(
        self,
        candidate: dict,
        profile: dict,
        *,
        purpose: str = "quality_evaluation",
        evaluated_at: str = "2026-08-25T12:00:00Z",
    ) -> dict:
        profile_name = candidate["retention"]["storageClass"]
        return {
            "schemaVersion": "stage1c-artifact-admission-request-v1",
            "architectureRef": "adr-0016-stage-1c-risk-tiered-custody-v1",
            "requestId": f"admissionreq:{opaque(90)}",
            "evaluatedAt": evaluated_at,
            "datasetItemId": candidate["datasetItemId"],
            "expectedItemSha256": canonical_sha256(candidate),
            "requestedPurpose": purpose,
            "acquisitionEvidenceRef": candidate["provenance"]["sourceReference"],
            "expectedEligibilityClass": candidate["eligibilityClass"],
            "expectedStorageProfile": profile_name,
            "profileVerificationRef": profile["verificationId"],
            "profileVerificationSha256": canonical_sha256(profile),
            "storageBindingEvidenceRef": f"evidence:{opaque(91)}",
            "claims": {
                "artifactBytesIncluded": False,
                "providerDetailsIncluded": False,
                "modelTrainingAuthorized": False,
                "qualityCalibrationAuthorized": False,
                "safetyCalibrationAuthorized": False,
                "publicationAuthorized": False,
                "demonstrationAuthorized": False,
                "syntheticDerivationAuthorized": False,
                "stage2Authorized": False,
            },
        }

    def candidate(
        self,
        *,
        source_kind: str = "public_domain",
        split: str = "development",
        purpose: str = "quality_evaluation",
    ) -> dict:
        return item(
            item_id=f"dataset.item.c11-{source_kind}.v1",
            family_id=f"source.family.c11-{source_kind}.v1",
            split=split,
            source_kind=source_kind,
            artifact_state="external_available",
            granted_purpose=purpose,
        )

    def assert_blocked(self, result: dict, reason: str) -> None:
        self.assertEqual(result["decision"], "blocked")
        self.assertIn(reason, result["reasonCodes"])

    def test_repository_contract_and_zero_state_are_fail_closed(self) -> None:
        schema = validate_repository_contract()
        request = load_json_object(
            ROOT / "examples" / "stage1c-artifact-admission.zero-state.v1.json"
        )
        catalog = load_json_object(
            ROOT / "examples" / "dataset-catalog.metadata-only.v1.json"
        )
        result = evaluate_admission(request, catalog=catalog, schema=schema)
        self.assertEqual(result["decision"], "blocked")
        self.assertIn("artifact_not_external_available", result["reasonCodes"])
        self.assertIn("missing_expected_item_sha256", result["reasonCodes"])
        self.assertIn("missing_requested_purpose", result["reasonCodes"])
        self.assertIn("missing_profile_verification_sha256", result["reasonCodes"])
        self.assertIn("missing_profile_verification_record", result["reasonCodes"])

    def test_all_three_storage_profiles_can_be_eligible(self) -> None:
        cases = (
            (
                self.candidate(source_kind="public_domain"),
                self.pass_profile("stage1c-managed-standard-verification.zero-state.v1.json"),
            ),
            (
                self.candidate(source_kind="licensed"),
                self.pass_profile("stage1c-managed-restricted-verification.zero-state.v1.json"),
            ),
            (
                self.candidate(source_kind="user_provided"),
                self.pass_profile("stage1c-vault-verification.zero-state.v1.json"),
            ),
        )
        for candidate, profile in cases:
            with self.subTest(profile=candidate["retention"]["storageClass"]):
                request = self.request(candidate, profile)
                result = evaluate_admission(
                    request,
                    catalog=self.catalog(candidate),
                    profile_record=profile,
                )
                self.assertEqual(result, {"decision": "eligible", "reasonCodes": []})

    def test_incomplete_profile_verification_blocks_admission(self) -> None:
        candidate = self.candidate()
        profile = load_json_object(
            ROOT / "examples" / "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        request = self.request(candidate, profile)
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assert_blocked(result, "profile_verification_not_pass")

    def test_invalid_profile_record_blocks_without_leaking_values(self) -> None:
        candidate = self.candidate()
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        profile["unexpectedProviderUrl"] = "https://example.invalid/private"
        request = self.request(candidate, profile)
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assert_blocked(result, "profile_verification_record_invalid")

    def test_profile_reference_mismatch_blocks_admission(self) -> None:
        candidate = self.candidate()
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        request = self.request(candidate, profile)
        request["profileVerificationRef"] = "stdver:opq_ffffffffffffffff"
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assert_blocked(result, "profile_verification_ref_mismatch")

    def test_item_digest_mismatch_blocks_admission(self) -> None:
        candidate = self.candidate()
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        request = self.request(candidate, profile)
        request["expectedItemSha256"] = "f" * 64
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assert_blocked(result, "item_sha256_mismatch")

    def test_profile_digest_mismatch_blocks_admission(self) -> None:
        candidate = self.candidate()
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        request = self.request(candidate, profile)
        request["profileVerificationSha256"] = "f" * 64
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assert_blocked(result, "profile_verification_sha256_mismatch")

    def test_future_profile_verification_cannot_authorize_past_admission(self) -> None:
        candidate = self.candidate()
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        profile["assessedAt"] = "2026-08-26T00:00:00Z"
        request = self.request(candidate, profile, evaluated_at="2026-08-25T12:00:00Z")
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assert_blocked(result, "profile_verification_after_evaluation_time")

    def test_acquisition_evidence_must_bind_catalog_source_reference(self) -> None:
        candidate = self.candidate()
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        request = self.request(candidate, profile)
        request["acquisitionEvidenceRef"] = f"evidence:{opaque(999)}"
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assert_blocked(result, "acquisition_evidence_mismatch")

    def test_storage_binding_evidence_is_required(self) -> None:
        candidate = self.candidate()
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        request = self.request(candidate, profile)
        request["storageBindingEvidenceRef"] = None
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assert_blocked(result, "missing_storage_binding_evidence")

    def test_only_current_stage1c_purpose_may_be_active(self) -> None:
        candidate = self.candidate()
        candidate["permissions"]["demonstration"] = permission("granted")
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        request = self.request(candidate, profile)
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assert_blocked(result, "active_purpose_set_not_exact")

    def test_requested_purpose_must_be_current_at_evaluation_time(self) -> None:
        candidate = self.candidate()
        candidate["permissions"]["quality_evaluation"] = permission(
            "granted",
            authorized_on="2026-08-26",
        )
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        request = self.request(candidate, profile)
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assert_blocked(result, "requested_purpose_not_current")

    def test_reviews_cannot_postdate_admission_evaluation(self) -> None:
        candidate = self.candidate()
        candidate["provenance"]["rightsReview"]["verifiedOn"] = "2026-08-26"
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        request = self.request(candidate, profile)
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assert_blocked(result, "review_completed_after_evaluation_time")

    def test_retention_cannot_be_expired_at_admission(self) -> None:
        candidate = self.candidate()
        candidate["retention"]["policy"] = "external_until_date"
        candidate["retention"]["expiresOn"] = "2026-08-25"
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        request = self.request(candidate, profile)
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assert_blocked(result, "retention_expired")

    def test_request_purpose_must_match_realized_split(self) -> None:
        candidate = self.candidate()
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        request = self.request(candidate, profile, purpose="held_out_evaluation")
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assert_blocked(result, "purpose_split_mismatch")
        self.assert_blocked(result, "active_purpose_set_not_exact")

    def test_unknown_dataset_item_is_blocked(self) -> None:
        candidate = self.candidate()
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        request = self.request(candidate, profile)
        request["datasetItemId"] = "dataset.item.unknown.v1"
        result = evaluate_admission(
            request,
            catalog=self.catalog(candidate),
            profile_record=profile,
        )
        self.assertEqual(
            result,
            {"decision": "blocked", "reasonCodes": ["unknown_dataset_item"]},
        )

    def test_authorization_expansion_claim_is_rejected_by_schema(self) -> None:
        request = load_json_object(
            ROOT / "examples" / "stage1c-artifact-admission.zero-state.v1.json"
        )
        request = copy.deepcopy(request)
        request["claims"]["stage2Authorized"] = True
        with self.assertRaises(ArtifactAdmissionError):
            validate_request(request)

    def test_evaluation_is_deterministic_and_non_mutating(self) -> None:
        candidate = self.candidate()
        profile = self.pass_profile(
            "stage1c-managed-standard-verification.zero-state.v1.json"
        )
        request = self.request(candidate, profile)
        catalog = self.catalog(candidate)
        request_before = copy.deepcopy(request)
        catalog_before = copy.deepcopy(catalog)
        profile_before = copy.deepcopy(profile)
        first = evaluate_admission(request, catalog=catalog, profile_record=profile)
        second = evaluate_admission(request, catalog=catalog, profile_record=profile)
        self.assertEqual(first, second)
        self.assertEqual(request, request_before)
        self.assertEqual(catalog, catalog_before)
        self.assertEqual(profile, profile_before)


if __name__ == "__main__":
    unittest.main()
