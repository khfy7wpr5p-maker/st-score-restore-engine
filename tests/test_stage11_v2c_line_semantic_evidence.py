from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2c" / "v2c-line-semantic-evidence.v1.json"


class Stage11V2cLineSemanticEvidenceTests(unittest.TestCase):
    def _payload(self) -> dict:
        return json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_evidence_is_bound_to_frozen_candidate_and_teacher_review(self) -> None:
        payload = self._payload()
        self.assertEqual("stage11.v2c.line-semantic-evidence.v1", payload["schemaVersion"])
        self.assertEqual(
            "7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234",
            payload["inputs"]["candidatePackageSha256"],
        )
        self.assertEqual(
            "ad083a7ac30f466ec9718d896273a3ce7b4811e248ad859071d49bbf77ef3a0a",
            payload["inputs"]["teacherReviewPdfSha256"],
        )
        self.assertEqual(
            "evidence/stage11/v2c/v2c-teacher-review-resolution.v1.json",
            payload["inputs"]["teacherReviewResolution"],
        )
        self.assertTrue(payload["execution"]["all20CandidateOutputsReproducedAndHashMatchedFull20Evidence"])
        self.assertFalse(payload["inputs"]["heldOutAccessed"])
        self.assertFalse(payload["inputs"]["trainingPerformed"])
        self.assertFalse(payload["inputs"]["weightsMutated"])

    def test_teacher_ground_truth_is_complete_but_detector_coverage_is_separate(self) -> None:
        payload = self._payload()
        self.assertEqual(1.0, payload["teacherGroundTruth"]["annotationCoverage"])
        self.assertEqual(222, payload["teacherGroundTruth"]["independentlyAnnotatedPresentOrAbsentClassCount"])
        self.assertEqual(0, payload["teacherGroundTruth"]["effectiveUnknownReviewRequiredCount"])
        self.assertTrue(payload["teacherGroundTruth"]["followupConflictResolutionComplete"])
        self.assertEqual(171, payload["coverage"]["eligibleExpectedPresentClassPageCount"])
        self.assertEqual(10, payload["coverage"]["confidentlyEvaluatedExpectedPresentClassPageCount"])
        self.assertAlmostEqual(10 / 171, payload["coverage"]["applicableClassDetectorCoverage"])
        self.assertFalse(payload["coverage"]["automaticSemanticPassEvidenceAvailable"])

    def test_line_detector_results_cannot_claim_semantic_success(self) -> None:
        payload = self._payload()
        staff = payload["classResults"]["staff_line"]
        tab = payload["classResults"]["tab_line"]
        self.assertEqual(10, staff["sourceConfidentlyEvaluatedPresentPages"])
        self.assertEqual(30, staff["matchedCount"])
        self.assertAlmostEqual(0.6, staff["sourceRecallOnDetectorEvaluatedPresent"])
        self.assertEqual(0, tab["sourceConfidentlyEvaluatedPresentPages"])
        self.assertEqual(2, len(tab["candidateDetectionsOnExpectedAbsentPages"]))
        self.assertFalse(payload["safetyAssessment"]["detectorCoverageSufficientForSemanticPreservationClaim"])
        self.assertEqual("blocked", payload["safetyAssessment"]["disposition"])
        self.assertFalse(payload["safetyAssessment"]["hardBlocker"])
        self.assertTrue(payload["claimBoundary"]["teacherGroundTruthComplete"])
        self.assertFalse(payload["claimBoundary"]["semanticPreservationEstablished"])
        self.assertFalse(payload["claimBoundary"]["productionPromotionAuthorized"])
        self.assertFalse(payload["claimBoundary"]["stage12EntryAuthorized"])

    def test_all_twenty_page_results_are_present_and_unique(self) -> None:
        payload = self._payload()
        rows = payload["pageResults"]
        self.assertEqual(20, len(rows))
        self.assertEqual(20, len({row[0] for row in rows}))
        self.assertTrue(all(len(row[-1]) == 64 for row in rows))


if __name__ == "__main__":
    unittest.main()
