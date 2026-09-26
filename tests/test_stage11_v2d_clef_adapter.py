from __future__ import annotations

import unittest

import cv2
import numpy as np

from st_score_restore.stage11_v2d_clef_adapter import detect_tab_clef_markers, resolve_oemer_clef_candidates


class Stage11V2dClefAdapterTests(unittest.TestCase):
    def test_resolves_treble_and_bass_and_keeps_keys_separate(self) -> None:
        result = resolve_oemer_clef_candidates(
            [
                (80.0, 100.0, 98.0, 142.0),
                (82.0, 180.0, 93.0, 196.0),
                (108.0, 104.0, 118.0, 128.0),
                (350.0, 200.0, 355.0, 214.0),
            ],
            source_width=720,
            source_height=914,
        )

        self.assertEqual(["treble", "bass"], result["clefTypes"])
        self.assertEqual(2, len(result["clefBoxes"]))
        self.assertEqual([2, 3], result["keyCandidateIndexes"])
        self.assertGreater(result["clefBoxes"][0][2] - result["clefBoxes"][0][0], 18.0)
        self.assertGreater(result["clefBoxes"][1][3] - result["clefBoxes"][1][1], 28.0)

    def test_suppresses_nearby_follow_on_key_but_preserves_distant_parallel_clef(self) -> None:
        result = resolve_oemer_clef_candidates(
            [
                (84.0, 180.0, 98.0, 218.0),
                (107.0, 183.0, 118.0, 207.0),
                (146.0, 180.0, 159.0, 218.0),
            ],
            source_width=720,
            source_height=914,
        )

        self.assertEqual([0, 2], result["sourceCandidateIndexes"])
        self.assertEqual([1], result["keyCandidateIndexes"])

    def test_preserves_wide_parallel_bass_near_follow_on_boundary(self) -> None:
        result = resolve_oemer_clef_candidates(
            [
                (84.0, 668.0, 94.0, 684.0),
                (137.0, 668.0, 148.0, 684.5),
            ],
            source_width=720,
            source_height=914,
        )

        self.assertEqual([0, 1], result["sourceCandidateIndexes"])
        self.assertEqual(["bass", "bass"], result["clefTypes"])

    def test_expansion_is_clipped_to_source_bounds(self) -> None:
        result = resolve_oemer_clef_candidates(
            [(0.0, 0.0, 15.0, 35.0)],
            source_width=600,
            source_height=800,
        )

        self.assertEqual(1, len(result["clefBoxes"]))
        x1, y1, x2, y2 = result["clefBoxes"][0]
        self.assertEqual((0.0, 0.0), (x1, y1))
        self.assertLessEqual(x2, 600.0)
        self.assertLessEqual(y2, 800.0)

    def test_rejects_invalid_source_geometry(self) -> None:
        with self.assertRaises(ValueError):
            resolve_oemer_clef_candidates([], source_width=0, source_height=100)

    def test_detects_external_tab_marker_on_six_line_system(self) -> None:
        image = np.full((700, 520), 255, dtype=np.uint8)
        for index in range(6):
            cv2.line(image, (80, 100 + index * 12), (500, 100 + index * 12), 0, 1)
        cv2.putText(image, "TAB", (20, 136), cv2.FONT_HERSHEY_SIMPLEX, 0.45, 0, 1, cv2.LINE_8)

        result = detect_tab_clef_markers(image)

        self.assertEqual(["tab"], result["clefTypes"])
        self.assertEqual("external_horizontal", result["detections"][0]["layout"])

    def test_detects_embedded_vertical_tab_marker(self) -> None:
        image = np.full((1000, 620), 255, dtype=np.uint8)
        for index in range(6):
            cv2.line(image, (70, 90 + index * 25), (600, 90 + index * 25), 0, 1)
        for letter, y in zip("TAB", (118, 162, 206)):
            cv2.putText(image, letter, (82, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 0, 2, cv2.LINE_8)

        result = detect_tab_clef_markers(image)

        self.assertEqual(["tab"], result["clefTypes"])
        self.assertEqual("embedded_vertical", result["detections"][0]["layout"])

    def test_abstains_on_five_line_staff(self) -> None:
        image = np.full((220, 520), 255, dtype=np.uint8)
        for index in range(5):
            cv2.line(image, (60, 90 + index * 12), (500, 90 + index * 12), 0, 1)
        cv2.putText(image, "TAB", (15, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.45, 0, 1, cv2.LINE_8)

        result = detect_tab_clef_markers(image)

        self.assertEqual([], result["clefBoxes"])


if __name__ == "__main__":
    unittest.main()
