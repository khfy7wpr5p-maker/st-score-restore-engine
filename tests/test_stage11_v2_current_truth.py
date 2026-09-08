import copy
import json
import unittest
from pathlib import Path

from st_score_restore.stage11_v2_current_truth import Stage11V2CurrentTruthError, validate_stage11_v2_current_truth

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2_SYMBOL_PRESERVATION_CURRENT_TRUTH.json"


class Stage11V2CurrentTruthTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(TRUTH.read_text(encoding="utf-8"))

    def test_current_truth_records_v2a_heldout_and_stage9a_pass(self):
        result = validate_stage11_v2_current_truth(self.payload)
        self.assertTrue(result["implementationReady"])
        self.assertFalse(result["v2DevelopmentGatePassed"])
        self.assertTrue(result["v2aDevelopmentGatePassed"])
        self.assertTrue(result["heldOutEvaluationCompleted"])
        self.assertTrue(result["stage9aEvaluationCompleted"])
        self.assertTrue(result["candidateCheckpointFrozen"])
        self.assertFalse(result["finalModelSelected"])
        self.assertFalse(result["stage12EntryAuthorized"])
        self.assertFalse(result["productionInferenceAuthorized"])

    def test_cannot_rewrite_v2a_checkpoint_identity(self):
        payload = copy.deepcopy(self.payload)
        payload["v2aResult"]["bestCheckpointSha256"] = "0" * 64
        with self.assertRaises(Stage11V2CurrentTruthError):
            validate_stage11_v2_current_truth(payload)

    def test_cannot_hide_mse_regression(self):
        payload = copy.deepcopy(self.payload)
        payload["v2aResult"]["mseRegressionObserved"] = False
        with self.assertRaises(Stage11V2CurrentTruthError):
            validate_stage11_v2_current_truth(payload)

    def test_consumed_heldout_retuning_guard_is_mandatory(self):
        payload = copy.deepcopy(self.payload)
        payload["gates"]["furtherTuningAgainstConsumedHeldoutForbidden"] = False
        with self.assertRaises(Stage11V2CurrentTruthError):
            validate_stage11_v2_current_truth(payload)

    def test_cannot_silently_select_production_model(self):
        payload = copy.deepcopy(self.payload)
        payload["gates"]["finalModelSelected"] = True
        with self.assertRaises(Stage11V2CurrentTruthError):
            validate_stage11_v2_current_truth(payload)

    def test_cannot_authorize_stage12_or_production(self):
        for key in ("stage12EntryAuthorized", "productionInferenceAuthorized"):
            payload = copy.deepcopy(self.payload)
            payload["gates"][key] = True
            with self.assertRaises(Stage11V2CurrentTruthError):
                validate_stage11_v2_current_truth(payload)


if __name__ == "__main__":
    unittest.main()
