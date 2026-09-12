from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from st_score_restore import stage11_v2d_staff_line_multisystem_source_detector as mod


class StaffLineMultiSystemSourceDetectorTests(unittest.TestCase):
    @staticmethod
    def _page(*, systems: list[tuple[int, int]] | None = None, six_line: bool = False) -> np.ndarray:
        image = np.full((520, 820), 255, dtype=np.uint8)
        if six_line:
            for index in range(6):
                y = 100 + index * 12
                cv2.line(image, (90, y), (730, y), 0, 2, cv2.LINE_8)
            return image
        for top, spacing in systems or []:
            for index in range(5):
                y = top + index * spacing
                cv2.line(image, (90, y), (730, y), 0, 2, cv2.LINE_8)
            # Add staff-crossing symbol-like ink to ensure the detector does not depend
            # on pristine uninterrupted synthetic lines.
            cv2.line(image, (250, top - 8), (250, top + spacing * 4 + 8), 0, 3, cv2.LINE_8)
            cv2.circle(image, (250, top + spacing * 2), 6, 0, -1)
        return image

    def test_detects_multiple_standard_staff_systems(self):
        image = self._page(systems=[(80, 11), (300, 13)])
        detections = mod.detect_staff_systems(image)
        self.assertEqual(2, len(detections))
        self.assertEqual([1, 2], [item.system_index for item in detections])
        self.assertLess(detections[0].bbox[1], detections[1].bbox[1])
        for detection in detections:
            self.assertEqual(5, len(detection.lines))
            self.assertTrue(all(line.line_index == index for index, line in enumerate(detection.lines, start=1)))
            self.assertTrue(0.5 <= detection.confidence <= 0.99)

    def test_rejects_six_equally_spaced_tab_like_system(self):
        image = self._page(six_line=True)
        self.assertEqual([], mod.detect_staff_systems(image))

    def test_line_output_uses_source_supported_extent_not_full_width(self):
        image = self._page(systems=[(120, 12)])
        detection = mod.detect_staff_systems(image)[0]
        self.assertGreater(detection.bbox[0], 0)
        self.assertLess(detection.bbox[2], image.shape[1])
        for line in detection.lines:
            self.assertGreaterEqual(line.x_extent[0], 80)
            self.assertLessEqual(line.x_extent[1], 740)
            self.assertTrue(line.segments)

    def test_blank_page_abstains(self):
        image = np.full((300, 500), 255, dtype=np.uint8)
        self.assertEqual([], mod.detect_staff_systems(image))

    def test_detector_is_deterministic_and_has_no_page_identity_input(self):
        image = self._page(systems=[(90, 10), (280, 12)])
        first = [item.as_dict() for item in mod.detect_staff_systems(image)]
        second = [item.as_dict() for item in mod.detect_staff_systems(image.copy())]
        self.assertEqual(first, second)
        self.assertNotIn("page_id", mod.detect_staff_systems.__code__.co_varnames[: mod.detect_staff_systems.__code__.co_argcount])

    def test_source_folder_freeze_is_non_authorizing_and_repeatable(self):
        image = self._page(systems=[(100, 12)])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "source"
            source_dir.mkdir()
            source_path = source_dir / "page-a.png"
            self.assertTrue(cv2.imwrite(str(source_path), image))
            first_path = root / "raw-a.json"
            second_path = root / "raw-b.json"
            first = mod.freeze_source_folder(source_dir, first_path)
            second = mod.freeze_source_folder(source_dir, second_path)
            self.assertEqual(first["artifactSha256"], second["artifactSha256"])
            artifact = json.loads(first_path.read_text(encoding="utf-8"))
            self.assertTrue(artifact["sourceOnly"])
            self.assertFalse(artifact["teacherArtifactLoadedDuringInference"])
            self.assertFalse(artifact["restoredOutputsLoadedDuringInference"])
            self.assertFalse(artifact["heldOutAccessed"])
            self.assertFalse(artifact["trainingOrFineTuningPerformed"])
            self.assertEqual(mod.DETECTOR_VERSION, artifact["detectorVersion"])
            self.assertEqual(1, artifact["pageCount"])
            self.assertEqual(1, artifact["pages"][0]["systemCount"])
            for value in artifact["claimBoundary"].values():
                self.assertFalse(value)
            self.assertEqual(
                first["artifactSha256"],
                Path(str(first_path) + ".sha256").read_text(encoding="utf-8").strip(),
            )

    def test_invalid_config_fails_closed(self):
        with self.assertRaises(mod.StaffLineMultiSystemDetectorError):
            mod.detect_staff_systems(
                self._page(systems=[(100, 12)]),
                config=mod.DetectorConfig(min_spacing_px=80, max_spacing_px=20),
            )


if __name__ == "__main__":
    unittest.main()
