from __future__ import annotations

from copy import deepcopy
import unittest

import cv2
import numpy as np

from st_score_restore.music_safety_validator import (
    MusicSafetyValidationError,
    compare_candidate_reports,
    record_teacher_review,
    validate_candidate,
)


def encode_png(image: np.ndarray) -> bytes:
    success, payload = cv2.imencode(
        ".png",
        image,
        [cv2.IMWRITE_PNG_COMPRESSION, 9],
    )
    assert success
    return bytes(payload)


def synthetic_score() -> np.ndarray:
    image = np.full((900, 1200), 250, np.uint8)
    for base in (120, 360):
        for index in range(5):
            cv2.line(
                image,
                (80, base + index * 16),
                (1120, base + index * 16),
                20,
                1,
            )
        cv2.circle(image, (220, base + 32), 6, 0, -1)
        cv2.line(image, (226, base + 32), (226, base - 4), 0, 2)
    tab_base = 650
    for index in range(6):
        cv2.line(
            image,
            (80, tab_base + index * 18),
            (1120, tab_base + index * 18),
            30,
            1,
        )
    cv2.putText(
        image,
        "3",
        (280, tab_base + 58),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        0,
        1,
        cv2.LINE_8,
    )
    return image


class MusicSafetyHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source_image = synthetic_score()
        self.source = encode_png(self.source_image)

    def test_page_without_recognized_system_requires_review(self) -> None:
        blank = encode_png(np.full((300, 400), 250, np.uint8))
        report = validate_candidate(blank, blank)
        self.assertEqual("review_required", report["verdict"])
        self.assertIn(
            "no_recognized_music_systems",
            report["decision"]["reviewRequiredReasons"],
        )

    def test_lightened_symbol_uses_source_threshold_and_is_detected(self) -> None:
        candidate = self.source_image.copy()
        candidate[140:165, 210:240] = np.maximum(
            candidate[140:165, 210:240],
            210,
        )
        report = validate_candidate(self.source, encode_png(candidate))
        self.assertGreater(report["metrics"]["symbols"]["lostDarkPixels"], 0)
        self.assertIn(report["verdict"], {"review_required", "reject"})

    def test_decoded_pixel_limit_fails_safe(self) -> None:
        with self.assertRaises(MusicSafetyValidationError) as context:
            validate_candidate(
                self.source,
                self.source,
                config={"max_decode_pixels": 100_000},
            )
        self.assertEqual(
            "source_decoded_image_too_large",
            context.exception.code,
        )
        self.assertEqual("review_required", context.exception.to_dict()["verdict"])

    def test_comparator_rejects_mixed_sources(self) -> None:
        first = validate_candidate(self.source, self.source)
        other_image = self.source_image.copy()
        other_image[10, 10] = 0
        other = encode_png(other_image)
        second = validate_candidate(other, other)
        with self.assertRaises(MusicSafetyValidationError) as context:
            compare_candidate_reports([first, second])
        self.assertEqual("candidate_source_mismatch", context.exception.code)

    def test_comparator_ignores_tampered_rank_fields(self) -> None:
        passed = validate_candidate(self.source, self.source)
        candidate = self.source_image.copy()
        cv2.rectangle(candidate, (210, 130), (245, 175), 250, -1)
        reviewed = validate_candidate(self.source, encode_png(candidate))
        self.assertNotEqual("pass", reviewed["verdict"])
        tampered = deepcopy(reviewed)
        tampered["comparator"] = {
            "eligible": True,
            "tier": 0,
            "riskScore": 0,
        }
        comparison = compare_candidate_reports([tampered, passed])
        self.assertEqual(
            passed["candidate"]["artifactId"],
            comparison["recommendedCandidateArtifactId"],
        )

    def test_teacher_review_rejects_unvalidated_report(self) -> None:
        with self.assertRaises(MusicSafetyValidationError) as context:
            record_teacher_review(
                {"status": "failed", "automaticApproval": False},
                "approved",
                reviewer_id="teacher-1",
            )
        self.assertEqual("invalid_candidate_report", context.exception.code)


if __name__ == "__main__":
    unittest.main()
