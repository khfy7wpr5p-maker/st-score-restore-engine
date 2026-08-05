from __future__ import annotations

import unittest

from st_score_restore.dataset_manifest import (
    DatasetManifestError,
    canonical_sha256,
)
from st_score_restore.dataset_snapshot_policy import (
    validate_authorized_dataset_snapshot,
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
                "authorizationReference": "auth:purpose-001",
                "authorizedBy": "dataset-reviewer",
                "authorizedOn": "2026-08-06",
            }
        )
    return value


def approved_item(*, split: str, granted_purpose: str | None) -> dict:
    permissions = {name: permission() for name in PURPOSES}
    if granted_purpose is not None:
        permissions[granted_purpose] = permission("granted")
    return {
        "datasetItemId": "dataset.item.snapshot-policy.v1",
        "sourceFamilyId": "source.family.snapshot-policy.v1",
        "parentItemId": None,
        "artifact": {
            "state": "external_available",
            "sha256": "a" * 64,
            "byteSize": 1000,
            "storageLocator": "custody:object-001",
        },
        "provenance": {
            "sourceKind": "public_domain",
            "sourceReference": "rights:source-001",
            "rightsHolder": "Public domain",
            "licenseId": "Public-Domain-1.0",
            "usageBasis": "Stage 1A snapshot policy test.",
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
        "retention": {
            "policy": "delete_after_validation",
            "expiresOn": None,
            "storageClass": "custody_external",
            "deletionRequired": True,
        },
        "syntheticGeneration": None,
        "review": {
            "status": "approved",
            "reviewedBy": "dataset-reviewer",
            "reviewedOn": "2026-08-06",
            "notes": "Contract test.",
        },
        "assertions": {
            "teacherApprovalImpliedDatasetPermission": False,
            "teacherApprovalImpliedTrainingPermission": False,
            "originalBytesInGit": False,
        },
    }


def catalog_with(item: dict) -> dict:
    return {
        "schemaVersion": "1.0.0",
        "catalogId": "dataset.catalog.snapshot-policy.v1",
        "description": "Snapshot authorization test.",
        "items": [item],
    }


def snapshot_for(catalog: dict, item: dict) -> dict:
    return {
        "schemaVersion": "1.0.0",
        "snapshotId": "dataset.snapshot.snapshot-policy.v1",
        "datasetId": catalog["catalogId"],
        "version": "1.0.0",
        "createdAt": "2026-08-06T00:00:00Z",
        "catalogSha256": canonical_sha256(catalog),
        "assignments": [
            {
                "datasetItemId": item["datasetItemId"],
                "sourceFamilyId": item["sourceFamilyId"],
                "split": item["split"],
                "itemSha256": canonical_sha256(item),
            }
        ],
        "heldOutFrozen": item["split"] == "held_out",
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


class DatasetSnapshotPolicyTests(unittest.TestCase):
    def test_development_snapshot_requires_development_purpose(self) -> None:
        item = approved_item(split="development", granted_purpose=None)
        catalog = catalog_with(item)
        with self.assertRaisesRegex(
            DatasetManifestError,
            "not authorized for its split",
        ):
            validate_authorized_dataset_snapshot(
                snapshot_for(catalog, item), catalog=catalog
            )

    def test_publication_permission_does_not_authorize_calibration(self) -> None:
        item = approved_item(
            split="calibration", granted_purpose="publication"
        )
        catalog = catalog_with(item)
        with self.assertRaisesRegex(
            DatasetManifestError,
            "not authorized for its split",
        ):
            validate_authorized_dataset_snapshot(
                snapshot_for(catalog, item), catalog=catalog
            )

    def test_calibration_snapshot_accepts_safety_calibration_grant(self) -> None:
        item = approved_item(
            split="calibration", granted_purpose="safety_calibration"
        )
        catalog = catalog_with(item)
        result = validate_authorized_dataset_snapshot(
            snapshot_for(catalog, item), catalog=catalog
        )
        self.assertEqual(result["assignments"][0]["split"], "calibration")


if __name__ == "__main__":
    unittest.main()
