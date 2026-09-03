from __future__ import annotations

import json
from pathlib import Path
import unittest

from st_score_restore.stage4_wikimedia_reference_gate import (
    build_wikimedia_reference_completion_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
WORK_PACKAGE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"
COMPLETION = ROOT / "evidence/stage4/corpus-expansion/wikimedia/human-label-completion.v1.json"


class Stage4WikimediaHumanLabelCompletionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.package = json.loads(WORK_PACKAGE.read_text(encoding="utf-8"))
        self.completion = json.loads(COMPLETION.read_text(encoding="utf-8"))

    def test_completion_rebuilds_exactly_from_external_human_rows(self) -> None:
        rows = [
            {
                "labelId": record["labelId"],
                "observationId": record["observationId"],
                "findingType": record["findingType"],
                "referenceLabel": record["referenceLabel"],
                "reviewerReference": record["reviewerReference"],
                "provenanceReference": record["provenanceReference"],
                "reviewedOn": record["reviewedOn"],
            }
            for record in self.completion["bundle"]["records"]
        ]
        rebuilt = build_wikimedia_reference_completion_candidate(self.package, rows)
        self.assertEqual(rebuilt, self.completion)

    def test_seven_supplied_labels_are_all_clear(self) -> None:
        records = self.completion["bundle"]["records"]
        self.assertEqual(len(records), 7)
        self.assertEqual({record["referenceLabel"] for record in records}, {"clear"})
        self.assertEqual(
            self.completion["labelCounts"],
            {"clear": 7, "not_assessed": 0, "possible": 0, "probable": 0},
        )

    def test_completion_does_not_open_downstream_gates(self) -> None:
        assertions = self.completion["assertions"]
        self.assertTrue(assertions["humanLabelsPresent"])
        for key in (
            "labelsAutomaticallyGenerated",
            "modelPredictionsUsedAsReferenceLabels",
            "referenceBundleAccepted",
            "candidateDerivationEligible",
            "expansionCalibrationExecutionAuthorized",
            "expansionCalibrationExecuted",
            "heldOutIncludedInDevelopmentReview",
            "productionThresholdChangeAuthorized",
            "productionResourceLimitChangeAuthorized",
            "stage4ExitPass",
            "stage5EntryAuthorized",
        ):
            self.assertFalse(assertions[key], key)

    def test_committed_work_package_remains_pristine(self) -> None:
        reviews = self.package["item"]["pages"][0]["reviews"]
        self.assertEqual(len(reviews), 7)
        for row in reviews:
            for field in ("referenceLabel", "reviewerReference", "provenanceReference", "reviewedOn"):
                self.assertIsNone(row[field], f"{row['findingType']}:{field}")


if __name__ == "__main__":
    unittest.main()
