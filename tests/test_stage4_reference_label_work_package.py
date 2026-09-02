from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage4_reference_label_work_package import (
    Stage4ReferenceLabelWorkPackageError,
    WORK_PACKAGE_CANONICAL_SHA256,
    summarize_reference_label_work_package,
    validate_reference_label_work_package,
)

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "evidence" / "stage4" / "reference-labels" / "work-package.v1.json"


class Stage4ReferenceLabelWorkPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = json.loads(PACKAGE.read_text(encoding="utf-8"))

    def test_empty_human_review_package_validates(self) -> None:
        value = validate_reference_label_work_package(self.raw)
        self.assertEqual(value["state"], "awaiting_human_labels")
        self.assertEqual(WORK_PACKAGE_CANONICAL_SHA256, "93e1a61bbdd698dbabf1ba88164453056acf3f2ea37fa159305a0f244b2253ba")

    def test_summary_is_non_authorizing(self) -> None:
        summary = summarize_reference_label_work_package(self.raw)
        self.assertEqual(summary["developmentItemCount"], 2)
        self.assertEqual(summary["pageCount"], 6)
        self.assertEqual(summary["reviewSlotCount"], 42)
        self.assertFalse(summary["humanLabelsPresent"])
        self.assertFalse(summary["referenceBundleAccepted"])
        self.assertFalse(summary["realDataCalibrationExecutionAuthorized"])
        self.assertFalse(summary["heldOutIncluded"])

    def test_human_label_cannot_appear_in_template(self) -> None:
        mutated = deepcopy(self.raw)
        mutated["items"][0]["pages"][0]["reviews"][0]["referenceLabel"] = "probable"
        with self.assertRaises(Stage4ReferenceLabelWorkPackageError):
            validate_reference_label_work_package(mutated)

    def test_reviewer_or_provenance_cannot_be_prepopulated(self) -> None:
        for field, value in (
            ("reviewerReference", "reviewer:opaque-001"),
            ("provenanceReference", "evidence:opaque-001"),
            ("reviewedOn", "2026-09-02"),
        ):
            mutated = deepcopy(self.raw)
            mutated["items"][0]["pages"][0]["reviews"][0][field] = value
            with self.assertRaises(Stage4ReferenceLabelWorkPackageError):
                validate_reference_label_work_package(mutated)

    def test_chopin_cannot_enter_development_items(self) -> None:
        mutated = deepcopy(self.raw)
        mutated["items"][0]["datasetItemId"] = "dataset.item.imslp82860-chopin-op69.v2"
        with self.assertRaises(Stage4ReferenceLabelWorkPackageError):
            validate_reference_label_work_package(mutated)

    def test_model_prediction_permission_cannot_be_enabled(self) -> None:
        mutated = deepcopy(self.raw)
        mutated["reviewScope"]["modelPredictionsAllowedAsReference"] = True
        with self.assertRaises(Stage4ReferenceLabelWorkPackageError):
            validate_reference_label_work_package(mutated)


if __name__ == "__main__":
    unittest.main()
