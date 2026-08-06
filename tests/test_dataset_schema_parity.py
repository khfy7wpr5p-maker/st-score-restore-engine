from __future__ import annotations
import copy
import json
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from st_score_restore.dataset_manifest import DatasetManifestError, validate_dataset_catalog, validate_dataset_snapshot
from tools.validate_dataset_manifest import ROOT, validate_repository_contract, validate_schema_parity
try:
    from .dataset_test_item_helpers import item
    from .dataset_test_snapshot_helpers import catalog, snapshot_for
except ImportError:
    from dataset_test_item_helpers import item
    from dataset_test_snapshot_helpers import catalog, snapshot_for

class DatasetSchemaParityTests(unittest.TestCase):

    def setUp(self) -> None:
        self.catalog_schema = json.loads((ROOT / 'schemas' / 'dataset-catalog.schema.json').read_text(encoding='utf-8'))
        self.snapshot_schema = json.loads((ROOT / 'schemas' / 'dataset-snapshot.schema.json').read_text(encoding='utf-8'))

    def test_repository_contract_and_schema_parity_pass(self) -> None:
        validate_repository_contract()

    def test_purpose_drift_is_detected(self) -> None:
        catalog_schema = copy.deepcopy(self.catalog_schema)
        permissions = catalog_schema['$defs']['item']['properties']['permissions']
        permissions['required'].remove('synthetic_derivation')
        with self.assertRaisesRegex(DatasetManifestError, 'purpose required-field drift'):
            validate_schema_parity(catalog_schema, self.snapshot_schema)

    def test_opaque_actor_pattern_drift_is_detected(self) -> None:
        catalog_schema = copy.deepcopy(self.catalog_schema)
        catalog_schema['$defs']['permission']['properties']['authorizedBy']['pattern'] = '.*'
        with self.assertRaisesRegex(DatasetManifestError, 'permission.authorizedBy pattern drift'):
            validate_schema_parity(catalog_schema, self.snapshot_schema)

    def test_entry_decision_drift_is_detected(self) -> None:
        snapshot_schema = copy.deepcopy(self.snapshot_schema)
        snapshot_schema['properties']['entryDecisionId']['const'] = 'other'
        with self.assertRaisesRegex(DatasetManifestError, 'constant drift'):
            validate_schema_parity(self.catalog_schema, snapshot_schema)

    def test_nested_required_drift_is_detected(self) -> None:
        catalog_schema = copy.deepcopy(self.catalog_schema)
        catalog_schema['$defs']['item']['properties']['privacy']['required'].remove('reviewedBy')
        with self.assertRaisesRegex(DatasetManifestError, 'privacy required-field drift'):
            validate_schema_parity(catalog_schema, self.snapshot_schema)

    def test_created_at_pattern_drift_is_detected(self) -> None:
        snapshot_schema = copy.deepcopy(self.snapshot_schema)
        snapshot_schema['properties']['createdAt']['pattern'] = '^\\d{4}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$'
        with self.assertRaisesRegex(DatasetManifestError, 'snapshot.createdAt pattern drift'):
            validate_schema_parity(self.catalog_schema, snapshot_schema)

    def test_valid_catalog_and_snapshot_pass_both_engines(self) -> None:
        source = item(artifact_state='external_available', split='development', granted_purpose='quality_evaluation')
        source_catalog = catalog([source])
        snapshot = snapshot_for(source_catalog, [source])
        Draft202012Validator(self.catalog_schema).validate(source_catalog)
        Draft202012Validator(self.snapshot_schema).validate(snapshot)
        validate_dataset_catalog(source_catalog)
        validate_dataset_snapshot(snapshot, catalog=source_catalog)

    def test_structural_invalid_fails_both_engines(self) -> None:
        source_catalog = catalog([item()])
        del source_catalog['descriptionCode']
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.catalog_schema).validate(source_catalog)
        with self.assertRaises(DatasetManifestError):
            validate_dataset_catalog(source_catalog)

    def test_semantic_invalid_passes_schema_but_fails_python(self) -> None:
        first = item('dataset.item.dev.v1', artifact_state='external_available', split='development', granted_purpose='quality_evaluation')
        second = item('dataset.item.held.v1', artifact_state='external_available', split='held_out', granted_purpose='held_out_evaluation', artifact_sha='b' * 64)
        source_catalog = catalog([first, second])
        Draft202012Validator(self.catalog_schema).validate(source_catalog)
        with self.assertRaisesRegex(DatasetManifestError, 'source-family split leakage'):
            validate_dataset_catalog(source_catalog)

    def test_created_at_acceptance_is_identical(self) -> None:
        source = item(artifact_state='external_available', split='development', granted_purpose='quality_evaluation')
        source_catalog = catalog([source])
        valid = snapshot_for(source_catalog, [source])
        Draft202012Validator(self.snapshot_schema).validate(valid)
        validate_dataset_snapshot(valid, catalog=source_catalog)
        invalid = copy.deepcopy(valid)
        invalid['createdAt'] = '2026-08T00:00:00Z'
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.snapshot_schema).validate(invalid)
        with self.assertRaises(DatasetManifestError):
            validate_dataset_snapshot(invalid, catalog=source_catalog)

    def test_free_text_parameter_rejected_by_both_engines(self) -> None:
        parent = item('dataset.item.parent.v1', artifact_state='external_available', split='development', granted_purpose='synthetic_derivation')
        child = item('dataset.item.synthetic.v1', family_id=parent['sourceFamilyId'], artifact_state='external_available', split='development', source_kind='synthetic', artifact_sha='b' * 64)
        child['parentItemId'] = parent['datasetItemId']
        child['syntheticGeneration'] = {'generator': 'shadow-generator', 'generatorVersion': '1.0.0', 'generatorCommit': 'c' * 64, 'generatedOn': '2026-08-02', 'derivationAuthorizationReference': parent['permissions']['synthetic_derivation']['authorizationReference'], 'seed': 7, 'parameters': {'operator': 'jane.doe'}}
        source_catalog = catalog([parent, child])
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.catalog_schema).validate(source_catalog)
        with self.assertRaises(DatasetManifestError):
            validate_dataset_catalog(source_catalog)
if __name__ == '__main__':
    unittest.main()
