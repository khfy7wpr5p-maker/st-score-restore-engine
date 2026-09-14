from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage11_v2c_semantic_preservation import Stage11V2cSemanticPreservationError
from st_score_restore.stage11_v2d_spatial_teacher_review import validate_spatial_review_work_package

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "evidence" / "stage11" / "v2d" / "v2d-spatial-teacher-review-work-package.v1.json"


class Stage11V2dSpatialTeacherReviewTests(unittest.TestCase):
    def _package(self) -> dict:
        return json.loads(PACKAGE.read_text(encoding="utf-8"))

    def test_pristine_package_covers_exact_teacher_present_pages(self) -> None:
        result = validate_spatial_review_work_package(self._package())
        self.assertEqual("pass", result["status"])
        self.assertEqual(5, result["sourceAssetCount"])
        self.assertEqual(18, result["reviewPageCount"])
        self.assertEqual(90, result["humanAnnotationFieldCount"])
        self.assertEqual(0, result["humanAnnotationsPopulated"])
        self.assertFalse(result["newColabRunRequiredNow"])

    def test_repository_package_cannot_contain_prefilled_clef_boxes(self) -> None:
        package = copy.deepcopy(self._package())
        package["pages"][0]["humanAnnotations"]["clefBoxes"] = [
            {"boxId": "c1", "xMin": 1, "yMin": 2, "xMaxExclusive": 3, "yMaxExclusive": 4}
        ]
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_spatial_review_work_package(package)

    def test_repository_package_cannot_contain_prefilled_staff_mask(self) -> None:
        package = copy.deepcopy(self._package())
        package["pages"][0]["humanAnnotations"]["staffLineMaskPng"] = {
            "path": "masks/example.png",
            "sha256": "0" * 64,
        }
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_spatial_review_work_package(package)

    def test_model_or_restored_output_cannot_be_shown_during_review(self) -> None:
        for key in ("modelOutputShown", "restoredOutputShown"):
            with self.subTest(key=key):
                package = copy.deepcopy(self._package())
                package["independenceBoundary"][key] = True
                with self.assertRaises(Stage11V2cSemanticPreservationError):
                    validate_spatial_review_work_package(package)

    def test_source_asset_identity_is_hash_bound(self) -> None:
        package = copy.deepcopy(self._package())
        package["sourceAssets"][0]["sha256"] = "0" * 64
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_spatial_review_work_package(package)

    def test_page_scope_cannot_drift_to_held_out_or_absent_pages(self) -> None:
        package = copy.deepcopy(self._package())
        package["pages"][0]["pageId"] = "beethoven-op48-no3-p1"
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_spatial_review_work_package(package)

    def test_package_cannot_open_downstream_claims_or_request_colab(self) -> None:
        for key in (
            "teacherSpatialLabelsComplete",
            "detectorQualified",
            "semanticPreservationEstablished",
            "overallStage11PassAuthorized",
            "productionReady",
            "productionPromotionAuthorized",
            "stage12EntryAuthorized",
            "newColabRunRequiredNow",
        ):
            with self.subTest(key=key):
                package = copy.deepcopy(self._package())
                package["claimBoundary"][key] = True
                with self.assertRaises(Stage11V2cSemanticPreservationError):
                    validate_spatial_review_work_package(package)


if __name__ == "__main__":
    unittest.main()
