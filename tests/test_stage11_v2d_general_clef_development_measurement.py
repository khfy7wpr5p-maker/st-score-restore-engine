from __future__ import annotations

import json
from pathlib import Path
import unittest

from st_score_restore.stage11_v2d_general_clef_development_measurement import (
    validate_general_clef_development_measurement,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/stage11/v2d/v2d-general-clef-successor-v1-development-measurement.v1.json"


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
