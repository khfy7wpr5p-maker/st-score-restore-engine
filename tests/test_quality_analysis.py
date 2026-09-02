from __future__ import annotations

import hashlib
import unittest

import cv2
import numpy as np

from st_score_restore.quality_analysis import (
    ANALYZER_VERSION,
    CALIBRATION_STATE,
    FINDING_TYPES,
    QualityAnalysisConfig,
    QualityAnalysisError,
    analyze_quality_bytes,
)


def _encode_png(image: np.ndarray) -> bytes:
    ok, payload = cv2.imencode(".png", image)
    if not ok:
        raise AssertionError("PNG encoding failed")
    return bytes(payload)


def _encode_jpeg(image: np.ndarray, quality: int) -> bytes:
    ok, payload = cv2.imencode(
        ".jpg",
        image,
        [cv2.IMWRITE_JPEG_QUALITY, quality],
    )
    if not ok:
        raise AssertionError("JPEG encoding failed")
    return bytes(payload)


def _finding(report: dict, finding_type: str) -> dict:
    return next(item for item in report["findings"] if item["type"] == finding_type)


def _staff_page(width: int = 1000, height: int = 800) -> np.ndarray:
    image = np.full((height, width), 245, dtype=np.uint8)
    for start in (180, 430):
        for offset in range(5):
            y = start + offset * 12
            cv2.line(image, (80, y), (width - 80, y), 0, 2)
    for x in range(120, width - 100, 90):
        cv2.line(image, (x, 165), (x, 245), 30, 2)
        cv2.line(image, (x, 415), (x, 495), 30, 2)
    cv2.rectangle(image, (30, 30), (width - 31, height - 31), 80, 3)
    return image


def _tab_page(width: int = 1000, height: int = 800) -> np.ndarray:
    image = np.full((height, width), 245, dtype=np.uint8)
    for offset in range(6):
        y = 260 + offset * 14
        cv2.line(image, (70, y), (width - 70, y), 0, 2)
    return image


