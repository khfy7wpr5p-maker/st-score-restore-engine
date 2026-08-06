from __future__ import annotations

import copy
import json
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from st_score_restore.dataset_manifest import (
    DatasetManifestError,
    validate_dataset_catalog,
    validate_dataset_snapshot,
)
from tools.validate_dataset_manifest import ROOT, validate_repository_contract
from tools.dataset_schema_parity import validate_schema_parity
try:
    from .dataset_test_item_helpers import item
    from .dataset_test_snapshot_helpers import catalog, snapshot_for
except ImportError:
    from dataset_test_item_helpers import item
    from dataset_test_snapshot_helpers import catalog, snapshot_for


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
        schema = copy.deepcopy(self.catalog_schema)
        permissions = schema["$defs"]["item"]["properties"]["permissions"]
        permissions["required"].remove("synthetic_derivation")
        with self.assertRaisesRegex(DatasetManifestError, "purpose required-field drift"):
            validate_schema_parity(schema, self.snapshot_schema)

    def test_opaque_actor_pattern_drift_is_detected(self) -> None:
        schema = copy.deepcopy(self.catalog_schema)
        schema["$defs"]["permission"]["properties"]["authorizedBy"]["pattern"] = ".*"
        with self.assertRaisesRegex(DatasetManifestError, "authorizedBy pattern drift"):
            validate_schema_parity(schema, self.snapshot_schema)

    def test_entry_decision_drift_is_detected(self) -> None:
        schema = copy.deepcopy(self.snapshot_schema)
        schema["properties"]["entryDecisionId"]["const"] = "other"
        with self.assertRaisesRegex(DatasetManifestError, "constant drift"):
            validate_schema_parity(self.catalog_schema, schema)

    def test_nested_required_drift_is_detected(self) -> None:
        schema = copy.deepcopy(self.catalog_schema)
        schema["$defs"]["item"]["properties"]["privacy"]["required"].remove(
            "reviewedBy"
        )
        with self.assertRaisesRegex(DatasetManifestError, "privacy required-field drift"):
            validate_schema_parity(schema, self.snapshot_schema)

    def test_created_at_pattern_drift_is_detected(self) -> None:
        schema = copy.deepcopy(self.snapshot_schema)
        schema["properties"]["createdAt"]["pattern"] = (
            r"^\d{4}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        )
        with self.assertRaisesRegex(DatasetManifestError, "createdAt pattern drift"):
            validate_schema_parity(self.catalog_schema, schema)

    def test_snapshot_id_reference_drift_is_detected(self) -> None:
        schema = copy.deepcopy(self.snapshot_schema)
        schema["properties"]["snapshotId"]["$ref"] = "#/$defs/missing"
        with self.assertRaisesRegex(DatasetManifestError, "snapshotId reference drift"):
            validate_schema_parity(self.catalog_schema, schema)

    def test_snapshot_assignment_split_drift_is_detected(self) -> None:
        schema = copy.deepcopy(self.snapshot_schema)
        schema["properties"]["assignments"]["items"]["properties"]["split"]["enum"].append("unassigned")
        with self.assertRaisesRegex(DatasetManifestError, "snapshot assignment splits"):
            validate_schema_parity(self.catalog_schema, schema)

    def test_generator_commit_pattern_drift_is_detected(self) -> None:
        schema = copy.deepcopy(self.catalog_schema)
        variants = schema["$defs"]["item"]["properties"]["syntheticGeneration"]["oneOf"]
        object_variant = next(value for value in variants if value.get("type") == "object")
        object_variant["properties"]["generatorCommit"]["pattern"] = ".*"
        with self.assertRaisesRegex(DatasetManifestError, "generatorCommit pattern drift"):
            validate_schema_parity(schema, self.snapshot_schema)

    def test_parameter_key_pattern_drift_is_detected(self) -> None:
        schema = copy.deepcopy(self.catalog_schema)
        variants = schema["$defs"]["parameterValue"]["oneOf"]
        object_variant = next(value for value in variants if value.get("type") == "object")
        object_variant["propertyNames"]["pattern"] = ".*"
        with self.assertRaisesRegex(DatasetManifestError, "parameterValue.propertyNames pattern drift"):
            validate_schema_parity(schema, self.snapshot_schema)

    def test_gap_code_pattern_drift_is_detected(self) -> None:
        schema = copy.deepcopy(self.snapshot_schema)
        schema["properties"]["coverage"]["properties"]["gapCodes"]["items"]["pattern"] = ".*"
        with self.assertRaisesRegex(DatasetManifestError, "gapCodes pattern drift"):
            validate_schema_parity(self.catalog_schema, schema)

    def test_unknown_object_fields_cannot_be_reopened(self) -> None:
        schema = copy.deepcopy(self.catalog_schema)
        schema["$defs"]["item"]["properties"]["privacy"]["additionalProperties"] = True
        with self.assertRaisesRegex(DatasetManifestError, "additionalProperties=false"):
            validate_schema_parity(schema, self.snapshot_schema)

    def test_restriction_value_drift_is_detected(self) -> None:
        schema = copy.deepcopy(self.catalog_schema)
        variants = schema["$defs"]["restriction"]["oneOf"]
        split_variant = next(
            value
            for value in variants
            if value["properties"]["type"]["const"] == "split_allowlist"
        )
        split_variant["properties"]["values"]["items"]["enum"].append("unassigned")
        with self.assertRaisesRegex(DatasetManifestError, "split restriction values"):
            validate_schema_parity(schema, self.snapshot_schema)

    def test_valid_catalog_and_snapshot_pass_both_engines(self) -> None:
        source = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        source_catalog = catalog([source])
        snapshot = snapshot_for(source_catalog, [source])
        Draft202012Validator(self.catalog_schema).validate(source_catalog)
        Draft202012Validator(self.snapshot_schema).validate(snapshot)
        validate_dataset_catalog(source_catalog)
        validate_dataset_snapshot(snapshot, catalog=source_catalog)

    def test_structural_invalid_fails_both_engines(self) -> None:
        source_catalog = catalog([item()])
        del source_catalog["descriptionCode"]
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.catalog_schema).validate(source_catalog)
        with self.assertRaises(DatasetManifestError):
            validate_dataset_catalog(source_catalog)

    def test_semantic_invalid_passes_schema_but_fails_python(self) -> None:
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
        source_catalog = catalog([first, second])
        Draft202012Validator(self.catalog_schema).validate(source_catalog)
        with self.assertRaisesRegex(DatasetManifestError, "source-family split leakage"):
            validate_dataset_catalog(source_catalog)

    def test_created_at_acceptance_is_identical(self) -> None:
        source = item(
            artifact_state="external_available",
            split="development",
            granted_purpose="quality_evaluation",
        )
        source_catalog = catalog([source])
        valid = snapshot_for(source_catalog, [source])
        Draft202012Validator(self.snapshot_schema).validate(valid)
        validate_dataset_snapshot(valid, catalog=source_catalog)
        invalid = copy.deepcopy(valid)
        invalid["createdAt"] = "2026-08T00:00:00Z"
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.snapshot_schema).validate(invalid)
        with self.assertRaises(DatasetManifestError):
            validate_dataset_snapshot(invalid, catalog=source_catalog)

    def test_free_text_parameter_rejected_by_both_engines(self) -> None:
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
            "parameters": {"operator": "jane.doe"},
        }
        source_catalog = catalog([parent, child])
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.catalog_schema).validate(source_catalog)
        with self.assertRaises(DatasetManifestError):
            validate_dataset_catalog(source_catalog)


if __name__ == "__main__":
    unittest.main()
