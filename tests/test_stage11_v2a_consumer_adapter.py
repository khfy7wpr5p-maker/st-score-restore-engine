import copy
import json
import unittest
from pathlib import Path

import numpy as np

from st_score_restore.stage11_v2a_consumer_adapter import (
    Stage11V2aConsumerAdapterError,
    axis_starts,
    build_tile_plan,
    normalize_grayscale,
    run_tiled_adapter,
    validate_consumer_adapter_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-consumer-adapter-evidence.v1.json"


class Stage11V2aConsumerAdapterTests(unittest.TestCase):
    def test_uint8_normalization_is_exact(self):
        value = np.array([[0, 127, 255]], dtype=np.uint8)
        normalized = normalize_grayscale(value)
        self.assertEqual(normalized.dtype, np.float32)
        self.assertAlmostEqual(float(normalized[0, 0]), 0.0)
        self.assertAlmostEqual(float(normalized[0, 2]), 1.0)

    def test_float_range_is_fail_closed(self):
        with self.assertRaises(Stage11V2aConsumerAdapterError):
            normalize_grayscale(np.array([[1.01]], dtype=np.float32))
        with self.assertRaises(Stage11V2aConsumerAdapterError):
            normalize_grayscale(np.array([[np.nan]], dtype=np.float32))

    def test_tiling_has_expected_overlap_and_coverage(self):
        self.assertEqual(axis_starts(512), [0])
        self.assertEqual(axis_starts(700), [0, 448])
        self.assertEqual(build_tile_plan(700, 900), [(0, 0), (0, 448), (448, 0), (448, 448)])

    def test_identity_patch_runner_preserves_arbitrary_shape(self):
        image = np.linspace(0.0, 1.0, 300 * 700, dtype=np.float32).reshape(300, 700)
        restored, metrics = run_tiled_adapter(image, lambda patch: patch.copy())
        self.assertEqual(restored.shape, image.shape)
        self.assertTrue(np.allclose(restored, image, atol=1e-7))
        self.assertEqual(metrics["tileCount"], 2)

    def test_real_synthetic_execution_evidence_passes(self):
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        result = validate_consumer_adapter_evidence(payload)
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["syntheticIntegrationValidated"])
        self.assertFalse(result["productionInferenceAuthorized"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_evidence_cannot_silently_authorize_production(self):
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        payload["authorization"]["productionInferenceAuthorized"] = True
        with self.assertRaises(Stage11V2aConsumerAdapterError):
            validate_consumer_adapter_evidence(payload)

    def test_evidence_package_identity_is_pinned(self):
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        payload["packageSha256"] = "0" * 64
        with self.assertRaises(Stage11V2aConsumerAdapterError):
            validate_consumer_adapter_evidence(payload)

    def test_heldout_access_cannot_be_hidden(self):
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        payload["heldOutAccessed"] = True
        with self.assertRaises(Stage11V2aConsumerAdapterError):
            validate_consumer_adapter_evidence(payload)


if __name__ == "__main__":
    unittest.main()
