from __future__ import annotations

import hashlib
import inspect
import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from st_score_restore import stage11_v2d_staff_line_multisystem_source_detector_v1_2 as parent
from st_score_restore import stage11_v2d_staff_line_multisystem_source_detector_v1_3 as mod


class StaffLineMultiSystemSourceDetectorV13Tests(unittest.TestCase):
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
        image = StaffLineMultiSystemSourceDetectorV13Tests._page(systems=[(80, 12)])
        top, spacing = 300, 12
        for index in range(5):
            y = top + index * spacing
            for left, right in ((90, 296), (306, 512), (522, 728)):
                cv2.line(image, (left, y), (right, y), 0, 1, cv2.LINE_8)
        for x in (250, 600):
            cv2.line(image, (x, top - 5), (x, top + spacing * 4 + 5), 0, 1, cv2.LINE_8)
        return image

    @staticmethod
    def _detection(spacing: float, provenance: str, top: float) -> mod.StaffSystemDetection:
        lines = tuple(
            mod.StaffLineDetection(
                index + 1,
                top + index * spacing,
                (90, 730),
                ((90, int(round(top + index * spacing)), 730, int(round(top + index * spacing))),),
            )
            for index in range(5)
        )
        return mod.StaffSystemDetection(
            0,
            (90, int(top - 4), 730, int(top + 4 * spacing + 5)),
            spacing,
            0.90,
            lines,
            provenance,
            parent.DETECTOR_VERSION,
        )

    def test_spacing_consensus_preserves_anchors_and_suppresses_weak_outlier(self):
        anchor = "source-only:v1.2-parent-preserved:source-only:v1-compatibility+v1.1-local-spacing-topology"
        weak = "source-only:v1.2-parent-anchored-horizontal-template"
        detections = [
            self._detection(10.0, anchor, 40),
            self._detection(10.2, anchor, 120),
            self._detection(10.5, weak, 200),
            self._detection(16.0, weak, 300),
        ]
        kept, diagnostics = mod._apply_spacing_consensus(detections, mod.SpacingConsensusConfig())
        self.assertEqual(3, len(kept))
        self.assertEqual([1, 2, 3], [item.system_index for item in kept])
        self.assertEqual(mod.DETECTOR_VERSION, kept[-1].detector_version)
        self.assertEqual(1, diagnostics["suppressedWeakSystemCount"])
        self.assertEqual("anchor-grade-median", diagnostics["referenceSpacingSource"])

    def test_no_anchor_uses_source_candidate_median_and_single_candidate_fails_open(self):
        weak = "source-only:v1.2-parent-preserved:source-only:v1.1-skew-tolerant-horizontal-segment"
        three = [
            self._detection(10.0, weak, 40),
            self._detection(10.2, weak, 120),
            self._detection(16.0, weak, 220),
        ]
        kept, diagnostics = mod._apply_spacing_consensus(three, mod.SpacingConsensusConfig())
        self.assertEqual(2, len(kept))
        self.assertEqual("all-source-candidate-median", diagnostics["referenceSpacingSource"])
        one, one_diag = mod._apply_spacing_consensus([three[0]], mod.SpacingConsensusConfig())
        self.assertEqual(1, len(one))
        self.assertEqual("insufficient-source-consensus-fail-open", one_diag["referenceSpacingSource"])

    def test_preserves_true_multisystem_five_line_order(self):
        detections = mod.detect_staff_systems(self._page(systems=[(80, 11), (300, 13)]))
        self.assertEqual(2, len(detections))
        self.assertEqual([1, 2], [item.system_index for item in detections])
        self.assertTrue(all(len(item.lines) == 5 for item in detections))
        self.assertTrue(all(item.detector_version == mod.DETECTOR_VERSION for item in detections))
        self.assertTrue(all([line.center_y for line in item.lines] == sorted(line.center_y for line in item.lines) for item in detections))

    def test_faint_broken_recovery_is_not_lost_when_spacing_agrees(self):
        image = self._parent_plus_broken_system()
        detections = mod.detect_staff_systems(image)
        self.assertEqual(2, len(detections))
        recovered = [item for item in detections if "parent-anchored" in item.provenance]
        self.assertEqual(1, len(recovered))
        self.assertAlmostEqual(300.0, recovered[0].lines[0].center_y, delta=2.0)

    def test_six_line_tab_blank_and_decorative_negatives_abstain(self):
        self.assertEqual([], mod.detect_staff_systems(self._page(six_line=True)))
        blank = np.full((300, 500), 255, dtype=np.uint8)
        self.assertEqual([], mod.detect_staff_systems(blank))
        decorative = blank.copy()
        for y, left, right in ((60, 40, 160), (95, 240, 450), (160, 80, 300), (230, 180, 470)):
            cv2.line(decorative, (left, y), (right, y), 0, 2, cv2.LINE_8)
        self.assertEqual([], mod.detect_staff_systems(decorative))

    def test_deterministic_and_has_no_teacher_holdout_page_identity_channel(self):
        image = self._parent_plus_broken_system()
        first, first_diag = mod.detect_staff_systems_with_diagnostics(image)
        second, second_diag = mod.detect_staff_systems_with_diagnostics(image.copy())
        self.assertEqual([item.as_dict() for item in first], [item.as_dict() for item in second])
        self.assertEqual(first_diag, second_diag)
        sig = inspect.signature(mod.detect_staff_systems)
        self.assertEqual(["image", "parent_config", "consensus_config"], list(sig.parameters))
        self.assertEqual(inspect.Parameter.KEYWORD_ONLY, sig.parameters["parent_config"].kind)
        self.assertEqual(inspect.Parameter.KEYWORD_ONLY, sig.parameters["consensus_config"].kind)
        self.assertTrue(first_diag["sourceOnly"])
        for key in ("teacherCoordinatesUsed", "restoredOutputsUsed", "heldOutAccessed", "trainingUsed", "pageIdentityUsed", "pageSpecificRulesUsed"):
            self.assertFalse(first_diag[key])

    def test_freeze_repeatability_and_source_identity_mismatch_fail_closed(self):
        image = self._parent_plus_broken_system()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            page = source / "page-a.png"
            self.assertTrue(cv2.imwrite(str(page), image))
            source_sha = hashlib.sha256(page.read_bytes()).hexdigest()
            a, b = root / "a.json", root / "b.json"
            first = mod.freeze_source_folder(source, a, expected_source_sha256={page.name: source_sha})
            second = mod.freeze_source_folder(source, b, expected_source_sha256={page.name: source_sha})
            self.assertEqual(first["artifactSha256"], second["artifactSha256"])
            self.assertEqual(a.read_bytes(), b.read_bytes())
            artifact = json.loads(a.read_text(encoding="utf-8"))
            self.assertEqual(1, artifact["sourceIdentityExpectedCount"])
            self.assertEqual(1, artifact["sourceIdentityMatchedCount"])
            self.assertTrue(artifact["sourceOnly"])
            self.assertFalse(artifact["teacherArtifactLoadedDuringInference"])
            self.assertFalse(artifact["heldOutAccessed"])
            self.assertFalse(artifact["pageSpecificRulesUsed"])
            self.assertTrue(all(value is False for value in artifact["claimBoundary"].values()))
            with self.assertRaises(mod.StaffLineMultiSystemDetectorV13Error):
                mod.freeze_source_folder(source, root / "bad.json", expected_source_sha256={page.name: "0" * 64})

    def test_frozen_parent_transform_is_repeatable_and_rejects_identity_mismatch(self):
        anchor = "source-only:v1.2-parent-preserved:source-only:v1-compatibility+v1.1-local-spacing-topology"
        weak = "source-only:v1.2-parent-anchored-horizontal-template"
        systems = [
            self._detection(10.0, anchor, 40).as_dict(),
            self._detection(10.2, anchor, 120).as_dict(),
            self._detection(16.0, weak, 220).as_dict(),
        ]
        parent_payload = {
            "detectorVersion": parent.DETECTOR_VERSION,
            "sourceOnly": True,
            "teacherArtifactLoadedDuringInference": False,
            "teacherCoordinatesUsedDuringInference": False,
            "restoredOutputsLoadedDuringInference": False,
            "heldOutAccessed": False,
            "pageSpecificRulesUsed": False,
            "detectorSourceSha256": "1" * 64,
            "sourceIdentityExpectedCount": 1,
            "sourceIdentityMatchedCount": 1,
            "pages": [{
                "pageId": "dev-a",
                "sourceFileName": "dev-a.png",
                "sourceSha256": "2" * 64,
                "width": 820,
                "height": 520,
                "systems": systems,
                "diagnostics": {},
            }],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parent_path = root / "parent.json"
            parent_path.write_text(json.dumps(parent_payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            parent_sha = hashlib.sha256(parent_path.read_bytes()).hexdigest()
            a, b = root / "a.json", root / "b.json"
            first = mod.freeze_frozen_parent_artifact(parent_path, a, expected_parent_artifact_sha256=parent_sha)
            second = mod.freeze_frozen_parent_artifact(parent_path, b, expected_parent_artifact_sha256=parent_sha)
            self.assertEqual(first["artifactSha256"], second["artifactSha256"])
            self.assertEqual(a.read_bytes(), b.read_bytes())
            artifact = json.loads(a.read_text(encoding="utf-8"))
            self.assertEqual(2, artifact["pages"][0]["systemCount"])
            self.assertEqual(1, artifact["suppressedWeakSystemCount"])
            self.assertFalse(artifact["teacherArtifactLoadedDuringInference"])
            with self.assertRaises(mod.StaffLineMultiSystemDetectorV13Error):
                mod.freeze_frozen_parent_artifact(parent_path, root / "bad.json", expected_parent_artifact_sha256="0" * 64)

    def test_invalid_consensus_config_fails_closed(self):
        with self.assertRaises(mod.StaffLineMultiSystemDetectorV13Error):
            mod.detect_staff_systems(
                self._page(systems=[(100, 12)]),
                consensus_config=mod.SpacingConsensusConfig(weak_spacing_ratio_min=1.01),
            )


if __name__ == "__main__":
    unittest.main()
