from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage11_v2c_semantic_preservation import Stage11V2cSemanticPreservationError
from st_score_restore.stage11_v2c_teacher_review import materialize_teacher_review_manifest
from st_score_restore.stage11_v2d_detector_benchmark import (
    benchmark_coverage_from_present_pairs,
    teacher_present_class_pairs,
    validate_detector_benchmark_result,
    validate_detector_candidate_registry,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "evidence" / "stage11" / "v2d" / "v2d-detector-candidate-registry.v1.json"
BASE_MANIFEST = ROOT / "evidence" / "stage11" / "v2c" / "v2c-expected-class-manifest.v1.json"
OVERLAY = ROOT / "evidence" / "stage11" / "v2c" / "v2c-teacher-review-overlay.v1.json"
RESOLUTION = ROOT / "evidence" / "stage11" / "v2c" / "v2c-teacher-review-resolution.v1.json"


class Stage11V2dDetectorBenchmarkTests(unittest.TestCase):
    def _teacher_manifest(self) -> dict:
        base = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
        overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))
        resolution = json.loads(RESOLUTION.read_text(encoding="utf-8"))
        return materialize_teacher_review_manifest(base, overlay, resolution)["manifest"]

    def test_registry_is_inference_only_and_fail_closed(self) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        result = validate_detector_candidate_registry(payload)
        self.assertEqual("pass", result["status"])
        self.assertEqual(2, result["candidateCount"])
        self.assertEqual(0, result["productionAdmittedCandidateCount"])
        self.assertTrue(result["allTrainingForbidden"])
        self.assertTrue(result["allHeldOutAccessForbidden"])

    def test_registry_rejects_production_admission_without_explicit_weight_license(self) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        payload = copy.deepcopy(payload)
        payload["candidates"][0]["scope"]["productionAdmissionAuthorized"] = True
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_detector_candidate_registry(payload)

    def test_teacher_ground_truth_is_complete_and_has_171_present_pairs(self) -> None:
        manifest = self._teacher_manifest()
        pairs = teacher_present_class_pairs(manifest)
        self.assertEqual(171, len(pairs))

    def test_coverage_denominator_uses_only_teacher_present_pairs(self) -> None:
        manifest = self._teacher_manifest()
        eligible = sorted(teacher_present_class_pairs(manifest))
        result = benchmark_coverage_from_present_pairs(manifest, eligible[:17])
        self.assertEqual(171, result["eligibleExpectedPresentClassPageCount"])
        self.assertEqual(17, result["confidentlyEvaluatedExpectedPresentClassPageCount"])
        self.assertAlmostEqual(17 / 171, result["applicableClassDetectorCoverage"])

    def test_detector_cannot_mark_teacher_absent_pair_as_evaluable_present(self) -> None:
        manifest = self._teacher_manifest()
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            benchmark_coverage_from_present_pairs(
                manifest,
                [("beethoven-op48-no3-p1", "notehead")],
            )

    def test_gpu_benchmark_result_cannot_claim_semantic_completion(self) -> None:
        payload = {
            "schemaVersion": "stage11.v2d.detector-benchmark-result.v1",
            "contractId": "stage11.v2c.semantic-preservation.nonheldout.v1",
            "boundary": {
                "developmentOnly": True,
                "teacherGroundTruthFrozen": True,
                "detectorOutputUsedAsGroundTruth": False,
                "trainingPerformed": False,
                "fineTuningPerformed": False,
                "heldOutAccessed": False,
                "productionPromotionAuthorized": False,
                "stage12EntryAuthorized": False,
            },
            "runtime": {
                "purpose": "exploratory_detector_benchmark",
                "device": "GPU",
                "finalCanonicalCpuRerunRequired": True,
            },
            "coverage": {
                "eligibleExpectedPresentClassPageCount": 171,
                "confidentlyEvaluatedExpectedPresentClassPageCount": 80,
                "applicableClassDetectorCoverage": 80 / 171,
            },
            "claimBoundary": {
                "semanticPreservationEstablished": False,
                "productionReady": False,
            },
        }
        result = validate_detector_benchmark_result(payload)
        self.assertEqual("pass", result["status"])
        self.assertTrue(result["finalCanonicalCpuRerunRequired"])

        tampered = copy.deepcopy(payload)
        tampered["claimBoundary"]["semanticPreservationEstablished"] = True
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_detector_benchmark_result(tampered)


if __name__ == "__main__":
    unittest.main()
