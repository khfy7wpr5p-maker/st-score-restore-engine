from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage4_expanded_real_development_execution_evidence import (
    Stage4ExpandedRealDevelopmentExecutionEvidenceError,
    validate_expanded_real_development_execution_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = json.loads(
    (ROOT / "evidence/stage4/calibration/expanded-real-development-execution.v1.json").read_text(encoding="utf-8")
)


class Stage4ExpandedRealDevelopmentExecutionEvidenceTests(unittest.TestCase):
    def test_canonical_expanded_evidence_is_valid(self) -> None:
        value = validate_expanded_real_development_execution_evidence(EVIDENCE)
        self.assertEqual("executed_abstained", value["state"])
        self.assertEqual(49, value["scope"]["privateMetricRecordCount"])
        self.assertEqual(30, value["scope"]["measuredRecordCount"])
        self.assertEqual(19, value["scope"]["notApplicableRecordCount"])
        self.assertEqual(2, value["scope"]["measuredSourceFamilyCount"])
        self.assertEqual(0, value["summary"]["candidateDerivedCount"])
        self.assertTrue(value["assertions"]["realDataCalibrationExecuted"])
        self.assertFalse(value["assertions"]["executionEvidenceAccepted"])

    def test_noise_overlap_reasons_are_immutable(self) -> None:
        changed = deepcopy(EVIDENCE)
        noise = next(item for item in changed["findingOutcomes"] if item["findingType"] == "noise")
        noise["reasonCodes"] = ["insufficient_reference_class_support"]
        with self.assertRaises(Stage4ExpandedRealDevelopmentExecutionEvidenceError):
            validate_expanded_real_development_execution_evidence(changed)

    def test_threshold_claim_fails_closed(self) -> None:
        changed = deepcopy(EVIDENCE)
        changed["assertions"]["thresholdsCalibrated"] = True
        with self.assertRaises(Stage4ExpandedRealDevelopmentExecutionEvidenceError):
            validate_expanded_real_development_execution_evidence(changed)

    def test_execution_acceptance_cannot_be_smuggled_in(self) -> None:
        changed = deepcopy(EVIDENCE)
        changed["assertions"]["executionEvidenceAccepted"] = True
        with self.assertRaises(Stage4ExpandedRealDevelopmentExecutionEvidenceError):
            validate_expanded_real_development_execution_evidence(changed)

    def test_private_metric_or_threshold_field_fails_closed(self) -> None:
        for leaked in ({"rawValue": 0.5}, {"possibleThreshold": 0.1}):
            changed = deepcopy(EVIDENCE)
            changed["privateLeak"] = leaked
            with self.assertRaises(Stage4ExpandedRealDevelopmentExecutionEvidenceError):
                validate_expanded_real_development_execution_evidence(changed)


if __name__ == "__main__":
    unittest.main()
