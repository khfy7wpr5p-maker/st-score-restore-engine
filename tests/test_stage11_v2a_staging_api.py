import copy
import json
import unittest
from pathlib import Path

import cv2
import numpy as np

from st_score_restore.stage11_v2a_staging_api import (
    Stage11V2aStagingApiError,
    decode_grayscale_png,
    encode_grayscale_png,
    process_staging_request,
    validate_request_metadata,
    validate_staging_api_evidence,
)
from st_score_restore.stage11_v2a_staging_api_current_truth import (
    Stage11V2aStagingApiCurrentTruthError,
    validate_stage11_v2a_staging_api_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-staging-api-evidence.v1.json"
TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_STAGING_API_CURRENT_TRUTH.json"


class Stage11V2aStagingApiTests(unittest.TestCase):
    def test_grayscale_png_roundtrip(self):
        image = np.arange(256, dtype=np.uint8).reshape(16, 16)
        encoded = encode_grayscale_png(image)
        decoded = decode_grayscale_png(encoded)
        self.assertTrue(np.array_equal(decoded, image))

    def test_color_png_fails_closed(self):
        image = np.zeros((8, 8, 3), dtype=np.uint8)
        ok, encoded = cv2.imencode(".png", image)
        self.assertTrue(ok)
        with self.assertRaises(Stage11V2aStagingApiError):
            decode_grayscale_png(encoded.tobytes())

    def test_request_metadata_rejects_real_user_kind(self):
        with self.assertRaises(Stage11V2aStagingApiError):
            validate_request_metadata({"requestId": "x", "sourceDataKind": "real_user"})

    def test_transport_adapter_preserves_shape_with_identity_restore(self):
        image = np.arange(400, dtype=np.uint8).reshape(20, 20)
        body = encode_grayscale_png(image)
        def restore(source):
            return source.astype(np.float32) / 255.0, {"tileCount": 1}
        response_body, meta = process_staging_request(
            body,
            {"requestId": "synthetic:test-1", "sourceDataKind": "synthetic_only"},
            restore,
        )
        self.assertEqual(decode_grayscale_png(response_body).shape, image.shape)
        self.assertEqual(meta["inputShape"], [20, 20])
        self.assertEqual(meta["outputShape"], [20, 20])
        self.assertFalse(meta["networkRouteRegistered"])
        self.assertFalse(meta["productionInferenceAuthorized"])

    def test_real_execution_evidence_passes(self):
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        result = validate_staging_api_evidence(payload)
        self.assertTrue(result["stagingRequestResponseValidated"])
        self.assertFalse(result["productionInferenceAuthorized"])
        self.assertFalse(result["realUserRolloutAuthorized"])

    def test_current_truth_passes(self):
        payload = json.loads(TRUTH.read_text(encoding="utf-8"))
        result = validate_stage11_v2a_staging_api_current_truth(payload)
        self.assertTrue(result["stagingRequestResponseValidated"])
        self.assertEqual(result["nextBoundary"], "shadow-mode-application-service-handoff")

    def test_truth_cannot_register_network_route(self):
        payload = json.loads(TRUTH.read_text(encoding="utf-8"))
        payload["safety"]["networkRouteRegistered"] = True
        with self.assertRaises(Stage11V2aStagingApiCurrentTruthError):
            validate_stage11_v2a_staging_api_current_truth(payload)

    def test_evidence_cannot_hide_real_user_data(self):
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        payload["realUserDataUsed"] = True
        with self.assertRaises(Stage11V2aStagingApiError):
            validate_staging_api_evidence(payload)


if __name__ == "__main__":
    unittest.main()
