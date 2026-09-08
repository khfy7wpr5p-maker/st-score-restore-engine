from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage11_v2a_shadow_corpus_expansion import (
    EXPANDED_PAGE_COUNT,
    EXPANDED_SOURCE_FAMILY_COUNT,
    SECOND_DATASET_ITEM_ID,
    Stage11V2aShadowCorpusExpansionError,
    validate_shadow_corpus_expansion_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/stage11/v2a/v2a-shadow-corpus-expanded-evidence.v1.json"
TRUTH = ROOT / "docs/live/ST_SCORE_RESTORE_STAGE11_V2A_SHADOW_CORPUS_EXPANDED_CURRENT_TRUTH.json"


def evidence_payload() -> dict:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


class Stage11V2aShadowCorpusExpansionTests(unittest.TestCase):
    def test_committed_expanded_evidence_passes(self) -> None:
        result = validate_shadow_corpus_expansion_evidence(evidence_payload())
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["expandedNonheldoutCorpusObserved"])
        self.assertEqual(result["pageObservationCount"], EXPANDED_PAGE_COUNT)
        self.assertEqual(result["sourceFamilyCount"], EXPANDED_SOURCE_FAMILY_COUNT)
        self.assertFalse(result["productionInferenceAuthorized"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_second_family_is_expected_public_development_item(self) -> None:
        payload = evidence_payload()
        second = payload["corpus"][1]
        self.assertEqual(second["datasetItemId"], SECOND_DATASET_ITEM_ID)
        self.assertEqual(second["split"], "development")
        self.assertEqual(second["eligibilityClass"], "open_corpus")
        self.assertEqual(second["purpose"], "quality_evaluation")
        self.assertEqual(second["inputKind"], "png")

    def test_held_out_second_family_fails_closed(self) -> None:
        payload = evidence_payload()
        payload["corpus"][1]["split"] = "held_out"
        with self.assertRaises(Stage11V2aShadowCorpusExpansionError):
            validate_shadow_corpus_expansion_evidence(payload)

    def test_duplicate_source_family_fails_closed(self) -> None:
        payload = evidence_payload()
        payload["corpus"][1]["sourceFamilyId"] = payload["corpus"][0]["sourceFamilyId"]
        with self.assertRaises(Stage11V2aShadowCorpusExpansionError):
            validate_shadow_corpus_expansion_evidence(payload)

    def test_production_authorization_fails_closed(self) -> None:
        payload = evidence_payload()
        payload["authorization"]["productionInferenceAuthorized"] = True
        with self.assertRaises(Stage11V2aShadowCorpusExpansionError):
            validate_shadow_corpus_expansion_evidence(payload)

    def test_quality_decision_fails_closed(self) -> None:
        payload = evidence_payload()
        payload["aggregate"]["qualityDecisionMade"] = True
        with self.assertRaises(Stage11V2aShadowCorpusExpansionError):
            validate_shadow_corpus_expansion_evidence(payload)

    def test_current_truth_keeps_stage12_and_production_closed(self) -> None:
        truth = json.loads(TRUTH.read_text(encoding="utf-8"))
        self.assertEqual(truth["state"], "NONHELDOUT_SHADOW_CORPUS_SOURCE_FAMILIES_EXPANDED")
        self.assertEqual(truth["execution"]["sourceFamilyCount"], 2)
        self.assertEqual(truth["execution"]["pageObservationCount"], 5)
        self.assertFalse(truth["authorization"]["productionInferenceAuthorized"])
        self.assertFalse(truth["authorization"]["productionPromotionAuthorized"])
        self.assertFalse(truth["authorization"]["realUserRolloutAuthorized"])
        self.assertFalse(truth["authorization"]["stage12EntryAuthorized"])
        self.assertFalse(truth["interpretation"]["metricsAreQualityGate"])
        self.assertFalse(truth["interpretation"]["metricsMayTuneModel"])

    def test_mutating_nested_contract_does_not_escape_validation(self) -> None:
        payload = evidence_payload()
        mutated = deepcopy(payload)
        mutated["contract"]["comparison"]["tuningAllowed"] = True
        with self.assertRaises(Stage11V2aShadowCorpusExpansionError):
            validate_shadow_corpus_expansion_evidence(mutated)


if __name__ == "__main__":
    unittest.main()
