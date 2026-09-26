from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from st_score_restore import stage11_v2d_staff_line_multisystem_source_detector_v1_1 as mod


class StaffLineMultiSystemSourceDetectorV11Tests(unittest.TestCase):
    @staticmethod
    def _page(*, systems: list[tuple[int, int]] | None = None, six_line: bool = False) -> np.ndarray:
        image = np.full((520, 820), 255, dtype=np.uint8)
        if six_line:
            for index in range(6):
                y = 100 + index * 12
                cv2.line(image, (90, y), (730, y), 0, 2, cv2.LINE_8)
            for x in (220, 410, 620):
                cv2.line(image, (x, 94), (x, 172), 0, 2, cv2.LINE_8)
            return image
        for top, spacing in systems or []:
            for index in range(5):
                y = top + index * spacing
                cv2.line(image, (90, y), (730, y), 0, 2, cv2.LINE_8)
            for x in (220, 410, 620):
                cv2.line(image, (x, top - 8), (x, top + spacing * 4 + 8), 0, 2, cv2.LINE_8)
            cv2.circle(image, (410, top + spacing * 2), 5, 0, -1)
        return image

    def test_detects_multiple_five_line_systems(self):
        detections = mod.detect_staff_systems(self._page(systems=[(80, 11), (300, 13)]))
        self.assertEqual(2, len(detections))
        self.assertEqual([1, 2], [item.system_index for item in detections])
        self.assertTrue(all(len(item.lines) == 5 for item in detections))
        self.assertTrue(all(item.detector_version == mod.DETECTOR_VERSION for item in detections))

    def test_rejects_six_line_tab_like_system(self):
        self.assertEqual([], mod.detect_staff_systems(self._page(six_line=True)))

    def test_blank_page_abstains(self):
        self.assertEqual([], mod.detect_staff_systems(np.full((300, 500), 255, dtype=np.uint8)))

    def test_cross_staff_candidates_do_not_replace_local_spacing(self):
        detections = mod.detect_staff_systems(self._page(systems=[(70, 8), (300, 8)]))
        self.assertEqual(2, len(detections))
        self.assertTrue(all(item.staff_spacing < 16 for item in detections))

    def test_deterministic_and_no_page_or_teacher_identity_channel(self):
        image = self._page(systems=[(90, 10), (280, 12)])
        first, first_diag = mod.detect_staff_systems_with_diagnostics(image)
        second, second_diag = mod.detect_staff_systems_with_diagnostics(image.copy())
        self.assertEqual([item.as_dict() for item in first], [item.as_dict() for item in second])
        self.assertEqual(first_diag, second_diag)
        self.assertEqual(('image',), mod.detect_staff_systems.__code__.co_varnames[:mod.detect_staff_systems.__code__.co_argcount])
        self.assertTrue(first_diag['sourceOnly'])
        self.assertFalse(first_diag['teacherCoordinatesUsed'])
        self.assertFalse(first_diag['restoredOutputsUsed'])
        self.assertFalse(first_diag['pageIdentityUsed'])

    def test_freeze_is_repeatable_and_non_authorizing(self):
        image = self._page(systems=[(100, 12)])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source'
            source.mkdir()
            page = source / 'page-a.png'
            self.assertTrue(cv2.imwrite(str(page), image))
            source_sha = hashlib.sha256(page.read_bytes()).hexdigest()
            first_path = root / 'a.json'
            second_path = root / 'b.json'
            first = mod.freeze_source_folder(source, first_path, expected_source_sha256={page.name: source_sha})
            second = mod.freeze_source_folder(source, second_path, expected_source_sha256={page.name: source_sha})
            self.assertEqual(first['artifactSha256'], second['artifactSha256'])
            self.assertEqual(first_path.read_bytes(), second_path.read_bytes())
            artifact = json.loads(first_path.read_text(encoding='utf-8'))
            self.assertEqual(1, artifact['sourceIdentityExpectedCount'])
            self.assertEqual(1, artifact['sourceIdentityMatchedCount'])
            self.assertTrue(artifact['sourceOnly'])
            self.assertFalse(artifact['teacherArtifactLoadedDuringInference'])
            self.assertFalse(artifact['restoredOutputsLoadedDuringInference'])
            self.assertFalse(artifact['heldOutAccessed'])
            self.assertFalse(artifact['trainingOrFineTuningPerformed'])
            self.assertFalse(artifact['pageSpecificRulesUsed'])
            self.assertTrue(all(value is False for value in artifact['claimBoundary'].values()))
            self.assertEqual(first['artifactSha256'], Path(str(first_path) + '.sha256').read_text().strip())

    def test_invalid_config_fails_closed(self):
        with self.assertRaises(mod.StaffLineMultiSystemDetectorV11Error):
            mod.detect_staff_systems(
                self._page(systems=[(100, 12)]),
                config=mod.DetectorConfig(min_spacing_px=80, max_spacing_px=20),
            )


if __name__ == '__main__':
    unittest.main()
