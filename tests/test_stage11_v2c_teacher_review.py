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


class Stage11V2cTeacherReviewTests(unittest.TestCase):
    def _base(self) -> dict:
        return json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))

    def _overlay(self) -> dict:
        return json.loads(OVERLAY.read_text(encoding="utf-8"))

    def test_source_only_teacher_review_materializes_independent_manifest(self) -> None:
        result = materialize_teacher_review_manifest(self._base(), self._overlay())
        validation = validate_expected_class_manifest(result["manifest"])
        self.assertEqual(20, validation["pageCount"])
        self.assertEqual(170, validation["stateCounts"]["present"])
        self.assertEqual(50, validation["stateCounts"]["absent"])
        self.assertEqual(18, validation["stateCounts"]["not_applicable"])
        self.assertEqual(2, validation["stateCounts"]["unknown_review_required"])
        self.assertEqual(170, validation["eligiblePresentClassCount"])
        self.assertEqual(220, validation["independentlyAnnotatedClassCount"])
        self.assertAlmostEqual(220 / 222, validation["annotationCoverage"])
        self.assertEqual(238, result["acceptedResponseCount"])
        self.assertEqual(2, result["conflictCount"])
        self.assertEqual(EXPECTED_REVIEW_PDF_SHA256, result["sourceReviewPdfSha256"])

    def test_known_conflicts_fail_closed_to_unknown_review_required(self) -> None:
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

    def test_tampered_pdf_digest_is_rejected(self) -> None:
        overlay = copy.deepcopy(self._overlay())
        overlay["sourceReviewPdf"]["sha256"] = "0" * 64
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            materialize_teacher_review_manifest(self._base(), overlay)

    def test_detector_output_cannot_become_teacher_ground_truth(self) -> None:
        overlay = copy.deepcopy(self._overlay())
        overlay["independenceBoundary"]["detectorOutputUsedAsGroundTruth"] = True
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            materialize_teacher_review_manifest(self._base(), overlay)

    def test_conflict_cannot_be_silently_coerced_to_pass_state(self) -> None:
        overlay = copy.deepcopy(self._overlay())
        overlay["conflicts"][0]["effectiveState"] = "absent"
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            materialize_teacher_review_manifest(self._base(), overlay)


if __name__ == "__main__":
    unittest.main()
