import json
import unittest
from pathlib import Path

from st_score_restore.stage11_heldout_evidence import (
    Stage11HeldOutEvidenceError,
    validate_heldout_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/stage11/evaluation/deepscoresv2-dense-heldout-final.v1.json"


class Stage11HeldOutEvidenceTests(unittest.TestCase):
    def load(self):
        return json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_evidence_passes(self):
        result = validate_heldout_evidence(self.load())
        self.assertTrue(result["heldOutPass"])
        self.assertEqual(result["evaluatedPairs"], 704)
        self.assertFalse(result["finalStage11Pass"])

    def test_rejects_weight_mutation(self):
        payload = self.load()
        payload["checkpoint"]["weightsMutated"] = True
        with self.assertRaises(Stage11HeldOutEvidenceError):
            validate_heldout_evidence(payload)

    def test_rejects_heldout_tuning(self):
        payload = self.load()
        payload["execution"]["heldOutUsedForTuning"] = True
        with self.assertRaises(Stage11HeldOutEvidenceError):
            validate_heldout_evidence(payload)

    def test_rejects_metric_regression(self):
        payload = self.load()
        payload["metrics"]["restored"]["edgeLoss"] = 1.0
        with self.assertRaises(Stage11HeldOutEvidenceError):
            validate_heldout_evidence(payload)


if __name__ == "__main__":
    unittest.main()
