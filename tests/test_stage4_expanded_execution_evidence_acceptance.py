from __future__ import annotations

import json
import unittest
from pathlib import Path

from st_score_restore.stage4_expanded_execution_evidence_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    summarize_expanded_execution_evidence_acceptance,
    validate_expanded_execution_evidence_acceptance,
)

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_PATH = ROOT / "evidence/stage4/governance/expanded-development-execution-evidence-acceptance.v1.json"
EXECUTION_PATH = ROOT / "evidence/stage4/calibration/expanded-real-development-execution.v1.json"


class ExpandedExecutionEvidenceAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.acceptance = json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))
        cls.execution = json.loads(EXECUTION_PATH.read_text(encoding="utf-8"))

    def test_acceptance_is_valid(self) -> None:
        value = validate_expanded_execution_evidence_acceptance(self.acceptance, self.execution)
        self.assertTrue(value["assertions"]["executionEvidenceAccepted"])
        self.assertFalse(value["assertions"]["thresholdsCalibrated"])
        self.assertFalse(value["assertions"]["stage4ExitPass"])
        self.assertFalse(value["assertions"]["stage5EntryAuthorized"])

    def test_source_execution_remains_immutable(self) -> None:
        self.assertFalse(self.execution["assertions"]["executionEvidenceAccepted"])
        self.assertEqual(self.execution["summary"]["candidateDerivedCount"], 0)

    def test_summary_digest(self) -> None:
        summary = summarize_expanded_execution_evidence_acceptance(self.acceptance, self.execution)
        self.assertEqual(summary["acceptanceDigest"]["value"], ACCEPTANCE_CANONICAL_SHA256)
        self.assertTrue(summary["executionEvidenceAccepted"])


if __name__ == "__main__":
    unittest.main()
