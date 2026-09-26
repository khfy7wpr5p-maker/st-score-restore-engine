from __future__ import annotations

import hashlib
import inspect
import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from st_score_restore import stage11_v2d_staff_line_multisystem_source_detector_v1_3 as parent
from st_score_restore import stage11_v2d_staff_line_multisystem_source_detector_v1_4 as mod


class StaffLineMultiSystemSourceDetectorV14Tests(unittest.TestCase):
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
    def _detection(
        *,
        spacing: float = 10.0,
        top: float = 40.0,
        left: int = 90,
        right: int = 730,
        confidence: float = 0.95,
        provenance: str = "source-only:v1.2-parent-anchored-horizontal-template",
    ) -> mod.StaffSystemDetection:
        lines = tuple(
            mod.StaffLineDetection(
                index + 1,
                top + index * spacing,
                (left, right),
                ((left, int(round(top + index * spacing)), right, int(round(top + index * spacing))),),
            )
            for index in range(5)
        )
        return mod.StaffSystemDetection(
            0,
            (left, int(top - 4), right, int(top + 4 * spacing + 5)),
            spacing,
            confidence,
            lines,
            provenance,
            parent.DETECTOR_VERSION,
        )

    def test_source_evidence_floor_preserves_anchor_and_accepts_confidence_or_width(self):
        anchor = "source-only:v1.2-parent-preserved:source-only:v1-compatibility+v1.1-local-spacing-topology"
        weak = "source-only:v1.2-parent-anchored-horizontal-template"
        detections = [
            self._detection(top=40, left=100, right=300, confidence=0.70, provenance=anchor),
            self._detection(top=120, left=100, right=300, confidence=0.92, provenance=weak),
            self._detection(top=200, left=80, right=760, confidence=0.80, provenance=weak),
            self._detection(top=280, left=100, right=300, confidence=0.80, provenance=weak),
        ]
        kept, diagnostics = mod._apply_source_evidence_floor(
            detections,
            820,
            mod.WeakEvidenceConfig(),
        )
        self.assertEqual(3, len(kept))
        self.assertEqual([1, 2, 3], [item.system_index for item in kept])
        self.assertEqual(1, diagnostics["suppressedWeakSystemCount"])
        self.assertEqual(0, diagnostics["failOpenRestoredSystemCount"])
        self.assertTrue(all(item.detector_version == mod.DETECTOR_VERSION for item in kept))

    def test_fail_open_keeps_strongest_when_filter_would_empty_parent_page(self):
        weak = "source-only:v1.2-parent-anchored-horizontal-template"
        detections = [
            self._detection(top=80, left=100, right=300, confidence=0.82, provenance=weak),
            self._detection(top=180, left=100, right=310, confidence=0.89, provenance=weak),
        ]
        kept, diagnostics = mod._apply_source_evidence_floor(
            detections,
            820,
            mod.WeakEvidenceConfig(),
        )
        self.assertEqual(1, len(kept))
        self.assertAlmostEqual(0.89, kept[0].confidence)
        self.assertEqual(1, diagnostics["failOpenRestoredSystemCount"])
        self.assertEqual(1, diagnostics["suppressedWeakSystemCount"])

    def test_true_multisystem_and_negative_controls_remain_bounded(self):
        detections = mod.detect_staff_systems(self._page(systems=[(80, 11), (300, 13)]))
        self.assertEqual(2, len(detections))
        self.assertTrue(all(len(item.lines) == 5 for item in detections))
        self.assertTrue(all(item.detector_version == mod.DETECTOR_VERSION for item in detections))
        self.assertEqual([], mod.detect_staff_systems(self._page(six_line=True)))
        blank = np.full((300, 500), 255, dtype=np.uint8)
        self.assertEqual([], mod.detect_staff_systems(blank))

    def test_deterministic_and_has_no_teacher_holdout_page_identity_channel(self):
        image = self._page(systems=[(80, 11), (300, 13)])
        first, first_diag = mod.detect_staff_systems_with_diagnostics(image)
        second, second_diag = mod.detect_staff_systems_with_diagnostics(image.copy())
        self.assertEqual([item.as_dict() for item in first], [item.as_dict() for item in second])
        self.assertEqual(first_diag, second_diag)
        sig = inspect.signature(mod.detect_staff_systems)
        self.assertEqual(
            ["image", "parent_config", "consensus_config", "evidence_config"],
            list(sig.parameters),
        )
        for name in ("parent_config", "consensus_config", "evidence_config"):
            self.assertEqual(inspect.Parameter.KEYWORD_ONLY, sig.parameters[name].kind)
        self.assertTrue(first_diag["sourceOnly"])
        for key in (
            "teacherCoordinatesUsed",
            "restoredOutputsUsed",
            "heldOutAccessed",
            "trainingUsed",
            "pageIdentityUsed",
            "pageSpecificRulesUsed",
        ):
            self.assertFalse(first_diag[key])

    def test_freeze_source_folder_repeatability_and_identity_mismatch_fail_closed(self):
        image = self._page(systems=[(80, 11), (300, 13)])
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
            self.assertEqual(mod.DETECTOR_VERSION, artifact["detectorVersion"])
            self.assertEqual(parent.DETECTOR_VERSION, artifact["parentDetectorVersion"])
            self.assertTrue(artifact["sourceOnly"])
            self.assertFalse(artifact["teacherArtifactLoadedDuringInference"])
            self.assertFalse(artifact["heldOutAccessed"])
            self.assertFalse(artifact["pageSpecificRulesUsed"])
            self.assertTrue(all(value is False for value in artifact["claimBoundary"].values()))
            with self.assertRaises(mod.StaffLineMultiSystemDetectorV14Error):
                mod.freeze_source_folder(
                    source,
                    root / "bad.json",
                    expected_source_sha256={page.name: "0" * 64},
                )

    def test_frozen_parent_transform_repeatable_and_rejects_identity_mismatch(self):
        weak = "source-only:v1.2-parent-anchored-horizontal-template"
        anchor = "source-only:v1.2-parent-preserved:source-only:v1-compatibility+v1.1-local-spacing-topology"
        systems = [
            self._detection(top=40, left=80, right=760, confidence=0.80, provenance=weak).as_dict(),
            self._detection(top=140, left=100, right=300, confidence=0.70, provenance=anchor).as_dict(),
            self._detection(top=240, left=100, right=300, confidence=0.80, provenance=weak).as_dict(),
        ]
        for index, item in enumerate(systems, start=1):
            item["systemIndex"] = index
            item["detectorVersion"] = parent.DETECTOR_VERSION
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
            parent_path.write_text(
                json.dumps(parent_payload, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            parent_sha = hashlib.sha256(parent_path.read_bytes()).hexdigest()
            a, b = root / "a.json", root / "b.json"
            first = mod.freeze_frozen_parent_artifact(
                parent_path, a, expected_parent_artifact_sha256=parent_sha
            )
            second = mod.freeze_frozen_parent_artifact(
                parent_path, b, expected_parent_artifact_sha256=parent_sha
            )
            self.assertEqual(first["artifactSha256"], second["artifactSha256"])
            self.assertEqual(a.read_bytes(), b.read_bytes())
            artifact = json.loads(a.read_text(encoding="utf-8"))
            self.assertEqual(2, artifact["pages"][0]["systemCount"])
            self.assertEqual(1, artifact["suppressedWeakSystemCount"])
            self.assertFalse(artifact["teacherArtifactLoadedDuringInference"])
            with self.assertRaises(mod.StaffLineMultiSystemDetectorV14Error):
                mod.freeze_frozen_parent_artifact(
                    parent_path,
                    root / "bad.json",
                    expected_parent_artifact_sha256="0" * 64,
                )

    def test_frozen_v1_2_transform_runs_v1_3_spacing_then_v1_4_evidence(self):
        weak = "source-only:v1.2-parent-anchored-horizontal-template"
        anchor = "source-only:v1.2-parent-preserved:source-only:v1-compatibility+v1.1-local-spacing-topology"
        systems = [
            self._detection(spacing=10.0, top=40, left=80, right=760, confidence=0.97, provenance=anchor).as_dict(),
            self._detection(spacing=10.2, top=140, left=100, right=300, confidence=0.92, provenance=weak).as_dict(),
            self._detection(spacing=16.0, top=240, left=100, right=300, confidence=0.95, provenance=weak).as_dict(),
        ]
        for index, item in enumerate(systems, start=1):
            item["systemIndex"] = index
            item["detectorVersion"] = mod.GRANDPARENT_DETECTOR_VERSION
        payload = {
            "detectorVersion": mod.GRANDPARENT_DETECTOR_VERSION,
            "sourceOnly": True,
            "teacherArtifactLoadedDuringInference": False,
            "teacherCoordinatesUsedDuringInference": False,
            "restoredOutputsLoadedDuringInference": False,
            "heldOutAccessed": False,
            "pageSpecificRulesUsed": False,
            "detectorSourceSha256": "3" * 64,
            "sourceIdentityExpectedCount": 1,
            "sourceIdentityMatchedCount": 1,
            "pages": [{
                "pageId": "dev-a",
                "sourceFileName": "dev-a.png",
                "sourceSha256": "4" * 64,
                "width": 820,
                "height": 520,
                "systems": systems,
                "diagnostics": {},
            }],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "v12.json"
            source.write_text(
                json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
            result = mod.freeze_frozen_v1_2_artifact(
                source,
                root / "v14.json",
                expected_v1_2_artifact_sha256=source_sha,
            )
            artifact = result["artifact"]
            self.assertEqual(1, artifact["spacingConsensusSuppressedWeakSystemCount"])
            self.assertEqual(0, artifact["sourceEvidenceSuppressedWeakSystemCount"])
            self.assertEqual(2, artifact["pages"][0]["systemCount"])
            self.assertEqual(mod.DETECTOR_VERSION, artifact["pages"][0]["systems"][0]["detectorVersion"])

    def test_invalid_evidence_config_fails_closed(self):
        with self.assertRaises(mod.StaffLineMultiSystemDetectorV14Error):
            mod.detect_staff_systems(
                self._page(systems=[(100, 12)]),
                evidence_config=mod.WeakEvidenceConfig(weak_confidence_min=1.01),
            )
        with self.assertRaises(mod.StaffLineMultiSystemDetectorV14Error):
            mod.WeakEvidenceConfig(weak_page_width_fraction_min=0.20).validate()


if __name__ == "__main__":
    unittest.main()
