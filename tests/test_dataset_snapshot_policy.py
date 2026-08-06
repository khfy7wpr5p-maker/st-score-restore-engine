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
    from .dataset_test_item_helpers import item, permission
    from .dataset_test_snapshot_helpers import catalog, snapshot_for
except ImportError:  # unittest discover adds tests/ directly to sys.path
    from dataset_test_item_helpers import item, permission
    from dataset_test_snapshot_helpers import catalog, snapshot_for


class DatasetSnapshotPolicyTests(unittest.TestCase):
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
            validate_authorized_dataset_snapshot(
                value, catalog=source_catalog
            )

    def test_future_authorization_is_rejected_at_snapshot_time(self) -> None:
        source = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        source["permissions"]["quality_evaluation"] = permission(
            "granted", authorized_on="2026-08-07"
        )
        source_catalog = catalog([source])
        with self.assertRaisesRegex(
            DatasetManifestError, "not validly authorized at snapshot time"
        ):
            validate_dataset_snapshot(
                snapshot_for(source_catalog, [source]),
                catalog=source_catalog,
            )

    def test_expiry_date_is_fail_closed(self) -> None:
        source = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        source["permissions"]["quality_evaluation"] = permission(
            "granted",
            authorized_on="2026-08-01",
            expires_on="2026-08-06",
        )
        source_catalog = catalog([source])
        with self.assertRaisesRegex(
            DatasetManifestError, "not validly authorized at snapshot time"
        ):
            validate_dataset_snapshot(
                snapshot_for(source_catalog, [source]),
                catalog=source_catalog,
            )

    def test_permission_is_valid_before_expiry(self) -> None:
        source = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        source["permissions"]["quality_evaluation"] = permission(
            "granted",
            authorized_on="2026-08-01",
            expires_on="2026-08-07",
            restrictions=[
                {
                    "type": "environment_allowlist",
                    "values": ["stage1_offline"],
                }
            ],
        )
        source_catalog = catalog([source])
        result = validate_dataset_snapshot(
            snapshot_for(source_catalog, [source]),
            catalog=source_catalog,
        )
        self.assertEqual(result["assignments"][0]["split"], "development")

    def test_held_out_cannot_be_authorized_by_calibration(self) -> None:
        source = item(
            artifact_state="external_available",
            split="held_out",
            granted_purpose="held_out_evaluation",
        )
        source["permissions"]["held_out_evaluation"] = permission()
        source["permissions"]["safety_calibration"] = permission("granted")
        with self.assertRaisesRegex(
            DatasetManifestError, "held_out item may grant only"
        ):
            catalog_value = catalog([source])
            validate_dataset_snapshot(
                snapshot_for(catalog_value, [source]),
                catalog=catalog_value,
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
                snapshot_for(source_catalog, [source]),
                catalog=source_catalog,
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
        with self.assertRaisesRegex(
            DatasetManifestError, "cannot activate model training"
        ):
            validate_dataset_snapshot(value, catalog=source_catalog)


if __name__ == "__main__":
    unittest.main()
