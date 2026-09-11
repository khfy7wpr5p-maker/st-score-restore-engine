"""P4.10 development-only C-clef localizer-v3 candidate-ceiling remeasurement.

P4.9 is spent holdout evidence and is reused only for development/failure analysis.
Phase A generates and freezes candidates before teacher truth is opened.
This runner cannot qualify the detector and cannot authorize Stage 11/production.
"""
from __future__ import annotations
import hashlib, json, math, os, statistics, types, urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import cv2
import numpy as np

ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/P4_C_CLEF_HOLDOUT_P4_9")
PREPARED = ROOT / "_PREPARED"
MANIFEST_PATH = PREPARED / "c_clef_p4_9_holdout_source_page_manifest.v1.json"
TEACHER_PATH = ROOT / "_ANNOTATIONS" / "c_clef_p4_9_holdout_teacher_boxes.v1.json"
OUT = ROOT / "_P4_10_LOCALIZER_V3_DEV_DIAGNOSTIC"
RAW_PATH = OUT / "p4_10_localizer_v3_candidates_before_teacher.v1.json"
RESULT_PATH = OUT / "p4_10_localizer_v3_candidate_ceiling_result.v1.json"

EXPECTED_MANIFEST_SHA256 = "8db0cf576137ec8cfd8458dd5b9cead73f49b4b2910bf6436e31e1e3737a7ece"
EXPECTED_TEACHER_SHA256 = "8ce56115b519df0429ec37964de9e694c44a0fdf081b74c9bff0484bf248f095"
EXPECTED_PAGE_COUNT = 11
EXPECTED_TEACHER_BOX_COUNT = 38
EXPECTED_LABEL_COUNTS = {"C1": 12, "C3": 21, "C4": 5, "AMBIGUOUS": 0}
PRIMARY_IOU = 0.50
MIN_POOLED_RECALL = 0.90
MIN_SUBTYPE_RECALL = 0.80

P45_COMMIT = "7130bdf94bcf9247a0b33e9342db22746b46f289"
P45_EXPECTED_SOURCE_SHA256 = "0bd631e0863f084204cb3927aa19c1da715e30c81371250a50b4ad97f107c426"
P45_URL = (
    "https://raw.githubusercontent.com/khfy7wpr5p-maker/st-score-restore-engine/"
    + P45_COMMIT
    + "/src/st_score_restore/stage11_v2d_c_clef_p4_5_source_image_localizer.py"
)

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
        raise RuntimeError("Frozen P4.5 module SHA mismatch: " + actual)
    module = types.ModuleType("p45_frozen_p410_v3")
    module.__file__ = "stage11_v2d_c_clef_p4_5_source_image_localizer.py"
    exec(compile(data.decode("utf-8"), module.__file__, "exec"), module.__dict__)
    return module

def grouped_runs(indices: np.ndarray) -> List[Tuple[int, int]]:
    if indices.size == 0:
        return []
    out = []
    start = prev = int(indices[0])
    for raw in indices[1:]:
        value = int(raw)
        if value > prev + 1:
            out.append((start, prev))
            start = value
        prev = value
    out.append((start, prev))
    return out

def sane_staff(staff: Dict[str, Any], height: int) -> bool:
    spacing = float(staff["spacing"])
    min_spacing = max(4.0, 0.0015 * float(height))
    max_spacing = max(20.0, 0.02 * float(height))
    if not (min_spacing <= spacing <= max_spacing):
        return False
    lines = np.asarray(staff["lines"], dtype=float)
    if lines.size != 5:
        return False
    gaps = np.diff(lines)
    return float(np.max(np.abs(gaps - np.median(gaps)))) <= max(2.0, 0.25 * spacing)

