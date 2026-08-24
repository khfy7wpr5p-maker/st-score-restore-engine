from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from st_score_restore.dataset_manifest import (
    DatasetManifestError,
    canonical_sha256,
    load_json_object,
    migrate_dataset_catalog_v1_2_to_v1_3,
    validate_dataset_catalog,
    validate_dataset_snapshot,
)
try:
    from .dataset_test_item_helpers import item, opaque, permission
    from .dataset_test_snapshot_helpers import catalog, snapshot_for
except ImportError:
    from dataset_test_item_helpers import item, opaque, permission
    from dataset_test_snapshot_helpers import catalog, snapshot_for


class DatasetManifestTests(unittest.TestCase):
    def test_metadata_only_unassigned_contract_is_valid(self) -> None:
        result = validate_dataset_catalog(catalog([item()]))
        self.assertEqual(result["items"][0]["split"], "unassigned")
        self.assertEqual(result["items"][0]["eligibilityClass"], "blocked")

    def test_entry_decision_is_required(self) -> None:
        value = catalog([item()])
        value["entryDecisionId"] = "adr-unknown"
        with self.assertRaisesRegex(DatasetManifestError, "entryDecisionId"):
            validate_dataset_catalog(value)

    def test_deidentification_digest_must_match_artifact(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            privacy_class="deidentified",
        )
        value["privacy"]["deidentifiedArtifactSha256"] = "b" * 64
        with self.assertRaisesRegex(DatasetManifestError, "de-identification digest"):
            validate_dataset_catalog(catalog([value]))

    def test_metadata_only_item_cannot_claim_deidentified_artifact_digest(self) -> None:
        value = item(privacy_class="deidentified")
        with self.assertRaisesRegex(
            DatasetManifestError, "available or revoked artifact digest"
        ):
            validate_dataset_catalog(catalog([value]))

    def test_opaque_actor_and_subject_ids_are_required(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        value["permissions"]["quality_evaluation"]["authorizedBy"] = (
            "actor.purpose:jane.doe"
        )
        with self.assertRaisesRegex(DatasetManifestError, "opaque identifier"):
            validate_dataset_catalog(catalog([value]))
        value = item()
        value["provenance"]["rightsHolderId"] = "subject:student-ali"
        with self.assertRaisesRegex(DatasetManifestError, "opaque identifier"):
            validate_dataset_catalog(catalog([value]))

    def test_opaque_tokens_are_accepted(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        value["provenance"]["rightsHolderId"] = f"subject:{opaque(999)}"
        validate_dataset_catalog(catalog([value]))

    def test_free_text_identity_channels_are_rejected(self) -> None:
        value = catalog([item()])
        value["descriptionCode"] = "teacher@example.com"
        with self.assertRaisesRegex(DatasetManifestError, "invalid opaque identifier"):
            validate_dataset_catalog(value)
        source = item()
        source["provenance"]["licenseId"] = "C:\\Users\\Jane\\license.pdf"
        with self.assertRaisesRegex(DatasetManifestError, "invalid opaque identifier"):
            validate_dataset_catalog(catalog([source]))

    def test_synthetic_parameters_reject_free_text(self) -> None:
        parent, child = self._synthetic_pair()
        child["syntheticGeneration"]["parameters"] = {"operator": "jane.doe"}
        with self.assertRaisesRegex(DatasetManifestError, "free-text strings"):
            validate_dataset_catalog(catalog([parent, child]))

    def test_synthetic_parameters_reject_non_finite_numbers(self) -> None:
        parent, child = self._synthetic_pair()
        child["syntheticGeneration"]["parameters"] = {"strength": float("nan")}
        with self.assertRaisesRegex(DatasetManifestError, "finite JSON number"):
            validate_dataset_catalog(catalog([parent, child]))

    def test_canonical_digest_rejects_non_finite_numbers(self) -> None:
        with self.assertRaisesRegex(DatasetManifestError, "non-finite"):
            canonical_sha256({"unsafe": float("inf")})

    def test_json_loader_rejects_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"schemaVersion":"1.3.0","schemaVersion":"1.3.0"}', encoding="utf-8")
            with self.assertRaisesRegex(DatasetManifestError, "duplicate JSON object key"):
                load_json_object(path)

    def test_json_loader_rejects_non_standard_nan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nan.json"
            path.write_text('{"unsafe":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(DatasetManifestError, "non-standard non-finite"):
                load_json_object(path)

    def test_json_loader_rejects_float_overflow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "overflow.json"
            path.write_text('{"unsafe":1e999}', encoding="utf-8")
            with self.assertRaisesRegex(DatasetManifestError, "out-of-range non-finite"):
                load_json_object(path)

    def test_machine_restrictions_are_enforced(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        value["permissions"]["quality_evaluation"] = permission(
            "granted",
            restrictions=[{"type": "split_allowlist", "values": ["calibration"]}],
        )
        with self.assertRaisesRegex(DatasetManifestError, "restriction excludes"):
            validate_dataset_catalog(catalog([value]))

    def test_unknown_restriction_is_rejected(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        value["permissions"]["quality_evaluation"] = permission(
            "granted", restrictions=[{"type": "free_text", "value": "allow"}]
        )
        with self.assertRaisesRegex(DatasetManifestError, "unsupported value"):
            validate_dataset_catalog(catalog([value]))

    def test_duplicate_restriction_type_is_rejected(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        value["permissions"]["quality_evaluation"] = permission(
            "granted",
            restrictions=[
                {"type": "split_allowlist", "values": ["development"]},
                {"type": "split_allowlist", "values": ["development"]},
            ],
        )
        with self.assertRaisesRegex(DatasetManifestError, "cannot repeat a type"):
            validate_dataset_catalog(catalog([value]))

    def test_invalid_environment_restriction_is_rejected(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        value["permissions"]["quality_evaluation"] = permission(
            "granted", restrictions=[{"type": "environment_allowlist", "values": ["production"]}],
        )
        with self.assertRaisesRegex(DatasetManifestError, "unsupported value"):
            validate_dataset_catalog(catalog([value]))

    def test_retention_restriction_cannot_exceed_item_retention(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        value["permissions"]["quality_evaluation"] = permission(
            "granted",
            restrictions=[{"type": "retention_not_after", "date": "2026-09-01"}],
        )
        with self.assertRaisesRegex(DatasetManifestError, "retention restriction"):
            validate_dataset_catalog(catalog([value]))

    def test_publication_cannot_ignore_external_export_restriction(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="publication",
        )
        value["permissions"]["publication"] = permission(
            "granted", restrictions=[{"type": "external_export", "allowed": False}]
        )
        with self.assertRaisesRegex(DatasetManifestError, "external-export restriction"):
            validate_dataset_catalog(catalog([value]))

    def test_pending_deletion_metadata_must_be_consistent(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        value["revocation"] = {
            "status": "pending_deletion",
            "effectiveOn": "2026-08-05",
            "reference": f"evidence:{opaque(301)}",
        }
        with self.assertRaisesRegex(DatasetManifestError, "pending deletion"):
            validate_dataset_catalog(catalog([value]))

    def test_revoked_item_requires_deletion_receipt(self) -> None:
        value = item(artifact_state="revoked", split="development")
        value["retention"]["deletionReceiptReference"] = None
        with self.assertRaisesRegex(DatasetManifestError, "completed deletion receipt"):
            validate_dataset_catalog(catalog([value]))

    def test_source_family_split_leakage_is_rejected(self) -> None:
        first = item(
            "dataset.item.dev.v1",
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        second = item(
            "dataset.item.held.v1",
            artifact_state="external_available",
            split="held_out",
            granted_purpose="held_out_evaluation",
            artifact_sha="b" * 64,
        )
        with self.assertRaisesRegex(DatasetManifestError, "source-family split leakage"):
            validate_dataset_catalog(catalog([first, second]))

    def test_all_three_risk_tier_profile_pairs_are_machine_valid(self) -> None:
        open_item = item(
            "dataset.item.open.v1",
            family_id="source.family.open.v1",
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            eligibility_class="open_corpus",
            storage_class="managed_standard",
        )
        restricted_item = item(
            "dataset.item.restricted.v1",
            family_id="source.family.restricted.v1",
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            privacy_class="deidentified",
            artifact_sha="b" * 64,
            eligibility_class="restricted_corpus",
            storage_class="managed_restricted",
        )
        sensitive_item = item(
            "dataset.item.sensitive.v1",
            family_id="source.family.sensitive.v1",
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            privacy_class="personal",
            artifact_sha="c" * 64,
            eligibility_class="sensitive_custody",
            storage_class="high_assurance_vault",
        )
        validate_dataset_catalog(catalog([open_item, restricted_item, sensitive_item]))

    def test_blocked_external_artifact_is_rejected(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            eligibility_class="blocked",
            storage_class="managed_standard",
        )
        with self.assertRaisesRegex(DatasetManifestError, "eligibility/storage profile mismatch"):
            validate_dataset_catalog(catalog([value]))

    def test_illegal_eligibility_profile_pair_is_rejected(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            eligibility_class="open_corpus",
            storage_class="managed_restricted",
        )
        with self.assertRaisesRegex(DatasetManifestError, "eligibility/storage profile mismatch"):
            validate_dataset_catalog(catalog([value]))

    def test_open_corpus_cannot_contain_personal_or_student_data(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            privacy_class="personal",
            eligibility_class="open_corpus",
            storage_class="managed_standard",
        )
        with self.assertRaisesRegex(DatasetManifestError, "open_corpus requires privacy"):
            validate_dataset_catalog(catalog([value]))

    def test_personal_data_requires_sensitive_custody(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            privacy_class="student",
            eligibility_class="restricted_corpus",
            storage_class="managed_restricted",
        )
        with self.assertRaisesRegex(DatasetManifestError, "requires sensitive_custody"):
            validate_dataset_catalog(catalog([value]))

    def _legacy_catalog(self, source: dict) -> dict:
        legacy = copy.deepcopy(catalog([source]))
        legacy["schemaVersion"] = "1.2.0"
        legacy_item = legacy["items"][0]
        legacy_item.pop("eligibilityClass")
        if legacy_item["artifact"]["state"] in {"external_available", "revoked"}:
            legacy_item["retention"]["storageClass"] = "custody_external"
        for permission_value in legacy_item["permissions"].values():
            for restriction in permission_value["restrictions"]:
                if restriction["type"] == "storage_class_allowlist":
                    restriction["values"] = ["custody_external"]
        return legacy

    def test_legacy_external_migration_never_downgrades_custody(self) -> None:
        source = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            eligibility_class="open_corpus",
            storage_class="managed_standard",
        )
        legacy = self._legacy_catalog(source)
        migrated = migrate_dataset_catalog_v1_2_to_v1_3(legacy)
        result = migrated["items"][0]
        self.assertEqual(migrated["schemaVersion"], "1.3.0")
        self.assertEqual(result["eligibilityClass"], "sensitive_custody")
        self.assertEqual(result["retention"]["storageClass"], "high_assurance_vault")
        self.assertNotEqual(result["retention"]["storageClass"], "managed_standard")

    def test_legacy_metadata_only_migration_remains_blocked(self) -> None:
        migrated = migrate_dataset_catalog_v1_2_to_v1_3(
            self._legacy_catalog(item())
        )
        result = migrated["items"][0]
        self.assertEqual(result["eligibilityClass"], "blocked")
        self.assertEqual(result["retention"]["storageClass"], "not_assigned")

    def test_legacy_external_without_custody_external_is_rejected(self) -> None:
        source = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        legacy = self._legacy_catalog(source)
        legacy["items"][0]["retention"]["storageClass"] = "managed_standard"
        with self.assertRaisesRegex(DatasetManifestError, "must use custody_external"):
            migrate_dataset_catalog_v1_2_to_v1_3(legacy)

    def _synthetic_pair(self) -> tuple[dict, dict]:
        parent = item(
            "dataset.item.parent.v1",
            artifact_state="external_available",
            split="development",
            granted_purpose="synthetic_derivation",
        )
        child = item(
            "dataset.item.synthetic.v1",
            family_id=parent["sourceFamilyId"],
            artifact_state="external_available",
            split="development",
            source_kind="synthetic",
            artifact_sha="b" * 64,
        )
        child["parentItemId"] = parent["datasetItemId"]
        child["syntheticGeneration"] = {
            "generator": "shadow-generator",
            "generatorVersion": "1.0.0",
            "generatorCommit": "c" * 64,
            "generatedOn": "2026-08-02",
            "derivationAuthorizationReference": parent["permissions"]["synthetic_derivation"]["authorizationReference"],
            "seed": 7,
            "parameters": {"strength": 0.25},
        }
        return parent, child

    def test_synthetic_parent_requires_real_approval_and_valid_derivation(self) -> None:
        parent, child = self._synthetic_pair()
        validate_dataset_catalog(catalog([parent, child]))
        unapproved = copy.deepcopy(parent)
        unapproved["provenance"]["rightsReview"] = {
            "status": "pending",
            "verifiedBy": None,
            "verifiedOn": None,
            "evidenceReference": None,
        }
        with self.assertRaisesRegex(DatasetManifestError, "external artifact requires approved rights"):
            validate_dataset_catalog(catalog([unapproved, child]))

    def test_synthetic_child_must_share_parent_assigned_split(self) -> None:
        parent, child = self._synthetic_pair()
        child["split"] = "unassigned"
        with self.assertRaisesRegex(DatasetManifestError, "parent's assigned split"):
            validate_dataset_catalog(catalog([parent, child]))
        parent, child = self._synthetic_pair()
        child["split"] = "calibration"
        with self.assertRaisesRegex(DatasetManifestError, "parent's assigned split"):
            validate_dataset_catalog(catalog([parent, child]))
        parent, child = self._synthetic_pair()
        validate_dataset_catalog(catalog([parent, child]))

    def test_teacher_approval_and_stage1_training_assertions_stay_false(self) -> None:
        value = item()
        value["assertions"]["stage1TrainingExecutionAuthorized"] = True
        with self.assertRaisesRegex(DatasetManifestError, "assertions must remain false"):
            validate_dataset_catalog(catalog([value]))

    def test_snapshot_is_digest_bound(self) -> None:
        source = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        source_catalog = catalog([source])
        value = snapshot_for(source_catalog, [source])
        validate_dataset_snapshot(value, catalog=source_catalog)
        value["catalogSha256"] = "0" * 64
        with self.assertRaisesRegex(DatasetManifestError, "does not match catalog"):
            validate_dataset_snapshot(value, catalog=source_catalog)


if __name__ == "__main__":
    unittest.main()
