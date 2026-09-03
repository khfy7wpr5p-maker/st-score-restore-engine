from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage4_wikimedia_reference_gate import (
    EXPECTED_REVIEW_COUNT,
    Stage4WikimediaReferenceGateError,
    build_wikimedia_reference_completion_candidate,
    validate_wikimedia_review_work_package,
)


ROOT = Path(__file__).resolve().parents[1]
WORK_PACKAGE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"


def _load_package() -> dict:
    return json.loads(WORK_PACKAGE.read_text(encoding="utf-8"))


def _contract_only_completed_rows(package: dict) -> list[dict]:
    """Synthetic unit-test input only; this is not repository human-review evidence."""

    rows = []
    for index, baseline in enumerate(package["item"]["pages"][0]["reviews"]):
        rows.append(
            {
                "labelId": baseline["labelId"],
                "observationId": baseline["observationId"],
                "findingType": baseline["findingType"],
                "referenceLabel": "clear" if index < 5 else "possible",
                "reviewerReference": "reviewer:opq_0123456789abcdef0123456789abcdef",
                "provenanceReference": "evidence:opq_fedcba9876543210fedcba9876543210",
                "reviewedOn": "2026-09-03",
            }
        )
    return rows


class Stage4WikimediaReferenceGateTests(unittest.TestCase):
    def test_committed_work_package_remains_pristine_and_awaiting_human_labels(self) -> None:
        package = validate_wikimedia_review_work_package(_load_package())
        reviews = package["item"]["pages"][0]["reviews"]
        self.assertEqual(len(reviews), EXPECTED_REVIEW_COUNT)
        for row in reviews:
            self.assertIsNone(row["referenceLabel"])
            self.assertIsNone(row["reviewerReference"])
            self.assertIsNone(row["provenanceReference"])
            self.assertIsNone(row["reviewedOn"])

    def test_completion_cannot_be_built_without_all_seven_external_human_rows(self) -> None:
        with self.assertRaises(Stage4WikimediaReferenceGateError) as raised:
            build_wikimedia_reference_completion_candidate(_load_package(), [])
        self.assertEqual(raised.exception.code, "human_labels_incomplete")

    def test_contract_only_complete_input_still_keeps_all_downstream_gates_closed(self) -> None:
        package = _load_package()
        candidate = build_wikimedia_reference_completion_candidate(
            package, _contract_only_completed_rows(package)
        )
        self.assertEqual(candidate["state"], "human_labels_complete_pending_separate_acceptance")
        self.assertEqual(len(candidate["bundle"]["records"]), EXPECTED_REVIEW_COUNT)
        self.assertEqual(candidate["labelCounts"], {"clear": 5, "not_assessed": 0, "possible": 2, "probable": 0})
        assertions = candidate["assertions"]
        self.assertTrue(assertions["humanLabelsPresent"])
        self.assertFalse(assertions["labelsAutomaticallyGenerated"])
        self.assertFalse(assertions["modelPredictionsUsedAsReferenceLabels"])
        self.assertFalse(assertions["referenceBundleAccepted"])
        self.assertFalse(assertions["candidateDerivationEligible"])
        self.assertFalse(assertions["expansionCalibrationExecutionAuthorized"])
        self.assertFalse(assertions["expansionCalibrationExecuted"])
        self.assertFalse(assertions["heldOutIncludedInDevelopmentReview"])
        self.assertFalse(assertions["stage4ExitPass"])
        self.assertFalse(assertions["stage5EntryAuthorized"])

    def test_non_opaque_reviewer_reference_is_rejected(self) -> None:
        package = _load_package()
        rows = _contract_only_completed_rows(package)
        rows[0]["reviewerReference"] = "reviewer:Jane-Doe"
        with self.assertRaises(Stage4WikimediaReferenceGateError) as raised:
            build_wikimedia_reference_completion_candidate(package, rows)
        self.assertEqual(raised.exception.code, "reviewer_reference_not_opaque")

    def test_model_or_generated_truth_fields_are_not_accepted(self) -> None:
        package = _load_package()
        rows = _contract_only_completed_rows(package)
        rows[0]["predictedLabel"] = "clear"
        with self.assertRaises(Stage4WikimediaReferenceGateError) as raised:
            build_wikimedia_reference_completion_candidate(package, rows)
        self.assertEqual(raised.exception.code, "invalid_completed_reviews")

    def test_committed_work_package_cannot_be_prelabelled(self) -> None:
        package = deepcopy(_load_package())
        package["item"]["pages"][0]["reviews"][0]["referenceLabel"] = "clear"
        with self.assertRaises(Stage4WikimediaReferenceGateError) as raised:
            validate_wikimedia_review_work_package(package)
        self.assertEqual(raised.exception.code, "committed_human_truth_forbidden")

    def test_review_identity_mismatch_is_rejected(self) -> None:
        package = _load_package()
        rows = _contract_only_completed_rows(package)
        rows[0]["observationId"] = "stage4.obs.out-of-scope.v1"
        with self.assertRaises(Stage4WikimediaReferenceGateError) as raised:
            build_wikimedia_reference_completion_candidate(package, rows)
        self.assertEqual(raised.exception.code, "review_identity_mismatch")


if __name__ == "__main__":
    unittest.main()
