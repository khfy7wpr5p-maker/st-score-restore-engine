"""GPU detector acceleration for the Stage 11 V2d canonical CPU notehead rerun.

Restore stays on the exact canonical CPU profile. The measurement-only Oemer seg_net
moves to ONNX Runtime CUDA only after exact notehead-box equivalence is proven against
the durable CPU canary artifacts from the previous cost-bounded run.

The CUDA session is fail-closed: ONNX Runtime's whole-session execution fallback is
disabled, while CPU remains a graph-partition provider only for operators that CUDA EP
does not support. A small real-image batch probe selects a stable detector batch before
the expensive canary pair is run.
"""
from __future__ import annotations

import argparse, json, platform, time
from pathlib import Path
from typing import Any, Mapping

import cv2
import numpy as np

from .stage11_v2d_colab_runner import CACHE_ROOT, RESULT_ROOT, _atomic_write_json, _load_cache_manifest
from . import stage11_v2d_canonical_cpu_notehead_semantic_rerun as cpu

RESULT_SCHEMA = "stage11.v2d.canonical-cpu-restore-gpu-notehead-semantic-rerun.v1"
GPU_ORT = "1.20.2"
GPU_PROVIDER = "CUDAExecutionProvider"
GPU_LOGIC_BASE = "oemer-dbe2a933-segnet-notehead-fast-step256-gpu-equivalence-nofallback.v2"
GPU_PROVIDER_OPTIONS = {
    "device_id": "0",
    "cudnn_conv_algo_search": "DEFAULT",
    "cudnn_conv_use_max_workspace": "0",
    "do_copy_in_default_stream": "1",
    "use_tf32": "0",
}
GPU_BATCH_CANDIDATES = (16, 8, 4, 2, 1)
CANARY_PAGE_ID = "beethoven-op48-no3-p2"
MAX_PROJECTED_GPU_SECONDS = 45 * 60
MAX_TOTAL_WALL_SECONDS = 60 * 60
RUN_ROOT = CACHE_ROOT / "canonical_cpu_restore_gpu_notehead_semantic_v1"
MANIFEST_PATH = RUN_ROOT / "manifest.json"
SOURCE_DET_DIR = RUN_ROOT / "source_notehead_detector"
RESTORED_DET_DIR = RUN_ROOT / "restored_notehead_detector"
PAGE_DIR = RUN_ROOT / "pages"
RESULT_NAME = "v2d_canonical_cpu_restore_gpu_notehead_semantic_rerun_result.json"


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return payload


def _canonical_boxes(payload: Mapping[str, Any]) -> list[tuple[float, float, float, float]]:
    return sorted(tuple(map(float, box)) for box in payload.get("boxes") or [])


def _gpu_preflight() -> tuple[Any, Any, dict[str, Any]]:
    if platform.python_version() != cpu.PYTHON:
        raise RuntimeError(f"requires Python {cpu.PYTHON}; got {platform.python_version()}")
    import torch, onnxruntime as ort
    if torch.__version__ != cpu.TORCH or torch.cuda.is_available():
        raise RuntimeError(f"Restore must remain CPU-only torch {cpu.TORCH}; got {torch.__version__}")
    if ort.__version__ != GPU_ORT or GPU_PROVIDER not in ort.get_available_providers():
        raise RuntimeError(f"requires onnxruntime-gpu {GPU_ORT} with {GPU_PROVIDER}; got {ort.__version__} {ort.get_available_providers()}")
    torch.set_num_threads(cpu.INTRA)
    torch.set_num_interop_threads(cpu.INTER)
    torch.use_deterministic_algorithms(False)
    runtime = {
        "python": platform.python_version(), "torch": torch.__version__, "restoreDevice": "CPU",
        "restoreIntraopThreads": cpu.INTRA, "restoreInteropThreads": cpu.INTER,
        "detectorOnnxruntime": ort.__version__, "detectorProvider": GPU_PROVIDER,
        "availableProviders": ort.get_available_providers(), "cpuModel": cpu._cpu_model(),
        "cudaProviderOptions": dict(GPU_PROVIDER_OPTIONS), "wholeSessionFallbackDisabled": True,
    }
    print("CANONICAL CPU RESTORE + GPU DETECTOR PREFLIGHT PASS:", runtime["python"], runtime["torch"], runtime["detectorOnnxruntime"], GPU_PROVIDER)
    return torch, ort, runtime


