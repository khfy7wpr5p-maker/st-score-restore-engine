import copy
import json
import unittest
from pathlib import Path

from st_score_restore.stage11_v2a_consumer_adapter_current_truth import (
    Stage11V2aConsumerAdapterCurrentTruthError,
    validate_stage11_v2a_consumer_adapter_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_CONSUMER_ADAPTER_CURRENT_TRUTH.json"


class Stage11V2aConsumerAdapterCurrentTruthTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(TRUTH.read_text(encoding="utf-8"))

    def test_current_truth_passes(self):
        result = validate_stage11_v2a_consumer_adapter_current_truth(self.payload)
        self.assertTrue(result["syntheticConsumerIntegrationPassed"])
        self.assertTrue(result["candidatePackageFrozen"])
        self.assertFalse(result["productionInferenceAuthorized"])
        self.assertFalse(result["stage12EntryAuthorized"])
        self.assertEqual(result["nextBoundary"], "staging-only-api-adapter")

    def test_candidate_package_identity_is_immutable(self):
        payload = copy.deepcopy(self.payload)
        payload["candidate"]["packageSha256"] = "0" * 64
        with self.assertRaises(Stage11V2aConsumerAdapterCurrentTruthError):
            validate_stage11_v2a_consumer_adapter_current_truth(payload)

    def test_synthetic_only_boundary_is_mandatory(self):
        payload = copy.deepcopy(self.payload)
        payload["safety"]["syntheticInputsOnly"] = False
        with self.assertRaises(Stage11V2aConsumerAdapterCurrentTruthError):
            validate_stage11_v2a_consumer_adapter_current_truth(payload)

    def test_cannot_authorize_production_or_stage12(self):
        for key in (
            "productionInferenceAuthorized",
            "productionPromotionAuthorized",
            "finalProductionModelSelectionAuthorized",
            "stage12EntryAuthorized",
        ):
            payload = copy.deepcopy(self.payload)
            payload["authorization"][key] = True
            with self.assertRaises(Stage11V2aConsumerAdapterCurrentTruthError):
                validate_stage11_v2a_consumer_adapter_current_truth(payload)

    def test_heldout_access_flag_must_stay_false(self):
        payload = copy.deepcopy(self.payload)
        payload["safety"]["heldOutAccessed"] = True
        with self.assertRaises(Stage11V2aConsumerAdapterCurrentTruthError):
            validate_stage11_v2a_consumer_adapter_current_truth(payload)


if __name__ == "__main__":
    unittest.main()
