import copy
import json
import unittest
from pathlib import Path

from st_score_restore.stage11_v2a_acceptance import (
    Stage11V2aAcceptanceError,
    validate_stage11_v2a_acceptance,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-evaluation-acceptance.v1.json"


class Stage11V2aAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_acceptance_snapshot_passes(self):
        result = validate_stage11_v2a_acceptance(self.payload)
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["developmentGatePassed"])
        self.assertTrue(result["heldoutPassed"])
        self.assertTrue(result["stage9aPassed"])
        self.assertTrue(result["candidateCheckpointFrozen"])
        self.assertFalse(result["idealInkRecallTargetReached"])
        self.assertTrue(result["mseRegressionObserved"])
        self.assertFalse(result["productionPromotionAuthorized"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_checkpoint_identity_is_immutable(self):
        payload = copy.deepcopy(self.payload)
        payload["checkpointSha256"] = "0" * 64
        with self.assertRaises(Stage11V2aAcceptanceError):
            validate_stage11_v2a_acceptance(payload)

    def test_heldout_metric_cannot_be_rewritten(self):
        payload = copy.deepcopy(self.payload)
        payload["heldout"]["metrics"]["inkRecallDelta"] = -0.01
        with self.assertRaises(Stage11V2aAcceptanceError):
            validate_stage11_v2a_acceptance(payload)

    def test_stage9a_pass_cannot_be_promoted_to_musical_truth(self):
        payload = copy.deepcopy(self.payload)
        payload["stage9a"]["musicalTruthImplied"] = True
        with self.assertRaises(Stage11V2aAcceptanceError):
            validate_stage11_v2a_acceptance(payload)

    def test_consumed_heldout_cannot_become_tuning_data(self):
        payload = copy.deepcopy(self.payload)
        payload["decision"]["furtherTuningAgainstConsumedHeldoutForbidden"] = False
        with self.assertRaises(Stage11V2aAcceptanceError):
            validate_stage11_v2a_acceptance(payload)

    def test_production_and_stage12_remain_closed(self):
        for key in ("productionPromotionAuthorized", "stage12EntryAuthorized", "productionInferenceAuthorized"):
            payload = copy.deepcopy(self.payload)
            payload["decision"][key] = True
            with self.assertRaises(Stage11V2aAcceptanceError):
                validate_stage11_v2a_acceptance(payload)


if __name__ == "__main__":
    unittest.main()