def _cpu_canary(v2d_manifest: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], float]:
    old_manifest = _json(cpu.MANIFEST_PATH)
    if old_manifest.get("schemaVersion") != cpu.SCHEMA:
        raise RuntimeError("CPU canary manifest missing/mismatched")
    source_record = v2d_manifest["sourcePages"].get(CANARY_PAGE_ID)
    restored_record = old_manifest.get("restoredPages", {}).get(CANARY_PAGE_ID)
    if not isinstance(source_record, dict) or not isinstance(restored_record, dict):
        raise RuntimeError("CPU canary source/restore record missing")
    source_path = CACHE_ROOT / "source_pages" / f"{CANARY_PAGE_ID}.png"
    restored_path = cpu.RESTORE_DIR / f"{CANARY_PAGE_ID}.png"
    if not cpu._valid(restored_record, restored_path, cpu._restore_fp(source_record)):
        raise RuntimeError("CPU canary restored artifact invalid")
    source_image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if source_image is None:
        raise RuntimeError("CPU canary source unreadable")
    source_unit = cpu._unit(cpu._resize(source_image))
    source_det = cpu._load_det(cpu.SOURCE_DET_DIR/f"{CANARY_PAGE_ID}.json", old_manifest.get("sourceDetector", {}).get(CANARY_PAGE_ID), cpu._det_fp(source_record, source_unit))
    restored_det = cpu._load_det(cpu.RESTORED_DET_DIR/f"{CANARY_PAGE_ID}.json", old_manifest.get("restoredDetector", {}).get(CANARY_PAGE_ID), cpu._det_fp(restored_record, source_unit))
    if source_det is None or restored_det is None:
        raise RuntimeError("validated CPU canary detector artifacts missing; refusing expensive CPU regeneration")
    return source_det, restored_det, old_manifest, source_unit


def _seed_gpu_manifest(old_cpu_manifest: Mapping[str, Any]) -> dict[str, Any]:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    if MANIFEST_PATH.is_file():
        payload = _json(MANIFEST_PATH)
        if payload.get("schemaVersion") == cpu.SCHEMA:
            return payload
    payload = {
        "schemaVersion": cpu.SCHEMA,
        "restoredPages": dict(old_cpu_manifest.get("restoredPages") or {}),
        "sourceDetector": {}, "restoredDetector": {}, "pageResults": {},
    }
    _atomic_write_json(MANIFEST_PATH, payload)
    return payload


def _gpu_session(ort: Any, checkpoint: Path) -> Any:
    so = ort.SessionOptions()
    so.intra_op_num_threads = cpu.INTRA
    so.inter_op_num_threads = cpu.INTER
    so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    providers = [(GPU_PROVIDER, dict(GPU_PROVIDER_OPTIONS)), "CPUExecutionProvider"]
    sess = ort.InferenceSession(str(checkpoint), sess_options=so, providers=providers)
    if not sess.get_providers() or sess.get_providers()[0] != GPU_PROVIDER:
        raise RuntimeError(f"CUDA session not primary: {sess.get_providers()}")
    if len(sess.get_inputs()) != 1 or not sess.get_outputs():
        raise RuntimeError("seg_net GPU session preflight failed")
    shape = sess.get_inputs()[0].shape
    if len(shape) != 4 or not isinstance(shape[1], int) or not isinstance(shape[2], int):
        raise RuntimeError(f"unexpected seg_net input shape: {shape}")
    sess.disable_fallback()
    return sess


