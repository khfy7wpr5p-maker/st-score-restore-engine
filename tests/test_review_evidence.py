from __future__ import annotations

import hashlib
import unittest

import cv2
import numpy as np

from st_score_restore.review_evidence import ReviewEvidenceError, generate_review_evidence


def png(image: np.ndarray) -> bytes:
    ok, out = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    assert ok
    return bytes(out)


def artifact_id(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


class EvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        source = np.full((120, 200), 255, np.uint8)
        cv2.line(source, (10, 40), (190, 40), 0, 1)
        cv2.circle(source, (80, 60), 5, 0, -1)
        candidate = source.copy()
        candidate[56:65, 76:85] = 255
        self.source = png(source)
        self.candidate = png(candidate)
        self.report = {
            "status": "completed",
            "automaticApproval": False,
            "reportId": "safety-report:" + "1" * 64,
            "source": {
                "artifactId": artifact_id(self.source),
                "widthPixels": 200,
                "heightPixels": 120,
            },
            "candidate": {
                "artifactId": artifact_id(self.candidate),
                "widthPixels": 200,
                "heightPixels": 120,
            },
            "registration": {
                "method": "phase_correlation_translation",
                "resizedToSource": False,
                "translationX": 0.0,
                "translationY": 0.0,
                "response": 1.0,
                "reliable": True,
            },
            "findings": [
                {
                    "code": "symbol_loss_region",
                    "severity": "high",
                    "region": {
                        "x": 70,
                        "y": 50,
                        "width": 30,
                        "height": 30,
                        "normalized": {},
                    },
                    "semanticCertainty": "not_claimed",
                },
                {
                    "code": "registration_uncertain",
                    "severity": "medium",
                    "region": None,
                    "semanticCertainty": "not_claimed",
                },
            ],
        }

    def make(self):
        return generate_review_evidence(
            self.source,
            self.candidate,
            self.report,
            source_artifact_id=artifact_id(self.source),
            candidate_artifact_id=artifact_id(self.candidate),
            safety_report_artifact_id="sha256:" + "2" * 64,
            page_number=1,
            attempt_id="attempt_1",
        )

    def test_deterministic_and_binary_parent_integrity(self):
        one = self.make()
        two = self.make()
        self.assertEqual(one.bundle_bytes, two.bundle_bytes)
        self.assertEqual(
            [item.data for item in one.artifacts],
            [item.data for item in two.artifacts],
        )
        self.assertEqual(2, len(one.artifacts))
        self.assertEqual(
            artifact_id(one.artifacts[0].data),
            one.artifacts[0].artifact_id,
        )
        self.assertEqual("0.5.0", one.bundle["generatorVersion"])
        self.assertFalse(one.bundle["automaticApproval"])
        self.assertFalse(one.bundle["semanticRecognitionClaimed"])
        display = one.bundle["displayIntegrity"]
        self.assertEqual("grayscale_luminance_evidence", display["rendering"])
        self.assertEqual("not_inspected", display["inputColorProfiles"])
        self.assertFalse(display["colorManagementValidated"])
        self.assertNotIn("colorInterpretation", display)

    def test_regions_are_clipped_normalized_and_nonregional_preserved(self):
        result = self.make().bundle
        first = result["findings"][0]
        self.assertEqual(
            {"x": 46, "y": 26, "width": 78, "height": 78},
            first["cropBounds"],
        )
        self.assertEqual(0.35, first["normalizedRegion"]["x"])
        self.assertIsNone(result["findings"][1]["cropBounds"])
        self.assertEqual(1, result["navigation"]["regionalFindingCount"])

    def test_parent_mismatch_fails(self):
        with self.assertRaises(ReviewEvidenceError) as caught:
            generate_review_evidence(
                self.source,
                self.candidate,
                self.report,
                source_artifact_id="sha256:" + "0" * 64,
                candidate_artifact_id=artifact_id(self.candidate),
                safety_report_artifact_id="sha256:" + "2" * 64,
                page_number=1,
                attempt_id="a",
            )
        self.assertEqual("evidence_parent_mismatch", caught.exception.code)

    def test_no_regional_findings_produces_json_only_bundle(self):
        report = dict(self.report)
        report["findings"] = [self.report["findings"][1]]
        result = generate_review_evidence(
            self.source,
            self.candidate,
            report,
            source_artifact_id=artifact_id(self.source),
            candidate_artifact_id=artifact_id(self.candidate),
            safety_report_artifact_id="sha256:" + "2" * 64,
            page_number=1,
            attempt_id="a",
        )
        self.assertEqual((), result.artifacts)
        self.assertEqual(0, result.bundle["navigation"]["regionalFindingCount"])


if __name__ == "__main__":
    unittest.main()
