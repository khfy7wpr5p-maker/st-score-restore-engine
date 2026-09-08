import copy
import json
import unittest
from pathlib import Path

from st_score_restore.stage11_v2a_packaging_current_truth import (
    Stage11V2aPackagingCurrentTruthError,
    validate_stage11_v2a_packaging_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_PACKAGING_CURRENT_TRUTH.json"


class Stage11V2aPackagingCurrentTruthTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(TRUTH.read_text(encoding="utf-8"))

    def test_pending_packaging_truth_passes(self):
        result = validate_stage11_v2a_packaging_current_truth(self.payload)
        self.assertTrue(result["implementationReady"])
        self.assertFalse(result["executionCompleted"])
        self.assertTrue(result["candidateCheckpointFrozen"])
        self.assertTrue(result["candidatePackagingAuthorized"])
        self.assertFalse(result["productionInferenceAuthorized"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_checkpoint_identity_cannot_change(self):
        payload = copy.deepcopy(self.payload)
        payload["candidate"]["checkpointSha256"] = "0" * 64
        with self.assertRaises(Stage11V2aPackagingCurrentTruthError):
            validate_stage11_v2a_packaging_current_truth(payload)

    def test_execution_cannot_be_claimed_without_real_evidence(self):
        payload = copy.deepcopy(self.payload)
        payload["execution"]["completed"] = True
        payload["execution"]["packageSha256"] = "a" * 64
        payload["execution"]["packageSizeBytes"] = 123
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
