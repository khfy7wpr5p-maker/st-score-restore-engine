from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "evidence/stage11/v2d/v2d-general-clef-successor-prequalification-policy.v1.json"


class Stage11V2dGeneralClefPrequalificationPolicyTests(unittest.TestCase):
    def _payload(self) -> dict:
        self.assertTrue(POLICY.is_file(), "frozen general-clef prequalification policy must be committed")
        return json.loads(POLICY.read_text(encoding="utf-8"))

    def test_candidate_and_policy_are_frozen_before_any_fresh_holdout(self) -> None:
        payload = self._payload()

        self.assertEqual(
            "stage11.v2d.general-clef-successor-prequalification-policy.v1",
            payload["schemaVersion"],
        )
        self.assertEqual(
            "FROZEN_BEFORE_NEW_INDEPENDENT_HOLDOUT_ACCESS",
            payload["status"],
        )
        self.assertEqual(
            "stage11-general-clef-candidate-generator.hybrid-oemer-staff-relative-c-review.v2",
            payload["candidate"]["candidateGeneratorId"],
        )
        self.assertEqual(
            "1cc4108319eb0c0531f4fbeced0d30738c6bd541",
            payload["candidate"]["candidateGeneratorBlobSha"],
        )
        self.assertEqual(
            "8bef05863aa15df9da102f5bfd71345435657bbc",
            payload["candidate"]["successorBlobSha"],
        )
        self.assertTrue(payload["claimBoundary"]["generalClefCandidateFrozen"])
        self.assertTrue(payload["claimBoundary"]["prequalificationPolicyFrozen"])
        self.assertFalse(payload["holdoutFirewall"]["newIndependentHoldoutOpenedByThisArtifact"])
        self.assertFalse(payload["claimBoundary"]["freshIndependentHoldoutAccessed"])
        self.assertFalse(payload["claimBoundary"]["detectorQualified"])

    def test_frozen_typed_thresholds_match_approved_development_gate(self) -> None:
        payload = self._payload()
        thresholds = payload["frozenThresholds"]

        self.assertEqual(0.90, thresholds["typedPooledPrecisionMinimum"])
        self.assertEqual(0.85, thresholds["typedPooledRecallMinimum"])
        self.assertEqual(
            {"treble": 0.90, "bass": 0.85, "tab": 0.80},
            thresholds["typedSubtypeRecallMinimum"],
        )
        self.assertEqual(0.80, thresholds["cClefReviewPrecisionMinimum"])
        self.assertEqual(0.80, thresholds["cClefReviewRecallMinimum"])
        self.assertTrue(thresholds["determinismRequired"])
        self.assertTrue(thresholds["allCriteriaConjunctive"])

    def test_soprano_scope_is_review_only_and_never_auto_typed(self) -> None:
        payload = self._payload()
        scope = payload["qualificationScope"]["sopranoAndCClef"]

        self.assertEqual("EXPLICIT_REVIEW_ONLY", scope["mode"])
        self.assertEqual("unknown", scope["requiredOutputClefType"])
        self.assertEqual("REVIEW_REQUIRED", scope["requiredStatus"])
        self.assertEqual("POSSIBLE_C_CLEF", scope["requiredReason"])
        self.assertFalse(scope["autoSubtypeAssignmentAllowed"])
        self.assertFalse(scope["typedSopranoQualificationClaimAllowed"])

    def test_independent_holdout_firewall_is_one_shot_and_disjoint(self) -> None:
        payload = self._payload()
        holdout = payload["independentHoldoutRequirements"]

        self.assertIn("18-page/213-box general-clef development corpus", holdout["disjointFrom"])
        self.assertIn("P4.7 spent holdout", holdout["disjointFrom"])
        self.assertIn("P4.9 spent holdout", holdout["disjointFrom"])
        self.assertTrue(holdout["teacherTruthFrozenBlindToPredictions"])
        self.assertTrue(holdout["sourceBytesAndManifestFrozenBeforeInference"])
        self.assertTrue(holdout["candidateABDeterminismRequired"])
        self.assertTrue(holdout["noPostAccessCodeOrThresholdChanges"])
        self.assertTrue(holdout["oneShotPassFail"])
        self.assertTrue(holdout["representativeTrebleBassTabRequired"])
        self.assertTrue(holdout["positiveAndNegativeEvidenceRequired"])
        self.assertEqual(
            "NO_OVERALL_GENERAL_CLEF_QUALIFICATION_CLAIM",
            holdout["ifNoIndependentCClefReviewPositiveAvailable"],
        )


if __name__ == "__main__":
    unittest.main()