def strict_projection_staffs(gray: np.ndarray) -> List[Dict[str, Any]]:
    height, width = gray.shape[:2]
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    min_spacing = max(4.0, 0.0015 * float(height))
    max_spacing = max(20.0, 0.02 * float(height))
    found = []
    for left, right in ((0.08, 0.92), (0.15, 0.85), (0.25, 0.75)):
        x0, x1 = int(round(left * width)), int(round(right * width))
        if x1 <= x0:
            continue
        span = x1 - x0
        projection = np.count_nonzero(ink[:, x0:x1] > 0, axis=1) / float(span)
        for coverage in (0.30, 0.24, 0.18, 0.12):
            centers = np.asarray(
                [(a + b) / 2.0 for a, b in grouped_runs(np.flatnonzero(projection >= coverage))],
                dtype=float,
            )
            for i in range(max(0, len(centers) - 4)):
                lines = centers[i : i + 5]
                gaps = np.diff(lines)
                spacing = float(np.median(gaps))
                if not (min_spacing <= spacing <= max_spacing):
                    continue
                if float(np.max(np.abs(gaps - spacing))) > max(2.0, 0.22 * spacing):
                    continue
                prev_gap = float(lines[0] - centers[i - 1]) if i > 0 else 999.0 * spacing
                next_gap = float(centers[i + 5] - lines[-1]) if i + 5 < len(centers) else 999.0 * spacing
                if prev_gap < 2.0 * spacing or next_gap < 2.0 * spacing:
                    continue
                support = float(np.mean([projection[int(round(y))] for y in lines]))
                found.append({
                    "lines": [float(v) for v in lines],
                    "spacing": spacing,
                    "source": "strict_projection",
                    "support": support,
                    "gapCv": float(np.std(gaps) / spacing) if spacing else 1.0,
                })
    found.sort(key=lambda s: (-float(s["support"]), float(s["gapCv"])))
    selected = []
    for staff in found:
        center = float(np.mean(staff["lines"]))
        spacing = float(staff["spacing"])
        duplicate = False
        for existing in selected:
            ec = float(np.mean(existing["lines"]))
            es = float(existing["spacing"])
            if abs(center - ec) < 0.60 * max(spacing, es) and abs(spacing - es) < 0.25 * max(spacing, es):
                duplicate = True
                break
        if not duplicate:
            selected.append(staff)
    return sorted(selected, key=lambda s: float(np.mean(s["lines"])))

def select_staffs(gray: np.ndarray, p45) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    height = int(gray.shape[0])
    primary = []
    for raw in p45.detect_staffs(gray):
        item = dict(raw)
        item["source"] = "p45"
        if sane_staff(item, height):
            primary.append(item)
    if len(primary) >= 3:
        return primary, {"path": "p45_sane", "p45Sane": len(primary), "projectionFallback": 0}
    fallback = strict_projection_staffs(gray)
    return fallback, {
        "path": "strict_projection_fallback",
        "p45Sane": len(primary),
        "projectionFallback": len(fallback),
    }

def full_width_candidates(gray: np.ndarray, staffs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    height, width = gray.shape[:2]
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    out = []
    for staff_index, staff in enumerate(staffs):
        lines = np.asarray(staff["lines"], dtype=float)
        spacing = float(staff["spacing"])
        y0 = max(0, int(math.floor(lines[0] - 2.8 * spacing)))
        y1 = min(height, int(math.ceil(lines[-1] + 2.8 * spacing)))
        if y1 <= y0:
            continue
        roi = ink[y0:y1, :].copy()
        line_width = max(7, int(round(2.2 * spacing)))
        horizontal = cv2.morphologyEx(
            roi,
            cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_RECT, (line_width, 1)),
        )
        removal = cv2.dilate(
            horizontal,
            cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(1, int(round(0.20 * spacing))))),
        )
        clean = roi.copy()
        clean[removal > 0] = 0

        x_profile = np.count_nonzero(clean > 0, axis=0)
        active = np.flatnonzero(x_profile >= max(1, int(round(0.20 * spacing))))
        runs = grouped_runs(active)
        groups: List[Tuple[int, int]] = []
        for a, b in runs:
            if (b - a + 1) < max(1.0, 0.10 * spacing):
                continue
            if groups and (a - groups[-1][1]) <= 0.65 * spacing:
                groups[-1] = (groups[-1][0], b)
            else:
                groups.append((a, b))

        centers = []
        for a, b in groups:
            group_width = b - a + 1
            if group_width <= 5.0 * spacing:
                centers.append((a + b) / 2.0)
            else:
                x = a + 1.5 * spacing
                while x <= b - 1.5 * spacing:
                    centers.append(float(x))
                    x += 1.25 * spacing
        dedup_centers = []
        for x in sorted(centers):
            if not dedup_centers or x - dedup_centers[-1] >= 0.35 * spacing:
                dedup_centers.append(float(x))

        sizes = [(3.2, 5.2, "base")]
        if spacing < 10.0:
            sizes.append((3.0, 4.8, "small_spacing"))
        if spacing < 9.0 and (float(width) / spacing) > 180.0:
            sizes.append((3.4, 5.4, "dense_wide_page"))

        for base_x in dedup_centers:
            for x_offset_spaces in (0.0, 1.25):
                x_center = base_x + x_offset_spaces * spacing
                for line_index, anchor in ((4, "C1"), (2, "C3"), (1, "C4")):
                    y_center = float(lines[line_index])
                    for width_spaces, height_spaces, size_tag in sizes:
                        x1 = max(0.0, x_center - 0.5 * width_spaces * spacing)
                        x2 = min(float(width), x_center + 0.5 * width_spaces * spacing)
                        yy1 = max(0.0, y_center - 0.5 * height_spaces * spacing)
                        yy2 = min(float(height), y_center + 0.5 * height_spaces * spacing)
                        if x2 <= x1 or yy2 <= yy1:
                            continue
                        out.append({
                            "bbox": [x1, yy1, x2, yy2],
                            "staffIndex": int(staff_index),
                            "staffSource": str(staff.get("source", "unknown")),
                            "staffSpacing": spacing,
                            "anchor": anchor,
                            "xOffsetStaffSpaces": x_offset_spaces,
                            "sizeTag": size_tag,
                        })
    return out

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

