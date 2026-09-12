from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage11_v2c_semantic_preservation import Stage11V2cSemanticPreservationError
from st_score_restore.stage11_v2d_clef_source_qualification import (
    PRIMARY_IOU_THRESHOLD,
    box_iou,
    build_clef_source_qualification_measurement,
    greedy_one_to_one_match,
    validate_clef_source_qualification_contract,
)
from st_score_restore.stage11_v2d_spatial_teacher_review import EXPECTED_PAGES

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "evidence" / "stage11" / "v2d" / "v2d-clef-source-qualification-contract.v1.json"
PAGE_COUNTS = [9, 12, 6, 8, 10, 12, 12, 15, 15, 12, 12, 12, 12, 12, 14, 12, 16, 12]


class Stage11V2dClefSourceQualificationTests(unittest.TestCase):
    def _contract(self) -> dict:
        return json.loads(CONTRACT.read_text(encoding="utf-8"))

    def _records(self) -> list[dict]:
        records = []
        for (page_id, source_id, _page_number), count in zip(EXPECTED_PAGES, PAGE_COUNTS):
            records.append({
                "pageId": page_id,
                "sourceFamily": source_id,
                "sourceOnly": True,
                "teacherBoxCount": count,
                "tp": count,
                "fp": 0,
                "fn": 0,
                "precision": 1.0,
                "recall": 1.0,
                "f1": 1.0,
            })
        return records

    def test_contract_preregisters_source_only_iou_0_50(self) -> None:
        result = validate_clef_source_qualification_contract(self._contract())
        self.assertEqual("pass", result["status"])
        self.assertEqual(0.50, PRIMARY_IOU_THRESHOLD)

    def test_threshold_cannot_drift_after_measurement(self) -> None:
        contract = self._contract()
        contract["matching"]["primaryIouThreshold"] = 0.20
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_clef_source_qualification_contract(contract)

    def test_contract_cannot_use_restored_images_or_auto_qualify(self) -> None:
        for section, key in (
            ("scope", "restoredImagesEvaluated"),
            ("decisionBoundary", "detectorQualified"),
            ("decisionBoundary", "preservationMeasurementAuthorizedByThisArtifact"),
        ):
            with self.subTest(section=section, key=key):
                contract = self._contract()
                contract[section][key] = True
                with self.assertRaises(Stage11V2cSemanticPreservationError):
                    validate_clef_source_qualification_contract(contract)

    def test_iou_and_one_to_one_matching(self) -> None:
        self.assertAlmostEqual(1.0, box_iou([0, 0, 10, 10], [0, 0, 10, 10]))
        result = greedy_one_to_one_match(
            [[0, 0, 10, 10], [20, 20, 30, 30]],
            [[0, 0, 10, 10], [21, 21, 31, 31], [50, 50, 60, 60]],
        )
        self.assertEqual((2, 1, 0), (result["tp"], result["fp"], result["fn"]))

    def test_measurement_aggregates_page_family_and_pooled(self) -> None:
        result = build_clef_source_qualification_measurement(self._records())
        self.assertEqual(213, result["pooledMetrics"]["tp"])
        self.assertEqual(0, result["pooledMetrics"]["fp"])
        self.assertEqual(0, result["pooledMetrics"]["fn"])
        self.assertEqual({"beethoven", "wikimedia", "barley", "carulli", "bach"}, set(result["sourceFamilyMetrics"]))
        self.assertFalse(result["decisionBoundary"]["detectorQualified"])

    def test_measurement_rejects_restored_or_count_drift(self) -> None:
        records = self._records()
        records[0]["sourceOnly"] = False
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            build_clef_source_qualification_measurement(records)
        records = self._records()
        records[0]["teacherBoxCount"] += 1
        records[0]["fn"] += 1
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            build_clef_source_qualification_measurement(records)


if __name__ == "__main__":
    unittest.main()
