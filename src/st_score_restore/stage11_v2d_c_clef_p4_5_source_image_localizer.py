"""P4.5 source-image-first C-clef localizer development measurement.

No EOMER / ONNX / Restore inference is used. Candidate generation reads only
source PNGs + the source manifest. Teacher truth is opened only after all page
candidates have been generated, and is then used strictly for evaluation.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import cv2
import numpy as np

PLAN_VERSION = "stage11.v2d.c-clef-p4_5-source-image-localizer-plan.v1"
SCHEMA_VERSION = "stage11.v2d.c-clef-p4_5-source-image-localizer-result.v1"

EXPECTED_MANIFEST_SHA256 = "365d45462b9d7b422a640e47bacdd5c8a5f16860198dec37121946411f6b3294"
EXPECTED_TEACHER_SHA256 = "1104d916faaf8d3c391cca9eda0354d21259f722cdcfe0f414c140796a5ffc5b"
EXPECTED_PAGE_COUNT = 29
EXPECTED_BOX_COUNT = 71
EXPECTED_LABEL_COUNTS = {"C1": 20, "C3": 36, "C4": 15, "AMBIGUOUS": 0}

ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/C_CLEF_SOURCE_PAGES")
MANIFEST_PATH = ROOT / "_PREPARED" / "c_clef_source_page_manifest.v1.json"
TEACHER_PATH = ROOT / "_ANNOTATIONS" / "c_clef_teacher_boxes.v1.json"
OUT_ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/P4_C_CLEF_SOURCE_LOCALIZER_P4_5")
RAW_CANDIDATES_PATH = OUT_ROOT / "p4_5_source_image_candidates.v1.json"
RESULT_PATH = OUT_ROOT / "p4_5_source_image_localizer_result.v1.json"

DARK_THRESHOLD = 180
CENTRAL_LEFT = 0.18
CENTRAL_RIGHT = 0.82
ROW_COVERAGES = (0.35, 0.40, 0.45, 0.50, 0.55)
STAFF_SPACING_MIN = 5.0
STAFF_SPACING_MAX = 50.0
STAFF_GAP_DEV_RATIO = 0.25
STAFF_GAP_DEV_MIN_PX = 3.0
STAFF_DEDUP_CENTER_SPACES = 0.60
STAFF_DEDUP_SPACING_RATIO = 0.35
HLINE_KERNEL_WIDTH_RATIO = 0.04
HLINE_KERNEL_MIN_PX = 25
HLINE_VERTICAL_DILATE_PX = 3
BAR_PROBE_TOP_SPACES = 2.0
BAR_PROBE_BOTTOM_SPACES = 2.0
BAR_PROBE_LEFT_RATIO = 0.30
BAR_STRONG_OCCUPANCY = 0.75
BAR_MAX_LEFT_RATIO = 0.20
GLYPH_X_OFFSET_SPACES = 0.20
GLYPH_WINDOW_WIDTH_SPACES = 4.50
GLYPH_TOP_MARGIN_SPACES = 2.0
GLYPH_BOTTOM_MARGIN_SPACES = 2.5
RECONNECT_W_SPACES = 0.15
RECONNECT_H_SPACES = 0.60
COMP_MIN_W_SPACES = 1.0
COMP_MAX_W_SPACES = 4.8
COMP_MIN_H_SPACES = 2.5
COMP_MAX_H_SPACES = 7.0
COMP_MIN_AREA_SPACES2 = 0.6
PRIMARY_IOU = 0.50
DIAGNOSTIC_IOU = 0.30


def fail(message: str) -> None:
    raise RuntimeError("P4.5 SOURCE LOCALIZER BLOCKED: " + message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, payload: Dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


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


def staff_candidates_for_coverage(gray: np.ndarray, coverage: float) -> List[Dict[str, Any]]:
    height, width = gray.shape[:2]
    x0 = int(round(CENTRAL_LEFT * width))
    x1 = int(round(CENTRAL_RIGHT * width))
    if x1 <= x0:
        return []
    projection = np.count_nonzero(gray[:, x0:x1] < DARK_THRESHOLD, axis=1)
    required = int(round(coverage * (x1 - x0)))
    runs = grouped_runs(np.flatnonzero(projection >= required))
    centers = np.asarray([(a + b) / 2.0 for a, b in runs], dtype=float)

    result: List[Dict[str, Any]] = []
    for index in range(max(0, len(centers) - 4)):
        lines = centers[index:index + 5]
        gaps = np.diff(lines)
        spacing = float(np.median(gaps))
        if not (STAFF_SPACING_MIN <= spacing <= STAFF_SPACING_MAX):
            continue
        tolerance = max(STAFF_GAP_DEV_MIN_PX, STAFF_GAP_DEV_RATIO * spacing)
        if float(np.max(np.abs(gaps - spacing))) > tolerance:
            continue
        result.append({
            "lines": [float(v) for v in lines],
            "spacing": spacing,
            "gapCv": float(np.std(gaps) / spacing) if spacing else 1.0,
            "rowCoverage": float(coverage),
        })
    return result


def detect_staffs(gray: np.ndarray) -> List[Dict[str, Any]]:
    pool: List[Dict[str, Any]] = []
    for coverage in ROW_COVERAGES:
        pool.extend(staff_candidates_for_coverage(gray, coverage))

    selected: List[Dict[str, Any]] = []
    for candidate in sorted(pool, key=lambda item: (float(np.mean(item["lines"])), item["gapCv"])):
        center = float(np.mean(candidate["lines"]))
        spacing = float(candidate["spacing"])
        match_index = None
        for index, existing in enumerate(selected):
            existing_center = float(np.mean(existing["lines"]))
            existing_spacing = float(existing["spacing"])
            if (
                abs(center - existing_center) <= STAFF_DEDUP_CENTER_SPACES * max(spacing, existing_spacing)
                and abs(spacing - existing_spacing) <= STAFF_DEDUP_SPACING_RATIO * max(spacing, existing_spacing)
            ):
                match_index = index
                break
        if match_index is None:
            selected.append(candidate)
        elif candidate["gapCv"] < selected[match_index]["gapCv"]:
            selected[match_index] = candidate

    return sorted(selected, key=lambda item: float(np.mean(item["lines"])))


def prepare_symbol_mask(gray: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    width = gray.shape[1]
    kernel_width = max(HLINE_KERNEL_MIN_PX, int(round(width * HLINE_KERNEL_WIDTH_RATIO)))
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 1))
    horizontal_lines = cv2.morphologyEx(ink, cv2.MORPH_OPEN, horizontal_kernel)
    removal_mask = cv2.dilate(
        horizontal_lines,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, HLINE_VERTICAL_DILATE_PX)),
    )
    symbols = ink.copy()
    symbols[removal_mask > 0] = 0
    return symbols, horizontal_lines


def find_barline_end(gray: np.ndarray, lines: Sequence[float]) -> Tuple[int, List[List[int]]]:
    height, width = gray.shape[:2]
    line_array = np.asarray(lines, dtype=float)
    spacing = float(np.median(np.diff(line_array)))
    y0 = max(0, int(round(line_array[0] - BAR_PROBE_TOP_SPACES * spacing)))
    y1 = min(height, int(round(line_array[-1] + BAR_PROBE_BOTTOM_SPACES * spacing)))
    x_limit = max(1, int(round(BAR_PROBE_LEFT_RATIO * width)))
    region = (gray[y0:y1, :x_limit] < DARK_THRESHOLD).astype(np.uint8)
    x_projection = np.sum(region, axis=0)
    strong_threshold = BAR_STRONG_OCCUPANCY * max(1, y1 - y0)
    runs = grouped_runs(np.flatnonzero(x_projection >= strong_threshold))
    plausible = [(a, b) for a, b in runs if a < BAR_MAX_LEFT_RATIO * width]
    if plausible:
        return max(b for _, b in plausible), [[int(a), int(b)] for a, b in plausible]

    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    local_kernel_width = max(8, int(round(2.0 * spacing)))
    local_lines = cv2.morphologyEx(
        ink,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (local_kernel_width, 1)),
    )
    starts: List[int] = []
    for line_y in line_array:
        yy = int(round(line_y))
        band = local_lines[max(0, yy - 1):min(height, yy + 2), :x_limit]
        xs = np.flatnonzero(np.any(band > 0, axis=0))
        if xs.size:
            starts.append(int(xs.min()))
    if starts:
        return int(round(float(np.median(starts)))), []
    return 0, []


def localize_candidate(gray: np.ndarray, staff: Dict[str, Any], symbols: np.ndarray) -> Dict[str, Any] | None:
    height, width = gray.shape[:2]
    lines = np.asarray(staff["lines"], dtype=float)
    spacing = float(np.median(np.diff(lines)))
    bar_end, strong_bar_groups = find_barline_end(gray, lines)

    x0 = max(0, int(round(bar_end + GLYPH_X_OFFSET_SPACES * spacing)))
    x1 = min(width, int(round(x0 + GLYPH_WINDOW_WIDTH_SPACES * spacing)))
    y0 = max(0, int(round(lines[0] - GLYPH_TOP_MARGIN_SPACES * spacing)))
    y1 = min(height, int(round(lines[-1] + GLYPH_BOTTOM_MARGIN_SPACES * spacing)))
    if x1 <= x0 or y1 <= y0:
        return None

    roi = symbols[y0:y1, x0:x1]
    reconnect_width = max(1, int(round(RECONNECT_W_SPACES * spacing)))
    reconnect_height = max(3, int(round(RECONNECT_H_SPACES * spacing)))
    reconnected = cv2.morphologyEx(
        roi,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (reconnect_width, reconnect_height)),
    )

    count, _, stats, _ = cv2.connectedComponentsWithStats((reconnected > 0).astype(np.uint8), connectivity=8)
    components: List[Dict[str, Any]] = []
    for component_id in range(1, count):
        cx = int(stats[component_id, cv2.CC_STAT_LEFT])
        cy = int(stats[component_id, cv2.CC_STAT_TOP])
        cw = int(stats[component_id, cv2.CC_STAT_WIDTH])
        ch = int(stats[component_id, cv2.CC_STAT_HEIGHT])
        area = int(stats[component_id, cv2.CC_STAT_AREA])
        width_spaces = cw / spacing
        height_spaces = ch / spacing
        area_spaces2 = area / (spacing * spacing)
        if not (COMP_MIN_W_SPACES <= width_spaces <= COMP_MAX_W_SPACES):
            continue
        if not (COMP_MIN_H_SPACES <= height_spaces <= COMP_MAX_H_SPACES):
            continue
        if area_spaces2 < COMP_MIN_AREA_SPACES2:
            continue
        components.append({
            "componentId": component_id,
            "bbox": [x0 + cx, y0 + cy, x0 + cx + cw, y0 + cy + ch],
            "widthInStaffSpaces": width_spaces,
            "heightInStaffSpaces": height_spaces,
            "areaInStaffSpacesSquared": area_spaces2,
            "areaPixels": area,
        })

    if not components:
        return None

    components.sort(key=lambda item: (item["bbox"][0], -item["areaPixels"]))
    chosen = dict(components[0])
    chosen.update({
        "staffLines": [float(v) for v in lines],
        "staffSpacing": spacing,
        "staffCenterY": float(np.mean(lines)),
        "barlineEndX": int(bar_end),
        "strongBarGroups": strong_bar_groups,
        "glyphWindow": [x0, y0, x1, y1],
        "method": "source-image-leftmost-qualified-component-after-system-barline",
    })
    return chosen


def generate_page_candidates(image_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        fail("Unreadable source image: " + str(image_path))
    symbols, _ = prepare_symbol_mask(gray)
    staffs = detect_staffs(gray)
    candidates: List[Dict[str, Any]] = []
    for staff_index, staff in enumerate(staffs):
        candidate = localize_candidate(gray, staff, symbols)
        if candidate is None:
            continue
        candidate["staffIndex"] = int(staff_index)
        candidates.append(candidate)
    diagnostics = {
        "detectedStaffCount": len(staffs),
        "candidateCount": len(candidates),
        "imageWidth": int(gray.shape[1]),
        "imageHeight": int(gray.shape[0]),
    }
    return candidates, diagnostics


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


def teacher_box_xyxy(box: Dict[str, Any]) -> List[float]:
    x = float(box["x"])
    y = float(box["y"])
    return [x, y, x + float(box["width"]), y + float(box["height"])]


def greedy_match(candidates: Sequence[Dict[str, Any]], teacher_boxes: Sequence[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
    edges: List[Tuple[float, int, int]] = []
    for candidate_index, candidate in enumerate(candidates):
        for teacher_index, teacher_box in enumerate(teacher_boxes):
            score = box_iou(candidate["bbox"], teacher_box_xyxy(teacher_box))
            if score >= threshold:
                edges.append((score, candidate_index, teacher_index))
    edges.sort(key=lambda item: item[0], reverse=True)
    used_candidates = set()
    used_teacher = set()
    matches: List[Dict[str, Any]] = []
    for score, candidate_index, teacher_index in edges:
        if candidate_index in used_candidates or teacher_index in used_teacher:
            continue
        used_candidates.add(candidate_index)
        used_teacher.add(teacher_index)
        matches.append({
            "iou": float(score),
            "candidateIndex": int(candidate_index),
            "teacherIndex": int(teacher_index),
            "teacherLabel": teacher_boxes[teacher_index]["label"],
            "teacherBoxId": teacher_boxes[teacher_index]["id"],
        })
    return matches


def metric(tp: int, fp: int, fn: int) -> Dict[str, Any]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def evaluate(raw_pages: Dict[str, Any], teacher: Dict[str, Any], threshold: float) -> Dict[str, Any]:
    per_page: Dict[str, Any] = {}
    subtype_totals = {label: {"tp": 0, "fn": 0} for label in ("C1", "C3", "C4")}
    total_tp = total_fp = total_fn = 0

    for page_id in sorted(raw_pages):
        candidates = raw_pages[page_id]["candidates"]
        teacher_boxes = teacher["pages"][page_id]["boxes"]
        matches = greedy_match(candidates, teacher_boxes, threshold)
        matched_teacher = {item["teacherIndex"] for item in matches}
        tp = len(matches)
        fp = len(candidates) - tp
        fn = len(teacher_boxes) - tp
        total_tp += tp
        total_fp += fp
        total_fn += fn

        for index, box in enumerate(teacher_boxes):
            label = box["label"]
            if label not in subtype_totals:
                continue
            if index in matched_teacher:
                subtype_totals[label]["tp"] += 1
            else:
                subtype_totals[label]["fn"] += 1

        per_page[page_id] = {
            "candidateCount": len(candidates),
            "teacherBoxCount": len(teacher_boxes),
            "matches": matches,
            "metrics": metric(tp, fp, fn),
            "unmatchedTeacherBoxes": [
                {"id": box["id"], "label": box["label"], "bbox": teacher_box_xyxy(box)}
                for index, box in enumerate(teacher_boxes)
                if index not in matched_teacher
            ],
        }

    subtype = {}
    for label, counts in subtype_totals.items():
        tp = counts["tp"]
        fn = counts["fn"]
        subtype[label] = {
            "tp": tp,
            "fn": fn,
            "teacherBoxes": tp + fn,
            "recall": tp / (tp + fn) if tp + fn else 0.0,
        }

    return {
        "threshold": threshold,
        "pooled": metric(total_tp, total_fp, total_fn),
        "perTeacherSubtype": subtype,
        "perPage": per_page,
    }


def main() -> None:
    started = time.time()
    if not MANIFEST_PATH.is_file():
        fail("Source manifest missing")
    manifest_sha = sha256_file(MANIFEST_PATH)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        fail("Source manifest SHA mismatch: " + manifest_sha)

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    pages = manifest.get("pages")
    if manifest.get("pageCount") != EXPECTED_PAGE_COUNT or not isinstance(pages, list) or len(pages) != EXPECTED_PAGE_COUNT:
        fail("Source manifest is not the frozen 29-page artifact")
    page_ids = [page.get("pageId") for page in pages]
    if len(set(page_ids)) != EXPECTED_PAGE_COUNT:
        fail("Source manifest does not contain 29 unique page IDs")

    print("=" * 72)
    print("P4.5 SOURCE-IMAGE C-CLEF LOCALIZER")
    print("EOMER/ONNX/GPU: NOT USED")
    print("Teacher truth: NOT READ during candidate generation")
    print("=" * 72)

    raw_pages: Dict[str, Any] = {}
    for page_index, page in enumerate(pages, start=1):
        page_id = page["pageId"]
        image_path = (ROOT / page["imagePath"]).resolve()
        if image_path != ROOT and ROOT not in image_path.parents:
            fail("Unsafe imagePath: " + page_id)
        if not image_path.is_file():
            fail("Source image missing: " + page_id)
        actual_sha = sha256_file(image_path)
        if actual_sha != page["imageSha256"]:
            fail("Source image SHA mismatch: " + page_id)

        candidates, diagnostics = generate_page_candidates(image_path)
        if diagnostics["imageWidth"] != int(page["width"]) or diagnostics["imageHeight"] != int(page["height"]):
            fail("Source dimensions mismatch: " + page_id)
        raw_pages[page_id] = {
            "pageId": page_id,
            "sourceGroup": page.get("sourceGroup"),
            "sourceImageSha256": actual_sha,
            "diagnostics": diagnostics,
            "candidates": candidates,
        }
        print(f"P4.5 GENERATED {page_index:02d}/{EXPECTED_PAGE_COUNT} {page_id} | staffs={diagnostics['detectedStaffCount']} candidates={diagnostics['candidateCount']}")

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    raw_payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_5-source-image-candidates.v1",
        "planVersion": PLAN_VERSION,
        "status": "CANDIDATES_GENERATED_BEFORE_TEACHER_EVALUATION",
        "sourceManifestSha256": manifest_sha,
        "pageCount": EXPECTED_PAGE_COUNT,
        "teacherTruthReadDuringCandidateGeneration": False,
        "eomerUsed": False,
        "onnxUsed": False,
        "restoreModelLoaded": False,
        "pages": raw_pages,
    }
    atomic_json(RAW_CANDIDATES_PATH, raw_payload)
    raw_sha = sha256_file(RAW_CANDIDATES_PATH)
    print("PASS — raw candidates frozen before teacher evaluation")
    print("RAW SHA-256:", raw_sha)

    if not TEACHER_PATH.is_file():
        fail("Teacher truth missing after candidate generation")
    teacher_sha = sha256_file(TEACHER_PATH)
    if teacher_sha != EXPECTED_TEACHER_SHA256:
        fail("Teacher truth SHA mismatch: " + teacher_sha)
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("boxCount") != EXPECTED_BOX_COUNT:
        fail("Teacher truth is not the frozen 29-page / 71-box artifact")
    if teacher.get("labelCounts") != EXPECTED_LABEL_COUNTS:
        fail("Teacher label counts changed")
    if teacher.get("sourceManifestSha256") != manifest_sha:
        fail("Teacher truth is not bound to this source manifest")
    if set(teacher.get("pages", {})) != set(page_ids):
        fail("Teacher and manifest page IDs differ")

    primary = evaluate(raw_pages, teacher, PRIMARY_IOU)
    diagnostic = evaluate(raw_pages, teacher, DIAGNOSTIC_IOU)
    target_met = (
        primary["pooled"]["recall"] >= 0.90
        and all(primary["perTeacherSubtype"][label]["recall"] >= 0.80 for label in ("C1", "C3", "C4"))
    )

    result = {
        "schemaVersion": SCHEMA_VERSION,
        "planVersion": PLAN_VERSION,
        "status": "COMPLETE",
        "sourceOnly": True,
        "eomerUsed": False,
        "onnxUsed": False,
        "gpuUsed": False,
        "restoreModelLoaded": False,
        "teacherTruthReadDuringCandidateGeneration": False,
        "heldOutAccessed": False,
        "trainingUsed": False,
        "sourceManifestSha256": manifest_sha,
        "teacherTruthSha256": teacher_sha,
        "rawCandidateArtifact": {"path": str(RAW_CANDIDATES_PATH), "sha256": raw_sha},
        "pageCount": EXPECTED_PAGE_COUNT,
        "teacherBoxCount": EXPECTED_BOX_COUNT,
        "primaryMeasurement": primary,
        "diagnosticMeasurement": diagnostic,
        "developmentLocalizationTarget": {
            "pooledRecallMinimum": 0.90,
            "eachSubtypeRecallMinimum": 0.80,
            "met": bool(target_met),
        },
        "interpretationBoundary": {
            "localizationOnly": True,
            "subtypeClassifierIncluded": False,
            "detectorQualified": False,
            "qualificationDecisionAuthorized": False,
            "productionInferenceAuthorized": False,
            "semanticPreservationEstablished": False,
            "overallStage11PassAuthorized": False,
            "stage12EntryAuthorized": False,
        },
        "runtimeSeconds": time.time() - started,
    }
    atomic_json(RESULT_PATH, result)
    result_sha = sha256_file(RESULT_PATH)

    print()
    print("=" * 72)
    print("P4.5 SOURCE-IMAGE LOCALIZATION COMPLETE")
    print("=" * 72)
    print("PRIMARY IoU 0.50:", primary["pooled"])
    print("SUBTYPE RECALL:", {k: v["recall"] for k, v in primary["perTeacherSubtype"].items()})
    print("DIAGNOSTIC IoU 0.30:", diagnostic["pooled"])
    print("DEVELOPMENT LOCALIZATION TARGET MET:", target_met)
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", result_sha)
    print("detectorQualified: False — localization-only development result")


if __name__ == "__main__":
    main()
