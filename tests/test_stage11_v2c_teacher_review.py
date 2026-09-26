from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage11_v2c_semantic_preservation import (
    Stage11V2cSemanticPreservationError,
    validate_expected_class_manifest,
)
from st_score_restore.stage11_v2c_teacher_review import (
    EXPECTED_REVIEW_PDF_SHA256,
    materialize_teacher_review_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
BASE_MANIFEST = ROOT / "evidence" / "stage11" / "v2c" / "v2c-expected-class-manifest.v1.json"
OVERLAY = ROOT / "evidence" / "stage11" / "v2c" / "v2c-teacher-review-overlay.v1.json"
RESOLUTION = ROOT / "evidence" / "stage11" / "v2c" / "v2c-teacher-review-resolution.v1.json"


class Stage11V2cTeacherReviewTests(unittest.TestCase):
    def _base(self) -> dict:
        return json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))

    def _overlay(self) -> dict:
        return json.loads(OVERLAY.read_text(encoding="utf-8"))

    def _resolution(self) -> dict:
        return json.loads(RESOLUTION.read_text(encoding="utf-8"))

    def test_source_only_teacher_review_plus_followup_materializes_complete_independent_manifest(self) -> None:
        result = materialize_teacher_review_manifest(self._base(), self._overlay(), self._resolution())
        validation = validate_expected_class_manifest(result["manifest"])
        self.assertEqual(20, validation["pageCount"])
        self.assertEqual(171, validation["stateCounts"]["present"])
        self.assertEqual(51, validation["stateCounts"]["absent"])
        self.assertEqual(18, validation["stateCounts"]["not_applicable"])
        self.assertEqual(0, validation["stateCounts"]["unknown_review_required"])
        self.assertEqual(171, validation["eligiblePresentClassCount"])
        self.assertEqual(222, validation["independentlyAnnotatedClassCount"])
        self.assertEqual(1.0, validation["annotationCoverage"])
        self.assertEqual(240, result["acceptedResponseCount"])
        self.assertEqual(0, result["conflictCount"])
        self.assertEqual(2, result["resolvedConflictCount"])
        self.assertEqual(EXPECTED_REVIEW_PDF_SHA256, result["sourceReviewPdfSha256"])

    def test_original_pdf_conflicts_remain_fail_closed_without_followup_resolution(self) -> None:
        manifest = materialize_teacher_review_manifest(self._base(), self._overlay())["manifest"]
        pages = {page["pageId"]: page for page in manifest["pages"]}
        self.assertEqual(
            "unknown_review_required",
            pages["carulli-morceaux-faciles-p3"]["classes"]["tab_string"]["state"],
        )
        self.assertEqual(
            "unknown_review_required",
            pages["bach-anna-magdalena-p24"]["classes"]["notehead"]["state"],
        )

    def test_followup_resolution_applies_only_to_the_two_teacher_confirmed_conflicts(self) -> None:
        manifest = materialize_teacher_review_manifest(self._base(), self._overlay(), self._resolution())["manifest"]
        pages = {page["pageId"]: page for page in manifest["pages"]}
        self.assertEqual("absent", pages["carulli-morceaux-faciles-p3"]["classes"]["tab_string"]["state"])
        self.assertEqual("present", pages["bach-anna-magdalena-p24"]["classes"]["notehead"]["state"])
        self.assertFalse(pages["carulli-morceaux-faciles-p3"]["classes"]["tab_string"]["reviewConflict"]["resolutionRequired"])
        self.assertFalse(pages["bach-anna-magdalena-p24"]["classes"]["notehead"]["reviewConflict"]["resolutionRequired"])

    def test_tampered_pdf_digest_is_rejected(self) -> None:
        overlay = copy.deepcopy(self._overlay())
        overlay["sourceReviewPdf"]["sha256"] = "0" * 64
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            materialize_teacher_review_manifest(self._base(), overlay, self._resolution())

    def test_detector_output_cannot_become_teacher_ground_truth(self) -> None:
        overlay = copy.deepcopy(self._overlay())
        overlay["independenceBoundary"]["detectorOutputUsedAsGroundTruth"] = True
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            materialize_teacher_review_manifest(self._base(), overlay, self._resolution())

    def test_original_conflict_cannot_be_silently_coerced_inside_pdf_overlay(self) -> None:
        overlay = copy.deepcopy(self._overlay())
        overlay["conflicts"][0]["effectiveState"] = "absent"
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            materialize_teacher_review_manifest(self._base(), overlay, self._resolution())

    def test_resolution_cannot_target_non_conflict(self) -> None:
        resolution = copy.deepcopy(self._resolution())
        resolution["resolutions"][0]["pageId"] = "carulli-morceaux-faciles-p4"
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            materialize_teacher_review_manifest(self._base(), self._overlay(), resolution)

    def test_resolution_cannot_claim_semantic_preservation_or_production(self) -> None:
        resolution = copy.deepcopy(self._resolution())
        resolution["claimBoundary"]["semanticPreservationEstablished"] = True
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            materialize_teacher_review_manifest(self._base(), self._overlay(), resolution)


if __name__ == "__main__":
    unittest.main()
