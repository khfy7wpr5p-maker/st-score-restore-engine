from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage4_wikimedia_reference_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    Stage4WikimediaReferenceAcceptanceError,
    summarize_wikimedia_reference_acceptance,
    validate_wikimedia_reference_acceptance,
)

ROOT = Path(__file__).resolve().parents[1]
WORK_PACKAGE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"
COMPLETION = ROOT / "evidence/stage4/corpus-expansion/wikimedia/human-label-completion.v1.json"
ACCEPTANCE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-bundle-acceptance.v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Stage4WikimediaReferenceAcceptanceTests(unittest.TestCase):
    def test_committed_acceptance_is_exact_and_fail_closed(self) -> None:
        value = validate_wikimedia_reference_acceptance(
            _load(ACCEPTANCE), _load(COMPLETION), _load(WORK_PACKAGE)
        )
        self.assertTrue(value["assertions"]["referenceBundleAccepted"])
        self.assertTrue(value["scope"]["candidateDerivationEligible"])
        self.assertFalse(value["assertions"]["realDataCalibrationExecutionAuthorized"])
        self.assertFalse(value["assertions"]["realDataCalibrationExecuted"])
        self.assertFalse(value["assertions"]["productionThresholdChangeAuthorized"])
        self.assertFalse(value["assertions"]["productionResourceLimitChangeAuthorized"])
        self.assertFalse(value["assertions"]["stage4ExitPass"])
        self.assertFalse(value["assertions"]["stage5EntryAuthorized"])

    def test_summary_reports_acceptance_without_execution_authority(self) -> None:
        summary = summarize_wikimedia_reference_acceptance(
            _load(ACCEPTANCE), _load(COMPLETION), _load(WORK_PACKAGE)
        )
        self.assertEqual(summary["acceptanceDigest"]["value"], ACCEPTANCE_CANONICAL_SHA256)
        self.assertEqual(summary["recordCount"], 7)
        self.assertEqual(summary["labelCounts"]["clear"], 7)
        self.assertTrue(summary["referenceBundleAccepted"])
        self.assertTrue(summary["candidateDerivationEligible"])
        self.assertFalse(summary["realDataCalibrationExecutionAuthorized"])
        self.assertFalse(summary["heldOutIncluded"])
        self.assertFalse(summary["stage4ExitPass"])
        self.assertFalse(summary["stage5EntryAuthorized"])

    def test_completion_remains_separate_pending_evidence(self) -> None:
        completion = _load(COMPLETION)
        self.assertEqual(completion["state"], "human_labels_complete_pending_separate_acceptance")
        self.assertFalse(completion["assertions"]["referenceBundleAccepted"])
        self.assertFalse(completion["assertions"]["candidateDerivationEligible"])

    def test_mutated_human_truth_is_rejected(self) -> None:
        completion = deepcopy(_load(COMPLETION))
        completion["bundle"]["records"][0]["referenceLabel"] = "probable"
        with self.assertRaises(Stage4WikimediaReferenceAcceptanceError):
            validate_wikimedia_reference_acceptance(
                _load(ACCEPTANCE), completion, _load(WORK_PACKAGE)
            )

    def test_authority_binding_drift_is_rejected(self) -> None:
        acceptance = deepcopy(_load(ACCEPTANCE))
        acceptance["decisionAuthorityReference"] = "authority:other"
        with self.assertRaises(Stage4WikimediaReferenceAcceptanceError):
            validate_wikimedia_reference_acceptance(
                acceptance, _load(COMPLETION), _load(WORK_PACKAGE)
            )

    def test_acceptance_cannot_authorize_calibration_execution(self) -> None:
        acceptance = deepcopy(_load(ACCEPTANCE))
        acceptance["assertions"]["realDataCalibrationExecutionAuthorized"] = True
        with self.assertRaises(Stage4WikimediaReferenceAcceptanceError):
            validate_wikimedia_reference_acceptance(
                acceptance, _load(COMPLETION), _load(WORK_PACKAGE)
            )

    def test_acceptance_cannot_include_held_out(self) -> None:
        acceptance = deepcopy(_load(ACCEPTANCE))
        acceptance["scope"]["heldOutIncluded"] = True
        with self.assertRaises(Stage4WikimediaReferenceAcceptanceError):
            validate_wikimedia_reference_acceptance(
                acceptance, _load(COMPLETION), _load(WORK_PACKAGE)
            )


if __name__ == "__main__":
    unittest.main()
