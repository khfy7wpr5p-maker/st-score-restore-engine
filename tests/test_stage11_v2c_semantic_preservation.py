from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

import numpy as np

from st_score_restore.stage11_v2c_semantic_preservation import (
    CONTRACT_ID,
    MANIFEST_SCHEMA_VERSION,
    SEMANTIC_CLASSES,
    SemanticDetection,
    Stage11V2cSemanticPreservationError,
    conservative_line_system_detector,
    decide_v2c_disposition,
    detector_coverage_from_manifest,
    match_same_class_one_to_one,
    run_detector_safely,
    semantic_preservation_contract,
    suppress_duplicate_detections,
    validate_corpus_plan,
    validate_current_truth,
    validate_expected_class_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PLAN = ROOT / "evidence" / "stage11" / "v2c" / "v2c-corpus-plan.v1.json"
EXPECTED_MANIFEST = ROOT / "evidence" / "stage11" / "v2c" / "v2c-expected-class-manifest.v1.json"
CURRENT_TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2C_CURRENT_TRUTH.json"


def _d(class_id: str, bbox=(10.0, 10.0, 20.0, 20.0), confidence: float = 0.9) -> SemanticDetection:
    return SemanticDetection(
        class_id=class_id,
        bbox=bbox,
        confidence=confidence,
        provenance="test:synthetic",
        detector_version="test.v1",
    )


def _manifest() -> dict:
    classes = {}
    for class_id in SEMANTIC_CLASSES:
        classes[class_id] = {"state": "unknown_review_required", "provenance": {}}
    classes["staff_line"] = {
        "state": "present",
        "provenance": {"type": "teacher_annotation", "evidenceRef": "teacher:test:staff"},
    }
    classes["tab_line"] = {
        "state": "absent",
        "provenance": {"type": "independent_review", "evidenceRef": "review:test:no-tab"},
    }
    return {
        "schemaVersion": MANIFEST_SCHEMA_VERSION,
        "contractId": CONTRACT_ID,
        "pages": [
            {
                "pageId": "page.test.1",
                "sourceFamilyId": "source.family.test.v1",
                "split": "development",
                "classes": classes,
            }
        ],
    }


class Stage11V2cSemanticPreservationTests(unittest.TestCase):
    def test_contract_keeps_model_heldout_production_and_stage12_closed(self) -> None:
        contract = semantic_preservation_contract()
        self.assertTrue(contract["candidate"]["weightsFrozen"])
        self.assertEqual(5, contract["runtime"]["intraopThreads"])
        self.assertEqual(1, contract["runtime"]["interopThreads"])
        self.assertFalse(contract["scope"]["sharedMusicSafetyValidatorModified"])
        self.assertFalse(contract["scope"]["httpApiModified"])
        self.assertFalse(contract["authorization"]["trainingAuthorized"])
        self.assertFalse(contract["authorization"]["heldOutAccessAuthorized"])
        self.assertFalse(contract["authorization"]["productionPromotionAuthorized"])
        self.assertFalse(contract["authorization"]["stage12EntryAuthorized"])

    def test_same_class_matching_is_one_to_one(self) -> None:
        source = [_d("notehead"), _d("notehead", (30, 10, 40, 20))]
        candidate = [_d("notehead", (10, 10, 20, 20)), _d("notehead", (30, 10, 40, 20))]
        result = match_same_class_one_to_one(source, candidate, class_id="notehead")
        self.assertEqual(2, result["matchedCount"])
        self.assertEqual(1.0, result["sourceRecall"])
        self.assertFalse(result["crossClassMatchingAllowed"])

    def test_cross_class_matching_is_forbidden(self) -> None:
        result = match_same_class_one_to_one([_d("notehead")], [_d("stem")], class_id="notehead")
        self.assertEqual(1, result["sourceCount"])
        self.assertEqual(0, result["candidateCount"])
        self.assertEqual(0, result["matchedCount"])

    def test_duplicate_detections_are_suppressed_within_class_only(self) -> None:
        detections = [
            _d("notehead", confidence=0.95),
            _d("notehead", (10.2, 10.2, 20.2, 20.2), confidence=0.80),
            _d("stem", confidence=0.70),
        ]
        kept = suppress_duplicate_detections(detections, iou_threshold=0.8)
        self.assertEqual(2, len(kept))
        self.assertEqual({"notehead", "stem"}, {item.class_id for item in kept})

    def test_confidence_threshold_boundary_is_inclusive(self) -> None:
        result = match_same_class_one_to_one(
            [_d("rest", confidence=0.5)],
            [_d("rest", confidence=0.5)],
            class_id="rest",
            confidence_threshold=0.5,
        )
        self.assertEqual(1, result["matchedCount"])

    def test_manifest_distinguishes_present_absent_not_applicable_and_unknown(self) -> None:
        manifest = _manifest()
        manifest["pages"][0]["classes"]["tab_string"] = {
            "state": "not_applicable",
            "provenance": {},
        }
        result = validate_expected_class_manifest(manifest)
        self.assertEqual(1, result["stateCounts"]["present"])
        self.assertEqual(1, result["stateCounts"]["absent"])
        self.assertEqual(1, result["stateCounts"]["not_applicable"])
        self.assertGreater(result["stateCounts"]["unknown_review_required"], 0)

    def test_detector_coverage_denominator_uses_only_independently_present_classes(self) -> None:
        manifest = _manifest()
        coverage = detector_coverage_from_manifest(
            manifest,
            {"page.test.1": {"staff_line"}},
            {"page.test.1": {"tab_line"}},
        )
        self.assertEqual(1, coverage["eligiblePresentClassCount"])
        self.assertEqual(1.0, coverage["applicableClassDetectorCoverage"])
        self.assertEqual(1.0, coverage["absenceEvaluationCoverage"])
        self.assertGreater(coverage["unknownReviewRequiredClassCount"], 0)

    def test_tampered_detector_derived_expected_presence_is_rejected(self) -> None:
        manifest = _manifest()
        manifest["pages"][0]["classes"]["staff_line"]["provenance"]["type"] = "detector_output"
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_expected_class_manifest(manifest)

    def test_detector_failure_returns_abstention_not_pass(self) -> None:
        def broken(_image):
            raise RuntimeError("boom")

        result = run_detector_safely(broken, np.zeros((16, 16), dtype=np.uint8), detector_name="broken.v1")
        self.assertEqual([], result["detections"])
        self.assertEqual(1, len(result["abstentions"]))
        self.assertIn("detector_failure", result["abstentions"][0]["reason"])

    def test_line_system_detector_identifies_clean_five_line_staff_only(self) -> None:
        image = np.full((100, 200), 255, dtype=np.uint8)
        for row in (20, 28, 36, 44, 52):
            image[row, :] = 0
        detections = conservative_line_system_detector(image)
        self.assertEqual(5, len(detections))
        self.assertEqual({"staff_line"}, {item.class_id for item in detections})

    def test_real_v2c_corpus_plan_meets_target(self) -> None:
        plan = json.loads(CORPUS_PLAN.read_text(encoding="utf-8"))
        result = validate_corpus_plan(plan)
        self.assertEqual("pass", result["status"])
        self.assertEqual(5, result["sourceFamilyCount"])
        self.assertEqual(20, result["pageCount"])
        self.assertEqual(0, result["familyShortage"])
        self.assertEqual(0, result["pageShortage"])

    def test_real_expected_manifest_validates_but_cannot_create_pass_evidence(self) -> None:
        manifest = json.loads(EXPECTED_MANIFEST.read_text(encoding="utf-8"))
        result = validate_expected_class_manifest(manifest)
        self.assertEqual("pass", result["status"])
        self.assertEqual(7, result["pageCount"])
        self.assertEqual(0, result["eligiblePresentClassCount"])
        self.assertEqual(0.0, result["annotationCoverage"])

    def test_current_truth_validates_and_remains_blocked(self) -> None:
        payload = json.loads(CURRENT_TRUTH.read_text(encoding="utf-8"))
        result = validate_current_truth(payload)
        self.assertEqual("pass", result["status"])
        self.assertEqual("V2C_CORPUS_TARGET_MET_SEMANTIC_EVIDENCE_BLOCKED", result["state"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_tampered_current_truth_promotion_fails_closed(self) -> None:
        payload = json.loads(CURRENT_TRUTH.read_text(encoding="utf-8"))
        payload = copy.deepcopy(payload)
        payload["authorization"]["productionPromotionAuthorized"] = True
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_current_truth(payload)

    def test_decision_gate_blocks_insufficient_corpus_and_semantic_evidence(self) -> None:
        result = decide_v2c_disposition(
            determinism_passed=True,
            corpus_gate_passed=False,
            provenance_gate_passed=True,
            semantic_evidence_sufficient=False,
            teacher_review_required=False,
        )
        self.assertEqual("blocked", result["disposition"])
        self.assertIn("approved_corpus_insufficient", result["blockers"])
        self.assertIn("semantic_detector_coverage_insufficient", result["blockers"])

    def test_systematic_symbol_deletion_is_hard_blocker(self) -> None:
        result = decide_v2c_disposition(
            determinism_passed=True,
            corpus_gate_passed=True,
            provenance_gate_passed=True,
            semantic_evidence_sufficient=True,
            teacher_review_required=False,
            systematic_deletion_evidenced=True,
        )
        self.assertEqual("blocked", result["disposition"])
        self.assertTrue(result["hardBlocker"])


if __name__ == "__main__":
    unittest.main()
