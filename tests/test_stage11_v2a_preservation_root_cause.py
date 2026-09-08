from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

import numpy as np

from st_score_restore.stage11_v2a_preservation_root_cause import (
    Stage11V2aPreservationRootCauseError,
    classify_stage11_redesign,
    distance_tolerant_ink_metrics,
    preservation_root_cause_contract,
    robust_component_shift_metrics,
    validate_root_cause_current_truth,
    validate_root_cause_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-preservation-root-cause-evidence.v1.json"
CURRENT_TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_PRESERVATION_ROOT_CAUSE_CURRENT_TRUTH.json"


class Stage11V2aPreservationRootCauseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.current_truth = json.loads(CURRENT_TRUTH.read_text(encoding="utf-8"))

    def test_contract_keeps_shared_runtime_and_stage12_closed(self) -> None:
        contract = preservation_root_cause_contract()
        self.assertFalse(contract["scope"]["sharedMusicSafetyValidatorModified"])
        self.assertFalse(contract["scope"]["httpApiModified"])
        self.assertFalse(contract["scope"]["normalJobServiceModified"])
        self.assertFalse(contract["authorization"]["productionPromotionAuthorized"])
        self.assertFalse(contract["authorization"]["stage12EntryAuthorized"])

    def test_real_evidence_validates_and_remains_blocked(self) -> None:
        result = validate_root_cause_evidence(self.evidence)
        self.assertEqual("pass", result["status"])
        self.assertTrue(result["determinismRootCausePartiallyResolved"])
        self.assertTrue(result["wikimediaFalseVetoMechanismsDiagnosed"])
        self.assertEqual("blocked", result["preservationDisposition"])
        self.assertFalse(result["productionPromotionAuthorized"])

    def test_current_truth_validates_and_does_not_overclaim(self) -> None:
        result = validate_root_cause_current_truth(self.current_truth)
        self.assertEqual("pass", result["status"])
        self.assertEqual("ROOT_CAUSE_DIAGNOSED_VALIDATOR_REDESIGN_BLOCKED", result["state"])
        self.assertTrue(self.current_truth["determinism"]["wikimediaPr208Pr209ThreadProfileRootCauseEstablished"])
        self.assertFalse(self.current_truth["determinism"]["allFiveHistoricalDriftsFullyExplained"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_distance_tolerance_does_not_call_one_pixel_thickening_distant_invention(self) -> None:
        source = np.zeros((32, 32), dtype=bool)
        source[8:24, 15] = True
        candidate = source.copy()
        candidate[8:24, 16] = True
        metrics = distance_tolerant_ink_metrics(source, candidate, radius=2)
        self.assertGreater(metrics["rawInventedDarkPixels"], 0)
        self.assertEqual(0, metrics["distantInventedDarkPixels"])
        self.assertEqual(0, metrics["tolerantLostDarkPixels"])

    def test_distance_tolerance_preserves_true_far_invention_signal(self) -> None:
        source = np.zeros((32, 32), dtype=bool)
        source[5:10, 5:10] = True
        candidate = source.copy()
        candidate[24:28, 24:28] = True
        metrics = distance_tolerant_ink_metrics(source, candidate, radius=2)
        self.assertEqual(16, metrics["distantInventedDarkPixels"])

    def test_component_distribution_does_not_use_single_max_as_veto(self) -> None:
        source = np.zeros((128, 128), dtype=bool)
        candidate = np.zeros((128, 128), dtype=bool)
        for x in (10, 30, 50, 70, 90):
            source[20:23, x:x + 3] = True
            candidate[20:23, x + 1:x + 4] = True
        metrics = robust_component_shift_metrics(source, candidate, gate_fraction=0.05)
        self.assertGreater(metrics["matchRecall"], 0.9)
        self.assertFalse(metrics["singleMaximumUsedAsRejectVeto"])
        self.assertLess(metrics["p95ShiftPixels"], 2.0)

    def test_classifier_is_fail_closed_without_semantic_identity(self) -> None:
        tolerant = {"tolerantLossFraction": 0.0001, "distantInventionFraction": 0.005}
        components = {"matchRecall": 0.98, "p95ShiftPixels": 1.0}
        geometry = {"reliableForVeto": True}
        result = classify_stage11_redesign(tolerant, components, geometry, semantic_identity_established=False)
        self.assertEqual("review_required", result["verdict"])
        self.assertIn("semantic_identity_not_established", result["reviewRequiredReasons"])
        self.assertFalse(result["automaticApproval"])

    def test_classifier_rejects_material_robust_component_loss(self) -> None:
        tolerant = {"tolerantLossFraction": 0.001, "distantInventionFraction": 0.005}
        components = {"matchRecall": 0.5, "p95ShiftPixels": 1.0}
        geometry = {"reliableForVeto": False}
        result = classify_stage11_redesign(tolerant, components, geometry)
        self.assertEqual("reject", result["verdict"])
        self.assertIn("robust_component_recall_severe", result["rejectReasons"])

    def test_tampered_thread_profile_fails_closed(self) -> None:
        payload = copy.deepcopy(self.evidence)
        payload["determinism"]["threadProfiles"][1]["shadowSha256"] = "0" * 64
        with self.assertRaises(Stage11V2aPreservationRootCauseError):
            validate_root_cause_evidence(payload)

    def test_tampered_promotion_authorization_fails_closed(self) -> None:
        payload = copy.deepcopy(self.evidence)
        payload["authorization"]["productionPromotionAuthorized"] = True
        with self.assertRaises(Stage11V2aPreservationRootCauseError):
            validate_root_cause_evidence(payload)


if __name__ == "__main__":
    unittest.main()
