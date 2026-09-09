from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np

from st_score_restore.stage11_v2d_clef_source_qualification_colab import (
    PROGRESS_SCHEMA,
    SOURCE_TARGETS,
    _compute_page,
    _fingerprint,
    _load_progress,
    _page_descriptors,
    _teacher_boxes,
)
from st_score_restore.stage11_v2d_colab_runner import _detect_semantic_boxes
from st_score_restore.stage11_v2d_spatial_teacher_review import EXPECTED_PAGES


class Stage11V2dClefSourceQualificationColabTests(unittest.TestCase):
    def test_descriptors_match_exact_18_teacher_review_pages(self) -> None:
        descriptors = _page_descriptors()
        expected = [(source_id, page_number, page_id) for page_id, source_id, page_number in EXPECTED_PAGES]
        self.assertEqual(expected, descriptors)
        self.assertEqual(18, len(descriptors))
        self.assertNotIn("restore_model", SOURCE_TARGETS)
        self.assertTrue(all("restored" not in key.lower() for key in SOURCE_TARGETS))

    def test_teacher_boxes_preserve_completion_coordinates(self) -> None:
        page = {
            "clefBoxes": [
                {
                    "xMin": 10,
                    "yMin": 20,
                    "xMaxExclusive": 30,
                    "yMaxExclusive": 50,
                    "clefType": "soprano",
                }
            ]
        }
        self.assertEqual([[10.0, 20.0, 30.0, 50.0]], _teacher_boxes(page))

    def test_fingerprint_is_deterministic_and_binds_threshold_and_boxes(self) -> None:
        checkpoints = {"a": "1", "b": "2"}
        boxes = [[0.0, 0.0, 10.0, 10.0]]
        first = _fingerprint("page", "f" * 64, boxes, checkpoints)
        second = _fingerprint("page", "f" * 64, boxes, checkpoints)
        changed = _fingerprint("page", "f" * 64, [[0.0, 0.0, 11.0, 10.0]], checkpoints)
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)

    def test_compute_page_uses_source_clef_boxes_and_primary_iou_matching(self) -> None:
        teacher_page = {
            "clefBoxes": [
                {
                    "xMin": 0,
                    "yMin": 0,
                    "xMaxExclusive": 10,
                    "yMaxExclusive": 10,
                    "clefType": "treble",
                },
                {
                    "xMin": 20,
                    "yMin": 20,
                    "xMaxExclusive": 30,
                    "yMaxExclusive": 30,
                    "clefType": "soprano",
                },
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.png"
            source.write_bytes(b"source-only-test")
            detector_output = {
                "clef": [
                    (0.0, 0.0, 10.0, 10.0),
                    (21.0, 21.0, 31.0, 31.0),
                    (50.0, 50.0, 60.0, 60.0),
                ],
                "accidental": [(70.0, 10.0, 75.0, 20.0)],
            }
            with patch(
                "st_score_restore.stage11_v2d_clef_source_qualification_colab._detect_semantic_boxes",
                return_value=detector_output,
            ):
                record = _compute_page(
                    "bach",
                    "bach-anna-magdalena-p24",
                    source,
                    teacher_page,
                    object(),
                    {"unet_big/model.onnx": "a", "seg_net/model.onnx": "b"},
                )
        self.assertTrue(record["sourceOnly"])
        self.assertEqual(2, record["teacherBoxCount"])
        self.assertEqual(3, record["detectorBoxCount"])
        self.assertEqual((2, 1, 0), (record["tp"], record["fp"], record["fn"]))
        self.assertEqual(2, len(record["matches"]))
        self.assertEqual(1, record["keyCandidateCount"])
        self.assertEqual([[70.0, 10.0, 75.0, 20.0]], record["keyCandidateBoxes"])
        self.assertEqual("diagnostic_only_no_teacher_truth", record["keyMeasurementBoundary"])

    def test_semantic_boxes_are_normalized_to_source_image_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.png"
            self.assertTrue(cv2.imwrite(str(source), np.full((100, 200), 255, dtype=np.uint8)))

            def generate_pred(_path: str, use_tf: bool = False):
                self.assertFalse(use_tf)
                shape = (200, 400)
                staff = np.zeros(shape, dtype=np.uint8)
                symbols = np.zeros(shape, dtype=np.uint8)
                stems_rests = np.zeros(shape, dtype=np.uint8)
                notehead = np.zeros(shape, dtype=np.uint8)
                clefs_keys = np.zeros(shape, dtype=np.uint8)
                clefs_keys[60:90, 40:50] = 1
                clefs_keys[100:110, 100:105] = 1
                return staff, symbols, stems_rests, notehead, clefs_keys

            with patch(
                "st_score_restore.stage11_v2d_colab_runner.conservative_line_system_detector",
                return_value=[],
            ):
                boxes = _detect_semantic_boxes(source, generate_pred)

        self.assertEqual([(20.0, 30.0, 25.0, 45.0)], boxes["clef"])
        self.assertEqual([(50.0, 50.0, 52.5, 55.0)], boxes["accidental"])

    def test_progress_reuse_requires_exact_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "page.json"
            path.write_text(
                json.dumps({"schemaVersion": PROGRESS_SCHEMA, "fingerprint": "correct", "pageId": "p"}),
                encoding="utf-8",
            )
            self.assertIsNotNone(_load_progress(path, "correct"))
            self.assertIsNone(_load_progress(path, "wrong"))
            path.write_text("{broken", encoding="utf-8")
            self.assertIsNone(_load_progress(path, "correct"))


if __name__ == "__main__":
    unittest.main()
