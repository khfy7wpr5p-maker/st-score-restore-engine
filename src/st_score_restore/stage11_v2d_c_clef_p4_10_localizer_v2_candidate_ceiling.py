"""P4.10 development-only C-clef localizer-v2 candidate-ceiling diagnostic.

Purpose:
- P4.9 has already failed qualification and is now spent evidence.
- Reuse it only as development/failure-diagnostic data.
- Generate a deliberately broad candidate pool before teacher access.
- Measure whether staff fallback + fragmented-glyph rescue can recover a high
  recall ceiling before any precision gate is designed.

This runner cannot qualify a detector and cannot authorize Stage 11/production.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import statistics
import tempfile
import types
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import cv2
import numpy as np

ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/P4_C_CLEF_HOLDOUT_P4_9")
PREPARED = ROOT / "_PREPARED"
MANIFEST_PATH = PREPARED / "c_clef_p4_9_holdout_source_page_manifest.v1.json"
TEACHER_PATH = ROOT / "_ANNOTATIONS" / "c_clef_p4_9_holdout_teacher_boxes.v1.json"
OUT = ROOT / "_P4_10_LOCALIZER_V2_DEV_DIAGNOSTIC"
RAW_PATH = OUT / "p4_10_localizer_v2_candidates_before_teacher.v1.json"
RESULT_PATH = OUT / "p4_10_localizer_v2_candidate_ceiling_result.v1.json"

EXPECTED_MANIFEST_SHA256 = "8db0cf576137ec8cfd8458dd5b9cead73f49b4b2910bf6436e31e1e3737a7ece"
EXPECTED_TEACHER_SHA256 = "8ce56115b519df0429ec37964de9e694c44a0fdf081b74c9bff0484bf248f095"
EXPECTED_PAGE_COUNT = 11
EXPECTED_TEACHER_BOX_COUNT = 38
EXPECTED_LABEL_COUNTS = {"C1": 12, "C3": 21, "C4": 5, "AMBIGUOUS": 0}

P45_COMMIT = "7130bdf94bcf9247a0b33e9342db22746b46f289"
P45_EXPECTED_SOURCE_SHA256 = "0bd631e0863f084204cb3927aa19c1da715e30c81371250a50b4ad97f107c426"
P45_URL = (
    "https://raw.githubusercontent.com/khfy7wpr5p-maker/st-score-restore-engine/"
    + P45_COMMIT
    + "/src/st_score_restore/stage11_v2d_c_clef_p4_5_source_image_localizer.py"
)

CANONICAL_STAFF_SPACING_PX = 15.0
MIN_CANONICAL_FACTOR = 0.60
MAX_CANONICAL_FACTOR = 3.00
PRIMARY_IOU = 0.50
CANDIDATE_DEDUP_IOU = 0.90

WINDOW_LEFT_SPACES = 0.60
WINDOW_RIGHT_SPACES = 7.00
WINDOW_TOP_SPACES = 3.00
WINDOW_BOTTOM_SPACES = 3.00
MIN_COMP_W_SPACES = 0.20
MAX_COMP_W_SPACES = 5.75
MIN_COMP_H_SPACES = 1.00
MAX_COMP_H_SPACES = 8.00
MIN_COMP_AREA_SPACES2 = 0.05
MAX_COMPONENTS_FOR_MERGE = 14
MERGE_GAP_SPACES = 1.10
MERGE_MAX_WIDTH_SPACES = 6.25
MAX_CANDIDATES_PER_STAFF = 80


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def load_frozen_p45():
    data = urllib.request.urlopen(P45_URL, timeout=60).read()
    actual = sha256_bytes(data)
    if actual != P45_EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"Frozen P4.5 module SHA mismatch: {actual}")
    module = types.ModuleType("p45_frozen_p410")
    module.__file__ = "stage11_v2d_c_clef_p4_5_source_image_localizer.py"
    exec(compile(data.decode("utf-8"), module.__file__, "exec"), module.__dict__)
    return module


def grouped_runs(indices: np.ndarray) -> List[Tuple[int, int]]:
    if indices.size == 0:
        return []
    out: List[Tuple[int, int]] = []
    start = prev = int(indices[0])
    for raw in indices[1:]:
        value = int(raw)
        if value > prev + 1:
            out.append((start, prev))
            start = value
        prev = value
    out.append((start, prev))
    return out


def staff_center(staff: Dict[str, Any]) -> float:
    return float(np.mean(np.asarray(staff["lines"], dtype=float)))


def normalize_staff(lines: Sequence[float], source: str) -> Dict[str, Any] | None:
    arr = np.asarray(lines, dtype=float)
    if arr.size != 5:
        return None
    gaps = np.diff(arr)
    spacing = float(np.median(gaps))
    if not (4.0 <= spacing <= 60.0):
        return None
    tolerance = max(3.0, 0.38 * spacing)
    if float(np.max(np.abs(gaps - spacing))) > tolerance:
        return None
    return {
        "lines": [float(v) for v in arr],
        "spacing": spacing,
        "gapCv": float(np.std(gaps) / spacing) if spacing else 1.0,
        "source": source,
    }


def dedup_staffs(staffs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    priority = {"p45": 0, "projection": 1, "hough": 2}
    ordered = sorted(
        staffs,
        key=lambda s: (staff_center(s), priority.get(str(s.get("source")), 9), float(s.get("gapCv", 1.0))),
    )
    for candidate in ordered:
        center = staff_center(candidate)
        spacing = float(candidate["spacing"])
        match = None
        for i, existing in enumerate(selected):
            ec = staff_center(existing)
            es = float(existing["spacing"])
            if (
                abs(center - ec) <= 0.70 * max(spacing, es)
                and abs(spacing - es) <= 0.40 * max(spacing, es)
            ):
                match = i
                break
        if match is None:
            selected.append(candidate)
        else:
            old = selected[match]
            old_key = (priority.get(str(old.get("source")), 9), float(old.get("gapCv", 1.0)))
            new_key = (priority.get(str(candidate.get("source")), 9), float(candidate.get("gapCv", 1.0)))
            if new_key < old_key:
                selected[match] = candidate
    return sorted(selected, key=staff_center)


def projection_fallback_staffs(gray: np.ndarray) -> List[Dict[str, Any]]:
    height, width = gray.shape[:2]
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    bands = ((0.04, 0.96), (0.10, 0.90), (0.18, 0.82))
    coverages = (0.16, 0.22, 0.28, 0.34)
    found: List[Dict[str, Any]] = []
    for left, right in bands:
        x0 = max(0, int(round(left * width)))
        x1 = min(width, int(round(right * width)))
        if x1 <= x0:
            continue
        projection = np.count_nonzero(ink[:, x0:x1] > 0, axis=1)
        span = x1 - x0
        for coverage in coverages:
            required = max(1, int(round(coverage * span)))
            runs = grouped_runs(np.flatnonzero(projection >= required))
            centers = np.asarray([(a + b) / 2.0 for a, b in runs], dtype=float)
            for i in range(max(0, len(centers) - 4)):
                candidate = normalize_staff(centers[i:i+5], "projection")
                if candidate is not None:
                    candidate["projectionBand"] = [left, right]
                    candidate["projectionCoverage"] = coverage
                    found.append(candidate)
    return found


def cluster_values(values: Sequence[float], tolerance: float = 2.5) -> List[float]:
    if not values:
        return []
    vals = sorted(float(v) for v in values)
    groups: List[List[float]] = [[vals[0]]]
    for value in vals[1:]:
        if value - statistics.mean(groups[-1]) <= tolerance:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [float(statistics.mean(group)) for group in groups]


def hough_fallback_staffs(gray: np.ndarray) -> List[Dict[str, Any]]:
    height, width = gray.shape[:2]
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    min_len = max(80, int(round(width * 0.18)))
    threshold = max(45, int(round(width * 0.035)))
    max_gap = max(10, int(round(width * 0.025)))
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180.0,
        threshold=threshold,
        minLineLength=min_len,
        maxLineGap=max_gap,
    )
    ys: List[float] = []
    if lines is not None:
        for raw in lines[:, 0, :]:
            x1, y1, x2, y2 = map(int, raw)
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            if dx < min_len:
                continue
            if dy > max(2.0, 0.015 * dx):
                continue
            ys.append((y1 + y2) / 2.0)
    centers = np.asarray(cluster_values(ys, tolerance=2.5), dtype=float)
    found: List[Dict[str, Any]] = []
    for i in range(max(0, len(centers) - 4)):
        candidate = normalize_staff(centers[i:i+5], "hough")
        if candidate is not None:
            found.append(candidate)
    return found


def detect_staffs_v2(gray: np.ndarray, p45) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    frozen = []
    for s in p45.detect_staffs(gray):
        item = dict(s)
        item["source"] = "p45"
        frozen.append(item)
    projection = projection_fallback_staffs(gray)
    hough = hough_fallback_staffs(gray)
    merged = dedup_staffs([*frozen, *projection, *hough])
    return merged, {
        "p45": len(frozen),
        "projectionRaw": len(projection),
        "houghRaw": len(hough),
        "merged": len(merged),
    }


def box_iou(a: Sequence[float], b: Sequence[float]) -> float:
    ax1, ay1, ax2, ay2 = map(float, a)
    bx1, by1, bx2, by2 = map(float, b)
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0.0:
        return 0.0
    area_a = max(0.0, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(0.0, (bx2 - bx1) * (by2 - by1))
    union = area_a + area_b - inter
    return inter / union if union > 0.0 else 0.0


def clip_box(box: Sequence[float], width: int, height: int) -> List[float] | None:
    x1, y1, x2, y2 = map(float, box)
    x1 = min(max(0.0, x1), float(width))
    x2 = min(max(0.0, x2), float(width))
    y1 = min(max(0.0, y1), float(height))
    y2 = min(max(0.0, y2), float(height))
    if x2 <= x1 or y2 <= y1:
        return None
    return [x1, y1, x2, y2]


def bbox_union(a: Sequence[float], b: Sequence[float]) -> List[float]:
    return [
        min(float(a[0]), float(b[0])),
        min(float(a[1]), float(b[1])),
        max(float(a[2]), float(b[2])),
        max(float(a[3]), float(b[3])),
    ]


def candidate_variants(
    box: Sequence[float],
    spacing: float,
    width: int,
    height: int,
    source: str,
    staff_index: int,
) -> List[Dict[str, Any]]:
    x1, y1, x2, y2 = map(float, box)
    pads = (
        (0.0, 0.0, 0.0, 0.0, "raw"),
        (0.20, 0.20, 0.20, 0.20, "pad020"),
        (0.35, 0.25, 0.35, 0.35, "pad035"),
        (0.15, 0.10, 0.15, 0.50, "bottom050"),
    )
    out = []
    for lp, tp, rp, bp, tag in pads:
        clipped = clip_box(
            [x1 - lp*spacing, y1 - tp*spacing, x2 + rp*spacing, y2 + bp*spacing],
            width,
            height,
        )
        if clipped is not None:
            out.append({
                "bbox": clipped,
                "staffIndex": int(staff_index),
                "staffSpacing": float(spacing),
                "rescueSource": source,
                "geometryVariant": tag,
            })
    return out


def components_in_staff_window(
    gray: np.ndarray,
    symbols: np.ndarray,
    staff: Dict[str, Any],
    staff_index: int,
    p45,
) -> List[Dict[str, Any]]:
    height, width = gray.shape[:2]
    lines = np.asarray(staff["lines"], dtype=float)
    spacing = float(staff["spacing"])
    bar_end, _ = p45.find_barline_end(gray, lines)

    x0 = max(0, int(round(bar_end - WINDOW_LEFT_SPACES * spacing)))
    x1 = min(width, int(round(bar_end + WINDOW_RIGHT_SPACES * spacing)))
    y0 = max(0, int(round(lines[0] - WINDOW_TOP_SPACES * spacing)))
    y1 = min(height, int(round(lines[-1] + WINDOW_BOTTOM_SPACES * spacing)))
    if x1 <= x0 or y1 <= y0:
        return []

    roi = symbols[y0:y1, x0:x1]
    masks = []
    kernels = (
        (max(1, int(round(0.12 * spacing))), max(3, int(round(0.55 * spacing))), "close_v"),
        (max(2, int(round(0.35 * spacing))), max(2, int(round(0.30 * spacing))), "close_xy"),
    )
    masks.append(((roi > 0).astype(np.uint8) * 255, "raw"))
    for kw, kh, tag in kernels:
        closed = cv2.morphologyEx(
            roi,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_RECT, (kw, kh)),
        )
        masks.append((closed, tag))

    base_boxes: List[Tuple[List[float], str]] = []
    for mask, mask_tag in masks:
        count, _, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), connectivity=8)
        for cid in range(1, count):
            cx = int(stats[cid, cv2.CC_STAT_LEFT])
            cy = int(stats[cid, cv2.CC_STAT_TOP])
            cw = int(stats[cid, cv2.CC_STAT_WIDTH])
            ch = int(stats[cid, cv2.CC_STAT_HEIGHT])
            area = int(stats[cid, cv2.CC_STAT_AREA])
            ws = cw / spacing
            hs = ch / spacing
            area_s2 = area / (spacing * spacing)
            if not (MIN_COMP_W_SPACES <= ws <= MAX_COMP_W_SPACES):
                continue
            if not (MIN_COMP_H_SPACES <= hs <= MAX_COMP_H_SPACES):
                continue
            if area_s2 < MIN_COMP_AREA_SPACES2:
                continue
            box = [float(x0+cx), float(y0+cy), float(x0+cx+cw), float(y0+cy+ch)]
            base_boxes.append((box, mask_tag))

    unique: List[Tuple[List[float], str]] = []
    for box, tag in sorted(base_boxes, key=lambda item: (item[0][0], item[0][1], -(item[0][2]-item[0][0])*(item[0][3]-item[0][1]))):
        if any(box_iou(box, kept[0]) >= 0.88 for kept in unique):
            continue
        unique.append((box, tag))

    unique = unique[:MAX_COMPONENTS_FOR_MERGE]
    candidate_boxes: List[Tuple[List[float], str]] = list(unique)

    n = len(unique)
    for i in range(n):
        box_i = unique[i][0]
        merged = list(box_i)
        last_right = float(box_i[2])
        for j in range(i+1, min(n, i+3)):
            box_j = unique[j][0]
            gap = float(box_j[0]) - last_right
            new_box = bbox_union(merged, box_j)
            new_width_spaces = (new_box[2]-new_box[0]) / spacing
            if gap > MERGE_GAP_SPACES * spacing or new_width_spaces > MERGE_MAX_WIDTH_SPACES:
                break
            merged = new_box
            last_right = max(last_right, float(box_j[2]))
            candidate_boxes.append((list(merged), f"merge_{j-i+1}"))

    candidates: List[Dict[str, Any]] = []
    for box, source in candidate_boxes:
        candidates.extend(candidate_variants(box, spacing, width, height, source, staff_index))

    for box, source in candidate_boxes:
        x1b, _, x2b, _ = box
        anchored = [
            x1b - 0.15*spacing,
            float(lines[0] - 1.15*spacing),
            x2b + 0.20*spacing,
            float(lines[-1] + 1.15*spacing),
        ]
        clipped = clip_box(anchored, width, height)
        if clipped is not None:
            candidates.append({
                "bbox": clipped,
                "staffIndex": int(staff_index),
                "staffSpacing": float(spacing),
                "rescueSource": source,
                "geometryVariant": "staff_anchored",
            })

    deduped: List[Dict[str, Any]] = []
    for c in sorted(candidates, key=lambda item: (item["bbox"][0], -(item["bbox"][2]-item["bbox"][0])*(item["bbox"][3]-item["bbox"][1]))):
        if any(box_iou(c["bbox"], old["bbox"]) >= CANDIDATE_DEDUP_IOU for old in deduped):
            continue
        deduped.append(c)
        if len(deduped) >= MAX_CANDIDATES_PER_STAFF:
            break
    return deduped


def generate_candidates_v2(gray: np.ndarray, p45) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    symbols, _ = p45.prepare_symbol_mask(gray)
    staffs, staff_diag = detect_staffs_v2(gray, p45)
    page_candidates: List[Dict[str, Any]] = []

    with tempfile.NamedTemporaryFile(prefix="p410_", suffix=".png", delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        if not cv2.imwrite(str(temp_path), gray):
            raise RuntimeError("Could not write temporary page for frozen P4.5")
        frozen_candidates, frozen_diag = p45.generate_page_candidates(temp_path)
    finally:
        try:
            temp_path.unlink()
        except OSError:
            pass

    for c in frozen_candidates:
        item = dict(c)
        item["rescueSource"] = "frozen_p45"
        item["geometryVariant"] = "frozen"
        page_candidates.append(item)

    per_staff_counts = []
    for staff_index, staff in enumerate(staffs):
        current = components_in_staff_window(gray, symbols, staff, staff_index, p45)
        per_staff_counts.append(len(current))
        page_candidates.extend(current)

    deduped: List[Dict[str, Any]] = []
    for c in sorted(page_candidates, key=lambda item: (item["bbox"][1], item["bbox"][0])):
        if any(box_iou(c["bbox"], old["bbox"]) >= 0.95 for old in deduped):
            continue
        deduped.append(c)

    return deduped, {
        "staffSources": staff_diag,
        "mergedStaffCount": len(staffs),
        "frozenP45CandidateCount": len(frozen_candidates),
        "candidateCount": len(deduped),
        "perStaffCandidateCounts": per_staff_counts,
        "staffs": staffs,
        "imageWidth": int(gray.shape[1]),
        "imageHeight": int(gray.shape[0]),
    }


def map_candidates_to_input(candidates: Sequence[Dict[str, Any]], factor: float) -> List[Dict[str, Any]]:
    out = []
    for c in candidates:
        item = dict(c)
        item["bbox"] = [float(v)/factor for v in c["bbox"]]
        item["staffSpacing"] = float(c.get("staffSpacing", 1.0))/factor
        item["candidateScaleSource"] = "canonical"
        out.append(item)
    return out


def map_staffs_to_input(staffs: Sequence[Dict[str, Any]], factor: float) -> List[Dict[str, Any]]:
    out = []
    for s in staffs:
        item = dict(s)
        item["lines"] = [float(v)/factor for v in s["lines"]]
        item["spacing"] = float(s["spacing"])/factor
        out.append(item)
    return out


def teacher_xyxy(box: Dict[str, Any]) -> List[float]:
    x = float(box["x"])
    y = float(box["y"])
    w = float(box.get("w", box.get("width")))
    h = float(box.get("h", box.get("height")))
    return [x, y, x+w, y+h]


def greedy_match(candidates: Sequence[Dict[str, Any]], teacher_boxes: Sequence[Dict[str, Any]]):
    edges: List[Tuple[float, int, int]] = []
    for ci, c in enumerate(candidates):
        for ti, t in enumerate(teacher_boxes):
            score = box_iou(c["bbox"], teacher_xyxy(t))
            if score >= PRIMARY_IOU:
                edges.append((score, ci, ti))
    edges.sort(reverse=True)
    used_c, used_t = set(), set()
    matches = []
    for score, ci, ti in edges:
        if ci in used_c or ti in used_t:
            continue
        used_c.add(ci)
        used_t.add(ti)
        matches.append((ci, ti, float(score)))
    return matches


def staff_covers_teacher(staff: Dict[str, Any], teacher_box: Dict[str, Any]) -> bool:
    lines = np.asarray(staff["lines"], dtype=float)
    spacing = float(staff["spacing"])
    t = teacher_xyxy(teacher_box)
    cy = 0.5*(t[1]+t[3])
    return float(lines[0] - 2.5*spacing) <= cy <= float(lines[-1] + 2.5*spacing)


def metric(tp: int, fp: int, fn: int) -> Dict[str, Any]:
    precision = tp/(tp+fp) if tp+fp else 0.0
    recall = tp/(tp+fn) if tp+fn else 0.0
    f1 = 2*precision*recall/(precision+recall) if precision+recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def main() -> None:
    if not MANIFEST_PATH.is_file() or not TEACHER_PATH.is_file():
        raise RuntimeError("P4.9 prepared development artifacts missing")
    if sha256_file(MANIFEST_PATH) != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("P4.9 manifest SHA mismatch")
    if sha256_file(TEACHER_PATH) != EXPECTED_TEACHER_SHA256:
        raise RuntimeError("P4.9 teacher SHA mismatch")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("pageCount") != EXPECTED_PAGE_COUNT:
        raise RuntimeError("Expected 11-page P4.9 artifact")

    p45 = load_frozen_p45()

    print("=" * 76)
    print("P4.10 LOCALIZER-V2 CANDIDATE CEILING — DEVELOPMENT DIAGNOSTIC")
    print("P4.9 status: SPENT HOLDOUT / DEVELOPMENT DIAGNOSTIC ONLY")
    print("Teacher truth: NOT READ during Phase A")
    print("Precision gate: NOT DESIGNED")
    print("=" * 76)

    raw_pages: Dict[str, Any] = {}
    for page_index, page in enumerate(manifest["pages"], start=1):
        page_id = page["pageId"]
        image_path = PREPARED / page["imagePath"]
        if not image_path.is_file():
            raise RuntimeError("Prepared image missing: " + page_id)
        if sha256_file(image_path) != page["imageSha256"]:
            raise RuntimeError("Prepared image SHA mismatch: " + page_id)

        gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            raise RuntimeError("Unreadable page: " + page_id)

        orig_candidates, orig_diag = generate_candidates_v2(gray, p45)
        orig_staffs = orig_diag["staffs"]
        spacings = [float(s["spacing"]) for s in orig_staffs]
        if spacings:
            pre_spacing = float(statistics.median(spacings))
            factor = CANONICAL_STAFF_SPACING_PX / pre_spacing
            factor = min(MAX_CANONICAL_FACTOR, max(MIN_CANONICAL_FACTOR, factor))
            interpolation = cv2.INTER_CUBIC if factor >= 1.0 else cv2.INTER_AREA
            canonical_gray = cv2.resize(gray, None, fx=factor, fy=factor, interpolation=interpolation)
            canon_candidates, canon_diag = generate_candidates_v2(canonical_gray, p45)
            canon_mapped = map_candidates_to_input(canon_candidates, factor)
            canon_staffs = map_staffs_to_input(canon_diag["staffs"], factor)
        else:
            pre_spacing = None
            factor = 1.0
            canon_mapped = []
            canon_diag = {"candidateCount": 0, "mergedStaffCount": 0, "staffs": []}
            canon_staffs = []

        combined = []
        for c in orig_candidates:
            item = dict(c)
            item["candidateScaleSource"] = "original"
            combined.append(item)
        combined.extend(canon_mapped)

        deduped = []
        for c in sorted(combined, key=lambda item: (item["bbox"][1], item["bbox"][0])):
            if any(box_iou(c["bbox"], old["bbox"]) >= 0.95 for old in deduped):
                continue
            deduped.append(c)

        staff_union = dedup_staffs([*orig_staffs, *canon_staffs])
        raw_pages[page_id] = {
            "pageId": page_id,
            "sourcePdfName": page["sourcePdfName"],
            "sourcePageNumber": page["sourcePageNumber"],
            "sourceImageSha256": page["imageSha256"],
            "preCanonicalMedianStaffSpacing": pre_spacing,
            "canonicalFactor": factor,
            "originalDiagnostics": {k:v for k,v in orig_diag.items() if k != "staffs"},
            "canonicalDiagnostics": {k:v for k,v in canon_diag.items() if k != "staffs"},
            "staffs": staff_union,
            "candidates": deduped,
        }
        print(
            f"P4.10 GENERATED {page_index:02d}/{EXPECTED_PAGE_COUNT} {page_id} "
            f"staffs={len(staff_union)} candidates={len(deduped)} factor={factor:.3f}"
        )

    raw_payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_10-localizer-v2-candidates.v1",
        "status": "PHASE_A_FROZEN_BEFORE_TEACHER_ACCESS",
        "developmentOnly": True,
        "p4_9SpentHoldoutReclassifiedForDevelopmentDiagnostic": True,
        "teacherTruthReadDuringCandidateGeneration": False,
        "p4_5FrozenCommit": P45_COMMIT,
        "sourceManifestSha256": EXPECTED_MANIFEST_SHA256,
        "pageCount": EXPECTED_PAGE_COUNT,
        "pages": raw_pages,
    }
    atomic_json(RAW_PATH, raw_payload)
    raw_sha = sha256_file(RAW_PATH)
    print("PASS — candidate ceiling artifact frozen before teacher access")
    print("RAW SHA-256:", raw_sha)

    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("boxCount") != EXPECTED_TEACHER_BOX_COUNT:
        raise RuntimeError("Teacher artifact is not frozen P4.9 11-page / 38-box truth")
    if teacher.get("labelCounts") != EXPECTED_LABEL_COUNTS:
        raise RuntimeError("Teacher label counts changed")

    total_tp = total_fp = total_fn = 0
    subtype_total = Counter()
    subtype_tp = Counter()
    staff_total = staff_recovered = 0
    per_page = {}

    for page_id, page in raw_pages.items():
        candidates = page["candidates"]
        teacher_boxes = teacher["pages"][page_id]["boxes"]
        matches = greedy_match(candidates, teacher_boxes)
        matched_teacher = {ti for _, ti, _ in matches}
        tp = len(matches)
        fp = len(candidates) - tp
        fn = len(teacher_boxes) - tp
        total_tp += tp
        total_fp += fp
        total_fn += fn

        for ti, box in enumerate(teacher_boxes):
            label = box["label"]
            subtype_total[label] += 1
            if ti in matched_teacher:
                subtype_tp[label] += 1
            staff_total += 1
            if any(staff_covers_teacher(s, box) for s in page["staffs"]):
                staff_recovered += 1

        per_page[page_id] = {
            "candidateCount": len(candidates),
            "teacherBoxCount": len(teacher_boxes),
            "matchedTeacherCount": tp,
            "candidateRecall": tp/len(teacher_boxes) if teacher_boxes else 0.0,
            "matches": [
                {
                    "candidateIndex": ci,
                    "teacherIndex": ti,
                    "teacherLabel": teacher_boxes[ti]["label"],
                    "iou": score,
                }
                for ci, ti, score in matches
            ],
        }

    pooled = metric(total_tp, total_fp, total_fn)
    subtype = {}
    for label in ("C1", "C3", "C4"):
        total = int(subtype_total[label])
        tp = int(subtype_tp[label])
        subtype[label] = {
            "teacherBoxes": total,
            "tp": tp,
            "fn": total-tp,
            "candidateRecall": tp/total if total else 0.0,
        }

    target_met = (
        pooled["recall"] >= 0.90
        and all(subtype[label]["candidateRecall"] >= 0.80 for label in ("C1","C3","C4"))
    )

    result = {
        "schemaVersion": "stage11.v2d.c-clef-p4_10-localizer-v2-candidate-ceiling-result.v1",
        "status": "COMPLETE",
        "developmentOnly": True,
        "p4_9CannotQualifyThisDetector": True,
        "teacherTruthReadDuringCandidateGeneration": False,
        "candidateArtifactSha256": raw_sha,
        "pageCount": EXPECTED_PAGE_COUNT,
        "teacherBoxCount": EXPECTED_TEACHER_BOX_COUNT,
        "pooledCandidateCeiling": pooled,
        "perSubtype": subtype,
        "staffCoverage": {
            "teacherBoxes": staff_total,
            "coveredByAnyDetectedStaff": staff_recovered,
            "fraction": staff_recovered/staff_total if staff_total else 0.0,
        },
        "candidateCountTotal": sum(len(p["candidates"]) for p in raw_pages.values()),
        "perPage": per_page,
        "developmentCandidateCeilingTarget": {
            "pooledRecallAtLeast": 0.90,
            "eachSubtypeRecallAtLeast": 0.80,
            "met": bool(target_met),
        },
        "decisionBoundary": {
            "precisionGateDesigned": False,
            "detectorQualified": False,
            "overallStage11PassAuthorized": False,
            "productionInferenceAuthorized": False,
            "brandNewIndependentHoldoutRequiredAfterFutureFreeze": True,
        },
    }
    atomic_json(RESULT_PATH, result)

    print()
    print("=" * 76)
    print("P4.10 LOCALIZER-V2 CANDIDATE CEILING COMPLETE")
    print("=" * 76)
    print("POOLED CANDIDATE CEILING:", pooled)
    print("SUBTYPE CANDIDATE RECALL:", {k:v["candidateRecall"] for k,v in subtype.items()})
    print("STAFF COVERAGE:", result["staffCoverage"])
    print("CANDIDATE COUNT TOTAL:", result["candidateCountTotal"])
    print("TARGET MET:", target_met)
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", sha256_file(RESULT_PATH))
    print("detectorQualified: False — development candidate ceiling only")


if __name__ == "__main__":
    main()
