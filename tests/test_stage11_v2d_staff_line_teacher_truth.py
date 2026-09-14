from __future__ import annotations

import copy
import unittest
from pathlib import Path

from st_score_restore.stage11_v2d_staff_line_teacher_truth import (
    build_template,
    source_contracts,
    validate_teacher_truth,
)


class StaffLineTeacherTruthTests(unittest.TestCase):
    def _complete_artifact(self):
        artifact = build_template(Path("."))
        contracts = source_contracts(Path("."))
        artifact["status"] = "ANNOTATION_COMPLETE"
        artifact["completedPageCount"] = 20
        for page_id, page in artifact["pages"].items():
            contract = contracts[page_id]
            page["completed"] = True
            page["staffLineMaskPath"] = f"masks/{page_id}.png"
            page["staffLineMaskSha256"] = "0" * 64
            if not contract["expectedStaffPresent"]:
                page["systems"] = []
                continue
            width, height = contract["width"], contract["height"]
            x1, x2 = max(1, width // 10), max(2, width - width // 10)
            y0 = max(10, height // 4)
            step = max(2, height // 100)
            lines = [
                {
                    "lineIndex": index,
                    "centerlinePoints": [[x1, y0 + (index - 1) * step], [x2, y0 + (index - 1) * step]],
                }
                for index in range(1, 6)
            ]
            page["systems"] = [
                {
                    "systemId": "system-1",
                    "bbox": [x1, max(0, y0 - step), x2, min(height, y0 + 5 * step)],
                    "lineCount": 5,
                    "lines": lines,
                    "status": "CONFIRMED",
                }
            ]
        return artifact

    def test_frozen_source_contract_has_20_pages_and_18_staff_present(self):
        contracts = source_contracts(Path("."))
        self.assertEqual(20, len(contracts))
        self.assertEqual(18, sum(1 for item in contracts.values() if item["expectedStaffPresent"]))

    def test_template_is_blinded_and_incomplete(self):
        artifact = build_template(Path("."))
        self.assertFalse(artifact["detectorOutputsShownToTeacher"])
        self.assertFalse(artifact["restoredOutputsShownToTeacher"])
        self.assertFalse(artifact["lineDetectorGeometryShownToTeacher"])
        self.assertEqual(0, artifact["completedPageCount"])
        self.assertEqual(20, len(artifact["pages"]))

    def test_structurally_complete_human_artifact_passes_without_mask_byte_check(self):
        artifact = self._complete_artifact()
        self.assertEqual([], validate_teacher_truth(artifact, Path("."), require_complete=True))

    def test_detector_visibility_is_rejected(self):
        artifact = self._complete_artifact()
        artifact["detectorOutputsShownToTeacher"] = True
        errors = validate_teacher_truth(artifact, Path("."), require_complete=True)
        self.assertIn("detectorOutputsShownToTeacher must be false", errors)

    def test_destructive_or_incomplete_five_line_topology_is_rejected(self):
        artifact = self._complete_artifact()
        page = next(page for page in artifact["pages"].values() if page["expectedStaffPresent"])
        page["systems"][0]["lines"] = page["systems"][0]["lines"][:4]
        page["systems"][0]["lineCount"] = 4
        errors = validate_teacher_truth(artifact, Path("."), require_complete=True)
        self.assertTrue(any("exactly 5 lines" in error for error in errors))

    def test_teacher_absent_page_cannot_contain_system(self):
        artifact = self._complete_artifact()
        page = next(page for page in artifact["pages"].values() if not page["expectedStaffPresent"])
        page["systems"] = [{"systemId": "bad", "bbox": [0, 0, 1, 1], "lineCount": 0, "lines": [], "status": "AMBIGUOUS"}]
        errors = validate_teacher_truth(artifact, Path("."), require_complete=True)
        self.assertTrue(any("staff-absent page must have zero systems" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
