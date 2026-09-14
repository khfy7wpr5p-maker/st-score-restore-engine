"""Cost-bounded canonical CPU notehead semantic rerun for Stage 11 V2d.

Runs the frozen Restore package on CPU, persists the actual CPU outputs, and measures
notehead preservation against those exact outputs with a pinned seg_net-only ONNX
measurement path. No cross-host pixel identity with earlier V2c/V2d outputs is assumed.
Development-only: no training, held-out access, production promotion, or Stage 12.
"""
from __future__ import annotations

import argparse, hashlib, json, platform, time
from pathlib import Path
from typing import Any, Mapping

import cv2
import numpy as np

from .stage11_v2d_colab_runner import (
    CACHE_ROOT, OEMER_CHECKPOINTS, RESULT_ROOT, TARGETS,
    _atomic_write_bytes, _atomic_write_json, _greedy_recall,
    _load_cache_manifest, _restore_gray, _teacher_manifest,
    _validate_exact_file, sha256_file,
)

SCHEMA = "stage11.v2d.canonical-cpu-notehead-semantic-rerun.v1"
DETECTOR_SCHEMA = "stage11.v2d.notehead-fast-detector-record.v1"
PAGE_SCHEMA = "stage11.v2d.canonical-cpu-notehead-page.v1"
PYTHON = "3.13.5"; TORCH = "2.10.0+cpu"; ORT = "1.20.1"
INTRA = 5; INTER = 1; PROVIDER = "CPUExecutionProvider"
SEG_REL = "seg_net/model.onnx"
SEG_SHA = str(OEMER_CHECKPOINTS[SEG_REL]["sha256"])
SEG_SIZE = int(OEMER_CHECKPOINTS[SEG_REL]["size"])
LOGIC = "oemer-dbe2a933-segnet-notehead-fast-step256.v1"
STEP = 256; BATCH = 32; IOU = 0.20; RECALL_MARKER = 0.80
MAX_PROJECTED_DETECTOR_SECONDS = 90 * 60
MAX_TOTAL_WALL_SECONDS = 110 * 60
BENCHMARK_SHA = "63fdb35ed102c45544a1a97591f1b7b7269d8c2f13f87b4c858558ec5ce52568"
BENCHMARK_SIZE = 40685
RUN_ROOT = CACHE_ROOT / "canonical_cpu_notehead_semantic_v1"
RESTORE_DIR = RUN_ROOT / "restored_pages"
SOURCE_DET_DIR = RUN_ROOT / "source_notehead_detector"
RESTORED_DET_DIR = RUN_ROOT / "restored_notehead_detector"
PAGE_DIR = RUN_ROOT / "pages"
MANIFEST_PATH = RUN_ROOT / "manifest.json"
RESULT_NAME = "v2d_canonical_cpu_notehead_semantic_rerun_result.json"


def _fp(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict): raise RuntimeError(f"JSON object required: {path}")
    return payload


def _pixel_sha(gray: np.ndarray) -> str:
    if gray.dtype != np.uint8 or gray.ndim != 2: raise RuntimeError("uint8 grayscale required")
    return hashlib.sha256(np.ascontiguousarray(gray).tobytes()).hexdigest()


def _cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text(errors="replace").splitlines():
            if line.lower().startswith("model name") and ":" in line: return line.split(":", 1)[1].strip()
    except OSError: pass
    return "unknown"


def _runtime_preflight() -> tuple[Any, Any, dict[str, Any]]:
    if platform.python_version() != PYTHON: raise RuntimeError(f"requires Python {PYTHON}")
    import torch, onnxruntime as ort
    if torch.__version__ != TORCH: raise RuntimeError(f"requires torch {TORCH}; got {torch.__version__}")
    if torch.cuda.is_available(): raise RuntimeError("CPU-only torch required")
    if ort.__version__ != ORT or PROVIDER not in ort.get_available_providers():
        raise RuntimeError(f"requires onnxruntime {ORT} {PROVIDER}")
    torch.set_num_threads(INTRA); torch.set_num_interop_threads(INTER); torch.use_deterministic_algorithms(False)
    if torch.get_num_threads() != INTRA or torch.get_num_interop_threads() != INTER: raise RuntimeError("thread profile mismatch")
    runtime = {
        "python": platform.python_version(), "torch": torch.__version__, "onnxruntime": ort.__version__,
        "numpy": np.__version__, "opencv": cv2.__version__, "cpuModel": _cpu_model(),
        "restoreDevice": "CPU", "detectorProvider": PROVIDER,
        "intraopThreads": INTRA, "interopThreads": INTER, "deterministicAlgorithms": False,
    }
    print("CANONICAL CPU PREFLIGHT PASS:", runtime["python"], runtime["torch"], runtime["onnxruntime"], runtime["cpuModel"])
    return torch, ort, runtime


