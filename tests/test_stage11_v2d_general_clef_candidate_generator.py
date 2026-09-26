from __future__ import annotations

import inspect
import unittest

import cv2
import numpy as np

from st_score_restore.stage11_v2d_general_clef_candidate_generator import (
    generate_general_clef_candidates,
)


class Stage11V2dGeneralClefCandidateGeneratorTests(unittest.TestCase):
    @staticmethod
    def _five_line_page(*, width: int = 600, height: int = 300, clef_x: int | None = 360) -> np.ndarray:
        image = np.full((height, width), 255, dtype=np.uint8)
        rows = [110, 120, 130, 140, 150]
        for y in rows:
            cv2.line(image, (30, y), (width - 30, y), 0, 2, cv2.LINE_8)
        if clef_x is not None:
            cv2.ellipse(image, (clef_x, 130), (9, 28), 15, 0, 310, 0, 4, cv2.LINE_8)
            cv2.line(image, (clef_x - 3, 92), (clef_x + 3, 170), 0, 3, cv2.LINE_8)
        return image

    @staticmethod
    def _six_line_page(*, width: int = 600, height: int = 300) -> np.ndarray:
        image = np.full((height, width), 255, dtype=np.uint8)
        for y in [100, 110, 120, 130, 140, 150]:
            cv2.line(image, (70, y), (width - 30, y), 0, 2, cv2.LINE_8)
        return image

    def test_blank_page_has_no_candidates(self) -> None:
        image = np.full((300, 600), 255, dtype=np.uint8)
        result = generate_general_clef_candidates(image)
        self.assertEqual([], result["candidates"])
        self.assertTrue(result["diagnostics"]["source_only"])
        self.assertFalse(result["diagnostics"]["teacher_metadata_used"])
        self.assertFalse(result["diagnostics"]["page_identity_used"])

    def test_five_line_mid_staff_symbol_generates_presence_candidate(self) -> None:
        result = generate_general_clef_candidates(self._five_line_page())
        candidates = result["candidates"]
        self.assertTrue(candidates)
        mid = [c for c in candidates if c["bbox"][0] > 250]
        self.assertTrue(mid, "mid-staff candidate must not be suppressed by page-position rules")
        self.assertTrue(any(c["clef_type_or_unknown"] == "unknown" for c in mid))
        self.assertTrue(any(c["candidate_provenance"].startswith("source-only:staff-relative") for c in mid))

    def test_output_is_deterministic_and_in_source_bounds(self) -> None:
        image = self._five_line_page()
        first = generate_general_clef_candidates(image)
        second = generate_general_clef_candidates(image.copy())
        self.assertEqual(first, second)
        for candidate in first["candidates"]:
            x1, y1, x2, y2 = candidate["bbox"]
            self.assertGreaterEqual(x1, 0.0)
            self.assertGreaterEqual(y1, 0.0)
            self.assertLessEqual(x2, image.shape[1])
            self.assertLessEqual(y2, image.shape[0])
            self.assertLess(x1, x2)
            self.assertLess(y1, y2)

    def test_six_line_topology_alone_never_forces_tab_subtype(self) -> None:
        result = generate_general_clef_candidates(self._six_line_page())
        typed_tab = [c for c in result["candidates"] if c["clef_type_or_unknown"] == "tab"]
        self.assertEqual([], typed_tab)

    def test_inference_signature_has_no_teacher_or_identity_channel(self) -> None:
        signature = inspect.signature(generate_general_clef_candidates)
        self.assertEqual(["source_image"], list(signature.parameters))
        forbidden = {
            "teacher",
            "teacher_boxes",
            "teacher_labels",
            "page_id",
            "filename",
            "source_family",
            "heldout",
            "holdout",
        }
        self.assertTrue(forbidden.isdisjoint(signature.parameters))


if __name__ == "__main__":
    unittest.main()
