from __future__ import annotations

import copy
import unittest

from st_score_restore.dataset_manifest import (
    DatasetManifestError,
    canonical_sha256,
    validate_dataset_catalog,
    validate_dataset_snapshot,
)


PURPOSES = (
    "fixture_validation",
    "quality_evaluation",
    "quality_calibration",
    "pdf_pipeline_evaluation",
    "safety_calibration",
    "held_out_evaluation",
    "model_training",
    "publication",
    "demonstration",
)


def permission(status: str = "not_requested") -> dict:
    value = {
        "status": status,
        "authorizationReference": None,
        "authorizedBy": None,
        "authorizedOn": None,
        "expiresOn": None,
        "restrictions": [],
        "revokedOn": None,
        "revocationReference": None,
    }
    if status == "granted":
        value.update(
            {
                "authorizationReference": "auth:stage1a-purpose-001",
                "authorizedBy": "dataset-reviewer",
                "authorizedOn": "2026-08-06",
            }
        )
    return value


def item(
    item_id: str = "dataset.item.clean-staff.v1",
    *,
    family_id: str = "source.family.clean-staff.v1",
    split: str = "unassigned",
    source_kind: str = "public_domain",
    artifact_state: str = "metadata_only",
    granted_purpose: str | None = None,
) -> dict:
    permissions = {name: permission() for name in PURPOSES}
    if granted_purpose is not None:
        permissions[granted_purpose] = permission("granted")

    artifact = {
        "state": artifact_state,
        "sha256": None,
        "byteSize": None,
        "storageLocator": None,
    }
    review = {
        "status": "planned",
        "reviewedBy": None,
        "reviewedOn": None,
        "notes": "Metadata contract only.",
    }
    retention = {
        "policy": "metadata_only",
        "expiresOn": None,
        "storageClass": "not_assigned",
        "deletionRequired": False,
    }
    if artifact_state == "external_available":
        artifact.update(
            {
                "sha256": "a" * 64,
                "byteSize": 1234,
                "storageLocator": "custody:object-001",
            }
        )
        review.update(
            {
                "status": "approved",
                "reviewedBy": "dataset-reviewer",
                "reviewedOn": "2026-08-06",
            }
        )
        retention.update(
            {
                "policy": "delete_after_validation",
                "storageClass": "custody_external",
                "deletionRequired": True,
            }
        )

    return {
        "datasetItemId": item_id,
        "sourceFamilyId": family_id,
        "parentItemId": None,
        "artifact": artifact,
        "provenance": {
            "sourceKind": source_kind,
            "sourceReference": "rights:source-001",
            "rightsHolder": "Public domain",
            "licenseId": "Public-Domain-1.0",
            "usageBasis": "Stage 1A metadata contract test.",
        },
        "privacy": {
            "classification": "none",
            "reviewStatus": "not_required",
            "deidentificationMethod": None,
            "deidentifiedArtifactSha256": None,
        },
        "input": {
            "kind": "digital_pdf",
            "mediaType": "application/pdf",
            "notationKinds": ["staff"],
            "pageCount": 1,
            "degradations": ["none"],
        },
        "permissions": permissions,
        "split": split,
        "retention": retention,
        "syntheticGeneration": None,
        "review": review,
        "assertions": {
            "teacherApprovalImpliedDatasetPermission": False,
            "teacherApprovalImpliedTrainingPermission": False,
            "originalBytesInGit": False,
        },
    }


def catalog(items: list[dict]) -> dict:
    return {
        "schemaVersion": "1.0.0",
        "catalogId": "dataset.catalog.stage1a.v1",
        "description": "Stage 1A metadata contract test.",
        "items": items,
    }


def snapshot_for(source_catalog: dict, source: dict) -> dict:
    return {
        "schemaVersion": "1.0.0",
        "snapshotId": "dataset.snapshot.held-out.v1",
        "datasetId": source_catalog["catalogId"],
        "version": "1.0.0",
        "createdAt": "2026-08-06T00:00:00Z",
        "catalogSha256": canonical_sha256(source_catalog),
        "assignments": [
            {
                "datasetItemId": source["datasetItemId"],
                "sourceFamilyId": source["sourceFamilyId"],
                "split": source["split"],
                "itemSha256": canonical_sha256(source),
            }
        ],
        "heldOutFrozen": source["split"] == "held_out",
        "trainingUseActivated": False,
        "revokedItemIds": [],
        "coverage": {
            "realItemCount": 1,
            "syntheticItemCount": 0,
            "gapNotes": [],
        },
        "review": {
            "status": "approved",
            "reviewedBy": "dataset-reviewer",
            "reviewedOn": "2026-08-06",
            "notes": "Contract test.",
        },
    }


