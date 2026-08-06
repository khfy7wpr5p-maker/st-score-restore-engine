from __future__ import annotations
import copy
import unittest
from st_score_restore.dataset_manifest import DatasetManifestError, validate_dataset_catalog, validate_dataset_snapshot
try:
    from .dataset_test_item_helpers import item, opaque, permission
    from .dataset_test_snapshot_helpers import catalog, snapshot_for
except ImportError:
    from dataset_test_item_helpers import item, opaque, permission
    from dataset_test_snapshot_helpers import catalog, snapshot_for

class DatasetManifestTests(unittest.TestCase):

    def test_metadata_only_unassigned_contract_is_valid(self) -> None:
        result = validate_dataset_catalog(catalog([item()]))
        self.assertEqual(result['items'][0]['split'], 'unassigned')

    def test_entry_decision_is_required(self) -> None:
        value = catalog([item()])
        value['entryDecisionId'] = 'adr-unknown'
        with self.assertRaisesRegex(DatasetManifestError, 'entryDecisionId'):
            validate_dataset_catalog(value)

    def test_deidentification_digest_must_match_artifact(self) -> None:
        value = item(artifact_state='external_available', split='development', granted_purpose='quality_evaluation', privacy_class='deidentified')
        value['privacy']['deidentifiedArtifactSha256'] = 'b' * 64
        with self.assertRaisesRegex(DatasetManifestError, 'de-identification digest'):
            validate_dataset_catalog(catalog([value]))

    def test_metadata_only_item_cannot_claim_deidentified_artifact_digest(self) -> None:
        value = item(privacy_class='deidentified')
        with self.assertRaisesRegex(DatasetManifestError, 'available or revoked artifact digest'):
            validate_dataset_catalog(catalog([value]))

    def test_opaque_actor_and_subject_ids_are_required(self) -> None:
        value = item(artifact_state='external_available', split='development', granted_purpose='quality_evaluation')
        value['permissions']['quality_evaluation']['authorizedBy'] = 'actor.purpose:jane.doe'
        with self.assertRaisesRegex(DatasetManifestError, 'opaque identifier'):
            validate_dataset_catalog(catalog([value]))
        value = item()
        value['provenance']['rightsHolderId'] = 'subject:student-ali'
        with self.assertRaisesRegex(DatasetManifestError, 'opaque identifier'):
            validate_dataset_catalog(catalog([value]))

    def test_opaque_tokens_are_accepted(self) -> None:
        value = item(artifact_state='external_available', split='development', granted_purpose='quality_evaluation')
        value['provenance']['rightsHolderId'] = f'subject:{opaque(999)}'
        validate_dataset_catalog(catalog([value]))

    def test_free_text_identity_channels_are_rejected(self) -> None:
        value = catalog([item()])
        value['descriptionCode'] = 'teacher@example.com'
        with self.assertRaisesRegex(DatasetManifestError, 'invalid opaque identifier'):
            validate_dataset_catalog(value)
        source = item()
        source['provenance']['licenseId'] = 'C:\\Users\\Jane\\license.pdf'
        with self.assertRaisesRegex(DatasetManifestError, 'invalid opaque identifier'):
            validate_dataset_catalog(catalog([source]))

    def test_synthetic_parameters_reject_free_text(self) -> None:
        parent, child = self._synthetic_pair()
        child['syntheticGeneration']['parameters'] = {'operator': 'jane.doe'}
        with self.assertRaisesRegex(DatasetManifestError, 'free-text strings'):
            validate_dataset_catalog(catalog([parent, child]))

    def test_machine_restrictions_are_enforced(self) -> None:
        value = item(artifact_state='external_available', split='development', granted_purpose='quality_evaluation')
        value['permissions']['quality_evaluation'] = permission('granted', restrictions=[{'type': 'split_allowlist', 'values': ['calibration']}])
        with self.assertRaisesRegex(DatasetManifestError, 'restriction excludes'):
            validate_dataset_catalog(catalog([value]))

    def test_publication_cannot_ignore_external_export_restriction(self) -> None:
        value = item(artifact_state='external_available', split='development', granted_purpose='publication')
        value['permissions']['publication'] = permission('granted', restrictions=[{'type': 'external_export', 'allowed': False}])
        with self.assertRaisesRegex(DatasetManifestError, 'external-export restriction'):
            validate_dataset_catalog(catalog([value]))

    def test_revoked_item_requires_deletion_receipt(self) -> None:
        value = item(artifact_state='revoked', split='development')
        value['retention']['deletionReceiptReference'] = None
        with self.assertRaisesRegex(DatasetManifestError, 'completed deletion receipt'):
            validate_dataset_catalog(catalog([value]))

    def test_source_family_split_leakage_is_rejected(self) -> None:
        first = item('dataset.item.dev.v1', artifact_state='external_available', split='development', granted_purpose='quality_evaluation')
        second = item('dataset.item.held.v1', artifact_state='external_available', split='held_out', granted_purpose='held_out_evaluation', artifact_sha='b' * 64)
        with self.assertRaisesRegex(DatasetManifestError, 'source-family split leakage'):
            validate_dataset_catalog(catalog([first, second]))

    def _synthetic_pair(self) -> tuple[dict, dict]:
        parent = item('dataset.item.parent.v1', artifact_state='external_available', split='development', granted_purpose='synthetic_derivation')
        child = item('dataset.item.synthetic.v1', family_id=parent['sourceFamilyId'], artifact_state='external_available', split='development', source_kind='synthetic', artifact_sha='b' * 64)
        child['parentItemId'] = parent['datasetItemId']
        child['syntheticGeneration'] = {'generator': 'shadow-generator', 'generatorVersion': '1.0.0', 'generatorCommit': 'c' * 64, 'generatedOn': '2026-08-02', 'derivationAuthorizationReference': parent['permissions']['synthetic_derivation']['authorizationReference'], 'seed': 7, 'parameters': {'strength': 0.25}}
        return (parent, child)

    def test_synthetic_parent_requires_real_approval_and_valid_derivation(self) -> None:
        parent, child = self._synthetic_pair()
        validate_dataset_catalog(catalog([parent, child]))
        unapproved = copy.deepcopy(parent)
        unapproved['provenance']['rightsReview'] = {'status': 'pending', 'verifiedBy': None, 'verifiedOn': None, 'evidenceReference': None}
        with self.assertRaisesRegex(DatasetManifestError, 'external artifact requires approved rights'):
            validate_dataset_catalog(catalog([unapproved, child]))

    def test_synthetic_child_must_share_parent_assigned_split(self) -> None:
        parent, child = self._synthetic_pair()
        child['split'] = 'unassigned'
        with self.assertRaisesRegex(DatasetManifestError, "parent's assigned split"):
            validate_dataset_catalog(catalog([parent, child]))
        parent, child = self._synthetic_pair()
        child['split'] = 'calibration'
        with self.assertRaisesRegex(DatasetManifestError, "parent's assigned split"):
            validate_dataset_catalog(catalog([parent, child]))
        parent, child = self._synthetic_pair()
        validate_dataset_catalog(catalog([parent, child]))

    def test_teacher_approval_and_stage1_training_assertions_stay_false(self) -> None:
        value = item()
        value['assertions']['stage1TrainingExecutionAuthorized'] = True
        with self.assertRaisesRegex(DatasetManifestError, 'assertions must remain false'):
            validate_dataset_catalog(catalog([value]))

    def test_snapshot_is_digest_bound(self) -> None:
        source = item(artifact_state='external_available', split='development', granted_purpose='quality_evaluation')
        source_catalog = catalog([source])
        value = snapshot_for(source_catalog, [source])
        validate_dataset_snapshot(value, catalog=source_catalog)
        value['catalogSha256'] = '0' * 64
        with self.assertRaisesRegex(DatasetManifestError, 'does not match catalog'):
            validate_dataset_snapshot(value, catalog=source_catalog)
if __name__ == '__main__':
    unittest.main()
