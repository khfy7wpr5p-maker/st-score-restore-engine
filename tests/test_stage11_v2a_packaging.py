import copy
import unittest

from st_score_restore.stage11_v2a_packaging import (
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_CONFIG_SHA256,
    EXPECTED_DATASET_MD5,
    EXPECTED_MODEL_STATE_SHA256,
    EXPECTED_SOURCE_V2_CHECKPOINT_SHA256,
    PACKAGE_CONTRACT_ID,
    PACKAGE_EVIDENCE_TYPE,
    PACKAGE_SCHEMA_VERSION,
    Stage11V2aPackagingError,
    candidate_package_contract,
    validate_candidate_package_evidence,
)


def valid_synthetic_evidence():
    return {
        "schemaVersion": PACKAGE_SCHEMA_VERSION,
        "artifactType": PACKAGE_EVIDENCE_TYPE,
        "status": "completed",
        "contractId": PACKAGE_CONTRACT_ID,
        "checkpointSha256": EXPECTED_CHECKPOINT_SHA256,
        "configSha256": EXPECTED_CONFIG_SHA256,
        "datasetMd5": EXPECTED_DATASET_MD5,
        "sourceV2CheckpointSha256": EXPECTED_SOURCE_V2_CHECKPOINT_SHA256,
        "modelStateSha256Before": EXPECTED_MODEL_STATE_SHA256,
        "modelStateSha256After": EXPECTED_MODEL_STATE_SHA256,
        "weightsMutated": False,
        "optimizerCreated": False,
        "backpropagationExecuted": False,
        "heldOutAccessed": False,
        "package": {
            "format": "torchscript-trace",
            "sha256": "a" * 64,
            "sizeBytes": 123,
        },
        "smokeTest": {
            "inputShape": [1, 1, 512, 512],
            "outputShape": [1, 1, 512, 512],
            "finite": True,
            "outputMin": 0.0,
            "outputMax": 1.0,
            "repeatMaxAbsDiff": 0.0,
            "reloadMaxAbsDiff": 0.0,
        },
        "authorization": {
            "candidatePackagingAuthorized": True,
            "productionInferenceAuthorized": False,
            "productionPromotionAuthorized": False,
            "stage12EntryAuthorized": False,
        },
    }


class Stage11V2aPackagingTests(unittest.TestCase):
    def test_contract_freezes_candidate_and_input_shape(self):
        contract = candidate_package_contract()
        self.assertEqual(contract["checkpointSha256"], EXPECTED_CHECKPOINT_SHA256)
        self.assertEqual(contract["input"]["patchHeight"], 512)
        self.assertEqual(contract["input"]["patchWidth"], 512)
        self.assertFalse(contract["authorization"]["productionInferenceAuthorized"])
        self.assertFalse(contract["authorization"]["stage12EntryAuthorized"])

    def test_synthetic_contract_evidence_passes(self):
        result = validate_candidate_package_evidence(valid_synthetic_evidence())
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["portableCandidateCreated"])
        self.assertFalse(result["productionInferenceAuthorized"])

    def test_checkpoint_identity_cannot_change(self):
        evidence = valid_synthetic_evidence()
        evidence["checkpointSha256"] = "b" * 64
        with self.assertRaises(Stage11V2aPackagingError):
            validate_candidate_package_evidence(evidence)

    def test_packaging_cannot_access_heldout(self):
        evidence = valid_synthetic_evidence()
        evidence["heldOutAccessed"] = True
        with self.assertRaises(Stage11V2aPackagingError):
            validate_candidate_package_evidence(evidence)

    def test_smoke_shape_and_range_fail_closed(self):
        evidence = valid_synthetic_evidence()
        evidence["smokeTest"]["outputShape"] = [1, 1, 256, 256]
        with self.assertRaises(Stage11V2aPackagingError):
            validate_candidate_package_evidence(evidence)
        evidence = valid_synthetic_evidence()
        evidence["smokeTest"]["outputMax"] = 1.01
        with self.assertRaises(Stage11V2aPackagingError):
            validate_candidate_package_evidence(evidence)

    def test_production_and_stage12_stay_closed(self):
        for key in ("productionInferenceAuthorized", "productionPromotionAuthorized", "stage12EntryAuthorized"):
            evidence = valid_synthetic_evidence()
            evidence["authorization"][key] = True
            with self.assertRaises(Stage11V2aPackagingError):
                validate_candidate_package_evidence(evidence)


if __name__ == "__main__":
    unittest.main()
