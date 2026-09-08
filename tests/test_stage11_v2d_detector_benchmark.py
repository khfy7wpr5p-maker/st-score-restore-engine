from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from st_score_restore.stage11_v2c_semantic_preservation import Stage11V2cSemanticPreservationError
from st_score_restore.stage11_v2c_teacher_review import materialize_teacher_review_manifest
from st_score_restore.stage11_v2d_detector_benchmark import (
    benchmark_coverage_from_present_pairs,
    teacher_present_class_pairs,
    validate_detector_benchmark_result,
    validate_detector_candidate_registry,
)
from st_score_restore.stage11_v2d_colab_runner import (
    CACHE_SCHEMA_VERSION,
    OEMER_CHECKPOINTS,
    _atomic_write_json,
    _cache_record_valid,
    _detector_progress_fingerprint,
    _file_record,
    _load_cache_manifest,
    _load_detector_page_record,
    _page_descriptors,
    _validate_exact_file,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "evidence" / "stage11" / "v2d" / "v2d-detector-candidate-registry.v1.json"
BASE_MANIFEST = ROOT / "evidence" / "stage11" / "v2c" / "v2c-expected-class-manifest.v1.json"
OVERLAY = ROOT / "evidence" / "stage11" / "v2c" / "v2c-teacher-review-overlay.v1.json"
RESOLUTION = ROOT / "evidence" / "stage11" / "v2c" / "v2c-teacher-review-resolution.v1.json"
RUNNER = ROOT / "src" / "st_score_restore" / "stage11_v2d_colab_runner.py"
RESUME = ROOT / "src" / "st_score_restore" / "stage11_v2d_colab_resume.py"
NOTEBOOK = ROOT / "notebooks" / "stage11_v2d_colab_gpu_detector_benchmark.ipynb"


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

    def test_exact_file_validation_rejects_size_or_sha_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "exact.bin"
            payload = b"stage11-v2d-exact"
            path.write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            self.assertTrue(_validate_exact_file(path, len(payload), digest))
            self.assertFalse(_validate_exact_file(path, len(payload) + 1, digest))
            self.assertFalse(_validate_exact_file(path, len(payload), "0" * 64))

    def test_cache_record_reuses_only_exact_matching_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "page.bin"
            path.write_bytes(b"valid-page")
            record = _file_record(path, "fingerprint-v1")
            self.assertTrue(_cache_record_valid(record, path, "fingerprint-v1"))
            self.assertFalse(_cache_record_valid(record, path, "stale-fingerprint"))
            path.write_bytes(b"corrupt-page")
            self.assertFalse(_cache_record_valid(record, path, "fingerprint-v1"))

    def test_detector_progress_is_atomic_sha_bound_and_fingerprint_sensitive(self) -> None:
        source = {"sha256": "1" * 64}
        restored = {"sha256": "2" * 64}
        teacher_page = {
            "pageId": "beethoven-op48-no3-p1",
            "classes": {"notehead": {"state": "present"}},
        }
        checkpoints = {rel: str(spec["sha256"]) for rel, spec in OEMER_CHECKPOINTS.items()}
        fingerprint = _detector_progress_fingerprint(
            "beethoven-op48-no3-p1", source, restored, teacher_page, checkpoints
        )
        changed = _detector_progress_fingerprint(
            "beethoven-op48-no3-p1",
            {"sha256": "3" * 64},
            restored,
            teacher_page,
            checkpoints,
        )
        self.assertNotEqual(fingerprint, changed)
        payload = {
            "schemaVersion": "stage11.v2d.detector-page-progress.v1",
            "pageId": "beethoven-op48-no3-p1",
            "fingerprint": fingerprint,
            "sourceEvaluablePairs": [],
            "semanticMatchedPairs": [],
            "pairMetrics": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "detector.json"
            _atomic_write_json(path, payload)
            record = _file_record(path, fingerprint)
            loaded = _load_detector_page_record(
                path, record, "beethoven-op48-no3-p1", fingerprint
            )
            self.assertEqual(payload, loaded)
            path.write_text("{}", encoding="utf-8")
            self.assertIsNone(
                _load_detector_page_record(
                    path, record, "beethoven-op48-no3-p1", fingerprint
                )
            )

    def test_cache_manifest_rejects_invalid_page_maps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "cache_manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "schemaVersion": CACHE_SCHEMA_VERSION,
                        "sourcePages": [],
                        "restoredPages": {},
                    }
                ),
                encoding="utf-8",
            )
            rebuilt = _load_cache_manifest(path)
            self.assertEqual({}, rebuilt["sourcePages"])
            self.assertEqual({}, rebuilt["restoredPages"])
            self.assertEqual({}, rebuilt["detectorPages"])

    def test_exact_20_page_order_starts_with_beethoven_p1(self) -> None:
        descriptors = _page_descriptors()
        self.assertEqual(20, len(descriptors))
        self.assertEqual("beethoven-op48-no3-p1", descriptors[0][2])
        self.assertEqual(20, len({page_id for _, _, page_id in descriptors}))

    def test_runner_has_no_deprecated_numpy_alias_assignments_or_old_content_cache_paths(self) -> None:
        runner = RUNNER.read_text(encoding="utf-8")
        resume = RESUME.read_text(encoding="utf-8")
        for source in (runner, resume):
            tree = ast.parse(source)
            for node in ast.walk(tree):
                targets = []
                if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                    raw_targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    targets.extend(raw_targets)
                for target in targets:
                    self.assertFalse(
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "np"
                        and target.attr in {"bool", "int", "float"}
                    )
        old_paths = ("/content/" + "v2d_work", "/content/" + "v2d_exact_bytes")
        for forbidden in old_paths:
            self.assertNotIn(forbidden, runner)
            self.assertNotIn(forbidden, resume)

    def test_notebook_uses_only_robust_runner_and_persistent_recovery_contract(self) -> None:
        notebook = NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn('onnxruntime==1.20.1', notebook)
        self.assertIn('dbe2a933d630d0f74805d717960eb259473f5978', notebook)
        self.assertIn('st_score_restore.stage11_v2d_colab_runner', notebook)
        self.assertIn('PYTHONUNBUFFERED', notebook)
        self.assertIn('PYTHONFAULTHANDLER', notebook)
        self.assertIn('v2d_recovery_full.log', notebook)
        self.assertNotIn('/content/' + 'v2d_work', notebook)
        self.assertNotIn('/content/' + 'v2d_exact_bytes', notebook)
        self.assertNotIn('Python-3.13-compatible', notebook)


if __name__ == "__main__":
    unittest.main()
