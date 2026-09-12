from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage11_v2c_semantic_preservation import Stage11V2cSemanticPreservationError
from st_score_restore.stage11_v2d_clef_teacher_completion import (
    SOURCE_BUNDLE,
    validate_clef_taxonomy_amendment,
    validate_clef_teacher_completion,
    validate_clef_teacher_completion_binding,
)
from st_score_restore.stage11_v2d_spatial_teacher_review import EXPECTED_PAGES

ROOT = Path(__file__).resolve().parents[1]
AMENDMENT = ROOT / "evidence" / "stage11" / "v2d" / "v2d-clef-teacher-taxonomy-amendment.v1.json"
BINDING = ROOT / "evidence" / "stage11" / "v2d" / "v2d-clef-box-teacher-completion-binding.v1.json"
PAGE_COUNTS = [9, 12, 6, 8, 10, 12, 12, 15, 15, 12, 12, 12, 12, 12, 14, 12, 16, 12]


class Stage11V2dClefTeacherCompletionTests(unittest.TestCase):
    def _amendment(self) -> dict:
        return json.loads(AMENDMENT.read_text(encoding="utf-8"))

    def _binding(self) -> dict:
        return json.loads(BINDING.read_text(encoding="utf-8"))

    def _completion(self) -> dict:
        pages = []
        serial = 0
        for (page_id, _source_id, _page_number), count in zip(EXPECTED_PAGES, PAGE_COUNTS):
            boxes = []
            for index in range(count):
                serial += 1
                clef_type = "soprano" if serial in (1, 2) else "treble"
                x = 2 + (index % 10) * 3
                y = 2 + (index // 10) * 3
                boxes.append({
                    "boxId": f"{page_id}-clef-{serial}",
                    "xMin": x,
                    "yMin": y,
                    "xMaxExclusive": x + 2,
                    "yMaxExclusive": y + 2,
                    "clefType": clef_type,
                    "truncated": False,
                    "ambiguous": False,
                })
            pages.append({
                "pageId": page_id,
                "reviewImage": {
                    "path": f"source-pages/{page_id}.png",
                    "byteSize": 100,
                    "sha256": "a" * 64,
                    "width": 100,
                    "height": 100,
                },
                "teacherState": "present",
                "clefBoxes": boxes,
                "reviewerStatus": "completed",
            })
        return {
            "schemaVersion": "stage11.v2d.clef-box-teacher-review-completion.v1",
            "contractId": "stage11.v2c.semantic-preservation.nonheldout.v1",
            "reviewerName": "Teacher",
            "reviewDate": "2026-09-09",
            "sourceReviewBundle": copy.deepcopy(SOURCE_BUNDLE),
            "independenceBoundary": {
                "reviewBasis": "source_page_only",
                "modelOutputShown": False,
                "restoredOutputShown": False,
                "detectorOutputUsedAsGroundTruth": False,
            },
            "pages": pages,
            "summary": {
                "reviewPageCount": 18,
                "completedPageCount": 18,
                "clefBoxCount": 213,
                "clefBoxLabelsComplete": True,
                "staffLineLabelsComplete": False,
            },
            "claimBoundary": {
                "clefBoxLabelsComplete": True,
                "teacherSpatialLabelsComplete": False,
                "detectorQualified": False,
                "semanticPreservationEstablished": False,
                "overallStage11PassAuthorized": False,
                "productionReady": False,
                "productionPromotionAuthorized": False,
                "stage12EntryAuthorized": False,
                "newColabRunRequiredNow": False,
            },
        }

    def test_taxonomy_amendment_and_binding_pass(self) -> None:
        self.assertEqual("pass", validate_clef_taxonomy_amendment(self._amendment())["status"])
        result = validate_clef_teacher_completion_binding(self._binding())
        self.assertEqual("pass", result["status"])
        self.assertEqual(213, result["clefBoxCount"])

    def test_synthetic_completion_with_soprano_passes(self) -> None:
        result = validate_clef_teacher_completion(self._completion(), self._amendment())
        self.assertEqual(213, result["clefBoxCount"])
        self.assertEqual(2, result["clefTypeCounts"]["soprano"])

    def test_pristine_package_cannot_be_marked_mutated(self) -> None:
        amendment = self._amendment()
        amendment["workPackage"]["mutated"] = True
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_clef_taxonomy_amendment(amendment)

    def test_invalid_type_duplicate_and_out_of_bounds_fail_closed(self) -> None:
        for mutation in ("invalid_type", "duplicate", "out_of_bounds"):
            with self.subTest(mutation=mutation):
                completion = self._completion()
                first = completion["pages"][0]["clefBoxes"]
                if mutation == "invalid_type":
                    first[0]["clefType"] = "mezzo_soprano"
                elif mutation == "duplicate":
                    first[1]["boxId"] = first[0]["boxId"]
                else:
                    first[0]["xMaxExclusive"] = 101
                with self.assertRaises(Stage11V2cSemanticPreservationError):
                    validate_clef_teacher_completion(completion, self._amendment())

    def test_summary_and_downstream_claims_fail_closed(self) -> None:
        completion = self._completion()
        completion["summary"]["clefBoxCount"] = 214
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_clef_teacher_completion(completion, self._amendment())
        for section, key in (
            ("summary", "staffLineLabelsComplete"),
            ("claimBoundary", "teacherSpatialLabelsComplete"),
            ("claimBoundary", "detectorQualified"),
            ("claimBoundary", "semanticPreservationEstablished"),
            ("claimBoundary", "overallStage11PassAuthorized"),
            ("claimBoundary", "productionReady"),
            ("claimBoundary", "stage12EntryAuthorized"),
        ):
            with self.subTest(section=section, key=key):
                completion = self._completion()
                completion[section][key] = True
                with self.assertRaises(Stage11V2cSemanticPreservationError):
                    validate_clef_teacher_completion(completion, self._amendment())

    def test_binding_hash_drift_fails_closed(self) -> None:
        binding = self._binding()
        binding["completion"]["sha256"] = "0" * 64
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_clef_teacher_completion_binding(binding)


if __name__ == "__main__":
    unittest.main()
