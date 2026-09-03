from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage4_real_development_execution_evidence import (
    Stage4RealDevelopmentExecutionEvidenceError,
    validate_real_development_execution_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = json.loads((ROOT / "evidence/stage4/calibration/real-development-execution.v1.json").read_text(encoding="utf-8"))


class Stage4RealDevelopmentExecutionEvidenceTests(unittest.TestCase):
    def test_canonical_evidence_is_valid(self) -> None:
        validated = validate_real_development_execution_evidence(EVIDENCE)
        self.assertEqual(validated["state"], "executed_abstained")
        self.assertTrue(validated["assertions"]["realDataCalibrationExecuted"])
        self.assertFalse(validated["assertions"]["thresholdsCalibrated"])
        self.assertEqual(validated["summary"]["candidateDerivedCount"], 0)

    def test_threshold_claim_fails_closed(self) -> None:
        changed = deepcopy(EVIDENCE)
        changed["assertions"]["thresholdsCalibrated"] = True
        with self.assertRaises(Stage4RealDevelopmentExecutionEvidenceError):
            validate_real_development_execution_evidence(changed)

    def test_held_out_claim_fails_closed(self) -> None:
        changed = deepcopy(EVIDENCE)
        changed["assertions"]["heldOutEvaluationUsed"] = True
        with self.assertRaises(Stage4RealDevelopmentExecutionEvidenceError):
            validate_real_development_execution_evidence(changed)

    def test_private_row_field_fails_closed(self) -> None:
        changed = deepcopy(EVIDENCE)
        changed["privateLeak"] = {"rawValue": 0.5}
        with self.assertRaises(Stage4RealDevelopmentExecutionEvidenceError):
            validate_real_development_execution_evidence(changed)


if __name__ == "__main__":
    unittest.main()
