import json
import unittest
from pathlib import Path

from st_score_restore.stage11_v2_current_truth import Stage11V2CurrentTruthError, validate_stage11_v2_current_truth

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2_SYMBOL_PRESERVATION_CURRENT_TRUTH.json"


class Stage11V2CurrentTruthTests(unittest.TestCase):
    def test_current_truth_records_v2_review_and_v2a_ready(self):
        payload = json.loads(TRUTH.read_text(encoding="utf-8"))
        result = validate_stage11_v2_current_truth(payload)
        self.assertTrue(result["implementationReady"])
        self.assertTrue(result["developmentTrainingCompleted"])
        self.assertFalse(result["v2DevelopmentGatePassed"])
        self.assertTrue(result["v2aFineTuneAuthorized"])
        self.assertFalse(result["heldOutEvaluationAuthorized"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_cannot_silently_authorize_heldout(self):
        payload = json.loads(TRUTH.read_text(encoding="utf-8"))
        payload["gates"]["heldOutEvaluationAuthorized"] = True
        with self.assertRaises(Stage11V2CurrentTruthError):
            validate_stage11_v2_current_truth(payload)


if __name__ == "__main__":
    unittest.main()
