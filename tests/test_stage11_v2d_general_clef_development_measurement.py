from __future__ import annotations

import json
from pathlib import Path
import unittest

from st_score_restore.stage11_v2d_general_clef_development_measurement import (
    validate_general_clef_development_measurement,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/stage11/v2d/v2d-general-clef-successor-v1-development-measurement.v1.json"
EVIDENCE_V2 = ROOT / "evidence/stage11/v2d/v2d-general-clef-successor-v2-development-measurement.v2.json"


class Stage11V2dGeneralClefDevelopmentMeasurementTests(unittest.TestCase):
    def test_bound_development_replay_is_valid_and_fail_closed(self) -> None:
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        result = validate_general_clef_development_measurement(payload)

        self.assertEqual("PARTIAL_PASS_SOPRANO_UNRESOLVED", result["disposition"])
        self.assertEqual(213, result["teacher_box_count"])
        self.assertEqual(201, result["tp"])
        self.assertEqual(4, result["fp"])
        self.assertEqual(12, result["fn"])
        self.assertFalse(result["detector_qualified"])
        self.assertFalse(result["holdout_authorized"])

    def test_review_only_soprano_resolution_v2_is_freeze_ready_without_typed_claim(self) -> None:
        self.assertTrue(EVIDENCE_V2.is_file(), "v2 development evidence must be committed")
        payload = json.loads(EVIDENCE_V2.read_text(encoding="utf-8"))
        result = validate_general_clef_development_measurement(payload)

        self.assertEqual(
            "DEVELOPMENT_FREEZE_READY_WITH_SOPRANO_REVIEW_ONLY",
            result["disposition"],
        )
        self.assertEqual(2, result["soprano_review_tp"])
        self.assertEqual(0, result["soprano_review_fp"])
        self.assertEqual(0, result["soprano_review_fn"])
        self.assertTrue(result["development_freeze_ready"])
        self.assertFalse(result["soprano_typed_support_established"])
        self.assertFalse(result["candidate_frozen"])
        self.assertFalse(result["holdout_authorized"])

    def test_selection_disclosure_cannot_be_reclassified_as_qualification(self) -> None:
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        payload["selectionDisclosure"]["developmentTruthUsedForThresholdSelection"] = False

        with self.assertRaises(ValueError):
            validate_general_clef_development_measurement(payload)

    def test_soprano_blocker_is_mandatory(self) -> None:
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        payload["perSubtype"]["soprano"]["typedTp"] = 2
        payload["perSubtype"]["soprano"]["typedFn"] = 0

        with self.assertRaises(ValueError):
            validate_general_clef_development_measurement(payload)


if __name__ == "__main__":
    unittest.main()