def _probe_batch(sess: Any, image_path: Path, batch_size: int) -> float:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"cannot read GPU probe image: {image_path}")
    image = cpu._resize(image)
    inp = sess.get_inputs()[0]
    out_meta = sess.get_outputs()[0]
    wh, ww = int(inp.shape[1]), int(inp.shape[2])
    coords = [(y, x) for y in cpu._positions(image.shape[0], wh) for x in cpu._positions(image.shape[1], ww)]
    batch_coords = coords[: min(batch_size, len(coords))]
    batch = np.stack([image[y:y+wh, x:x+ww] for y, x in batch_coords])
    t0 = time.monotonic()
    sess.run([out_meta.name], {inp.name: batch})
    elapsed = time.monotonic() - t0
    if sess.get_providers()[0] != GPU_PROVIDER:
        raise RuntimeError(f"CUDA session provider changed after probe: {sess.get_providers()}")
    return elapsed


def _select_gpu_batch(ort: Any, checkpoint: Path, source_path: Path) -> tuple[Any, int, float]:
    failures: list[str] = []
    for batch_size in GPU_BATCH_CANDIDATES:
        sess = _gpu_session(ort, checkpoint)
        try:
            elapsed = _probe_batch(sess, source_path, batch_size)
        except Exception as exc:
            failures.append(f"batch={batch_size}: {type(exc).__name__}: {exc}")
            print(f"GPU batch probe FAILED: batch={batch_size} {type(exc).__name__}")
            continue
        print(f"TRUE GPU BATCH PROBE PASS: batch={batch_size} elapsed={elapsed:.2f}s provider={sess.get_providers()[0]}")
        return sess, batch_size, elapsed
    raise RuntimeError("no true-CUDA detector batch passed; refusing CPU fallback; " + " | ".join(failures))


def _patch_cpu_module(torch: Any, ort: Any, runtime: Mapping[str, Any], batch_size: int) -> None:
    cpu.ORT = GPU_ORT
    cpu.PROVIDER = GPU_PROVIDER
    cpu.BATCH = batch_size
    cpu.LOGIC = f"{GPU_LOGIC_BASE}-batch{batch_size}"
    cpu.MAX_PROJECTED_DETECTOR_SECONDS = MAX_PROJECTED_GPU_SECONDS
    cpu.MAX_TOTAL_WALL_SECONDS = MAX_TOTAL_WALL_SECONDS
    cpu.RUN_ROOT = RUN_ROOT
    cpu.MANIFEST_PATH = MANIFEST_PATH
    cpu.SOURCE_DET_DIR = SOURCE_DET_DIR
    cpu.RESTORED_DET_DIR = RESTORED_DET_DIR
    cpu.PAGE_DIR = PAGE_DIR
    cpu.RESULT_NAME = RESULT_NAME
    # Reuse the already-established canonical CPU thread profile instead of calling
    # torch.set_num_interop_threads() a second time inside the delegated runner.
    cpu._runtime_preflight = lambda: (torch, ort, dict(runtime))
    cpu._session = lambda _ort, checkpoint: _gpu_session(_ort, checkpoint)
    # Intentionally keep cpu.SCHEMA and cpu.RESTORE_DIR unchanged so existing canonical CPU
    # restore fingerprints and durable CPU outputs remain reusable.


def _blocked(runtime: Mapping[str, Any], source_exact: bool, restored_exact: bool, projected: float, status: str) -> Path:
    out = RESULT_ROOT / RESULT_NAME
    _atomic_write_json(out, {
        "schemaVersion": RESULT_SCHEMA, "generatedOn": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "status": status,
        "runtime": dict(runtime),
        "canary": {"pageId": CANARY_PAGE_ID, "sourceBoxesExact": source_exact, "restoredBoxesExact": restored_exact, "projectedGpuDetectorSecondsFor18Pages": projected, "maxAllowedProjectedGpuDetectorSeconds": MAX_PROJECTED_GPU_SECONDS},
        "claimBoundary": {"semanticPreservationEstablished": False, "productionReady": False, "stage12EntryAuthorized": False},
    })
    return out