class QualityAnalysisTests(unittest.TestCase):
    def test_report_is_deterministic_and_source_bound(self):
        raw = _encode_png(_staff_page())
        first = analyze_quality_bytes(raw, source_name="staff.png")
        second = analyze_quality_bytes(raw, source_name="staff.png")

        self.assertEqual(first, second)
        self.assertEqual("analyzed", first["status"])
        self.assertEqual(ANALYZER_VERSION, first["analyzerVersion"])
        self.assertTrue(first["sourceReturnedUnmodified"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), first["sourceDigest"]["value"])
        self.assertEqual(CALIBRATION_STATE, first["calibration"]["state"])
        self.assertFalse(first["calibration"]["heldOutThresholdTuningUsed"])
        self.assertEqual(set(FINDING_TYPES), {item["type"] for item in first["findings"]})
        self.assertFalse(first["assertions"]["sourceBytesModified"])
        self.assertFalse(first["assertions"]["generativeOperationsUsed"])
        self.assertFalse(first["assertions"]["symbolCompletionUsed"])
        self.assertFalse(first["assertions"]["omrPerformed"])
        self.assertFalse(first["assertions"]["musicalCorrectnessAssessed"])
        self.assertFalse(first["assertions"]["trainingPermissionInferred"])
        self.assertFalse(first["assertions"]["calibrationPermissionInferred"])
        self.assertEqual(
            first["reportDigest"],
            second["reportDigest"],
        )

    def test_blur_metric_detects_strong_blur(self):
        source = _staff_page()
        sharp = analyze_quality_bytes(_encode_png(source), source_name="sharp.png")
        blurred_image = cv2.GaussianBlur(source, (31, 31), 8)
        blurred = analyze_quality_bytes(
            _encode_png(blurred_image),
            source_name="blurred.png",
        )

        self.assertGreater(
            sharp["metrics"]["blur"]["laplacianVariance"],
            blurred["metrics"]["blur"]["laplacianVariance"],
        )
        self.assertEqual("probable", _finding(blurred, "blur")["status"])

    def test_skew_metric_detects_rotated_staff_lines(self):
        image = _staff_page()
        height, width = image.shape
        matrix = cv2.getRotationMatrix2D((width / 2, height / 2), 2.0, 1.0)
        rotated = cv2.warpAffine(
            image,
            matrix,
            (width, height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=245,
        )
        report = analyze_quality_bytes(_encode_png(rotated), source_name="skew.png")
        metric = report["metrics"]["skew"]

        self.assertGreater(metric["lineCount"], 0)
        self.assertGreaterEqual(abs(metric["angleDegrees"]), 1.0)
        self.assertEqual("probable", _finding(report, "skew")["status"])

    def test_noise_metric_detects_deterministic_noise(self):
        source = _staff_page()
        rng = np.random.default_rng(12345)
        noise = rng.normal(0.0, 28.0, source.shape)
        noisy = np.clip(source.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        report = analyze_quality_bytes(_encode_png(noisy), source_name="noise.png")

        self.assertGreater(report["metrics"]["noise"]["residualP90"], 0.05)
        self.assertEqual("probable", _finding(report, "noise")["status"])

    def test_uneven_lighting_and_shadow_are_measured(self):
        width, height = 1000, 800
        gradient = np.tile(
            np.linspace(95, 245, width, dtype=np.float32),
            (height, 1),
        ).astype(np.uint8)
        for offset in range(5):
            cv2.line(gradient, (80, 300 + offset * 12), (920, 300 + offset * 12), 20, 2)
        report = analyze_quality_bytes(
            _encode_png(gradient),
            source_name="lighting.png",
        )

        self.assertGreater(
            report["metrics"]["unevenLighting"]["coefficientOfVariation"],
            0.14,
        )
        self.assertEqual("probable", _finding(report, "uneven_lighting")["status"])
        self.assertGreater(report["metrics"]["shadow"]["strength"], 0.10)

    def test_glare_metric_detects_large_clipped_patch(self):
        image = np.full((800, 1000), 180, dtype=np.uint8)
        cv2.rectangle(image, (600, 100), (980, 470), 255, -1)
        cv2.rectangle(image, (40, 40), (960, 760), 80, 3)
        report = analyze_quality_bytes(_encode_png(image), source_name="glare.png")

        self.assertGreater(report["metrics"]["glare"]["score"], 0.22)
        self.assertEqual("probable", _finding(report, "glare")["status"])

    def test_jpeg_quantization_detects_heavy_compression(self):
        source = _staff_page()
        high = analyze_quality_bytes(
            _encode_jpeg(source, 95),
            source_name="high.jpg",
        )
        low = analyze_quality_bytes(
            _encode_jpeg(source, 20),
            source_name="low.jpg",
        )

        high_metric = high["metrics"]["compression"]
        low_metric = low["metrics"]["compression"]
        self.assertTrue(low_metric["applicable"])
        self.assertGreater(
            low_metric["quantization"]["meanQuantization"],
            high_metric["quantization"]["meanQuantization"],
        )
        self.assertGreater(low_metric["score"], high_metric["score"])
        self.assertEqual("probable", _finding(low, "compression")["status"])

    def test_png_compression_finding_is_not_applicable(self):
        report = analyze_quality_bytes(
            _encode_png(_staff_page()),
            source_name="staff.png",
        )
        self.assertFalse(report["metrics"]["compression"]["applicable"])
        self.assertEqual("not_applicable", _finding(report, "compression")["status"])

    def test_staff_and_tab_visibility_are_geometric_evidence_only(self):
        staff = analyze_quality_bytes(_encode_png(_staff_page()), source_name="staff.png")
        tab = analyze_quality_bytes(_encode_png(_tab_page()), source_name="tab.png")

        self.assertGreaterEqual(staff["metrics"]["visibility"]["staffLikeGroupCount"], 1)
        self.assertEqual("observed", _finding(staff, "staff_visibility")["status"])
        self.assertGreaterEqual(tab["metrics"]["visibility"]["tabLikeGroupCount"], 1)
        self.assertEqual("observed", _finding(tab, "tab_visibility")["status"])
        self.assertTrue(tab["metrics"]["visibility"]["evidenceOnly"])
        self.assertFalse(tab["assertions"]["omrPerformed"])
        self.assertFalse(tab["assertions"]["musicalCorrectnessAssessed"])

    def test_digital_pdf_is_preserved_without_rasterization(self):
        pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj << /Type /Page /Font << >> >> endobj\n"
            b"%%EOF\n"
        )
        report = analyze_quality_bytes(pdf, source_name="digital.pdf")
        self.assertEqual("not_applicable_vector_pdf", report["status"])
        self.assertTrue(report["sourceReturnedUnmodified"])
        self.assertEqual({}, report["metrics"])
        self.assertFalse(report["assertions"]["sourceBytesModified"])

    def test_scanned_pdf_requires_stage3_renderer(self):
        pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj << /Type /Page /Subtype /Image >> endobj\n"
            b"%%EOF\n"
        )
        with self.assertRaises(QualityAnalysisError) as context:
            analyze_quality_bytes(pdf, source_name="scan.pdf")
        self.assertEqual("pdf_renderer_not_available", context.exception.code)

    def test_unknown_configuration_field_fails_closed(self):
        with self.assertRaises(QualityAnalysisError) as context:
            QualityAnalysisConfig.from_mapping({"invented_threshold": 1})
        self.assertEqual("invalid_configuration", context.exception.code)


if __name__ == "__main__":
    unittest.main()