def _selected_pages(repo: Path) -> tuple[dict[str, Any], list[str]]:
    selection = _json(repo / "evidence/stage11/v2d/v2d-class-selection-decision.v1.json")
    if selection.get("nextStep", {}).get("scope") != ["notehead"] or selection.get("nextStep", {}).get("canonicalCpuRerunRequired") is not True:
        raise RuntimeError("canonical rerun scope must remain notehead")
    if selection.get("claimBoundary", {}).get("semanticPreservationEstablished") is not False: raise RuntimeError("selection must remain fail-closed")
    teacher = _teacher_manifest(repo)
    pages = [str(p["pageId"]) for p in teacher["pages"] if p["classes"]["notehead"]["state"] == "present"]
    if len(pages) != 18: raise RuntimeError(f"expected 18 notehead pages, got {len(pages)}")
    return teacher, pages


def _manifest() -> dict[str, Any]:
    if MANIFEST_PATH.is_file():
        try: p = _json(MANIFEST_PATH)
        except (OSError, json.JSONDecodeError, RuntimeError): p = {}
        if p.get("schemaVersion") == SCHEMA and all(isinstance(p.get(k), dict) for k in ("restoredPages", "sourceDetector", "restoredDetector", "pageResults")): return p
    return {"schemaVersion": SCHEMA, "restoredPages": {}, "sourceDetector": {}, "restoredDetector": {}, "pageResults": {}}


def _record(path: Path, fingerprint: str, **extra: Any) -> dict[str, Any]:
    out = {"fingerprint": fingerprint, "byteSize": path.stat().st_size, "sha256": sha256_file(path)}; out.update(extra); return out


def _valid(record: Any, path: Path, fingerprint: str) -> bool:
    return isinstance(record, Mapping) and record.get("fingerprint") == fingerprint and isinstance(record.get("byteSize"), int) and isinstance(record.get("sha256"), str) and _validate_exact_file(path, int(record["byteSize"]), str(record["sha256"]))


def _source(v2d_manifest: Mapping[str, Any], page_id: str) -> tuple[Path, dict[str, Any]]:
    rec = v2d_manifest["sourcePages"].get(page_id); path = CACHE_ROOT / "source_pages" / f"{page_id}.png"
    if not isinstance(rec, dict) or not _validate_exact_file(path, int(rec["byteSize"]), str(rec["sha256"])): raise RuntimeError(f"source cache mismatch: {page_id}")
    return path, dict(rec)


def _restore_fp(source_record: Mapping[str, Any]) -> str:
    return _fp({"schema": SCHEMA, "sourceSha256": source_record["sha256"], "modelSha256": TARGETS["restore_model"]["sha256"], "algorithm": "v2d-frozen-restore-512-overlap64-png3.v1", "python": PYTHON, "torch": TORCH, "intra": INTRA, "inter": INTER})