class DatasetManifestTests(unittest.TestCase):
    def test_metadata_only_unassigned_contract_is_valid(self) -> None:
        result = validate_dataset_catalog(catalog([item()]))
        self.assertEqual(result["items"][0]["split"], "unassigned")
        self.assertTrue(
            all(
                value["status"] == "not_requested"
                for value in result["items"][0]["permissions"].values()
            )
        )

    def test_unassigned_item_cannot_activate_permission(self) -> None:
        value = item(
            artifact_state="external_available",
            granted_purpose="quality_evaluation",
        )
        with self.assertRaisesRegex(
            DatasetManifestError,
            "unassigned item cannot activate",
        ):
            validate_dataset_catalog(catalog([value]))

    def test_granted_permission_requires_authorization_evidence(self) -> None:
        value = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        value["permissions"]["quality_evaluation"][
            "authorizationReference"
        ] = None
        with self.assertRaisesRegex(
            DatasetManifestError,
            "requires authorization evidence",
        ):
            validate_dataset_catalog(catalog([value]))

    def test_held_out_cannot_be_used_for_calibration_or_training(self) -> None:
        value = item(
            artifact_state="external_available",
            split="held_out",
            granted_purpose="held_out_evaluation",
        )
        value["permissions"]["safety_calibration"] = permission("granted")
        with self.assertRaisesRegex(
            DatasetManifestError,
            "held_out item may grant only",
        ):
            validate_dataset_catalog(catalog([value]))

    def test_source_family_split_leakage_is_rejected(self) -> None:
        first = item(
            "dataset.item.development.v1",
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        second = item(
            "dataset.item.held-out.v1",
            artifact_state="external_available",
            split="held_out",
            granted_purpose="held_out_evaluation",
        )
        second["artifact"]["sha256"] = "b" * 64
        second["artifact"]["storageLocator"] = "custody:object-002"
        with self.assertRaisesRegex(
            DatasetManifestError,
            "source-family split leakage",
        ):
            validate_dataset_catalog(catalog([first, second]))

    def test_synthetic_item_must_share_non_synthetic_parent_family(self) -> None:
        parent = item()
        child = item(
            "dataset.item.synthetic-shadow.v1",
            source_kind="synthetic",
        )
        child["parentItemId"] = parent["datasetItemId"]
        child["syntheticGeneration"] = {
            "generator": "controlled-shadow-generator",
            "generatorVersion": "1.0.0",
            "generatorCommit": "c" * 64,
            "seed": 7,
            "parameters": {"strength": 0.25},
            "cleanSourceApproved": True,
        }
        validate_dataset_catalog(catalog([parent, child]))
        child["sourceFamilyId"] = "source.family.other.v1"
        with self.assertRaisesRegex(
            DatasetManifestError,
            "share sourceFamilyId",
        ):
            validate_dataset_catalog(catalog([parent, child]))

    def test_teacher_approval_assertions_cannot_enable_dataset_use(self) -> None:
        value = item()
        value["assertions"][
            "teacherApprovalImpliedTrainingPermission"
        ] = True
        with self.assertRaisesRegex(
            DatasetManifestError,
            "assertions must remain false",
        ):
            validate_dataset_catalog(catalog([value]))

    def test_valid_frozen_snapshot_is_digest_bound(self) -> None:
        source = item(
            artifact_state="external_available",
            split="held_out",
            granted_purpose="held_out_evaluation",
        )
        source_catalog = catalog([source])
        value = snapshot_for(source_catalog, source)
        validate_dataset_snapshot(value, catalog=source_catalog)
        value["catalogSha256"] = "0" * 64
        with self.assertRaisesRegex(
            DatasetManifestError,
            "does not match catalog",
        ):
            validate_dataset_snapshot(value, catalog=source_catalog)

    def test_revoked_item_cannot_appear_in_snapshot(self) -> None:
        active = item(
            "dataset.item.active.v1",
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        revoked = copy.deepcopy(active)
        revoked["datasetItemId"] = "dataset.item.revoked.v1"
        revoked["artifact"] = {
            "state": "revoked",
            "sha256": "b" * 64,
            "byteSize": 1200,
            "storageLocator": None,
        }
        revoked["permissions"]["quality_evaluation"] = permission()
        revoked["retention"] = {
            "policy": "delete_after_validation",
            "expiresOn": None,
            "storageClass": "custody_external",
            "deletionRequired": True,
        }
        revoked["review"] = {
            "status": "revoked",
            "reviewedBy": "dataset-reviewer",
            "reviewedOn": "2026-08-06",
            "notes": "Deletion receipt recorded outside Git.",
        }
        source_catalog = catalog([active, revoked])
        value = snapshot_for(source_catalog, active)
        value["assignments"].append(
            {
                "datasetItemId": revoked["datasetItemId"],
                "sourceFamilyId": revoked["sourceFamilyId"],
                "split": revoked["split"],
                "itemSha256": canonical_sha256(revoked),
            }
        )
        value["revokedItemIds"] = [revoked["datasetItemId"]]
        value["coverage"]["realItemCount"] = 2
        with self.assertRaisesRegex(
            DatasetManifestError,
            "requires approved external artifact",
        ):
            validate_dataset_snapshot(value, catalog=source_catalog)

    def test_stage1a_snapshot_cannot_activate_training(self) -> None:
        source = item(
            artifact_state="external_available",
            split="held_out",
            granted_purpose="held_out_evaluation",
        )
        source_catalog = catalog([source])
        value = snapshot_for(source_catalog, source)
        value["trainingUseActivated"] = True
        with self.assertRaisesRegex(
            DatasetManifestError,
            "cannot activate model training",
        ):
            validate_dataset_snapshot(value, catalog=source_catalog)


if __name__ == "__main__":
    unittest.main()
