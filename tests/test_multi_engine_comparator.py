from __future__ import annotations

import json
from pathlib import Path
import unittest

from st_score_restore.multi_engine_comparator import (
    OUTCOME_ORIGINAL_PREFERRED,
    OUTCOME_ORIGINAL_RETAINED,
    OUTCOME_REVIEW_REQUIRED,
    OUTCOME_VARIANT_PREFERRED,
    ComparatorContractError,
    compare_restoration_variants,
    run_synthetic_comparator_drills,
)

ROOT = Path(__file__).resolve().parents[1]


class Stage9ComparatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = "sha256:source"

    def variant(self, artifact: str, **overrides):
        item = {
            "artifactId": artifact,
            "engineId": "opencv",
            "engineVersion": "1",
            "configDigest": "sha256:config",
            "derivedFrom": self.source,
            "safetyVerdict": "pass",
            "qualityEvidence": {"documentQualityDelta": 1, "legibilityDelta": 1},
            "structuralRisk": 0.1,
        }
        item.update(overrides)
        return item

    def test_reject_cannot_win_even_with_huge_quality_evidence(self) -> None:
        safe = self.variant("sha256:safe")
        rejected = self.variant(
            "sha256:rejected",
            engineId="docres",
            safetyVerdict="reject",
            qualityEvidence={"documentQualityDelta": 9999, "legibilityDelta": 9999},
            structuralRisk=0,
        )
        result = compare_restoration_variants(self.source, [rejected, safe])
        self.assertEqual(OUTCOME_VARIANT_PREFERRED, result["outcome"])
        self.assertEqual("sha256:safe", result["recommendedArtifactId"])
        self.assertEqual(1, result["hardRejectedDerivativeCount"])

    def test_hard_semantic_veto_cannot_be_overridden(self) -> None:
        result = compare_restoration_variants(
            self.source,
            [self.variant("sha256:veto", semanticHardVeto=True, qualityEvidence={"documentQualityDelta": 500})],
        )
        self.assertEqual(OUTCOME_ORIGINAL_RETAINED, result["outcome"])
        self.assertEqual(self.source, result["recommendedArtifactId"])

    def test_original_wins_without_positive_improvement_evidence(self) -> None:
        no_gain = self.variant(
            "sha256:no-gain",
            qualityEvidence={"documentQualityDelta": 0, "legibilityDelta": 0, "contrastDelta": 0},
            structuralRisk=0,
        )
        result = compare_restoration_variants(self.source, [no_gain])
        self.assertEqual(OUTCOME_ORIGINAL_PREFERRED, result["outcome"])
        self.assertEqual(self.source, result["recommendedArtifactId"])
        self.assertTrue(result["originalSelectable"])

    def test_review_required_never_becomes_automatic_winner(self) -> None:
        result = compare_restoration_variants(
            self.source,
            [self.variant("sha256:review", safetyVerdict="review_required", qualityEvidence={"documentQualityDelta": 100})],
        )
        self.assertEqual(OUTCOME_REVIEW_REQUIRED, result["outcome"])
        self.assertEqual(self.source, result["recommendedArtifactId"])
        self.assertFalse(result["automaticFinalSelectionAuthorized"])

    def test_unknown_safety_fails_safe_to_review_with_original_retained(self) -> None:
        result = compare_restoration_variants(self.source, [self.variant("sha256:unknown", safetyVerdict="")])
        self.assertEqual(OUTCOME_REVIEW_REQUIRED, result["outcome"])
        self.assertEqual(self.source, result["recommendedArtifactId"])

    def test_provenance_mismatch_is_not_eligible(self) -> None:
        result = compare_restoration_variants(
            self.source,
            [self.variant("sha256:mismatch", derivedFrom="sha256:different")],
        )
        self.assertEqual(0, result["eligibleDerivativeCount"])
        self.assertEqual(OUTCOME_REVIEW_REQUIRED, result["outcome"])

    def test_exact_quality_tie_routes_to_review(self) -> None:
        a = self.variant("sha256:a", engineId="opencv")
        b = self.variant("sha256:b", engineId="docres")
        result = compare_restoration_variants(self.source, [a, b])
        self.assertEqual(OUTCOME_REVIEW_REQUIRED, result["outcome"])
        self.assertEqual(self.source, result["recommendedArtifactId"])
        self.assertIn("quality_evidence_tie", result["reasonCodes"])

    def test_order_is_deterministic(self) -> None:
        weak = self.variant("sha256:weak", qualityEvidence={"documentQualityDelta": 1, "legibilityDelta": 0})
        strong = self.variant("sha256:strong", qualityEvidence={"documentQualityDelta": 2, "legibilityDelta": 0})
        first = compare_restoration_variants(self.source, [weak, strong])
        second = compare_restoration_variants(self.source, [strong, weak])
        self.assertEqual(first["recommendedArtifactId"], second["recommendedArtifactId"])
        self.assertEqual("sha256:strong", first["recommendedArtifactId"])

    def test_non_finite_quality_evidence_is_rejected(self) -> None:
        with self.assertRaises(ComparatorContractError):
            compare_restoration_variants(
                self.source,
                [self.variant("sha256:bad", qualityEvidence={"documentQualityDelta": "NaN"})],
            )

    def test_contract_is_recommendation_only(self) -> None:
        result = compare_restoration_variants(self.source, [self.variant("sha256:safe")])
        self.assertTrue(result["recommendationOnly"])
        self.assertFalse(result["automaticFinalSelectionAuthorized"])
        self.assertFalse(result["teacherApprovalImplied"])
        self.assertFalse(result["omrCorrectnessImplied"])
        self.assertFalse(result["musicalTruthImplied"])

    def test_synthetic_drills_pass(self) -> None:
        self.assertEqual("PASS", run_synthetic_comparator_drills()["result"])

    def test_entry_authorization_scope_is_fail_closed(self) -> None:
        auth = json.loads((ROOT / "evidence/stage9/stage9-entry-authorization.v1.json").read_text(encoding="utf-8"))
        self.assertTrue(auth["scope"]["stage9EntryAuthorized"])
        self.assertFalse(auth["scope"]["stage9aEntryAuthorized"])
        self.assertFalse(auth["scope"]["stage10EntryAuthorized"])
        self.assertFalse(auth["scope"]["productionDeploymentAuthorized"])
        self.assertFalse(auth["scope"]["automaticFinalSelectionAuthorized"])


if __name__ == "__main__":
    unittest.main()