def _png(gray: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", gray, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    if not ok: raise RuntimeError("PNG encode failed")
    return buf.tobytes()


def _ensure_restore(page_id: str, source_path: Path, source_rec: Mapping[str, Any], model: Any, device: Any, runtime: Mapping[str, Any], manifest: dict[str, Any], repeat: bool) -> tuple[Path, dict[str, Any]]:
    RESTORE_DIR.mkdir(parents=True, exist_ok=True); path = RESTORE_DIR / f"{page_id}.png"; fingerprint = _restore_fp(source_rec); rec = manifest["restoredPages"].get(page_id)
    if _valid(rec, path, fingerprint):
        if repeat and rec.get("localRepeatPixelIdentityPassed") is not True: raise RuntimeError("first-page repeat proof missing")
        print("canonical restore cache reuse:", page_id); return path, dict(rec)
    gray = cv2.imread(str(source_path), cv2.IMREAD_GRAYSCALE)
    if gray is None: raise RuntimeError(f"cannot read {source_path}")
    t0 = time.monotonic(); first = _restore_gray(model, gray, device); repeat_passed = None; repeat_sha = None
    if repeat:
        second = _restore_gray(model, gray, device); repeat_passed = np.array_equal(first, second); repeat_sha = _pixel_sha(second)
        if not repeat_passed: raise RuntimeError(f"same-runtime CPU Restore repeat mismatch: {page_id}")
    elapsed = time.monotonic() - t0; _atomic_write_bytes(path, _png(first))
    rec = _record(path, fingerprint, outputPixelSha256=_pixel_sha(first), localRepeatPixelIdentityPassed=repeat_passed, localRepeatPixelSha256=repeat_sha, createdRuntime=dict(runtime), restoreElapsedSeconds=elapsed)
    manifest["restoredPages"][page_id] = rec; _atomic_write_json(MANIFEST_PATH, manifest)
    print(f"canonical restore SAVED: {page_id} ({elapsed:.1f}s)"); return path, dict(rec)


def _session(ort: Any, checkpoint: Path) -> Any:
    so = ort.SessionOptions(); so.intra_op_num_threads = INTRA; so.inter_op_num_threads = INTER; so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL; so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess = ort.InferenceSession(str(checkpoint), sess_options=so, providers=[PROVIDER])
    if sess.get_providers()[0] != PROVIDER or len(sess.get_inputs()) != 1 or not sess.get_outputs(): raise RuntimeError("seg_net session preflight failed")
    shape = sess.get_inputs()[0].shape
    if len(shape) != 4 or not isinstance(shape[1], int) or not isinstance(shape[2], int): raise RuntimeError(f"unexpected seg_net input shape: {shape}")
    return sess


def _resize(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]; pixels = w * h; ratio = (((3_000_000 / pixels) + (4_350_000 / pixels)) / 2.0) ** 0.5
    return cv2.resize(image, (max(1, round(ratio * w)), max(1, round(ratio * h))), interpolation=cv2.INTER_LINEAR)


def _positions(length: int, window: int) -> list[int]:
    if length <= window: return [0]
    last = length - window; out = list(range(0, last + 1, STEP))
    if out[-1] != last: out.append(last)
    return out


def _unit(image: np.ndarray) -> float:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY); rows = np.flatnonzero((gray < 128).mean(axis=1) >= 0.35)
    if len(rows) < 5: return 10.0
    groups: list[list[int]] = []
    for row in rows.tolist():
        if not groups or row > groups[-1][-1] + 1: groups.append([row])
        else: groups[-1].append(row)
    centers = np.asarray([np.mean(g) for g in groups]); diff = np.diff(centers); diff = diff[(diff >= 3) & (diff <= 40)]
    return float(np.median(diff)) if len(diff) else 10.0


def _seg_map(sess: Any, path: Path) -> tuple[np.ndarray, np.ndarray, int]:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None: raise RuntimeError(f"cannot read detector image: {path}")
    image = _resize(image); inp = sess.get_inputs()[0]; out_meta = sess.get_outputs()[0]; wh, ww = int(inp.shape[1]), int(inp.shape[2])
    ys, xs = _positions(image.shape[0], wh), _positions(image.shape[1], ww); coords = [(y, x) for y in ys for x in xs]
    channels = int(out_meta.shape[-1]) if isinstance(out_meta.shape[-1], int) else 4
    accum = np.zeros((image.shape[0], image.shape[1], channels), np.float32); weight = np.zeros((image.shape[0], image.shape[1], 1), np.float32)
    for start in range(0, len(coords), BATCH):
        bc = coords[start:start+BATCH]; batch = np.stack([image[y:y+wh, x:x+ww] for y, x in bc]); pred = sess.run([out_meta.name], {inp.name: batch})[0]
        for patch, (y, x) in zip(pred, bc): accum[y:y+wh, x:x+ww] += patch; weight[y:y+wh, x:x+ww] += 1
    if np.any(weight == 0): raise RuntimeError("detector tiling gap")
    return np.argmax(accum / weight, axis=-1).astype(np.uint8), image, len(coords)


