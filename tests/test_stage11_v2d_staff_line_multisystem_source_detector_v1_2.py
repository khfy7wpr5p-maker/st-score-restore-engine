from __future__ import annotations

import hashlib
import inspect
import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from st_score_restore import stage11_v2d_staff_line_multisystem_source_detector_v1_1 as parent
from st_score_restore import stage11_v2d_staff_line_multisystem_source_detector_v1_2 as mod


class StaffLineMultiSystemSourceDetectorV12Tests(unittest.TestCase):
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

    @staticmethod
    def _parent_plus_broken_system() -> np.ndarray:
        image = StaffLineMultiSystemSourceDetectorV12Tests._page(systems=[(80, 12)])
        top, spacing = 300, 12
        for index in range(5):
            y = top + index * spacing
            for left, right in ((90, 296), (306, 512), (522, 728)):
                cv2.line(image, (left, y), (right, y), 0, 1, cv2.LINE_8)
        for x in (250, 600):
            cv2.line(image, (x, top - 5), (x, top + spacing * 4 + 5), 0, 1, cv2.LINE_8)
        return image

    def test_preserves_parent_multisystem_behavior(self):
        detections = mod.detect_staff_systems(self._page(systems=[(80, 11), (300, 13)]))
        self.assertEqual(2, len(detections))
        self.assertEqual([1, 2], [item.system_index for item in detections])
        self.assertTrue(all(len(item.lines) == 5 for item in detections))
        self.assertTrue(all(item.detector_version == mod.DETECTOR_VERSION for item in detections))
        self.assertTrue(all([line.center_y for line in item.lines] == sorted(line.center_y for line in item.lines) for item in detections))

    def test_recovers_broken_source_staff_parent_v11_misses(self):
        image = self._parent_plus_broken_system()
        parent_detections = parent.detect_staff_systems(image)
        detections, diagnostics = mod.detect_staff_systems_with_diagnostics(image)
        self.assertEqual(1, len(parent_detections))
        self.assertEqual(2, len(detections))
        self.assertEqual(1, diagnostics['recovery']['acceptedRecoveryCount'])
        recovered = [item for item in detections if 'parent-anchored' in item.provenance]
        self.assertEqual(1, len(recovered))
        self.assertAlmostEqual(300.0, recovered[0].lines[0].center_y, delta=2.0)

    def test_rejects_six_line_tab_like_system(self):
        detections, diagnostics = mod.detect_staff_systems_with_diagnostics(self._page(six_line=True))
        self.assertEqual([], detections)
        self.assertTrue(diagnostics['recovery']['recoveryDisabledWithoutSourceSupportedParent'])

    def test_blank_and_decorative_only_pages_abstain(self):
        blank = np.full((300, 500), 255, dtype=np.uint8)
        self.assertEqual([], mod.detect_staff_systems(blank))
        decorative = blank.copy()
        for y, left, right in ((60, 40, 160), (95, 240, 450), (160, 80, 300), (230, 180, 470)):
            cv2.line(decorative, (left, y), (right, y), 0, 2, cv2.LINE_8)
        self.assertEqual([], mod.detect_staff_systems(decorative))

    def test_cross_staff_candidates_do_not_replace_parent_spacing(self):
        detections = mod.detect_staff_systems(self._page(systems=[(70, 8), (300, 8)]))
        self.assertEqual(2, len(detections))
        self.assertTrue(all(item.staff_spacing < 16 for item in detections))

    def test_deterministic_and_no_teacher_restored_or_page_channel(self):
        image = self._parent_plus_broken_system()
        first, first_diag = mod.detect_staff_systems_with_diagnostics(image)
        second, second_diag = mod.detect_staff_systems_with_diagnostics(image.copy())
        self.assertEqual([item.as_dict() for item in first], [item.as_dict() for item in second])
        self.assertEqual(first_diag, second_diag)
        sig = inspect.signature(mod.detect_staff_systems)
        self.assertEqual(['image', 'config'], list(sig.parameters))
        self.assertEqual(inspect.Parameter.KEYWORD_ONLY, sig.parameters['config'].kind)
        self.assertTrue(first_diag['sourceOnly'])
        for key in ('teacherCoordinatesUsed', 'restoredOutputsUsed', 'heldOutAccessed', 'trainingUsed', 'pageIdentityUsed', 'pageSpecificRulesUsed'):
            self.assertFalse(first_diag[key])

    def test_freeze_repeatability_and_identity_mismatch_fail_closed(self):
        image = self._parent_plus_broken_system()
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
            with self.assertRaises(mod.StaffLineMultiSystemDetectorV12Error):
                mod.freeze_source_folder(source, root / 'bad.json', expected_source_sha256={page.name: '0' * 64})

    def test_invalid_config_fails_closed(self):
        with self.assertRaises(mod.StaffLineMultiSystemDetectorV12Error):
            mod.detect_staff_systems(self._page(systems=[(100, 12)]), config=mod.DetectorConfig(recovery_width_factor=0.95))


if __name__ == '__main__':
    unittest.main()
