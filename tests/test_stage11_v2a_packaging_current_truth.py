import copy
import json
import unittest
from pathlib import Path

from st_score_restore.stage11_v2a_packaging import validate_candidate_package_evidence
from st_score_restore.stage11_v2a_packaging_current_truth import (
    Stage11V2aPackagingCurrentTruthError,
    validate_stage11_v2a_packaging_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_PACKAGING_CURRENT_TRUTH.json"
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-candidate-package-evidence.v1.json"


class Stage11V2aPackagingCurrentTruthTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(TRUTH.read_text(encoding="utf-8"))

    def test_completed_packaging_truth_passes(self):
        result = validate_stage11_v2a_packaging_current_truth(self.payload)
        self.assertTrue(result["implementationReady"])
        self.assertTrue(result["executionCompleted"])
        self.assertTrue(result["candidateCheckpointFrozen"])
        self.assertTrue(result["portableCandidateCreated"])
        self.assertTrue(result["candidatePackagingAuthorized"])
        self.assertEqual(
            result["packageSha256"],
            "7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234",
        )
        self.assertEqual(result["packageSizeBytes"], 7817857)
        self.assertFalse(result["productionInferenceAuthorized"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_committed_execution_evidence_matches_truth(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        evidence_result = validate_candidate_package_evidence(evidence)
        truth_result = validate_stage11_v2a_packaging_current_truth(self.payload)
        self.assertEqual(evidence_result["packageSha256"], truth_result["packageSha256"])
        self.assertEqual(int(evidence["package"]["sizeBytes"]), truth_result["packageSizeBytes"])
        self.assertFalse(evidence["heldOutAccessed"])
        self.assertFalse(evidence["weightsMutated"])
        self.assertFalse(evidence["optimizerCreated"])
        self.assertFalse(evidence["backpropagationExecuted"])

    def test_checkpoint_identity_cannot_change(self):
        payload = copy.deepcopy(self.payload)
        payload["candidate"]["checkpointSha256"] = "0" * 64
        with self.assertRaises(Stage11V2aPackagingCurrentTruthError):
            validate_stage11_v2a_packaging_current_truth(payload)

    def test_package_identity_cannot_change(self):
        payload = copy.deepcopy(self.payload)
        payload["execution"]["packageSha256"] = "0" * 64
        with self.assertRaises(Stage11V2aPackagingCurrentTruthError):
            validate_stage11_v2a_packaging_current_truth(payload)
        payload = copy.deepcopy(self.payload)
        payload["execution"]["packageSizeBytes"] += 1
        with self.assertRaises(Stage11V2aPackagingCurrentTruthError):
            validate_stage11_v2a_packaging_current_truth(payload)

    def test_execution_evidence_import_cannot_be_hidden(self):
        payload = copy.deepcopy(self.payload)
        payload["implementation"]["executionEvidenceImported"] = False
        with self.assertRaises(Stage11V2aPackagingCurrentTruthError):
            validate_stage11_v2a_packaging_current_truth(payload)

    def test_heldout_access_guard_is_mandatory(self):
        payload = copy.deepcopy(self.payload)
        payload["implementation"]["heldoutAccessForbidden"] = False
        with self.assertRaises(Stage11V2aPackagingCurrentTruthError):
            validate_stage11_v2a_packaging_current_truth(payload)

    def test_production_and_stage12_remain_closed(self):
        for key in (
            "productionInferenceAuthorized",
            "productionPromotionAuthorized",
            "finalProductionModelSelectionAuthorized",
            "stage12EntryAuthorized",
        ):
            payload = copy.deepcopy(self.payload)
            payload["authorization"][key] = True
            with self.assertRaises(Stage11V2aPackagingCurrentTruthError):
                validate_stage11_v2a_packaging_current_truth(payload)


if __name__ == "__main__":
    unittest.main()
