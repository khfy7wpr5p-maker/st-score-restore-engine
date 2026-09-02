from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage4_reference_label_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    ACCEPTANCE_DECISION,
    Stage4ReferenceLabelAcceptanceError,
    summarize_reference_label_acceptance,
    validate_reference_label_acceptance,
)
from st_score_restore.stage4_reference_label_completion import BUNDLE_ID
from st_score_restore.stage4_reference_labels import ReferenceLabelBundle, require_candidate_derivation_eligible

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "evidence/stage4/reference-labels/development-reference-bundle-acceptance.v1.json"
COMPLETION = ROOT / "evidence/stage4/reference-labels/development-human-label-completion.v1.json"


class Stage4ReferenceLabelAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
        cls.completion = json.loads(COMPLETION.read_text(encoding="utf-8"))

    def test_committed_acceptance_is_valid_and_fail_closed_downstream(self) -> None:
        value = validate_reference_label_acceptance(self.acceptance, self.completion)
        self.assertEqual(value["decision"], ACCEPTANCE_DECISION)
        self.assertTrue(value["assertions"]["referenceBundleAccepted"])
        self.assertFalse(value["assertions"]["realDataCalibrationExecutionAuthorized"])
        self.assertFalse(value["assertions"]["realDataCalibrationExecuted"])
        self.assertFalse(value["scope"]["heldOutIncluded"])
        self.assertFalse(value["scope"]["heldOutTuningAuthorized"])

        summary = summarize_reference_label_acceptance(self.acceptance, self.completion)
        self.assertEqual(summary["acceptanceDigest"]["value"], ACCEPTANCE_CANONICAL_SHA256)
        self.assertEqual(summary["recordCount"], 42)
        self.assertTrue(summary["candidateDerivationEligible"])
        self.assertFalse(summary["realDataCalibrationExecutionAuthorized"])
        self.assertFalse(summary["stage4ExitPass"])
        self.assertFalse(summary["stage5EntryAuthorized"])

    def test_acceptance_makes_only_development_bundle_derivation_eligible(self) -> None:
        records = self.completion["bundle"]["records"]
        bundle = ReferenceLabelBundle.from_records(BUNDLE_ID, records)
        require_candidate_derivation_eligible(bundle, accepted_real_reference_bundle=True)
        self.assertEqual(bundle.split, "development")
        self.assertEqual(bundle.data_class, "real")
        self.assertEqual(bundle.purpose, "safety_calibration")

    def test_tampered_bundle_binding_is_rejected(self) -> None:
        value = deepcopy(self.acceptance)
        value["bundleDigest"]["value"] = "0" * 64
        with self.assertRaises(Stage4ReferenceLabelAcceptanceError):
            validate_reference_label_acceptance(value, self.completion)

    def test_execution_authorization_cannot_be_smuggled_into_acceptance(self) -> None:
        value = deepcopy(self.acceptance)
        value["assertions"]["realDataCalibrationExecutionAuthorized"] = True
        with self.assertRaises(Stage4ReferenceLabelAcceptanceError):
            validate_reference_label_acceptance(value, self.completion)

    def test_completion_must_remain_immutable_pending_acceptance_evidence(self) -> None:
        completion = deepcopy(self.completion)
        completion["assertions"]["referenceBundleAccepted"] = True
        with self.assertRaises(Exception):
            validate_reference_label_acceptance(self.acceptance, completion)


if __name__ == "__main__":
    unittest.main()
