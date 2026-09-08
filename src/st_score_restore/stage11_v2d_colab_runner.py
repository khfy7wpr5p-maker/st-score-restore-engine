"""Robust Colab GPU runner for Stage 11 V2d detector benchmarking.

Development-only, inference-only. Never trains or mutates the frozen restore model.
The runner downloads only the six explicitly approved development artifacts by
Drive file id, verifies exact byte size + SHA-256, then benchmarks the pinned
Oemer detector against the frozen 100% teacher ground-truth manifest.
"""
from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch

from .stage11_v2c_teacher_review import materialize_teacher_review_manifest
from .stage11_v2d_detector_benchmark import (
    benchmark_coverage_from_present_pairs,
    teacher_present_class_pairs,
    validate_detector_benchmark_result,
)
from .stage11_v2c_semantic_preservation import conservative_line_system_detector


TARGETS: dict[str, dict[str, Any]] = {
    "restore_model": {
        "drive_id": "1oJ9lOEpq7trDD8XZpVwCzQzMQ2mk-wWD",
        "sha256": "7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234",
        "size": 7817857,
        "kind": "torchscript",
        "filename": "v2a_candidate_512.torchscript.pt",
    },
    "beethoven": {
        "drive_id": "1F6Xp6mmwsjmpk64GkcDqw6t0XpH_1IGk",
        "sha256": "c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c",
        "size": 1182561,
        "kind": "pdf",
        "filename": "beethoven-op48-no3.pdf",
        "pages": [1, 2, 3, 4],
        "page_ids": [
            "beethoven-op48-no3-p1",
            "beethoven-op48-no3-p2",
            "beethoven-op48-no3-p3",
            "beethoven-op48-no3-p4",
        ],
    },
    "wikimedia": {
        "drive_id": "1JYyN_nk0lYarszlBlC9nqVfeJxB0FEmz",
        "sha256": "36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb",
        "size": 34636,
        "kind": "png",
        "filename": "wikimedia-guitar-technical-exercise-no1.png",
        "pages": [1],
        "page_ids": ["wikimedia-guitar-technical-exercise-no1-p1"],
    },
    "barley": {
        "drive_id": "1TsmQFpcM4uv52MH37ilKFj1jYY4pyCrG",
        "sha256": "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e",
        "size": 84689,
        "kind": "pdf",
        "filename": "barley-your-face-your-tongue-your-wit.pdf",
        "pages": [1, 2],
        "page_ids": [
            "barley-your-face-your-tongue-your-wit-p1",
            "barley-your-face-your-tongue-your-wit-p2",
        ],
    },
    "carulli": {
        "drive_id": "1TkE4FVRb16IhVkYH5q10WOs4wPRDdhmi",
        "sha256": "db20e9ce755aa56dd9dbb0436a37a48545442e7961e471f813cde7aaa8fc0f22",
        "size": 4662523,
        "kind": "pdf",
        "filename": "carulli-morceaux-faciles.pdf",
        "pages": list(range(2, 11)),
        "page_ids": [f"carulli-morceaux-faciles-p{i}" for i in range(2, 11)],
    },
    "bach": {
        "drive_id": "1tgd9EEplOAwJmdurUGctvQ9Rzw6U4zvX",
        "sha256": "692d4317375048b9d520b4d756c3ce992e96ca82b10c3026a5925f1a878fc959",
        "size": 3235494,
        "kind": "pdf",
        "filename": "bach-anna-magdalena.pdf",
        "pages": [4, 10, 24, 40],
        "page_ids": [
            "bach-anna-magdalena-p4",
            "bach-anna-magdalena-p10",
            "bach-anna-magdalena-p24",
            "bach-anna-magdalena-p40",
        ],
    },
}


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _download_exact_drive_targets(dest_dir: Path) -> dict[str, Path]:
    """Download only approved development bytes by explicit Drive id."""
    from google.colab import auth  # type: ignore
    import google.auth  # type: ignore
    from googleapiclient.discovery import build  # type: ignore
    from googleapiclient.http import MediaIoBaseDownload  # type: ignore

    print("Authenticating Google Drive API for exact development bytes...")
    auth.authenticate_user()
    credentials, _ = google.auth.default()
    service = build("drive", "v3", credentials=credentials, cache_discovery=False)

    dest_dir.mkdir(parents=True, exist_ok=True)
    found: dict[str, Path] = {}
    for key, spec in TARGETS.items():
        out = dest_dir / str(spec["filename"])
        request = service.files().get_media(fileId=str(spec["drive_id"]))
        with io.FileIO(out, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request, chunksize=1024 * 1024)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status is not None:
                    print(f"{key}: {int(status.progress() * 100):3d}%")

        actual_size = out.stat().st_size
        actual_sha = sha256_file(out)
        if actual_size != int(spec["size"]):
            raise RuntimeError(
                f"Exact-byte size mismatch for {key}: {actual_size} != {spec['size']}"
            )
        if actual_sha != str(spec["sha256"]):
            raise RuntimeError(
                f"Exact-byte SHA mismatch for {key}: {actual_sha} != {spec['sha256']}"
            )
        found[key] = out
        print(f"verified {key}: {actual_size} bytes {actual_sha[:12]}...")
    return found