def run() -> Path:
    torch, ort, runtime = _gpu_preflight()
    v2d_manifest_path = CACHE_ROOT / "cache_manifest.json"
    if not v2d_manifest_path.is_file():
        raise RuntimeError("V2d cache manifest missing")
    v2d_manifest = _load_cache_manifest(v2d_manifest_path)
    cpu_source, cpu_restored, old_cpu_manifest, source_unit = _cpu_canary(v2d_manifest)
    gpu_manifest = _seed_gpu_manifest(old_cpu_manifest)

    checkpoint = CACHE_ROOT / "oemer_checkpoints" / cpu.SEG_REL
    if not cpu._validate_exact_file(checkpoint, cpu.SEG_SIZE, cpu.SEG_SHA):
        raise RuntimeError("seg_net checkpoint mismatch")
    source_record = v2d_manifest["sourcePages"][CANARY_PAGE_ID]
    restored_record = gpu_manifest["restoredPages"][CANARY_PAGE_ID]
    source_path = CACHE_ROOT / "source_pages" / f"{CANARY_PAGE_ID}.png"
    restored_path = cpu.RESTORE_DIR / f"{CANARY_PAGE_ID}.png"

    sess, gpu_batch, probe_seconds = _select_gpu_batch(ort, checkpoint, source_path)
    runtime["detectorBatch"] = gpu_batch
    runtime["gpuProbeSeconds"] = probe_seconds
    _patch_cpu_module(torch, ort, runtime, gpu_batch)

    gpu_source, se = cpu._ensure_det(SOURCE_DET_DIR/f"{CANARY_PAGE_ID}.json", source_path, source_record, source_unit, sess, gpu_manifest["sourceDetector"], gpu_manifest, CANARY_PAGE_ID, "source")
    gpu_restored, re = cpu._ensure_det(RESTORED_DET_DIR/f"{CANARY_PAGE_ID}.json", restored_path, restored_record, source_unit, sess, gpu_manifest["restoredDetector"], gpu_manifest, CANARY_PAGE_ID, "restored")
    measured = (se + re) or float(gpu_source.get("elapsedSeconds", 0)) + float(gpu_restored.get("elapsedSeconds", 0))
    projected = measured * 18
    source_exact = _canonical_boxes(cpu_source) == _canonical_boxes(gpu_source)
    restored_exact = _canonical_boxes(cpu_restored) == _canonical_boxes(gpu_restored)
    print("CPU↔GPU CANARY:", f"sourceExact={source_exact}", f"restoredExact={restored_exact}", f"pair={measured:.1f}s", f"projected18={projected/60:.1f}min", f"batch={gpu_batch}")
    if not source_exact or not restored_exact:
        out = _blocked(runtime, source_exact, restored_exact, projected, "BLOCKED_BY_CPU_GPU_EQUIVALENCE")
        raise RuntimeError(f"CPU/GPU notehead box equivalence failed; result saved: {out}")
    if projected > MAX_PROJECTED_GPU_SECONDS:
        out = _blocked(runtime, True, True, projected, "BLOCKED_BY_GPU_COST_BUDGET")
        raise RuntimeError(f"projected GPU detector runtime exceeds cost budget; result saved: {out}")
    print("CPU↔GPU CANARY EQUIVALENCE PASS")
    print("GPU COST BUDGET PASS")

    out = cpu.run_canonical_cpu_notehead_semantic_rerun()
    result = _json(out)
    result["schemaVersion"] = RESULT_SCHEMA
    result["status"] = "COMPLETE"
    result["detector"]["cpuReference"] = {
        "onnxruntime": "1.20.1", "provider": "CPUExecutionProvider", "canaryPageId": CANARY_PAGE_ID,
        "sourceBoxesExact": True, "restoredBoxesExact": True,
    }
    result["detector"]["gpuAdmittedAfterExactCpuCanaryBoxEquivalence"] = True
    result["detector"]["wholeSessionFallbackDisabled"] = True
    result["detector"]["cudaProviderOptions"] = dict(GPU_PROVIDER_OPTIONS)
    result["detector"]["selectedBatch"] = gpu_batch
    result["claimBoundary"]["gpuDetectorAdmittedOnlyAfterCpuCanaryEquivalence"] = True
    _atomic_write_json(out, result)
    print("CANONICAL CPU RESTORE + GPU NOTEHEAD SEMANTIC RERUN COMPLETE")
    print("SAVED:", out)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)
    if not args.run:
        raise SystemExit("Refusing implicit execution; pass --run")
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
