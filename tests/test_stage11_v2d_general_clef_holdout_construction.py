from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "evidence/stage11/v2d/v2d-general-clef-successor-holdout-construction.v1.json"


class Stage11V2dGeneralClefHoldoutConstructionTests(unittest.TestCase):
    def _payload(self) -> dict:
        self.assertTrue(
            STATE.is_file(),
            "fresh general-clef holdout construction state must be repository-bound",
        )
        return json.loads(STATE.read_text(encoding="utf-8"))

    def test_construction_is_open_but_incomplete_and_not_qualification(self) -> None:
        payload = self._payload()

        self.assertEqual(
            "stage11.v2d.general-clef-successor-holdout-construction.v1",
            payload["schemaVersion"],
        )
        self.assertEqual(
            "SOURCE_SET_CONSTRUCTION_OPENED_INCOMPLETE",
            payload["status"],
        )
        self.assertTrue(payload["authorization"]["freshHoldoutConstructionApproved"])
        self.assertTrue(payload["authorization"]["sourceAccessStarted"])
        self.assertFalse(payload["qualification"]["executed"])
        self.assertFalse(payload["teacherTruth"]["opened"])
        self.assertFalse(payload["claimBoundary"]["detectorQualified"])

    def test_frozen_candidate_and_thresholds_cannot_change_during_holdout(self) -> None:
        payload = self._payload()
        frozen = payload["frozenBindings"]

        self.assertEqual(
            "stage11-general-clef-candidate-generator.hybrid-oemer-staff-relative-c-review.v2",
            frozen["candidateGeneratorId"],
        )
        self.assertEqual(
            "1cc4108319eb0c0531f4fbeced0d30738c6bd541",
            frozen["candidateGeneratorBlobSha"],
        )
        self.assertEqual(
            "8bef05863aa15df9da102f5bfd71345435657bbc",
            frozen["successorBlobSha"],
        )
        self.assertEqual(
            "82a0876ba50bf2b204b1447d1e020a51d1e2e8a7",
            frozen["prequalificationPolicyBlobSha"],
        )
        self.assertFalse(payload["mutationBoundary"]["candidateMutationAllowed"])
        self.assertFalse(payload["mutationBoundary"]["thresholdMutationAllowed"])
        self.assertFalse(payload["mutationBoundary"]["postAccessCandidateSelectionAllowed"])

    def test_spent_and_development_sources_are_explicitly_excluded(self) -> None:
        payload = self._payload()
        exclusions = payload["independence"]["excludedEvidence"]

        self.assertIn("18-page/213-box general-clef development corpus", exclusions)
        self.assertIn("P4.7 spent holdout", exclusions)
        self.assertIn("P4.9 spent holdout", exclusions)
        self.assertIn("Barley general-clef development family", exclusions)
        self.assertIn("Wikimedia Guitar Technical Exercise development family", exclusions)

    def test_source_inventory_records_only_frozen_private_bindings_not_teacher_labels(self) -> None:
        payload = self._payload()
        inventory = {item["sourceRef"]: item for item in payload["sourceInventory"]}

        self.assertEqual(
            "f13755833ef51354e1d632292b48bfa72571bb0ca96d1d7c2e57b924919e2f47",
            inventory["private-source:tchaikovsky-staffline-v1_4"]["sha256"],
        )
        self.assertEqual(
            "abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5",
            inventory["private-source:nearer-phone-derivative-v1"]["sha256"],
        )
        self.assertEqual(
            "f720a48649c5e3fba806c2832b28dc664d166042143825a8a2f7ea70f3175875",
            inventory["private-source:debussy-string-quartet-op10-mxl"]["sha256"],
        )
        self.assertTrue(all("teacherBoxes" not in item for item in inventory.values()))

    def test_missing_required_inputs_block_freeze_and_one_shot_scoring(self) -> None:
        payload = self._payload()
        blockers = set(payload["blockers"])

        self.assertIn("FRESH_TAB_EXACT_BYTES_MISSING", blockers)
        self.assertIn("C_CLEF_RASTER_SOURCE_MISSING", blockers)
        self.assertIn("BLIND_CLEF_TEACHER_TRUTH_MISSING", blockers)
        self.assertFalse(payload["holdoutFreeze"]["ready"])
        self.assertFalse(payload["qualification"]["oneShotScoringAllowed"])
        self.assertFalse(payload["claimBoundary"]["overallGeneralClefQualificationClaimAllowed"])


if __name__ == "__main__":
    unittest.main()
