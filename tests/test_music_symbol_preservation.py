from __future__ import annotations

import unittest

from st_score_restore.multi_engine_comparator import compare_restoration_variants
from st_score_restore.music_symbol_preservation import (
    CONTRACT_VERSION,
    TAXONOMY_VERSION,
    PreservationContractError,
    apply_preservation_to_variant,
    assess_preservation_evidence,
    run_synthetic_mspm_drills,
    safe_assess_preservation_evidence,
)

SOURCE = "sha256:test-source"


def evidence(candidate: str, findings=None, *, coverage="complete", state="assessed"):
    return {
        "contractVersion": CONTRACT_VERSION,
        "taxonomyVersion": TAXONOMY_VERSION,
        "sourceArtifactId": SOURCE,
        "candidateArtifactId": candidate,
        "component": {
            "id": "test-component",
            "version": "1",
            "artifactDigest": "sha256:test-component",
            "mode": "synthetic",
        },
        "assessmentState": state,
        "coverageState": coverage,
        "findings": list(findings or []),
    }


def variant(candidate: str):
    return {
        "artifactId": candidate,
        "engineId": "opencv",
        "engineVersion": "test-1",
        "configDigest": "sha256:test-config",
        "derivedFrom": SOURCE,
        "safetyVerdict": "pass",
        "qualityEvidence": {
            "documentQualityDelta": 2,
            "legibilityDelta": 1,
            "contrastDelta": 1,
            "noiseReductionEvidence": 1,
        },
        "structuralRisk": 0,
    }


class MusicSymbolPreservationTests(unittest.TestCase):
    def test_material_symbol_loss_is_hard_veto(self):
        candidate = "sha256:missing"
        assessment = assess_preservation_evidence(
            evidence(
                candidate,
                [{
                    "evidenceId": "f1",
                    "symbolClass": "accidental",
                    "riskCode": "symbol_missing_after_restoration",
                    "disposition": "hard_veto",
                    "materiality": "material",
                }],
            )
        )
        self.assertTrue(assessment["semanticHardVeto"])
        handed = apply_preservation_to_variant(variant(candidate), assessment)
        result = compare_restoration_variants(SOURCE, [handed])
        self.assertEqual(result["recommendedArtifactId"], SOURCE)
        self.assertEqual(result["hardRejectedDerivativeCount"], 1)

    def test_uncertainty_routes_review_and_retains_original(self):
        candidate = "sha256:uncertain"
        assessment = assess_preservation_evidence(
            evidence(
                candidate,
                [{
                    "evidenceId": "f2",
                    "symbolClass": "tab_digit",
                    "riskCode": "semantic_comparison_uncertain",
                    "disposition": "review",
                    "materiality": "uncertain",
                }],
            )
        )
        handed = apply_preservation_to_variant(variant(candidate), assessment)
        self.assertEqual(handed["safetyVerdict"], "review_required")
        result = compare_restoration_variants(SOURCE, [handed])
        self.assertEqual(result["outcome"], "review_required")
        self.assertEqual(result["recommendedArtifactId"], SOURCE)

    def test_complete_no_harm_evidence_can_reach_comparator(self):
        candidate = "sha256:safe"
        assessment = assess_preservation_evidence(evidence(candidate))
        self.assertEqual(assessment["status"], "pass")
        handed = apply_preservation_to_variant(variant(candidate), assessment)
        result = compare_restoration_variants(SOURCE, [handed])
        self.assertEqual(result["recommendedArtifactId"], candidate)
        self.assertFalse(result["automaticFinalSelectionAuthorized"])

    def test_partial_coverage_cannot_silently_pass(self):
        candidate = "sha256:partial"
        assessment = assess_preservation_evidence(evidence(candidate, coverage="partial"))
        self.assertTrue(assessment["reviewRequired"])
        self.assertNotEqual(assessment["status"], "pass")

    def test_unknown_risk_cannot_create_unreviewed_hard_veto(self):
        candidate = "sha256:future-risk"
        assessment = assess_preservation_evidence(
            evidence(
                candidate,
                [{
                    "evidenceId": "f3",
                    "symbolClass": "future_symbol",
                    "riskCode": "future_risk",
                    "disposition": "hard_veto",
                    "materiality": "material",
                }],
            )
        )
        self.assertFalse(assessment["semanticHardVeto"])
        self.assertTrue(assessment["reviewRequired"])

    def test_malformed_evidence_fails_safe(self):
        candidate = "sha256:malformed"
        malformed = evidence("sha256:wrong")
        assessment = safe_assess_preservation_evidence(
            malformed,
            expected_source_artifact_id=SOURCE,
            expected_candidate_artifact_id=candidate,
        )
        self.assertTrue(assessment["reviewRequired"])
        handed = apply_preservation_to_variant(variant(candidate), assessment)
        result = compare_restoration_variants(SOURCE, [handed])
        self.assertEqual(result["recommendedArtifactId"], SOURCE)

    def test_direct_binding_mismatch_rejected(self):
        candidate = "sha256:candidate"
        assessment = assess_preservation_evidence(evidence(candidate))
        wrong_variant = variant("sha256:other")
        with self.assertRaises(PreservationContractError):
            apply_preservation_to_variant(wrong_variant, assessment)

    def test_synthetic_drills_pass_without_live_or_training(self):
        drills = run_synthetic_mspm_drills()
        self.assertEqual(drills["result"], "PASS")
        self.assertTrue(drills["syntheticOnly"])
        self.assertFalse(drills["realUserDataUsed"])
        self.assertFalse(drills["modelTrainingPerformed"])
        self.assertFalse(drills["productionInferencePerformed"])
        self.assertFalse(drills["stage10Activated"])


if __name__ == "__main__":
    unittest.main()
