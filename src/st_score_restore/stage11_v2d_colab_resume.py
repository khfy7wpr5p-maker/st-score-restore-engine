"""Resume Stage 11 V2d detector benchmarking from an existing Colab cache.

This module exists for a narrow recovery case: the frozen Restore GPU pass has
already completed, but a later Oemer ONNX detector initialization failed. It
reuses only development cache produced by the same V2d runner, re-verifies all
six exact input artifacts, preflights the pinned legacy-compatible ONNX Runtime
on both Oemer checkpoints, and then runs only the detector stage.

No training, fine-tuning, held-out access, production promotion, or Stage 12
authorization is possible here.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import cv2
import torch

from .stage11_v2c_teacher_review import materialize_teacher_review_manifest
from .stage11_v2d_detector_benchmark import (
    benchmark_coverage_from_present_pairs,
    teacher_present_class_pairs,
    validate_detector_benchmark_result,
)
from .stage11_v2d_colab_runner import (
    TARGETS,
    _detect_semantic_boxes,
    _greedy_recall,
    _prepare_oemer_checkpoints,
    sha256_file,
)

PINNED_ORT_VERSION = "1.20.1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _validate_exact_cache(exact_dir: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for key, spec in TARGETS.items():
        path = exact_dir / str(spec["filename"])
        if not path.is_file():
            raise FileNotFoundError(f"cached exact artifact missing: {key}: {path}")
        actual_size = path.stat().st_size
        if actual_size != int(spec["size"]):
            raise RuntimeError(
                f"cached exact artifact size mismatch for {key}: "
                f"{actual_size} != {spec['size']}"
            )
        actual_sha = sha256_file(path)
        if actual_sha != str(spec["sha256"]):
            raise RuntimeError(
                f"cached exact artifact SHA mismatch for {key}: "
                f"{actual_sha} != {spec['sha256']}"
            )
        found[key] = path
    return found


def _cached_page_paths(work: Path) -> tuple[dict[str, Path], dict[str, Path]]:
    source_dir = work / "source"
    restored_dir = work / "restored_gpu_exploratory"
    source: dict[str, Path] = {}
    restored: dict[str, Path] = {}
    for family, spec in TARGETS.items():
        if family == "restore_model":
            continue
        for page_id in spec["page_ids"]:
            page_id = str(page_id)
            src = source_dir / f"{page_id}.png"
            cand = restored_dir / f"{page_id}.png"
            if not src.is_file() or cv2.imread(str(src), cv2.IMREAD_GRAYSCALE) is None:
                raise FileNotFoundError(f"cached source page missing/unreadable: {src}")
            if not cand.is_file() or cv2.imread(str(cand), cv2.IMREAD_GRAYSCALE) is None:
                raise FileNotFoundError(f"cached restored page missing/unreadable: {cand}")
            source[page_id] = src
            restored[page_id] = cand
    if len(source) != 20 or len(restored) != 20:
        raise RuntimeError(
            f"cached page set incomplete: source={len(source)} restored={len(restored)}"
        )
    return source, restored


def _teacher_manifest() -> dict[str, Any]:
    repo = _repo_root()
    base = json.loads(
        (repo / "evidence/stage11/v2c/v2c-expected-class-manifest.v1.json").read_text()
    )
    overlay = json.loads(
        (repo / "evidence/stage11/v2c/v2c-teacher-review-overlay.v1.json").read_text()
    )
    resolution = json.loads(
        (repo / "evidence/stage11/v2c/v2c-teacher-review-resolution.v1.json").read_text()
    )
    teacher = materialize_teacher_review_manifest(base, overlay, resolution)["manifest"]
    pairs = teacher_present_class_pairs(teacher)
    if len(pairs) != 171:
        raise RuntimeError(f"teacher present-pair count mismatch: {len(pairs)}")
    return teacher


def _preflight_oemer_onnx() -> tuple[Any, dict[str, str], Any]:
    """Fail before the 40 detector calls if the legacy ONNX stack is incompatible."""
    import onnxruntime as ort  # type: ignore

    if ort.__version__ != PINNED_ORT_VERSION:
        raise RuntimeError(
            f"Oemer compatibility runtime mismatch: got onnxruntime {ort.__version__}; "
            f"required {PINNED_ORT_VERSION}. Re-run notebook cell 1."
        )
    if "CPUExecutionProvider" not in ort.get_available_providers():
        raise RuntimeError("CPUExecutionProvider unavailable for pinned Oemer detector")

    generate_pred, checkpoint_hashes = _prepare_oemer_checkpoints()

    from oemer import MODULE_PATH  # type: ignore

    for rel in ("unet_big/model.onnx", "seg_net/model.onnx"):
        model_path = Path(MODULE_PATH) / "checkpoints" / rel
        # Explicit CPU preflight avoids CUDA/cuDNN behavior changes in this old model.
        session = ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"]
        )
        if not session.get_inputs() or not session.get_outputs():
            raise RuntimeError(f"Oemer ONNX preflight produced invalid session: {rel}")
        del session
        print(f"Oemer preflight PASS: {rel} / ORT {ort.__version__} / CPU")
    return generate_pred, checkpoint_hashes, ort


def run_cached_detector_benchmark() -> Path:
    """Resume detector-only work from the verified 20-page exploratory cache."""
    if not torch.cuda.is_available():
        raise RuntimeError("GPU runtime required; cached Restore pass belongs to V2d GPU exploration")

    drive_root = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL")
    if not drive_root.exists():
        raise FileNotFoundError(f"Drive folder not mounted/found: {drive_root}")

    exact_dir = Path("/content/v2d_exact_bytes")
    work = Path("/content/v2d_work")
    found = _validate_exact_cache(exact_dir)
    page_paths, restored_paths = _cached_page_paths(work)
    teacher = _teacher_manifest()

    # Critical ordering: detector runtime preflight occurs before any long benchmark loop.
    generate_pred, checkpoint_hashes, ort = _preflight_oemer_onnx()

    teacher_pages = {page["pageId"]: page for page in teacher["pages"]}
    source_evaluable_pairs: set[tuple[str, str]] = set()
    semantic_matched_pairs: set[tuple[str, str]] = set()
    pair_metrics: list[dict[str, Any]] = []

    for index, page_id in enumerate(page_paths, 1):
        print(f"detector {index:02d}/20 {page_id}")
        source_dets = _detect_semantic_boxes(page_paths[page_id], generate_pred)
        candidate_dets = _detect_semantic_boxes(restored_paths[page_id], generate_pred)
        for class_id, record in teacher_pages[page_id]["classes"].items():
            if record["state"] != "present":
                continue
            source_boxes = source_dets.get(class_id, [])
            candidate_boxes = candidate_dets.get(class_id, [])
            if not source_boxes:
                continue
            source_evaluable_pairs.add((page_id, class_id))
            recall, matched, candidate_only = _greedy_recall(source_boxes, candidate_boxes)
            if recall >= 0.80:
                semantic_matched_pairs.add((page_id, class_id))
            pair_metrics.append(
                {
                    "pageId": page_id,
                    "classId": class_id,
                    "sourceCount": len(source_boxes),
                    "candidateCount": len(candidate_boxes),
                    "matchedCount": matched,
                    "sourceRecall": recall,
                    "candidateOnlyCount": candidate_only,
                }
            )

    source_cov = benchmark_coverage_from_present_pairs(teacher, source_evaluable_pairs)
    semantic_cov = benchmark_coverage_from_present_pairs(teacher, semantic_matched_pairs)

    result = {
        "schemaVersion": "stage11.v2d.detector-benchmark-result.v1",
        "contractId": "stage11.v2c.semantic-preservation.nonheldout.v1",
        "generatedOn": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "candidateId": "oemer-onnx-segmentation-dbe2a933",
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
            "device": "GPU_RESTORE_PLUS_CPU_DETECTOR",
            "torchVersion": torch.__version__,
            "cudaAvailable": torch.cuda.is_available(),
            "cudaDevice": torch.cuda.get_device_name(0),
            "onnxruntimeVersion": ort.__version__,
            "onnxProviders": ort.get_available_providers(),
            "detectorExecutionProvider": "CPUExecutionProvider",
            "restoreExecutionMode": "GPU exploratory cache reused; final canonical CPU rerun required",
            "finalCanonicalCpuRerunRequired": True,
            "cachedRestoreReused": True,
        },
        "inputs": {
            "teacherPresentClassPageCount": 171,
            "sourceFiles": {
                key: {
                    "sha256": TARGETS[key]["sha256"],
                    "byteSize": TARGETS[key]["size"],
                    "driveFileId": TARGETS[key]["drive_id"],
                    "cachedPath": str(found[key]),
                }
                for key in found
            },
            "oemerUpstreamCommit": "dbe2a933d630d0f74805d717960eb259473f5978",
            "oemerCheckpointSha256": checkpoint_hashes,
            "oemerCompatibilityRuntime": {
                "onnxruntime": PINNED_ORT_VERSION,
                "provider": "CPUExecutionProvider",
                "preflightPassed": True,
            },
        },
        "coverage": {
            "eligibleExpectedPresentClassPageCount": source_cov[
                "eligibleExpectedPresentClassPageCount"
            ],
            "confidentlyEvaluatedExpectedPresentClassPageCount": source_cov[
                "confidentlyEvaluatedExpectedPresentClassPageCount"
            ],
            "applicableClassDetectorCoverage": source_cov[
                "applicableClassDetectorCoverage"
            ],
            "classCoverage": source_cov["classCoverage"],
        },
        "semanticExploration": {
            "matchedAtRecallAtLeast0_80ClassPageCount": semantic_cov[
                "confidentlyEvaluatedExpectedPresentClassPageCount"
            ],
            "matchedAtRecallAtLeast0_80Coverage": semantic_cov[
                "applicableClassDetectorCoverage"
            ],
            "pairMetrics": pair_metrics,
        },
        "claimBoundary": {
            "semanticPreservationEstablished": False,
            "productionReady": False,
            "canonicalCpuEvidenceRequiredBeforeAnyUpgrade": True,
        },
    }

    print(validate_detector_benchmark_result(result))
    result_dir = drive_root / "V2D_RESULTS"
    result_dir.mkdir(exist_ok=True)
    out = result_dir / "v2d_colab_gpu_detector_benchmark_result.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("SAVED:", out)
    return out
