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

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-shadow-preservation-review-evidence.v1.json"


class Stage11V2aShadowPreservationReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

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

    def test_every_page_keeps_semantic_identity_unclaimed(self) -> None:
        for page in self.evidence["pages"]:
            review = page["review"]
            self.assertEqual("not_claimed", review["semanticClassAttribution"])
            self.assertFalse(review["automaticApproval"])
            self.assertFalse(review["automaticPromotionPerformed"])

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


if __name__ == "__main__":
    unittest.main()
