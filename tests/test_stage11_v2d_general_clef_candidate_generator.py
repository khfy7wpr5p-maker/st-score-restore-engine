from __future__ import annotations

import inspect
import unittest

import cv2
import numpy as np

from st_score_restore.stage11_v2d_general_clef_candidate_generator import (
    generate_general_clef_candidates,
    normalize_oemer_candidate_box,
    oemer_prediction_shape_for_source,
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

    def test_oemer_resize_coordinates_normalize_to_source_pixels(self) -> None:
        prediction_shape = oemer_prediction_shape_for_source(
            source_width=675,
            source_height=860,
        )
        self.assertEqual((1698, 2164), prediction_shape)

        normalized = normalize_oemer_candidate_box(
            [382.0, 619.0, 412.0, 700.0],
            source_width=675,
            source_height=860,
            prediction_shape=prediction_shape,
        )

        expected = [
            151.85512367491165,
            245.9981515711645,
            163.78091872791518,
            278.1885397412199,
        ]
        for actual, wanted in zip(normalized, expected):
            self.assertAlmostEqual(wanted, actual, places=9)

    def test_oemer_geometry_types_treble_and_bass_and_rejects_thin_negative(self) -> None:
        image = self._five_line_page(clef_x=None)
        staff_systems = [
            {
                "staff_index": 0,
                "line_rows": [110.0, 120.0, 130.0, 140.0, 150.0],
                "x1": 30.0,
                "x2": 570.0,
            }
        ]
        result = generate_general_clef_candidates(
            image,
            oemer_candidate_boxes=[
                [330.0, 98.0, 357.0, 163.0],
                [40.0, 114.0, 60.0, 146.0],
                [90.0, 115.0, 98.0, 145.0],
            ],
            oemer_prediction_shape=(600, 300),
            staff_systems=staff_systems,
        )

        typed = [
            (item["clef_type_or_unknown"], item["candidate_provenance"])
            for item in result["candidates"]
            if item["clef_type_or_unknown"] in {"treble", "bass"}
        ]
        self.assertEqual(
            [
                ("bass", "source-only:oemer-staff-relative:bass"),
                ("treble", "source-only:oemer-staff-relative:treble"),
            ],
            sorted(typed),
        )
        self.assertEqual(2, result["diagnostics"]["typed_standard_candidate_count"])

    def test_oemer_treble_path_preserves_mid_staff_candidate(self) -> None:
        image = self._five_line_page(clef_x=None)
        result = generate_general_clef_candidates(
            image,
            oemer_candidate_boxes=[[340.0, 98.0, 367.0, 163.0]],
            oemer_prediction_shape=(600, 300),
            staff_systems=[
                {
                    "staff_index": 0,
                    "line_rows": [110.0, 120.0, 130.0, 140.0, 150.0],
                    "x1": 30.0,
                    "x2": 570.0,
                }
            ],
        )

        treble = [
            item
            for item in result["candidates"]
            if item["clef_type_or_unknown"] == "treble"
        ]
        self.assertEqual(1, len(treble))
        self.assertGreater(treble[0]["bbox"][0], 300.0)

    def test_inference_signature_has_no_teacher_or_identity_channel(self) -> None:
        signature = inspect.signature(generate_general_clef_candidates)
        self.assertEqual(
            [
                "source_image",
                "oemer_candidate_boxes",
                "oemer_prediction_shape",
                "staff_systems",
            ],
            list(signature.parameters),
        )
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
