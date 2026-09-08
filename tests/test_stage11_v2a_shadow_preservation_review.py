from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage11_v2a_shadow_preservation_review import (
    Stage11V2aShadowPreservationReviewError,
    preservation_review_contract,
    validate_preservation_review_evidence,
)
from st_score_restore.stage11_v2a_shadow_preservation_review_current_truth import (
    Stage11V2aShadowPreservationCurrentTruthError,
    validate_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-shadow-preservation-review-evidence.v1.json"
CURRENT_TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_SHADOW_PRESERVATION_REVIEW_CURRENT_TRUTH.json"


class Stage11V2aShadowPreservationReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.current_truth = json.loads(CURRENT_TRUTH.read_text(encoding="utf-8"))

    def test_contract_keeps_production_and_stage12_closed(self) -> None:
        contract = preservation_review_contract()
        self.assertTrue(contract["authorization"]["preservationReviewAuthorized"])
        self.assertFalse(contract["authorization"]["productionInferenceAuthorized"])
        self.assertFalse(contract["authorization"]["productionPromotionAuthorized"])
        self.assertFalse(contract["authorization"]["stage12EntryAuthorized"])
        self.assertFalse(contract["scope"]["semanticPerClassIdentityClaimed"])

    def test_real_evidence_is_fail_closed_and_blocked(self) -> None:
        result = validate_preservation_review_evidence(self.evidence)
        self.assertEqual("pass", result["status"])
        self.assertEqual("blocked", result["preservationDisposition"])
        self.assertEqual(5, result["pageCount"])
        self.assertEqual(2, result["sourceFamilyCount"])
        self.assertFalse(result["productionPromotionAuthorized"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_current_truth_records_blocker_and_cross_run_drift(self) -> None:
        result = validate_current_truth(self.current_truth)
        self.assertEqual("pass", result["status"])
        self.assertEqual("NONHELDOUT_SHADOW_PRESERVATION_REVIEW_BLOCKED", result["state"])
        self.assertEqual("blocked", result["preservationDisposition"])
        self.assertEqual(1, result["priorShadowByteMatchCount"])
        self.assertEqual(5, result["priorShadowByteMatchTotal"])
        self.assertFalse(result["productionPromotionAuthorized"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_every_page_keeps_semantic_identity_unclaimed(self) -> None:
        for page in self.evidence["pages"]:
            review = page["review"]
            self.assertEqual("not_claimed", review["semanticClassAttribution"])
            self.assertFalse(review["automaticApproval"])
            self.assertFalse(review["automaticPromotionPerformed"])

    def test_wikimedia_preserves_staff_and_tab_system_counts_but_still_rejects(self) -> None:
        page = next(
            item for item in self.evidence["pages"]
            if item["datasetItemId"] == "dataset.item.wikimedia-guitar-technical-exercise-no1.v1"
        )
        review = page["review"]
        self.assertEqual(3, review["geometry"]["staff"]["sourceSystemCount"])
        self.assertEqual(3, review["geometry"]["staff"]["candidateSystemCount"])
        self.assertEqual(0.0, review["geometry"]["staff"]["lineBreakFraction"])
        self.assertEqual(3, review["geometry"]["tab"]["sourceSystemCount"])
        self.assertEqual(3, review["geometry"]["tab"]["candidateSystemCount"])
        self.assertEqual(0.0, review["geometry"]["tab"]["lineBreakFraction"])
        self.assertEqual("reject", review["verdict"])
        self.assertIn("component_shift_severe", review["rejectReasons"])
        self.assertIn("symbol_invention_severe", review["rejectReasons"])

    def test_tampering_with_production_authorization_fails(self) -> None:
        payload = copy.deepcopy(self.evidence)
        payload["authorization"]["productionPromotionAuthorized"] = True
        with self.assertRaises(Stage11V2aShadowPreservationReviewError):
            validate_preservation_review_evidence(payload)

    def test_tampering_with_aggregate_disposition_fails(self) -> None:
        payload = copy.deepcopy(self.evidence)
        payload["aggregate"]["preservationDisposition"] = "shadow_review_pass"
        with self.assertRaises(Stage11V2aShadowPreservationReviewError):
            validate_preservation_review_evidence(payload)

    def test_tampering_with_current_truth_drift_fails(self) -> None:
        payload = copy.deepcopy(self.current_truth)
        payload["crossRunIdentity"]["priorShadowOutputByteIdentityStable"] = True
        with self.assertRaises(Stage11V2aShadowPreservationCurrentTruthError):
            validate_current_truth(payload)


if __name__ == "__main__":
    unittest.main()
