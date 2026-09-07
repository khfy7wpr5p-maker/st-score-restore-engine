import json
import unittest
from pathlib import Path

from st_score_restore.stage11_first_gpu_run_evidence import (
    Stage11FirstGpuRunEvidenceError,
    validate_first_gpu_run_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/stage11/training/deepscoresv2-dense-first-gpu-run.v1.json"


class Stage11FirstGpuRunEvidenceTests(unittest.TestCase):
    def load(self):
        return json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_first_gpu_run_evidence_is_valid(self):
        result = validate_first_gpu_run_evidence(self.load())
        self.assertTrue(result["valid"])
        self.assertEqual(result["epochsCompleted"], 20)
        self.assertEqual(result["bestEpoch"], 19)
        self.assertTrue(result["firstGpuTrainingRunPass"])
        self.assertFalse(result["finalStage11Pass"])

    def test_rejects_held_out_tuning(self):
        payload = self.load()
        payload["runEvidence"]["heldOutUsedForTuning"] = True
        with self.assertRaises(Stage11FirstGpuRunEvidenceError):
            validate_first_gpu_run_evidence(payload)

    def test_rejects_checkpoint_identity_change(self):
        payload = self.load()
        payload["driveArtifacts"]["bestCheckpoint"]["sha256"] = "0" * 64
        with self.assertRaises(Stage11FirstGpuRunEvidenceError):
            validate_first_gpu_run_evidence(payload)

    def test_rejects_premature_final_stage11_pass(self):
        payload = self.load()
        payload["decision"]["finalStage11Pass"] = True
        with self.assertRaises(Stage11FirstGpuRunEvidenceError):
            validate_first_gpu_run_evidence(payload)

    def test_requires_development_improvement(self):
        payload = self.load()
        payload["metrics"]["epoch19"]["development"]["loss"] = 1.0
        with self.assertRaises(Stage11FirstGpuRunEvidenceError):
            validate_first_gpu_run_evidence(payload)


if __name__ == "__main__":
    unittest.main()
