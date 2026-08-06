from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from st_score_restore.dataset_manifest import DatasetManifestError
from tools.validate_dataset_manifest import (
    ROOT,
    validate_repository_contract,
    validate_schema_parity,
)


class DatasetSchemaParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog_schema = json.loads(
            (ROOT / "schemas" / "dataset-catalog.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.snapshot_schema = json.loads(
            (ROOT / "schemas" / "dataset-snapshot.schema.json").read_text(
                encoding="utf-8"
            )
        )

    def test_repository_contract_and_schema_parity_pass(self) -> None:
        validate_repository_contract()

    def test_purpose_drift_is_detected(self) -> None:
        catalog_schema = copy.deepcopy(self.catalog_schema)
        permissions = (
            catalog_schema["$defs"]["item"]["properties"]["permissions"]
        )
        permissions["required"].remove("synthetic_derivation")
        with self.assertRaisesRegex(
            DatasetManifestError, "purpose required-field drift"
        ):
            validate_schema_parity(
                catalog_schema,
                self.snapshot_schema,
            )

    def test_opaque_actor_pattern_drift_is_detected(self) -> None:
        catalog_schema = copy.deepcopy(self.catalog_schema)
        catalog_schema["$defs"]["permission"]["properties"]["authorizedBy"][
            "pattern"
        ] = ".*"
        with self.assertRaisesRegex(
            DatasetManifestError, "permission.authorizedBy pattern drift"
        ):
            validate_schema_parity(
                catalog_schema,
                self.snapshot_schema,
            )

    def test_entry_decision_drift_is_detected(self) -> None:
        snapshot_schema = copy.deepcopy(self.snapshot_schema)
        snapshot_schema["properties"]["entryDecisionId"]["const"] = "other"
        with self.assertRaisesRegex(
            DatasetManifestError, "entry-decision drift"
        ):
            validate_schema_parity(
                self.catalog_schema,
                snapshot_schema,
            )


if __name__ == "__main__":
    unittest.main()