def _render_pdf_page(pdf: Path, page_num: int, out_png: Path) -> None:
    base = out_png.with_suffix("")
    subprocess.run(
        [
            "pdftoppm",
            "-f",
            str(page_num),
            "-l",
            str(page_num),
            "-singlefile",
            "-r",
            "72",
            "-png",
            str(pdf),
            str(base),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    alt = Path(str(base) + ".png")
    if not out_png.exists() and alt.exists():
        alt.replace(out_png)
    if not out_png.exists():
        raise FileNotFoundError(out_png)


def _restore_gray(model: torch.jit.ScriptModule, gray_u8: np.ndarray, device: torch.device) -> np.ndarray:
    patch = 512
    overlap = 64
    stride = patch - overlap
    h, w = gray_u8.shape
    acc = np.zeros((h, w), np.float32)
    cnt = np.zeros((h, w), np.float32)
    with torch.inference_mode():
        for y in range(0, h, stride):
            for x in range(0, w, stride):
                y2, x2 = min(y + patch, h), min(x + patch, w)
                tile = np.full((patch, patch), 255, np.uint8)
                tile[: y2 - y, : x2 - x] = gray_u8[y:y2, x:x2]
                inp = torch.from_numpy(tile.astype(np.float32) / 255.0)[None, None].to(device)
                out = model(inp)
                if isinstance(out, (tuple, list)):
                    out = out[0]
                arr = out.detach().float().cpu().numpy().squeeze()
                arr = np.clip(arr, 0.0, 1.0)
                arr = (arr * 255.0 + 0.5).astype(np.uint8)
                crop = arr[: y2 - y, : x2 - x].astype(np.float32)
                acc[y:y2, x:x2] += crop
                cnt[y:y2, x:x2] += 1.0
    return np.clip(acc / np.maximum(cnt, 1.0), 0, 255).astype(np.uint8)


def _component_boxes(mask: np.ndarray, min_area: int = 4) -> list[tuple[int, int, int, int, int]]:
    m = (mask > 0).astype(np.uint8)
    n, _, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    boxes: list[tuple[int, int, int, int, int]] = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area >= min_area and w > 0 and h > 0:
            boxes.append((int(x), int(y), int(x + w), int(y + h), int(area)))
    return boxes


def _estimate_unit(staff_mask: np.ndarray) -> float:
    occ = (staff_mask > 0).mean(axis=1)
    rows = np.flatnonzero(occ >= 0.20)
    if len(rows) < 5:
        return 10.0
    groups: list[list[int]] = []
    for row in rows.tolist():
        if not groups or row > groups[-1][-1] + 1:
            groups.append([row])
        else:
            groups[-1].append(row)
    centers = np.array([np.mean(g) for g in groups], dtype=float)
    if len(centers) < 2:
        return 10.0
    diffs = np.diff(centers)
    diffs = diffs[(diffs >= 3) & (diffs <= 40)]
    return float(np.median(diffs)) if len(diffs) else 10.0


def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    return inter / ((ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter)


def _greedy_recall(src_boxes: list[tuple[float, float, float, float]], cand_boxes: list[tuple[float, float, float, float]], threshold: float = 0.20) -> tuple[float, int, int]:
    pairs: list[tuple[float, int, int]] = []
    for si, source in enumerate(src_boxes):
        for ci, candidate in enumerate(cand_boxes):
            overlap = _iou(source, candidate)
            if overlap >= threshold:
                pairs.append((overlap, si, ci))
    pairs.sort(reverse=True)
    used_src: set[int] = set()
    used_cand: set[int] = set()
    matched = 0
    for _, si, ci in pairs:
        if si in used_src or ci in used_cand:
            continue
        used_src.add(si)
        used_cand.add(ci)
        matched += 1
    return matched / max(1, len(src_boxes)), matched, max(0, len(cand_boxes) - matched)


def _prepare_oemer_checkpoints() -> tuple[Any, dict[str, str]]:
    # Compatibility aliases for older upstream Oemer code under modern NumPy.
    np.int = int  # type: ignore[attr-defined]
    np.float = float  # type: ignore[attr-defined]
    np.bool = bool  # type: ignore[attr-defined]

    from oemer import MODULE_PATH  # type: ignore
    from oemer.ete import generate_pred  # type: ignore

    checkpoints = {
        "unet_big/model.onnx": "https://github.com/BreezeWhite/oemer/releases/download/checkpoints/1st_model.onnx",
        "seg_net/model.onnx": "https://github.com/BreezeWhite/oemer/releases/download/checkpoints/2nd_model.onnx",
    }
    hashes: dict[str, str] = {}
    for rel, url in checkpoints.items():
        dest = Path(MODULE_PATH) / "checkpoints" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            print("downloading Oemer checkpoint", rel)
            urllib.request.urlretrieve(url, dest)
        hashes[rel] = sha256_file(dest)
    return generate_pred, hashes


def _detect_semantic_boxes(img_path: Path, generate_pred: Any) -> dict[str, list[tuple[float, float, float, float]]]:
    staff, symbols, stems_rests, notehead, clefs_keys = generate_pred(str(img_path), use_tf=False)
    unit = _estimate_unit(staff)
    out: dict[str, list[tuple[float, float, float, float]]] = {
        key: []
        for key in [
            "staff_line",
            "tab_line",
            "notehead",
            "stem",
            "beam_or_flag",
            "rest",
            "accidental",
            "clef",
            "barline",
        ]
    }

    for x1, y1, x2, y2, _ in _component_boxes(notehead, min_area=max(3, int(unit * unit * 0.08))):
        w, h = x2 - x1, y2 - y1
        if 0.35 * unit <= w <= 2.2 * unit and 0.35 * unit <= h <= 2.2 * unit:
            out["notehead"].append((float(x1), float(y1), float(x2), float(y2)))

    for x1, y1, x2, y2, _ in _component_boxes(stems_rests, min_area=max(3, int(unit * 0.5))):
        w, h = x2 - x1, y2 - y1
        box = (float(x1), float(y1), float(x2), float(y2))
        if h >= 3.6 * unit and w <= 1.5 * unit:
            out["barline"].append(box)
        elif h >= 1.8 * unit and w <= 1.2 * unit:
            out["stem"].append(box)
        elif 0.45 * unit <= w <= 3.0 * unit and 0.45 * unit <= h <= 3.6 * unit:
            out["rest"].append(box)

    for x1, y1, x2, y2, _ in _component_boxes(clefs_keys, min_area=max(3, int(unit * unit * 0.10))):
        w, h = x2 - x1, y2 - y1
        box = (float(x1), float(y1), float(x2), float(y2))
        if h >= 2.4 * unit and w >= 0.8 * unit:
            out["clef"].append(box)
        elif 0.45 * unit <= h <= 3.0 * unit and 0.25 * unit <= w <= 2.2 * unit:
            out["accidental"].append(box)

    residue = (symbols > 0).astype(np.uint8)
    residue[(notehead > 0) | (stems_rests > 0) | (clefs_keys > 0) | (staff > 0)] = 0
    for x1, y1, x2, y2, _ in _component_boxes(residue, min_area=max(3, int(unit * unit * 0.10))):
        w, h = x2 - x1, y2 - y1
        if (w >= 1.4 * unit and h <= 1.8 * unit) or (h >= 0.8 * unit and w <= 1.8 * unit):
            out["beam_or_flag"].append((float(x1), float(y1), float(x2), float(y2)))

    gray = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise RuntimeError(f"cannot read {img_path}")
    for detection in conservative_line_system_detector(gray):
        out[detection.class_id].append(tuple(map(float, detection.bbox)))
    return out


def run_colab_benchmark() -> Path:
    """Execute the exploratory V2d GPU benchmark and save JSON to Drive."""
    if not torch.cuda.is_available():
        raise RuntimeError("GPU runtime required: Colab > Runtime > Change runtime type > GPU")

    repo_root = Path(__file__).resolve().parents[2]
    drive_root = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL")
    if not drive_root.exists():
        raise FileNotFoundError(f"Drive folder not mounted/found: {drive_root}")

    exact_dir = Path("/content/v2d_exact_bytes")
    if exact_dir.exists():
        shutil.rmtree(exact_dir)
    found = _download_exact_drive_targets(exact_dir)

    base = json.loads((repo_root / "evidence/stage11/v2c/v2c-expected-class-manifest.v1.json").read_text())
    overlay = json.loads((repo_root / "evidence/stage11/v2c/v2c-teacher-review-overlay.v1.json").read_text())
    resolution = json.loads((repo_root / "evidence/stage11/v2c/v2c-teacher-review-resolution.v1.json").read_text())
    teacher = materialize_teacher_review_manifest(base, overlay, resolution)["manifest"]
    eligible_pairs = teacher_present_class_pairs(teacher)
    if len(eligible_pairs) != 171:
        raise RuntimeError(f"teacher present-pair count mismatch: {len(eligible_pairs)}")

    work = Path("/content/v2d_work")
    if work.exists():
        shutil.rmtree(work)
    src_dir = work / "source"
    restored_dir = work / "restored_gpu_exploratory"
    src_dir.mkdir(parents=True, exist_ok=True)
    restored_dir.mkdir(parents=True, exist_ok=True)

    page_paths: dict[str, Path] = {}
    for family, spec in TARGETS.items():
        if family == "restore_model":
            continue
        for page_num, page_id in zip(spec["pages"], spec["page_ids"]):
            out = src_dir / f"{page_id}.png"
            if spec["kind"] == "pdf":
                _render_pdf_page(found[family], int(page_num), out)
            else:
                shutil.copy2(found[family], out)
            page_paths[str(page_id)] = out
    if len(page_paths) != 20:
        raise RuntimeError(f"expected 20 development pages, got {len(page_paths)}")

    print("Running frozen restore model on GPU for exploratory comparison...")
    device = torch.device("cuda")
    model = torch.jit.load(str(found["restore_model"]), map_location=device).to(device).eval()
    restored_paths: dict[str, Path] = {}
    for index, (page_id, src_path) in enumerate(page_paths.items(), 1):
        gray = cv2.imread(str(src_path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            raise RuntimeError(f"cannot read {src_path}")
        restored = _restore_gray(model, gray, device)
        out = restored_dir / f"{page_id}.png"
        cv2.imwrite(str(out), restored, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        restored_paths[page_id] = out
        print(f"restore {index:02d}/20 {page_id}")
    del model
    torch.cuda.empty_cache()

    generate_pred, checkpoint_hashes = _prepare_oemer_checkpoints()
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

    import onnxruntime as ort  # type: ignore

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
            "device": "GPU",
            "torchVersion": torch.__version__,
            "cudaAvailable": torch.cuda.is_available(),
            "cudaDevice": torch.cuda.get_device_name(0),
            "onnxruntimeVersion": ort.__version__,
            "onnxProviders": ort.get_available_providers(),
            "restoreExecutionMode": "GPU exploratory; final canonical CPU rerun required",
            "finalCanonicalCpuRerunRequired": True,
        },
        "inputs": {
            "teacherPresentClassPageCount": 171,
            "sourceFiles": {
                key: {
                    "sha256": TARGETS[key]["sha256"],
                    "byteSize": TARGETS[key]["size"],
                    "driveFileId": TARGETS[key]["drive_id"],
                }
                for key in found
            },
            "oemerUpstreamCommit": "dbe2a933d630d0f74805d717960eb259473f5978",
            "oemerCheckpointSha256": checkpoint_hashes,
        },
        "coverage": {
            "eligibleExpectedPresentClassPageCount": source_cov["eligibleExpectedPresentClassPageCount"],
            "confidentlyEvaluatedExpectedPresentClassPageCount": source_cov["confidentlyEvaluatedExpectedPresentClassPageCount"],
            "applicableClassDetectorCoverage": source_cov["applicableClassDetectorCoverage"],
            "classCoverage": source_cov["classCoverage"],
        },
        "semanticExploration": {
            "matchedAtRecallAtLeast0_80ClassPageCount": semantic_cov["confidentlyEvaluatedExpectedPresentClassPageCount"],
            "matchedAtRecallAtLeast0_80Coverage": semantic_cov["applicableClassDetectorCoverage"],
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
