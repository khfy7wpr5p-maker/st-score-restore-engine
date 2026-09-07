from __future__ import annotations

import unittest

from st_score_restore.st_restore_selector import (
    DECISION_ORIGINAL,
    DECISION_REVIEW,
    DECISION_VARIANT,
    SelectorContractError,
    plan_engine_invocations,
    run_synthetic_selector_drills,
    select_source_variant,
)


class STRestoreSelectorTests(unittest.TestCase):
    def setUp(self):
        self.source = "sha256:test-source"
        self.variant = {
            "artifactId": "sha256:test-variant",
            "role": "restoration_variant",
            "engineId": "opencv",
            "engineVersion": "1",
            "configDigest": "sha256:cfg",
            "derivedFrom": self.source,
            "safetyVerdict": "pass",
            "hardVeto": False,
            "reviewRequired": False,
            "eligible": True,
        }
        self.comparator = {
            "contractVersion": "stage9.multi-engine-comparator.v1",
            "outcome": "restoration_variant_preferred",
            "recommendedArtifactId": self.variant["artifactId"],
            "recommendedRole": "restoration_variant",
            "recommendationOnly": True,
            "automaticFinalSelectionAuthorized": False,
            "originalSelectable": True,
            "originalArtifactId": self.source,
            "variants": [self.variant],
        }
        self.preservation = {
            self.variant["artifactId"]: {
                "contractVersion": "stage9a.mspm-evidence.v1",
                "sourceArtifactId": self.source,
                "candidateArtifactId": self.variant["artifactId"],
                "assessmentState": "assessed",
                "coverageState": "complete",
                "status": "pass",
                "semanticHardVeto": False,
                "reviewRequired": False,
                "automaticApproval": False,
            }
        }

    def test_synthetic_drills_pass(self):
        result = run_synthetic_selector_drills()
        self.assertEqual(result["result"], "PASS")
        self.assertFalse(result["liveSelectorActivated"])
        self.assertFalse(result["productionDeploymentPerformed"])

    def test_engine_plan_skips_unapproved_and_disabled_engines(self):
        result = plan_engine_invocations(
            self.source,
            [
                {"engineId": "opencv", "approvalState": "approved", "availabilityState": "available", "enabled": True},
                {"engineId": "docres", "approvalState": "unapproved", "availabilityState": "available", "enabled": True},
                {"engineId": "future", "approvalState": "approved", "availabilityState": "available", "enabled": False},
            ],
        )
        by_engine = {item["engineId"]: item for item in result["invocationPlan"]}
        self.assertEqual(by_engine["opencv"]["action"], "invoke")
        self.assertEqual(by_engine["docres"]["action"], "skip")
        self.assertEqual(by_engine["future"]["action"], "skip")
        self.assertTrue(result["originalIncluded"])

    def test_duplicate_engine_identity_fails_closed(self):
        with self.assertRaises(SelectorContractError):
            plan_engine_invocations(
                self.source,
                [
                    {"engineId": "opencv", "approvalState": "approved", "availabilityState": "available", "enabled": True},
                    {"engineId": "opencv", "approvalState": "approved", "availabilityState": "available", "enabled": True},
                ],
            )

    def test_safe_variant_can_be_selected_only_for_controlled_use(self):
        result = select_source_variant(self.source, self.comparator, self.preservation)
        self.assertEqual(result["decision"], DECISION_VARIANT)
        self.assertEqual(result["selectedArtifactId"], self.variant["artifactId"])
        self.assertFalse(result["automaticFinalSelectionAuthorized"])
        self.assertFalse(result["liveSelectorActivationAuthorized"])
        self.assertFalse(result["teacherApprovalImplied"])

    def test_missing_stage9a_evidence_returns_original_and_review(self):
        result = select_source_variant(self.source, self.comparator, {})
        self.assertEqual(result["decision"], DECISION_REVIEW)
        self.assertEqual(result["selectedArtifactId"], self.source)
        self.assertTrue(result["reviewRequired"])

    def test_stage9a_hard_veto_cannot_be_overridden(self):
        evidence = {self.variant["artifactId"]: dict(self.preservation[self.variant["artifactId"]])}
        evidence[self.variant["artifactId"]]["semanticHardVeto"] = True
        evidence[self.variant["artifactId"]]["status"] = "hard_veto"
        result = select_source_variant(self.source, self.comparator, evidence)
        self.assertEqual(result["decision"], DECISION_REVIEW)
        self.assertEqual(result["selectedArtifactId"], self.source)

    def test_review_outcome_retains_original(self):
        comparator = dict(self.comparator)
        comparator.update(
            outcome="review_required",
            recommendedArtifactId=self.source,
            recommendedRole="immutable_source",
        )
        result = select_source_variant(self.source, comparator, self.preservation)
        self.assertEqual(result["decision"], DECISION_REVIEW)
        self.assertEqual(result["selectedArtifactId"], self.source)

    def test_original_preferred_selects_original_without_review(self):
        comparator = dict(self.comparator)
        comparator.update(
            outcome="original_preferred",
            recommendedArtifactId=self.source,
            recommendedRole="immutable_source",
        )
        result = select_source_variant(self.source, comparator, self.preservation)
        self.assertEqual(result["decision"], DECISION_ORIGINAL)
        self.assertEqual(result["selectedArtifactId"], self.source)
        self.assertFalse(result["reviewRequired"])

    def test_stage9_scope_expansion_fails_safe(self):
        comparator = dict(self.comparator)
        comparator["automaticFinalSelectionAuthorized"] = True
        result = select_source_variant(self.source, comparator, self.preservation)
        self.assertEqual(result["decision"], DECISION_REVIEW)
        self.assertEqual(result["selectedArtifactId"], self.source)


if __name__ == "__main__":
    unittest.main()