def _boxes(class_map: np.ndarray, unit: float) -> list[tuple[float, float, float, float]]:
    mask = (class_map == 2).astype(np.uint8); n, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8); out = []; min_area = max(3, int(unit * unit * 0.08))
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if int(area) >= min_area and .35*unit <= w <= 2.2*unit and .35*unit <= h <= 2.2*unit: out.append((float(x), float(y), float(x+w), float(y+h)))
    return out


def _det_fp(image_rec: Mapping[str, Any], source_unit: float) -> str:
    return _fp({"schema": DETECTOR_SCHEMA, "imageSha256": image_rec["sha256"], "checkpointSha256": SEG_SHA, "logic": LOGIC, "provider": PROVIDER, "onnxruntime": ORT, "step": STEP, "batch": BATCH, "sourceUnit": round(source_unit, 6)})


def _load_det(path: Path, rec: Any, fingerprint: str) -> dict[str, Any] | None:
    if not _valid(rec, path, fingerprint): return None
    try: p = _json(path)
    except (OSError, json.JSONDecodeError, RuntimeError): return None
    return p if p.get("schemaVersion") == DETECTOR_SCHEMA and p.get("fingerprint") == fingerprint and isinstance(p.get("boxes"), list) and p.get("boxCount") == len(p["boxes"]) else None


def _ensure_det(path: Path, image_path: Path, image_rec: Mapping[str, Any], source_unit: float, sess: Any, rec_map: dict[str, Any], manifest: dict[str, Any], page_id: str, role: str) -> tuple[dict[str, Any], float]:
    path.parent.mkdir(parents=True, exist_ok=True); fingerprint = _det_fp(image_rec, source_unit); cached = _load_det(path, rec_map.get(page_id), fingerprint)
    if cached is not None: print(f"notehead detector cache reuse: {role} {page_id}"); return cached, 0.0
    t0 = time.monotonic(); class_map, resized, patches = _seg_map(sess, image_path)
    if role == "source" and abs(_unit(resized) - source_unit) > 1e-6: raise RuntimeError("source unit changed within detector pass")
    boxes = _boxes(class_map, source_unit); elapsed = time.monotonic() - t0
    payload = {"schemaVersion": DETECTOR_SCHEMA, "fingerprint": fingerprint, "pageId": page_id, "role": role, "imageSha256": image_rec["sha256"], "sourceUnit": source_unit, "patchCount": patches, "boxCount": len(boxes), "boxes": [list(b) for b in boxes], "elapsedSeconds": elapsed}
    _atomic_write_json(path, payload); rec_map[page_id] = _record(path, fingerprint); _atomic_write_json(MANIFEST_PATH, manifest)
    print(f"notehead detector SAVED: {role} {page_id} boxes={len(boxes)} patches={patches} ({elapsed:.1f}s)"); return payload, elapsed


def _page_fp(page_id: str, sdet: Mapping[str, Any], rdet: Mapping[str, Any], rrec: Mapping[str, Any]) -> str:
    return _fp({"schema": PAGE_SCHEMA, "pageId": page_id, "sourceDetector": sdet["fingerprint"], "restoredDetector": rdet["fingerprint"], "restoredSha256": rrec["sha256"], "iou": IOU, "recall": RECALL_MARKER})


def _budget_result(runtime: Mapping[str, Any], page_id: str, measured: float, projected: float) -> Path:
    out = RESULT_ROOT / RESULT_NAME; _atomic_write_json(out, {"schemaVersion": SCHEMA, "generatedOn": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "status": "BLOCKED_BY_COST_BUDGET", "scope": {"developmentOnly": True, "selectedSemanticClass": "notehead", "heldOutAccessed": False}, "runtime": dict(runtime), "canary": {"pageId": page_id, "measuredDetectorPairSeconds": measured, "projectedDetectorSecondsFor18Pages": projected, "maxAllowedProjectedDetectorSeconds": MAX_PROJECTED_DETECTOR_SECONDS}, "claimBoundary": {"semanticPreservationEstablished": False, "productionReady": False, "stage12EntryAuthorized": False}}); return out


