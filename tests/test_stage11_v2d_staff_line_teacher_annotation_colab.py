from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cv2

import st_score_restore.stage11_v2d_staff_line_teacher_annotation_colab as mod


class StaffLineTeacherAnnotationColabTests(unittest.TestCase):
    def _raw_system(self, *, stroke_width: int = 2, status: str = "CONFIRMED"):
        return {
            "status": status,
            "strokeWidth": stroke_width,
            "lines": [
                {"lineIndex": 1, "centerlinePoints": [[10, 20], [90, 20]]},
                {"lineIndex": 2, "centerlinePoints": [[10, 30], [90, 30]]},
                {"lineIndex": 3, "centerlinePoints": [[10, 40], [90, 40]]},
                {"lineIndex": 4, "centerlinePoints": [[10, 50], [90, 50]]},
                {"lineIndex": 5, "centerlinePoints": [[10, 60], [90, 60]]},
            ],
        }

    def test_frozen_source_inventory_is_exactly_20_pages(self):
        self.assertEqual(20, len(mod.PAGE_IDS))
        self.assertEqual(set(mod.PAGE_IDS), set(mod.SOURCE_SHA256))
        self.assertEqual(
            {"beethoven-op48-no3-p1", "beethoven-op48-no3-p4"},
            mod.STAFF_ABSENT,
        )

    def test_sanitize_requires_five_top_to_bottom_lines(self):
        cleaned = mod._sanitize_systems([self._raw_system()], width=100, height=100)
        self.assertEqual(1, len(cleaned))
        self.assertEqual([1, 2, 3, 4, 5], [line["lineIndex"] for line in cleaned[0]["lines"]])
        self.assertEqual("CONFIRMED", cleaned[0]["status"])
        self.assertEqual(5, cleaned[0]["lineCount"])

        bad = self._raw_system()
        bad["lines"][0], bad["lines"][4] = bad["lines"][4], bad["lines"][0]
        with self.assertRaisesRegex(ValueError, "top-to-bottom"):
            mod._sanitize_systems([bad], width=100, height=100)

    def test_sanitize_rejects_out_of_bounds_points(self):
        bad = self._raw_system()
        bad["lines"][2]["centerlinePoints"][1] = [1000, 40]
        with self.assertRaisesRegex(ValueError, "outside source image"):
            mod._sanitize_systems([bad], width=100, height=100)

    def test_render_mask_is_binary_and_ambiguous_systems_do_not_enter_truth_mask(self):
        confirmed = mod._sanitize_systems([self._raw_system(stroke_width=2)], 100, 100)
        ambiguous = mod._sanitize_systems(
            [self._raw_system(stroke_width=2, status="AMBIGUOUS")], 100, 100
        )
        with tempfile.TemporaryDirectory() as tmp:
            mask_dir = Path(tmp)
            with mock.patch.object(mod, "MASK_DIR", mask_dir):
                rel, sha = mod._render_mask("page", 100, 100, confirmed + ambiguous)
            self.assertEqual("masks/page.png", rel)
            self.assertEqual(64, len(sha))
            image = cv2.imread(str(mask_dir / "page.png"), cv2.IMREAD_GRAYSCALE)
            self.assertIsNotNone(image)
            values = set(image.reshape(-1).tolist())
            self.assertTrue(values.issubset({0, 255}))
            self.assertIn(255, values)

    def test_js_is_source_only_and_has_explicit_empty_confirmation(self):
        js = mod._annotation_js('{"image":"data:image/jpeg;base64,AA==","pageId":"p","pageNo":1,"pageCount":20,"previewWidth":10,"previewHeight":10,"sourceWidth":10,"sourceHeight":10,"expectedStaffPresent":false,"existingSystems":[]}')
        self.assertIn("Bu sayfada standart porte yok", js)
        self.assertIn("Yalnız kaynak nota gösteriliyor", js)
        self.assertNotIn("restored_pages", js)
        self.assertNotIn("detector_pages", js)


if __name__ == "__main__":
    unittest.main()