def teacher_xyxy(box: Dict[str, Any]) -> List[float]:
    return [
        float(box["x"]),
        float(box["y"]),
        float(box["x"] + box["w"]),
        float(box["y"] + box["h"]),
    ]

def greedy_match(candidates: Sequence[Dict[str, Any]], teacher_boxes: Sequence[Dict[str, Any]]):
    edges = []
    for ci, candidate in enumerate(candidates):
        cb = candidate["bbox"]
        for ti, teacher_box in enumerate(teacher_boxes):
            score = box_iou(cb, teacher_xyxy(teacher_box))
            if score >= PRIMARY_IOU:
                edges.append((score, ci, ti))
    edges.sort(reverse=True)
    used_c, used_t, matches = set(), set(), []
    for score, ci, ti in edges:
        if ci in used_c or ti in used_t:
            continue
        used_c.add(ci)
        used_t.add(ti)
        matches.append((ci, ti, float(score)))
    return matches

def main() -> None:
    if not MANIFEST_PATH.is_file() or not TEACHER_PATH.is_file():
        raise RuntimeError("P4.9 prepared manifest or teacher truth missing")
    manifest_sha = sha256_file(MANIFEST_PATH)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("Manifest SHA mismatch: " + manifest_sha)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    pages = manifest.get("pages", [])
    if len(pages) != EXPECTED_PAGE_COUNT or manifest.get("pageCount") != EXPECTED_PAGE_COUNT:
        raise RuntimeError("Expected frozen 11-page P4.9 manifest")
    if manifest.get("detectorOutputsAccessed") is not False:
        raise RuntimeError("Unsafe manifest provenance")

    p45 = load_frozen_p45()
    frozen_pages = {}
    candidate_total = 0

    print("=" * 76)
    print("P4.10 LOCALIZER-V3 DEVELOPMENT CANDIDATE CEILING")
    print("P4.9 qualification status: SPENT / DEVELOPMENT DIAGNOSTIC ONLY")
    print("Teacher truth: NOT READ during Phase A")
    print("=" * 76)

    for index, page in enumerate(pages, start=1):
        page_id = page["pageId"]
        image_path = PREPARED / page["imagePath"]
        if not image_path.is_file():
            raise RuntimeError("Prepared image missing: " + page_id)
        if sha256_file(image_path) != page["imageSha256"]:
            raise RuntimeError("Prepared image SHA mismatch: " + page_id)
        gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            raise RuntimeError("Unreadable image: " + page_id)
        staffs, staff_diag = select_staffs(gray, p45)
        candidates = full_width_candidates(gray, staffs)
        candidate_total += len(candidates)
        frozen_pages[page_id] = {
            "pageId": page_id,
            "sourcePdfName": page["sourcePdfName"],
            "sourcePageNumber": page["sourcePageNumber"],
            "sourceImageSha256": page["imageSha256"],
            "staffDiagnostics": staff_diag,
            "staffCount": len(staffs),
            "candidateCount": len(candidates),
            "candidates": candidates,
        }
        print(
            f"P4.10-V3 GENERATED {index:02d}/{EXPECTED_PAGE_COUNT} {page_id} "
            f"staffs={len(staffs)} candidates={len(candidates)} path={staff_diag['path']}"
        )

    raw_payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_10-localizer-v3-candidates.v1",
        "status": "PHASE_A_FROZEN_BEFORE_TEACHER_ACCESS",
        "developmentOnly": True,
        "p4_9SpentHoldoutReclassifiedForDevelopmentDiagnostic": True,
        "teacherTruthReadDuringCandidateGeneration": False,
        "sourceManifestSha256": manifest_sha,
        "pageCount": EXPECTED_PAGE_COUNT,
        "candidateCountTotal": candidate_total,
        "pages": frozen_pages,
    }
    atomic_json(RAW_PATH, raw_payload)
    raw_sha = sha256_file(RAW_PATH)
    print("PASS — localizer-v3 candidate artifact frozen before teacher access")
    print("RAW SHA-256:", raw_sha)

    teacher_sha = sha256_file(TEACHER_PATH)
    if teacher_sha != EXPECTED_TEACHER_SHA256:
        raise RuntimeError("Teacher SHA mismatch: " + teacher_sha)
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if teacher.get("boxCount") != EXPECTED_TEACHER_BOX_COUNT:
        raise RuntimeError("Teacher box count changed")
    if teacher.get("labelCounts") != EXPECTED_LABEL_COUNTS:
        raise RuntimeError("Teacher label counts changed")
    if teacher.get("detectorOutputsAccessed") is not False:
        raise RuntimeError("Teacher provenance violation")

    subtype_total = Counter()
    subtype_tp = Counter()
    total_tp = 0
    per_page = {}

    for page_id, page in frozen_pages.items():
        teacher_boxes = teacher["pages"][page_id]["boxes"]
        for box in teacher_boxes:
            subtype_total[box["label"]] += 1
        matches = greedy_match(page["candidates"], teacher_boxes)
        matched_t = {ti for _, ti, _ in matches}
        total_tp += len(matches)
        for ti in matched_t:
            subtype_tp[teacher_boxes[ti]["label"]] += 1
        per_page[page_id] = {
            "candidateCount": page["candidateCount"],
            "teacherBoxCount": len(teacher_boxes),
            "matchedTeacherCount": len(matches),
            "candidateRecall": len(matches) / len(teacher_boxes) if teacher_boxes else 0.0,
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

    pooled_recall = total_tp / EXPECTED_TEACHER_BOX_COUNT
    subtype = {}
    for label in ("C1", "C3", "C4"):
        total = int(subtype_total[label])
        tp = int(subtype_tp[label])
        subtype[label] = {
            "teacherBoxes": total,
            "tp": tp,
            "fn": total - tp,
            "candidateRecall": tp / total if total else 0.0,
        }

    target_met = (
        pooled_recall >= MIN_POOLED_RECALL
        and all(subtype[label]["candidateRecall"] >= MIN_SUBTYPE_RECALL for label in ("C1", "C3", "C4"))
    )

    result = {
        "schemaVersion": "stage11.v2d.c-clef-p4_10-localizer-v3-candidate-ceiling-result.v1",
        "status": "COMPLETE",
        "developmentOnly": True,
        "p4_9CannotQualifyThisDetector": True,
        "candidateArtifactSha256": raw_sha,
        "pageCount": EXPECTED_PAGE_COUNT,
        "teacherBoxCount": EXPECTED_TEACHER_BOX_COUNT,
        "candidateCountTotal": candidate_total,
        "pooledCandidateCeiling": {
            "tp": total_tp,
            "fn": EXPECTED_TEACHER_BOX_COUNT - total_tp,
            "recall": pooled_recall,
        },
        "perSubtype": subtype,
        "perPage": per_page,
        "developmentCandidateCeilingTarget": {
            "pooledRecallAtLeast": MIN_POOLED_RECALL,
            "eachSubtypeRecallAtLeast": MIN_SUBTYPE_RECALL,
            "met": bool(target_met),
        },
        "decisionBoundary": {
            "detectorQualified": False,
            "qualificationEvidence": False,
            "overallStage11PassAuthorized": False,
            "productionReady": False,
            "stage12EntryAuthorized": False,
            "nextIfTargetMet": "freeze and measure a precision gate on development data; qualification still requires a new independent holdout",
        },
    }
    atomic_json(RESULT_PATH, result)
    result_sha = sha256_file(RESULT_PATH)

    print()
    print("=" * 76)
    print("P4.10 LOCALIZER-V3 CANDIDATE CEILING COMPLETE")
    print("=" * 76)
    print("POOLED:", result["pooledCandidateCeiling"])
    print("SUBTYPE:", {k: v["candidateRecall"] for k, v in subtype.items()})
    print("CANDIDATE COUNT TOTAL:", candidate_total)
    print("TARGET MET:", target_met)
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", result_sha)
    print("detectorQualified: False — development candidate ceiling only")

if __name__ == "__main__":
    main()
