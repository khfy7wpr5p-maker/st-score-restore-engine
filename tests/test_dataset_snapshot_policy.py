from __future__ import annotations

import unittest

from st_score_restore.dataset_manifest import (
    DatasetManifestError,
    validate_dataset_snapshot,
)
from st_score_restore.dataset_snapshot_policy import (
    validate_authorized_dataset_snapshot,
)
try:
    from .dataset_test_item_helpers import item, opaque, permission
    from .dataset_test_snapshot_helpers import catalog, snapshot_for
except ImportError:  # unittest discover adds tests/ directly to sys.path
    from dataset_test_item_helpers import item, opaque, permission
    from dataset_test_snapshot_helpers import catalog, snapshot_for


class DatasetSnapshotPolicyTests(unittest.TestCase):
    def _authorized_source(self, **kwargs: object) -> dict:
        return item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
            **kwargs,
        )

    def test_public_snapshot_boundary_cannot_bypass_purpose_authorization(self) -> None:
        source = item(
            artifact_state="external_available",
            split="development",
            granted_purpose=None,
        )
        source_catalog = catalog([source])
        value = snapshot_for(source_catalog, [source])
        with self.assertRaisesRegex(
            DatasetManifestError, "not validly authorized at snapshot time"
        ):
            validate_dataset_snapshot(value, catalog=source_catalog)
        with self.assertRaisesRegex(
            DatasetManifestError, "not validly authorized at snapshot time"
        ):
            validate_authorized_dataset_snapshot(value, catalog=source_catalog)

    def test_future_authorization_is_rejected_at_snapshot_time(self) -> None:
        source = self._authorized_source()
        source["permissions"]["quality_evaluation"] = permission(
            "granted", authorized_on="2026-08-07"
        )
        source_catalog = catalog([source])
        with self.assertRaisesRegex(
            DatasetManifestError, "not validly authorized at snapshot time"
        ):
            validate_dataset_snapshot(
                snapshot_for(source_catalog, [source]), catalog=source_catalog
            )

    def test_expiry_date_is_fail_closed(self) -> None:
        source = self._authorized_source()
        source["permissions"]["quality_evaluation"] = permission(
            "granted", authorized_on="2026-08-01", expires_on="2026-08-06"
        )
        source_catalog = catalog([source])
        with self.assertRaisesRegex(
            DatasetManifestError, "not validly authorized at snapshot time"
        ):
            validate_dataset_snapshot(
                snapshot_for(source_catalog, [source]), catalog=source_catalog
            )

    def test_permission_is_valid_before_expiry(self) -> None:
        source = self._authorized_source()
        source["permissions"]["quality_evaluation"] = permission(
            "granted",
            authorized_on="2026-08-01",
            expires_on="2026-08-07",
            restrictions=[
                {"type": "environment_allowlist", "values": ["stage1_offline"]}
            ],
        )
        source_catalog = catalog([source])
        result = validate_dataset_snapshot(
            snapshot_for(source_catalog, [source]), catalog=source_catalog
        )
        self.assertEqual(result["assignments"][0]["split"], "development")

    def test_item_retention_expiry_is_fail_closed(self) -> None:
        source = self._authorized_source()
        source["retention"]["policy"] = "external_until_date"
        source["retention"]["expiresOn"] = "2026-08-06"
        source_catalog = catalog([source])
        with self.assertRaisesRegex(DatasetManifestError, "item retention expired"):
            validate_dataset_snapshot(
                snapshot_for(source_catalog, [source]), catalog=source_catalog
            )

    def test_pending_deletion_is_not_snapshot_eligible(self) -> None:
        source = self._authorized_source()
        source["retention"]["deletionRequired"] = True
        source["retention"]["deletionStatus"] = "pending"
        source["revocation"] = {
            "status": "pending_deletion",
            "effectiveOn": "2026-08-05",
            "reference": f"evidence:{opaque(120)}",
        }
        source_catalog = catalog([source])
        with self.assertRaisesRegex(DatasetManifestError, "revoked or pending deletion"):
            validate_dataset_snapshot(
                snapshot_for(source_catalog, [source]), catalog=source_catalog
            )

    def test_rights_review_after_snapshot_is_rejected(self) -> None:
        source = self._authorized_source()
        source["provenance"]["rightsReview"]["verifiedOn"] = "2026-08-07"
        source_catalog = catalog([source])
        with self.assertRaisesRegex(DatasetManifestError, "rights review was completed after"):
            validate_dataset_snapshot(
                snapshot_for(source_catalog, [source]), catalog=source_catalog
            )

    def test_privacy_review_after_snapshot_is_rejected(self) -> None:
        source = self._authorized_source(privacy_class="deidentified")
        source["privacy"]["reviewedOn"] = "2026-08-07"
        source_catalog = catalog([source])
        with self.assertRaisesRegex(DatasetManifestError, "privacy review was completed after"):
            validate_dataset_snapshot(
                snapshot_for(source_catalog, [source]), catalog=source_catalog
            )

    def test_dataset_review_after_snapshot_is_rejected(self) -> None:
        source = self._authorized_source()
        source["review"]["reviewedOn"] = "2026-08-07"
        source_catalog = catalog([source])
        with self.assertRaisesRegex(DatasetManifestError, "dataset review was completed after"):
            validate_dataset_snapshot(
                snapshot_for(source_catalog, [source]), catalog=source_catalog
            )

    def test_review_on_snapshot_date_is_allowed(self) -> None:
        source = self._authorized_source(privacy_class="deidentified")
        source["provenance"]["rightsReview"]["verifiedOn"] = "2026-08-06"
        source["privacy"]["reviewedOn"] = "2026-08-06"
        source["review"]["reviewedOn"] = "2026-08-06"
        source_catalog = catalog([source])
        validate_dataset_snapshot(
            snapshot_for(source_catalog, [source]), catalog=source_catalog
        )

    def test_storage_restriction_is_enforced_at_snapshot_time(self) -> None:
        source = self._authorized_source()
        source["permissions"]["quality_evaluation"] = permission(
            "granted",
            restrictions=[
                {"type": "storage_class_allowlist", "values": ["custody_external"]}
            ],
        )
        source["retention"]["storageClass"] = "not_assigned"
        # Catalog validation must fail before snapshot use because the restriction
        # contradicts the assigned artifact storage class.
        source_catalog = catalog([source])
        with self.assertRaises(DatasetManifestError):
            validate_dataset_snapshot(
                snapshot_for(source_catalog, [source]), catalog=source_catalog
            )

    def test_retention_restriction_is_enforced_at_snapshot_time(self) -> None:
        source = self._authorized_source()
        source["retention"]["policy"] = "external_until_date"
        source["retention"]["expiresOn"] = "2026-08-10"
        source["permissions"]["quality_evaluation"] = permission(
            "granted",
            restrictions=[
                {"type": "retention_not_after", "date": "2026-08-09"}
            ],
        )
        source_catalog = catalog([source])
        with self.assertRaises(DatasetManifestError):
            validate_dataset_snapshot(
                snapshot_for(source_catalog, [source]), catalog=source_catalog
            )

    def test_held_out_cannot_be_authorized_by_calibration(self) -> None:
        source = item(
            artifact_state="external_available",
            split="held_out",
            granted_purpose="held_out_evaluation",
        )
        source["permissions"]["held_out_evaluation"] = permission()
        source["permissions"]["safety_calibration"] = permission("granted")
        with self.assertRaisesRegex(DatasetManifestError, "held_out item may grant only"):
            source_catalog = catalog([source])
            validate_dataset_snapshot(
                snapshot_for(source_catalog, [source]), catalog=source_catalog
            )

    def test_publication_does_not_authorize_calibration_snapshot(self) -> None:
        source = item(
            artifact_state="external_available",
            split="calibration",
            granted_purpose="publication",
        )
        source_catalog = catalog([source])
        with self.assertRaisesRegex(
            DatasetManifestError, "not validly authorized at snapshot time"
        ):
            validate_dataset_snapshot(
                snapshot_for(source_catalog, [source]), catalog=source_catalog
            )

    def test_stage1_snapshot_never_activates_training(self) -> None:
        source = item(
            artifact_state="external_available",
            split="training_reserved",
            granted_purpose="model_training",
        )
        source_catalog = catalog([source])
        value = snapshot_for(source_catalog, [source])
        value["trainingUseActivated"] = True
        with self.assertRaisesRegex(DatasetManifestError, "cannot activate model training"):
            validate_dataset_snapshot(value, catalog=source_catalog)


if __name__ == "__main__":
    unittest.main()
