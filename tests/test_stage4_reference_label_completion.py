from __future__ import annotations

import json
from pathlib import Path
import unittest

from st_score_restore.stage4_reference_label_completion import (
    BUNDLE_CANONICAL_SHA256,
    COMPLETION_CANONICAL_SHA256,
    EXPECTED_LABEL_COUNTS,
    Stage4ReferenceLabelCompletionError,
    summarize_reference_label_completion,
    validate_reference_label_completion,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/stage4/reference-labels/development-human-label-completion.v1.json"


class Stage4ReferenceLabelCompletionTests(unittest.TestCase):
    def _load(self):
        return json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_committed_completion_evidence_is_valid_and_pending_acceptance(self):
        value = validate_reference_label_completion(self._load())
        self.assertEqual(value["state"], "human_labels_complete_pending_acceptance")
        self.assertEqual(len(value["bundle"]["records"]), 42)
        self.assertTrue(value["assertions"]["humanLabelsPresent"])
        self.assertFalse(value["assertions"]["referenceBundleAccepted"])
        self.assertFalse(value["assertions"]["realDataCalibrationExecuted"])
        self.assertEqual(value["labelCounts"], EXPECTED_LABEL_COUNTS)
        self.assertEqual(value["bundleDigest"]["value"], BUNDLE_CANONICAL_SHA256)

    def test_summary_keeps_real_execution_closed(self):
        summary = summarize_reference_label_completion(self._load())
        self.assertEqual(summary["completionDigest"]["value"], COMPLETION_CANONICAL_SHA256)
        self.assertEqual(summary["recordCount"], 42)
        self.assertFalse(summary["referenceBundleAccepted"])
        self.assertFalse(summary["realDataCalibrationExecutionAuthorized"])
        self.assertFalse(summary["heldOutIncluded"])

    def test_model_or_automatic_reference_claim_is_rejected(self):
        value = self._load()
        value["assertions"]["modelPredictionsUsedAsReferenceLabels"] = True
        with self.assertRaises(Stage4ReferenceLabelCompletionError):
            validate_reference_label_completion(value)

    def test_held_out_or_scope_substitution_is_rejected(self):
        value = self._load()
        value["bundle"]["records"][0]["datasetItemId"] = "dataset.item.imslp82860-chopin-op69.v2"
        with self.assertRaises((Stage4ReferenceLabelCompletionError, ValueError)):
            validate_reference_label_completion(value)

    def test_label_tampering_is_rejected_by_digest(self):
        value = self._load()
        value["bundle"]["records"][0]["referenceLabel"] = "probable"
        with self.assertRaises(Stage4ReferenceLabelCompletionError):
            validate_reference_label_completion(value)


if __name__ == "__main__":
    unittest.main()
