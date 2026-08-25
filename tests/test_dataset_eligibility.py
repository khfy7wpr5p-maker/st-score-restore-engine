from __future__ import annotations

import copy
import unittest

from st_score_restore.dataset_eligibility import resolve_required_eligibility_class
from st_score_restore.dataset_manifest import DatasetManifestError, validate_dataset_catalog

try:
    from .dataset_test_item_helpers import item, permission
    from .dataset_test_snapshot_helpers import catalog
except ImportError:
    from dataset_test_item_helpers import item, permission
    from dataset_test_snapshot_helpers import catalog


class DatasetEligibilityTests(unittest.TestCase):
    def test_public_domain_none_privacy_resolves_open(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        validate_dataset_catalog(catalog([value]))
        required = resolve_required_eligibility_class(
            artifact_state="external_available",
            source_kind="public_domain",
            usage_basis="public_domain",
            rights_status="approved",
            privacy_class="none",
            privacy_status="not_required",
            review_status="approved",
            permissions={"quality_evaluation": {"status": "granted", "restrictions": []}},
        )
        self.assertEqual(required, "open_corpus")

    def test_licensed_source_requires_restricted_corpus(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            source_kind="licensed",
        )
        validate_dataset_catalog(catalog([value]))
        self.assertEqual(value["eligibilityClass"], "restricted_corpus")
        self.assertEqual(value["retention"]["storageClass"], "managed_restricted")

    def test_user_provided_source_requires_sensitive_custody(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            source_kind="user_provided",
        )
        validate_dataset_catalog(catalog([value]))
        self.assertEqual(value["eligibilityClass"], "sensitive_custody")
        self.assertEqual(value["retention"]["storageClass"], "high_assurance_vault")

    def test_deidentified_artifact_requires_at_least_restricted(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            privacy_class="deidentified",
        )
        validate_dataset_catalog(catalog([value]))
        self.assertEqual(value["eligibilityClass"], "restricted_corpus")

    def test_declared_class_cannot_be_weaker_than_source_evidence(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            source_kind="licensed",
            eligibility_class="open_corpus",
            storage_class="managed_standard",
        )
        with self.assertRaisesRegex(
            DatasetManifestError, "weaker than evidence-derived restricted_corpus"
        ):
            validate_dataset_catalog(catalog([value]))

    def test_user_provided_cannot_be_downgraded_to_restricted(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            source_kind="user_provided",
            eligibility_class="restricted_corpus",
            storage_class="managed_restricted",
        )
        with self.assertRaisesRegex(
            DatasetManifestError, "weaker than evidence-derived sensitive_custody"
        ):
            validate_dataset_catalog(catalog([value]))

    def test_explicit_security_escalation_is_allowed(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            eligibility_class="sensitive_custody",
            storage_class="high_assurance_vault",
        )
        validate_dataset_catalog(catalog([value]))

    def test_storage_restriction_can_raise_minimum_class(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            eligibility_class="restricted_corpus",
            storage_class="managed_restricted",
        )
        value["permissions"]["quality_evaluation"] = permission(
            "granted",
            restrictions=[
                {
                    "type": "storage_class_allowlist",
                    "values": ["managed_restricted"],
                }
            ],
        )
        validate_dataset_catalog(catalog([value]))

    def test_high_assurance_only_restriction_requires_sensitive(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            eligibility_class="sensitive_custody",
            storage_class="high_assurance_vault",
        )
        value["permissions"]["quality_evaluation"] = permission(
            "granted",
            restrictions=[
                {
                    "type": "storage_class_allowlist",
                    "values": ["high_assurance_vault"],
                }
            ],
        )
        validate_dataset_catalog(catalog([value]))

    def test_source_and_usage_basis_mismatch_is_rejected(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        value["provenance"]["usageBasisCode"] = "license_grant"
        with self.assertRaisesRegex(
            DatasetManifestError, "sourceKind and usageBasisCode are inconsistent"
        ):
            validate_dataset_catalog(catalog([value]))

    def test_resolver_is_deterministic_and_non_mutating(self) -> None:
        permissions = {
            "quality_evaluation": {
                "status": "granted",
                "restrictions": [
                    {
                        "type": "storage_class_allowlist",
                        "values": ["managed_restricted", "high_assurance_vault"],
                    }
                ],
            }
        }
        before = copy.deepcopy(permissions)
        first = resolve_required_eligibility_class(
            artifact_state="external_available",
            source_kind="public_domain",
            usage_basis="public_domain",
            rights_status="approved",
            privacy_class="none",
            privacy_status="not_required",
            review_status="approved",
            permissions=permissions,
        )
        second = resolve_required_eligibility_class(
            artifact_state="external_available",
            source_kind="public_domain",
            usage_basis="public_domain",
            rights_status="approved",
            privacy_class="none",
            privacy_status="not_required",
            review_status="approved",
            permissions=permissions,
        )
        self.assertEqual(first, "restricted_corpus")
        self.assertEqual(second, first)
        self.assertEqual(permissions, before)


if __name__ == "__main__":
    unittest.main()
