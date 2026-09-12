"""Canonical CPU byte/pixel identity bridge for Stage 11 V2d notehead evidence.

This runner does not run Oemer again. It re-executes the frozen Restore package
under the already-recorded canonical CPU profile, proves that the resulting
pixels match the committed V2c canonical evidence, proves that the V2d cached
restored pixels are identical to those canonical pixels, and then reuses only
detector-page records whose SHA/fingerprint bindings still validate.

Development-only. No training, held-out access, production promotion, or Stage 12.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path
from typing import Any, Mapping

import cv2
import numpy as np

from .stage11_v2d_colab_runner import (
    CACHE_ROOT,
    RESULT_ROOT,
    TARGETS,
    _atomic_write_json,
    _detector_progress_fingerprint,
    _load_cache_manifest,
    _load_detector_page_record,
    _restore_gray,
    _teacher_manifest,
    _validate_exact_file,
)

SCHEMA_VERSION = "stage11.v2d.canonical-cpu-notehead-bridge.v1"
CANONICAL_PYTHON = "3.13.5"
CANONICAL_TORCH = "2.10.0+cpu"
CANONICAL_INTRAOP_THREADS = 5
CANONICAL_INTEROP_THREADS = 1
EXPECTED_BENCHMARK_SHA256 = "63fdb35ed102c45544a1a97591f1b7b7269d8c2f13f87b4c858558ec5ce52568"
EXPECTED_BENCHMARK_SIZE = 40685
RESULT_NAME = "v2d_canonical_cpu_notehead_bridge_result.json"
PAGE_PROGRESS_DIR = CACHE_ROOT / "canonical_cpu_notehead_bridge_pages"


def _pixel_sha(gray: np.ndarray) -> str:
    if gray.dtype != np.uint8 or gray.ndim != 2:
        raise RuntimeError("expected uint8 grayscale image")
    return hashlib.sha256(np.ascontiguousarray(gray).tobytes()).hexdigest()


def _png_sha(gray: np.ndarray) -> tuple[str, int]:
    ok, buf = cv2.imencode(".png", gray, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    if not ok:
        raise RuntimeError("canonical PNG encode failed")
    raw = buf.tobytes()
    return hashlib.sha256(raw).hexdigest(), len(raw)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return payload


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _canonical_pages(repo: Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    canonical = _load_json(repo / "evidence/stage11/v2c/v2c-full20-repeat-execution.v1.json")
    selection = _load_json(repo / "evidence/stage11/v2d/v2d-class-selection-decision.v1.json")
    if selection.get("nextStep", {}).get("scope") != ["notehead"]:
        raise RuntimeError("V2d canonical rerun scope must be exactly notehead")
    if selection.get("claimBoundary", {}).get("semanticPreservationEstablished") is not False:
        raise RuntimeError("selection evidence must remain fail-closed")
    teacher = _teacher_manifest(repo)
    selected = []
    for page in teacher["pages"]:
        if page["classes"]["notehead"]["state"] == "present":
            selected.append(str(page["pageId"]))
    if len(selected) != 18:
        raise RuntimeError(f"expected 18 teacher-present notehead pages, got {len(selected)}")
    return canonical, selection, selected


def _runtime_preflight() -> Any:
    if platform.python_version() != CANONICAL_PYTHON:
        raise RuntimeError(
            f"canonical CPU bridge requires Python {CANONICAL_PYTHON}; got {platform.python_version()}"
        )
    import torch

    if torch.__version__ != CANONICAL_TORCH:
        raise RuntimeError(f"canonical CPU bridge requires torch {CANONICAL_TORCH}; got {torch.__version__}")
    if torch.cuda.is_available():
        raise RuntimeError("canonical CPU bridge requires CPU-only torch runtime")
    torch.set_num_threads(CANONICAL_INTRAOP_THREADS)
    torch.set_num_interop_threads(CANONICAL_INTEROP_THREADS)
    torch.use_deterministic_algorithms(False)
    if torch.get_num_threads() != CANONICAL_INTRAOP_THREADS:
        raise RuntimeError("canonical intraop thread count mismatch")
    if torch.get_num_interop_threads() != CANONICAL_INTEROP_THREADS:
        raise RuntimeError("canonical interop thread count mismatch")
    print(
        "CANONICAL CPU PREFLIGHT PASS:",
        platform.python_version(),
        torch.__version__,
        f"intraop={torch.get_num_threads()}",
        f"interop={torch.get_num_interop_threads()}",
    )
    return torch


def _benchmark_result(selection: Mapping[str, Any]) -> dict[str, Any]:
    path = RESULT_ROOT / "v2d_colab_gpu_detector_benchmark_result.json"
    source = selection["sourceBenchmark"]
    expected_sha = str(source["sha256"])
    expected_size = int(source["byteSize"])
    if expected_sha != EXPECTED_BENCHMARK_SHA256 or expected_size != EXPECTED_BENCHMARK_SIZE:
        raise RuntimeError("selection source benchmark binding changed")
    if not _validate_exact_file(path, expected_size, expected_sha):
        raise RuntimeError(f"exact V2d benchmark result missing/mismatched: {path}")
    payload = _load_json(path)
    if payload.get("candidateId") != "oemer-onnx-segmentation-dbe2a933":
        raise RuntimeError("unexpected V2d detector candidate")
    if payload.get("claimBoundary", {}).get("semanticPreservationEstablished") is not False:
        raise RuntimeError("exploratory benchmark claim boundary changed")
    return payload


def _progress_fingerprint(
    *,
    page_id: str,
    source_pixel_sha: str,
    expected_output_pixel_sha: str,
    model_sha: str,
    benchmark_sha: str,
) -> str:
    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "pageId": page_id,
        "sourcePixelSha256": source_pixel_sha,
        "expectedCanonicalOutputPixelSha256": expected_output_pixel_sha,
        "modelSha256": model_sha,
        "benchmarkSha256": benchmark_sha,
        "python": CANONICAL_PYTHON,
        "torch": CANONICAL_TORCH,
        "intraopThreads": CANONICAL_INTRAOP_THREADS,
        "interopThreads": CANONICAL_INTEROP_THREADS,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load_progress(path: Path, fingerprint: str) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = _load_json(path)
    except (OSError, json.JSONDecodeError, RuntimeError):
        return None
    if payload.get("schemaVersion") != SCHEMA_VERSION or payload.get("fingerprint") != fingerprint:
        return None
    checks = payload.get("checks") or {}
    if not all(checks.get(k) is True for k in (
        "sourcePixelsMatchCanonical",
        "cpuPixelsMatchCanonical",
        "cachedRestoredPixelsMatchCanonical",
        "detectorRecordFingerprintValid",
    )):
        return None
    return payload


def run_canonical_cpu_notehead_bridge() -> Path:
    repo = _repo_root()
    canonical, selection, selected_pages = _canonical_pages(repo)
    benchmark = _benchmark_result(selection)
    torch = _runtime_preflight()

    manifest_path = CACHE_ROOT / "cache_manifest.json"
    manifest = _load_cache_manifest(manifest_path)
    if not manifest_path.is_file():
        raise RuntimeError("V2d cache manifest missing")

    model_spec = TARGETS["restore_model"]
    model_path = CACHE_ROOT / "exact_inputs" / str(model_spec["filename"])
    if not _validate_exact_file(model_path, int(model_spec["size"]), str(model_spec["sha256"])):
        raise RuntimeError("exact frozen Restore model missing/mismatched")

    canonical_by_page = {str(p["pageId"]): p for p in canonical["pages"]}
    teacher = _teacher_manifest(repo)
    teacher_by_page = {str(p["pageId"]): p for p in teacher["pages"]}
    checkpoint_hashes = {
        str(k): str(v) for k, v in benchmark["inputs"]["oemerCheckpointSha256"].items()
    }

    device = torch.device("cpu")
    model = torch.jit.load(str(model_path), map_location=device).to(device).eval()
    PAGE_PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

    pages: list[dict[str, Any]] = []
    recalls: list[float] = []

    for index, page_id in enumerate(selected_pages, 1):
        expected = canonical_by_page[page_id]
        source_path = CACHE_ROOT / "source_pages" / f"{page_id}.png"
        restored_path = CACHE_ROOT / "restored_pages" / f"{page_id}.png"
        source_record = manifest["sourcePages"].get(page_id)
        restored_record = manifest["restoredPages"].get(page_id)
        if not isinstance(source_record, dict) or not isinstance(restored_record, dict):
            raise RuntimeError(f"cache record missing: {page_id}")

        for path, record, label in (
            (source_path, source_record, "source"),
            (restored_path, restored_record, "restored"),
        ):
            if not _validate_exact_file(path, int(record["byteSize"]), str(record["sha256"])):
                raise RuntimeError(f"{label} cache bytes mismatch: {page_id}")

        source_gray = cv2.imread(str(source_path), cv2.IMREAD_GRAYSCALE)
        cached_gray = cv2.imread(str(restored_path), cv2.IMREAD_GRAYSCALE)
        if source_gray is None or cached_gray is None:
            raise RuntimeError(f"unreadable cache image: {page_id}")

        source_pixel_sha = _pixel_sha(source_gray)
        expected_source_pixel_sha = str(expected["sourcePixelSha256"])
        expected_output_pixel_sha = str(expected["decodedPixelSha256"])
        fingerprint = _progress_fingerprint(
            page_id=page_id,
            source_pixel_sha=source_pixel_sha,
            expected_output_pixel_sha=expected_output_pixel_sha,
            model_sha=str(model_spec["sha256"]),
            benchmark_sha=EXPECTED_BENCHMARK_SHA256,
        )
        progress_path = PAGE_PROGRESS_DIR / f"{page_id}.json"
        progress = _load_progress(progress_path, fingerprint)

        if progress is None:
            cpu_gray = _restore_gray(model, source_gray, device)
            cpu_pixel_sha = _pixel_sha(cpu_gray)
            cpu_png_sha, cpu_png_size = _png_sha(cpu_gray)
            cached_pixel_sha = _pixel_sha(cached_gray)

            detector_fp = _detector_progress_fingerprint(
                page_id,
                source_record,
                restored_record,
                teacher_by_page[page_id],
                checkpoint_hashes,
            )
            detector_path = CACHE_ROOT / "detector_pages" / f"{page_id}.json"
            detector_page = _load_detector_page_record(
                detector_path,
                manifest["detectorPages"].get(page_id),
                page_id,
                detector_fp,
            )
            if detector_page is None:
                raise RuntimeError(f"detector page fingerprint/bytes invalid: {page_id}")
            note_metrics = [
                m for m in detector_page["pairMetrics"] if m.get("classId") == "notehead"
            ]
            if len(note_metrics) != 1:
                raise RuntimeError(f"exactly one notehead metric required: {page_id}")
            metric = note_metrics[0]
            progress = {
                "schemaVersion": SCHEMA_VERSION,
                "fingerprint": fingerprint,
                "pageId": page_id,
                "checks": {
                    "sourcePixelsMatchCanonical": source_pixel_sha == expected_source_pixel_sha,
                    "cpuPixelsMatchCanonical": cpu_pixel_sha == expected_output_pixel_sha,
                    "cachedRestoredPixelsMatchCanonical": cached_pixel_sha == expected_output_pixel_sha,
                    "detectorRecordFingerprintValid": True,
                },
                "canonicalEvidence": {
                    "sourcePixelSha256": expected_source_pixel_sha,
                    "outputPixelSha256": expected_output_pixel_sha,
                    "outputPngSha256": str(expected["outputSha256"]),
                },
                "canonicalCpuExecution": {
                    "outputPixelSha256": cpu_pixel_sha,
                    "outputPngSha256": cpu_png_sha,
                    "outputPngByteSize": cpu_png_size,
                    "pngBytesMatchCommittedCanonical": cpu_png_sha == str(expected["outputSha256"]),
                },
                "existingV2dCache": {
                    "restoredFileSha256": str(restored_record["sha256"]),
                    "restoredPixelSha256": cached_pixel_sha,
                },
                "noteheadMetric": metric,
            }
            if not all(progress["checks"].values()):
                _atomic_write_json(progress_path, progress)
                raise RuntimeError(f"canonical CPU identity bridge failed: {page_id}")
            _atomic_write_json(progress_path, progress)
            print(f"canonical CPU bridge SAVED {index:02d}/{len(selected_pages)} {page_id}")
        else:
            print(f"canonical CPU bridge cache reuse {index:02d}/{len(selected_pages)} {page_id}")

        pages.append(progress)
        recalls.append(float(progress["noteheadMetric"]["sourceRecall"]))

    del model

    matched = sum(value >= 0.80 for value in recalls)
    result = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedOn": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "contractId": selection["contractId"],
        "scope": {
            "developmentOnly": True,
            "selectedSemanticClass": "notehead",
            "selectedTeacherPresentPageCount": len(selected_pages),
            "heldOutAccessed": False,
            "trainingPerformed": False,
            "fineTuningPerformed": False,
        },
        "runtime": {
            "device": "CPU",
            "python": platform.python_version(),
            "torch": torch.__version__,
            "intraopThreads": CANONICAL_INTRAOP_THREADS,
            "interopThreads": CANONICAL_INTEROP_THREADS,
            "deterministicAlgorithms": False,
            "restorePackageSha256": str(model_spec["sha256"]),
        },
        "bridge": {
            "canonicalCpuRestoreExecutedPageCount": len(pages),
            "canonicalCpuPixelsMatchedCommittedV2cCount": sum(
                p["checks"]["cpuPixelsMatchCanonical"] for p in pages
            ),
            "existingV2dCachePixelsMatchedCommittedV2cCount": sum(
                p["checks"]["cachedRestoredPixelsMatchCanonical"] for p in pages
            ),
            "detectorRecordFingerprintValidatedCount": sum(
                p["checks"]["detectorRecordFingerprintValid"] for p in pages
            ),
            "allSelectedPagesPixelIdentical": all(
                p["checks"]["cpuPixelsMatchCanonical"]
                and p["checks"]["cachedRestoredPixelsMatchCanonical"]
                for p in pages
            ),
            "benchmarkResultSha256": EXPECTED_BENCHMARK_SHA256,
        },
        "noteheadCanonicalEvidence": {
            "evaluatedPageCount": len(recalls),
            "pagesAtRecallGte0_80": matched,
            "rateAtRecallGte0_80": matched / len(recalls),
            "meanSourceRecall": sum(recalls) / len(recalls),
            "minimumSourceRecall": min(recalls),
        },
        "pages": pages,
        "claimBoundary": {
            "semanticPreservationEstablished": False,
            "productionReady": False,
            "detectorOutputUsedAsGroundTruth": False,
            "overallStage11PassAuthorized": False,
            "stage12EntryAuthorized": False,
            "noteheadRuntimeProvenanceUpgradedToCanonicalCpuByPixelIdentity": True,
        },
    }
    out = RESULT_ROOT / RESULT_NAME
    _atomic_write_json(out, result)
    print("CANONICAL CPU NOTEHEAD BRIDGE PASS")
    print("SAVED:", out)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)
    if not args.run:
        raise SystemExit("Refusing implicit execution; pass --run")
    run_canonical_cpu_notehead_bridge()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
