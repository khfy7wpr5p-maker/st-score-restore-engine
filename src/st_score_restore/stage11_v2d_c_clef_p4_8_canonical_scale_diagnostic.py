"""P4.8 development-only canonical staff-spacing diagnostic.

Purpose:
- use ONLY the frozen 29-page development corpus,
- never read the P4.7 holdout,
- synthetically scale development pages to 1.00 / 0.75 / 0.50,
- estimate staff spacing before teacher access,
- resize each page to a canonical median staff spacing of 15 px,
- run the frozen P4.5 localizer and frozen P4.6 filter unchanged,
- freeze candidates before teacher truth is opened,
- evaluate only after Phase A is frozen.

This is a diagnostic, not a qualification run.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import statistics
import tempfile
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import cv2

ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/C_CLEF_SOURCE_PAGES")
MANIFEST_PATH = ROOT / "_PREPARED" / "c_clef_source_page_manifest.v1.json"
TEACHER_PATH = ROOT / "_ANNOTATIONS" / "c_clef_teacher_boxes.v1.json"
OUT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/P4_C_CLEF_P4_8_CANONICAL_DEV_DIAGNOSTIC")
RAW_PATH = OUT / "p4_8_canonical_scale_candidates.v1.json"
RESULT_PATH = OUT / "p4_8_canonical_scale_diagnostic.v1.json"

EXPECTED_MANIFEST_SHA256 = "365d45462b9d7b422a640e47bacdd5c8a5f16860198dec37121946411f6b3294"
EXPECTED_TEACHER_SHA256 = "1104d916faaf8d3c391cca9eda0354d21259f722cdcfe0f414c140796a5ffc5b"
EXPECTED_PAGE_COUNT = 29
EXPECTED_TEACHER_BOX_COUNT = 71

P45_COMMIT = "7130bdf94bcf9247a0b33e9342db22746b46f289"
P46_COMMIT = "76caac8a7c76606bf09051ae5cd1704e32ef29dd"
P45_EXPECTED_SOURCE_SHA256 = "0bd631e0863f084204cb3927aa19c1da715e30c81371250a50b4ad97f107c426"
P46_EXPECTED_SOURCE_SHA256 = "33e05d64cdfdb32952887daae08cf623eb337a0ae544c154be763c923337e99a"

P45_URL = (
    "https://raw.githubusercontent.com/khfy7wpr5p-maker/st-score-restore-engine/"
    + P45_COMMIT
    + "/src/st_score_restore/stage11_v2d_c_clef_p4_5_source_image_localizer.py"
)
P46_URL = (
    "https://raw.githubusercontent.com/khfy7wpr5p-maker/st-score-restore-engine/"
    + P46_COMMIT
    + "/src/st_score_restore/stage11_v2d_c_clef_p4_6_offline_filter.py"
)

VARIANTS = {
    "scale_1_00": 1.00,
    "scale_0_75": 0.75,
    "scale_0_50": 0.50,
}

CANONICAL_STAFF_SPACING_PX = 15.0
MIN_CANONICAL_FACTOR = 0.60
MAX_CANONICAL_FACTOR = 3.00
PRIMARY_IOU = 0.50


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def load_frozen_module(name: str, url: str, expected_sha: str):
    data = urllib.request.urlopen(url, timeout=60).read()
    actual = sha256_bytes(data)
    if actual != expected_sha:
        raise RuntimeError(f"Frozen module SHA mismatch for {name}: {actual}")
    fd, temp_name = tempfile.mkstemp(prefix=name + "_", suffix=".py")
    os.close(fd)
    temp_path = Path(temp_name)
    temp_path.write_bytes(data)
    spec = importlib.util.spec_from_file_location(name, temp_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load frozen module: " + name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, temp_path


def box_iou(a: Sequence[float], b: Sequence[float]) -> float:
    ax1, ay1, ax2, ay2 = map(float, a)
    bx1, by1, bx2, by2 = map(float, b)
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(0.0, (bx2 - bx1) * (by2 - by1))
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def teacher_xyxy(box: Dict[str, Any], total_scale: float) -> List[float]:
    x = float(box["x"]) * total_scale
    y = float(box["y"]) * total_scale
    w = float(box["width"]) * total_scale
    h = float(box["height"]) * total_scale
    return [x, y, x + w, y + h]


def greedy_match(
    candidates: Sequence[Dict[str, Any]],
    teacher_boxes: Sequence[Dict[str, Any]],
    total_scale: float,
) -> List[Tuple[int, int, float]]:
    edges: List[Tuple[float, int, int]] = []
    for ci, candidate in enumerate(candidates):
        for ti, teacher_box in enumerate(teacher_boxes):
            score = box_iou(candidate["bbox"], teacher_xyxy(teacher_box, total_scale))
            if score >= PRIMARY_IOU:
                edges.append((score, ci, ti))
    edges.sort(reverse=True)
    used_c, used_t = set(), set()
    matches: List[Tuple[int, int, float]] = []
    for score, ci, ti in edges:
        if ci in used_c or ti in used_t:
            continue
        used_c.add(ci)
        used_t.add(ti)
        matches.append((ci, ti, float(score)))
    return matches


def metric(tp: int, fp: int, fn: int) -> Dict[str, float | int]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def evaluate_variant(variant_pages: Dict[str, Any], teacher: Dict[str, Any], filter_fn):
    raw_tp = raw_fp = raw_fn = 0
    filt_tp = filt_fp = filt_fn = 0
    raw_subtype = Counter()
    filt_subtype = Counter()
    subtype_total = Counter()
    pre_zero_staff = 0
    canonical_zero_staff = 0
    zero_candidate = 0

    for page_id, page in variant_pages.items():
        teacher_boxes = teacher["pages"][page_id]["boxes"]
        for box in teacher_boxes:
            subtype_total[box["label"]] += 1

        if page["preCanonicalStaffCount"] == 0:
            pre_zero_staff += 1
        if page["diagnostics"]["detectedStaffCount"] == 0:
            canonical_zero_staff += 1

        candidates = page["candidates"]
        if not candidates:
            zero_candidate += 1

        total_scale = float(page["inputScale"]) * float(page["canonicalFactor"])

        raw_matches = greedy_match(candidates, teacher_boxes, total_scale)
        raw_tp += len(raw_matches)
        raw_fp += len(candidates) - len(raw_matches)
        raw_fn += len(teacher_boxes) - len(raw_matches)
        for _, ti, _ in raw_matches:
            raw_subtype[teacher_boxes[ti]["label"]] += 1

        accepted = [candidate for candidate in candidates if filter_fn(candidate)[0]]
        filt_matches = greedy_match(accepted, teacher_boxes, total_scale)
        filt_tp += len(filt_matches)
        filt_fp += len(accepted) - len(filt_matches)
        filt_fn += len(teacher_boxes) - len(filt_matches)
        for _, ti, _ in filt_matches:
            filt_subtype[teacher_boxes[ti]["label"]] += 1

    labels = ("C1", "C3", "C4")
    return {
        "preCanonicalZeroStaffPages": pre_zero_staff,
        "canonicalZeroStaffPages": canonical_zero_staff,
        "zeroCandidatePages": zero_candidate,
        "raw": {
            "pooled": metric(raw_tp, raw_fp, raw_fn),
            "subtypeRecall": {
                label: raw_subtype[label] / subtype_total[label] if subtype_total[label] else 0.0
                for label in labels
            },
        },
        "frozenP4_6Filtered": {
            "pooled": metric(filt_tp, filt_fp, filt_fn),
            "subtypeRecall": {
                label: filt_subtype[label] / subtype_total[label] if subtype_total[label] else 0.0
                for label in labels
            },
        },
    }


def main() -> None:
    if not MANIFEST_PATH.is_file() or not TEACHER_PATH.is_file():
        raise RuntimeError("Frozen development artifacts are missing")
    if sha256_file(MANIFEST_PATH) != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("Development manifest SHA mismatch")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("pageCount") != EXPECTED_PAGE_COUNT:
        raise RuntimeError("Expected frozen 29-page development manifest")

    p45, p45_tmp = load_frozen_module("p45_frozen", P45_URL, P45_EXPECTED_SOURCE_SHA256)
    p46, p46_tmp = load_frozen_module("p46_frozen", P46_URL, P46_EXPECTED_SOURCE_SHA256)

    print("=" * 76)
    print("P4.8 CANONICAL STAFF-SPACING DEVELOPMENT DIAGNOSTIC")
    print("P4.7 holdout: NOT READ")
    print("P4.5 localizer: FROZEN")
    print("P4.6 filter: FROZEN / UNCHANGED")
    print("Canonical target staff spacing:", CANONICAL_STAFF_SPACING_PX, "px")
    print("Teacher truth: NOT READ during Phase A")
    print("=" * 76)

    raw_variants: Dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="p48_canonical_") as temp_dir:
        temp_root = Path(temp_dir)

        for variant_name, input_scale in VARIANTS.items():
            pages_out: Dict[str, Any] = {}

            for page_index, page in enumerate(manifest["pages"], start=1):
                page_id = page["pageId"]
                source_path = ROOT / page["imagePath"]
                if not source_path.is_file():
                    raise RuntimeError("Missing development source image: " + page_id)
                if sha256_file(source_path) != page["imageSha256"]:
                    raise RuntimeError("Development source image SHA mismatch: " + page_id)

                gray = cv2.imread(str(source_path), cv2.IMREAD_GRAYSCALE)
                if gray is None:
                    raise RuntimeError("Unreadable development image: " + page_id)

                if input_scale != 1.0:
                    gray = cv2.resize(
                        gray,
                        None,
                        fx=input_scale,
                        fy=input_scale,
                        interpolation=cv2.INTER_AREA,
                    )

                pre_staffs = p45.detect_staffs(gray)
                if not pre_staffs:
                    pages_out[page_id] = {
                        "pageId": page_id,
                        "inputScale": input_scale,
                        "preCanonicalStaffCount": 0,
                        "preCanonicalMedianStaffSpacing": None,
                        "canonicalFactor": 1.0,
                        "diagnostics": {
                            "detectedStaffCount": 0,
                            "candidateCount": 0,
                            "imageWidth": int(gray.shape[1]),
                            "imageHeight": int(gray.shape[0]),
                        },
                        "candidates": [],
                    }
                    print(f"{variant_name} {page_index:02d}/{EXPECTED_PAGE_COUNT} {page_id} preStaffs=0")
                    continue

                median_spacing = float(statistics.median(float(staff["spacing"]) for staff in pre_staffs))
                canonical_factor = CANONICAL_STAFF_SPACING_PX / median_spacing
                canonical_factor = min(MAX_CANONICAL_FACTOR, max(MIN_CANONICAL_FACTOR, canonical_factor))

                interpolation = cv2.INTER_CUBIC if canonical_factor >= 1.0 else cv2.INTER_AREA
                canonical = cv2.resize(
                    gray,
                    None,
                    fx=canonical_factor,
                    fy=canonical_factor,
                    interpolation=interpolation,
                )

                work_path = temp_root / f"{variant_name}-{page_id}.png"
                if not cv2.imwrite(str(work_path), canonical):
                    raise RuntimeError("Could not write canonical image: " + page_id)

                candidates, diagnostics = p45.generate_page_candidates(work_path)
                pages_out[page_id] = {
                    "pageId": page_id,
                    "inputScale": input_scale,
                    "preCanonicalStaffCount": len(pre_staffs),
                    "preCanonicalMedianStaffSpacing": median_spacing,
                    "canonicalFactor": float(canonical_factor),
                    "canonicalTargetStaffSpacing": CANONICAL_STAFF_SPACING_PX,
                    "diagnostics": diagnostics,
                    "candidates": candidates,
                }

                print(
                    f"{variant_name} {page_index:02d}/{EXPECTED_PAGE_COUNT} {page_id} "
                    f"preStaffs={len(pre_staffs)} spacing={median_spacing:.2f} "
                    f"factor={canonical_factor:.3f} staffs={diagnostics['detectedStaffCount']} "
                    f"candidates={diagnostics['candidateCount']}"
                )

            raw_variants[variant_name] = {
                "inputScale": input_scale,
                "pages": pages_out,
            }

    raw_payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_8-canonical-scale-candidates.v1",
        "status": "PHASE_A_COMPLETE_BEFORE_TEACHER_ACCESS",
        "developmentOnly": True,
        "p4_7HoldoutAccessed": False,
        "teacherTruthReadDuringCandidateGeneration": False,
        "manifestSha256": EXPECTED_MANIFEST_SHA256,
        "p4_5FrozenCommit": P45_COMMIT,
        "p4_6FrozenCommit": P46_COMMIT,
        "p4_6ThresholdsChanged": False,
        "canonicalStaffSpacingPx": CANONICAL_STAFF_SPACING_PX,
        "canonicalFactorClamp": [MIN_CANONICAL_FACTOR, MAX_CANONICAL_FACTOR],
        "variants": raw_variants,
    }
    atomic_json(RAW_PATH, raw_payload)
    raw_sha = sha256_file(RAW_PATH)
    print("PASS — canonical candidates frozen before teacher access")
    print("RAW SHA-256:", raw_sha)

    if sha256_file(TEACHER_PATH) != EXPECTED_TEACHER_SHA256:
        raise RuntimeError("Development teacher SHA mismatch")
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("boxCount") != EXPECTED_TEACHER_BOX_COUNT:
        raise RuntimeError("Development teacher artifact changed")

    diagnostics = {
        variant_name: evaluate_variant(variant["pages"], teacher, p46.filter_candidate)
        for variant_name, variant in raw_variants.items()
    }

    result = {
        "schemaVersion": "stage11.v2d.c-clef-p4_8-canonical-scale-diagnostic.v1",
        "status": "COMPLETE",
        "developmentOnly": True,
        "p4_7HoldoutAccessed": False,
        "teacherTruthReadDuringCandidateGeneration": False,
        "p4_6ThresholdsChanged": False,
        "canonicalStaffSpacingPx": CANONICAL_STAFF_SPACING_PX,
        "rawCandidateArtifactSha256": raw_sha,
        "diagnostics": diagnostics,
        "interpretationBoundary": {
            "detectorQualified": False,
            "productionInferenceAuthorized": False,
            "overallStage11PassAuthorized": False,
            "stage12EntryAuthorized": False,
            "newIndependentHoldoutRequiredAfterAnyP4_8Freeze": True,
        },
    }
    atomic_json(RESULT_PATH, result)

    print()
    print("=" * 76)
    print("P4.8 CANONICAL STAFF-SPACING DIAGNOSTIC COMPLETE")
    print("=" * 76)
    for variant_name, data in diagnostics.items():
        print(variant_name)
        print("  preCanonicalZeroStaffPages:", data["preCanonicalZeroStaffPages"])
        print("  canonicalZeroStaffPages:", data["canonicalZeroStaffPages"])
        print("  RAW:", data["raw"]["pooled"], data["raw"]["subtypeRecall"])
        print("  P4.6:", data["frozenP4_6Filtered"]["pooled"], data["frozenP4_6Filtered"]["subtypeRecall"])
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", sha256_file(RESULT_PATH))
    print("detectorQualified: False — development diagnostic only")

    try:
        p45_tmp.unlink(missing_ok=True)
        p46_tmp.unlink(missing_ok=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