def run_canonical_cpu_notehead_semantic_rerun() -> Path:
    repo = Path(__file__).resolve().parents[2]; teacher, selected = _selected_pages(repo); teacher_pages = {p["pageId"]: p for p in teacher["pages"]}
    benchmark = RESULT_ROOT / "v2d_colab_gpu_detector_benchmark_result.json"
    if not _validate_exact_file(benchmark, BENCHMARK_SIZE, BENCHMARK_SHA): raise RuntimeError("completed V2d benchmark result missing/mismatched")
    torch, ort, runtime = _runtime_preflight(); v2d_manifest_path = CACHE_ROOT / "cache_manifest.json"
    if not v2d_manifest_path.is_file(): raise RuntimeError("V2d cache manifest missing")
    v2d_manifest = _load_cache_manifest(v2d_manifest_path); manifest = _manifest(); RUN_ROOT.mkdir(parents=True, exist_ok=True); RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    model_spec = TARGETS["restore_model"]; model_path = CACHE_ROOT / "exact_inputs" / str(model_spec["filename"]); checkpoint = CACHE_ROOT / "oemer_checkpoints" / SEG_REL
    if not _validate_exact_file(model_path, int(model_spec["size"]), str(model_spec["sha256"])): raise RuntimeError("frozen Restore package mismatch")
    if not _validate_exact_file(checkpoint, SEG_SIZE, SEG_SHA): raise RuntimeError("seg_net checkpoint mismatch")
    device = torch.device("cpu"); model = torch.jit.load(str(model_path), map_location=device).to(device).eval(); sess = _session(ort, checkpoint)
    print("NOTEHEAD-ONLY DETECTOR PREFLIGHT PASS:", LOGIC, PROVIDER)
    pages = []; detector_seconds = 0.0; run_started = time.monotonic()
    for index, page_id in enumerate(selected, 1):
        if index > 1 and time.monotonic() - run_started > MAX_TOTAL_WALL_SECONDS: raise RuntimeError("total wall-clock cost budget exceeded; completed caches are safe")
        if teacher_pages[page_id]["classes"]["notehead"]["state"] != "present": raise RuntimeError(f"teacher state changed: {page_id}")
        source_path, source_rec = _source(v2d_manifest, page_id)
        restored_path, restored_rec = _ensure_restore(page_id, source_path, source_rec, model, device, runtime, manifest, index == 1)
        restored_gray = cv2.imread(str(restored_path), cv2.IMREAD_GRAYSCALE)
        if restored_gray is None or _pixel_sha(restored_gray) != restored_rec.get("outputPixelSha256"): raise RuntimeError(f"restored pixel binding mismatch: {page_id}")
        source_image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
        if source_image is None: raise RuntimeError(f"cannot read {source_path}")
        source_unit = _unit(_resize(source_image))
        sdet, se = _ensure_det(SOURCE_DET_DIR/f"{page_id}.json", source_path, source_rec, source_unit, sess, manifest["sourceDetector"], manifest, page_id, "source")
        rdet, re = _ensure_det(RESTORED_DET_DIR/f"{page_id}.json", restored_path, restored_rec, source_unit, sess, manifest["restoredDetector"], manifest, page_id, "restored")
        pair = se + re; detector_seconds += pair
        if index == 1:
            measured = pair or float(sdet.get("elapsedSeconds", 0)) + float(rdet.get("elapsedSeconds", 0)); projected = measured * len(selected)
            print(f"CANARY detector pair={measured:.1f}s projected18={projected/60:.1f}min")
            if projected > MAX_PROJECTED_DETECTOR_SECONDS:
                out = _budget_result(runtime, page_id, measured, projected); raise RuntimeError(f"projected detector runtime exceeds cost budget; result saved: {out}")
            print("CANARY COST BUDGET PASS")
        fingerprint = _page_fp(page_id, sdet, rdet, restored_rec); PAGE_DIR.mkdir(parents=True, exist_ok=True); page_path = PAGE_DIR/f"{page_id}.json"; page_result = None
        if _valid(manifest["pageResults"].get(page_id), page_path, fingerprint):
            try: candidate = _json(page_path); page_result = candidate if candidate.get("schemaVersion") == PAGE_SCHEMA and candidate.get("fingerprint") == fingerprint else None
            except Exception: page_result = None
        if page_result is None:
            sb = [tuple(map(float, b)) for b in sdet["boxes"]]; rb = [tuple(map(float, b)) for b in rdet["boxes"]]
            if not sb: raise RuntimeError(f"notehead source detector empty: {page_id}")
            recall, matched, cand_only = _greedy_recall(sb, rb, threshold=IOU)
            page_result = {"schemaVersion": PAGE_SCHEMA, "fingerprint": fingerprint, "pageId": page_id, "teacherState": "present", "canonicalRestoredFileSha256": restored_rec["sha256"], "canonicalRestoredPixelSha256": restored_rec["outputPixelSha256"], "detector": {"candidateId": "oemer-segnet-notehead-fast-dbe2a933", "logicVersion": LOGIC, "checkpointSha256": SEG_SHA, "provider": PROVIDER, "sourceUnit": source_unit}, "metric": {"classId": "notehead", "sourceCount": len(sb), "candidateCount": len(rb), "matchedCount": matched, "sourceRecall": recall, "candidateOnlyCount": cand_only, "recallAtLeast0_80": recall >= RECALL_MARKER}}
            _atomic_write_json(page_path, page_result); manifest["pageResults"][page_id] = _record(page_path, fingerprint); _atomic_write_json(MANIFEST_PATH, manifest); print(f"canonical semantic SAVED {index:02d}/{len(selected)} {page_id} recall={recall:.4f}")
        else: print(f"canonical semantic cache reuse {index:02d}/{len(selected)} {page_id}")
        pages.append(page_result)
    del model
    metrics = [p["metric"] for p in pages]; recalls = [float(m["sourceRecall"]) for m in metrics]; at_marker = sum(bool(m["recallAtLeast0_80"]) for m in metrics)
    result = {
        "schemaVersion": SCHEMA, "generatedOn": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "status": "COMPLETE", "contractId": "stage11.v2c.semantic-preservation.nonheldout.v1",
        "scope": {"developmentOnly": True, "selectedSemanticClass": "notehead", "selectedTeacherPresentPageCount": len(selected), "teacherGroundTruthFrozen": True, "detectorOutputUsedAsGroundTruth": False, "trainingPerformed": False, "fineTuningPerformed": False, "heldOutAccessed": False},
        "runtime": runtime,
        "restore": {"packageSha256": str(model_spec["sha256"]), "device": "CPU", "actualCpuOutputsPersistedAndHashBound": True, "crossHostPixelIdentityToEarlierV2cAssumed": False, "firstPageSameRuntimeRepeatPixelIdentityRequired": True},
        "detector": {"candidateId": "oemer-segnet-notehead-fast-dbe2a933", "upstreamRole": "measurement_only", "logicVersion": LOGIC, "checkpointSha256": SEG_SHA, "onnxruntime": ORT, "provider": PROVIDER, "step": STEP, "batch": BATCH, "matchIoUThreshold": IOU, "sourceRecallMarker": RECALL_MARKER, "fullOemerPipelineExecuted": False, "unetBigExecuted": False, "segNetOnly": True, "exploratoryBenchmarkSha256": BENCHMARK_SHA},
        "costControl": {"canaryProjectionLimitSeconds": MAX_PROJECTED_DETECTOR_SECONDS, "totalWallLimitSeconds": MAX_TOTAL_WALL_SECONDS, "detectorSecondsExecutedThisInvocation": detector_seconds, "totalWallSecondsThisInvocation": time.monotonic() - run_started},
        "noteheadEvidence": {"evaluatedPageCount": len(metrics), "pagesAtRecallGte0_80": at_marker, "rateAtRecallGte0_80": at_marker/len(metrics), "meanSourceRecall": sum(recalls)/len(recalls), "minimumSourceRecall": min(recalls), "maximumSourceRecall": max(recalls), "allTeacherPresentPagesEvaluated": len(metrics) == len(selected)},
        "pages": pages,
        "claimBoundary": {"noteheadCanonicalCpuSemanticRerunCompleted": True, "semanticPreservationEstablished": False, "overallStage11PassAuthorized": False, "productionReady": False, "productionPromotionAuthorized": False, "stage12EntryAuthorized": False},
    }
    out = RESULT_ROOT / RESULT_NAME; _atomic_write_json(out, result); print("CANONICAL CPU NOTEHEAD SEMANTIC RERUN COMPLETE"); print("SAVED:", out); return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--run", action="store_true"); args = parser.parse_args(argv)
    if not args.run: raise SystemExit("Refusing implicit execution; pass --run")
    run_canonical_cpu_notehead_semantic_rerun(); return 0


if __name__ == "__main__": raise SystemExit(main())
