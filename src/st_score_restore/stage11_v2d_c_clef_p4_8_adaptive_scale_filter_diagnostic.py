"""P4.8 adaptive C-clef scale/filter development diagnostic.

Development-only. Uses previously frozen P4.8 candidate artifacts and teacher truth.
P4.7 holdout is never read. The adaptive rule is:
- if pre-canonical median staff spacing < 12 px: use canonical candidate path
  with P4.8 normalized-geometry filter;
- otherwise preserve the original frozen P4.6 path.

No production/qualification authorization is implied by this diagnostic.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL")
ORIG_PATH = ROOT / "P4_C_CLEF_P4_8_DEV_DIAGNOSTIC" / "p4_8_development_scale_candidates.v1.json"
CANON_PATH = ROOT / "P4_C_CLEF_P4_8_CANONICAL_DEV_DIAGNOSTIC" / "p4_8_canonical_scale_candidates.v1.json"
TEACHER_PATH = ROOT / "C_CLEF_SOURCE_PAGES" / "_ANNOTATIONS" / "c_clef_teacher_boxes.v1.json"
OUT = ROOT / "P4_C_CLEF_P4_8_ADAPTIVE_DEV_DIAGNOSTIC"
RESULT_PATH = OUT / "p4_8_adaptive_scale_filter_diagnostic.v1.json"

EXPECTED_ORIG_SHA256 = "a73c2eb5df0466257e27ee33098d2546c3ce7d19665e4f42ac1a4a9b4a47699d"
EXPECTED_CANON_SHA256 = "347a8003282478dde9586a87a9076b2bdf2047d2f0abfe6e7b9514b2e807d3c8"
EXPECTED_TEACHER_SHA256 = "1104d916faaf8d3c391cca9eda0354d21259f722cdcfe0f414c140796a5ffc5b"
EXPECTED_PAGE_COUNT = 29
EXPECTED_TEACHER_BOXES = 71
PRIMARY_IOU = 0.50

# Principled trigger: this is the exact pixel-space boundary that caused the
# frozen P4.6 low-spacing branch to activate. Pages below it are canonicalized.
CANONICALIZE_BELOW_STAFF_SPACING_PX = 12.0

# P4.8 canonical-path filter. All thresholds except the trigger are expressed in
# staff-space-normalized geometry. They were selected only from development
# candidate/teacher data across 1.00/0.75/0.50 synthetic scale variants.
P48_MIN_AREA = 4.15
P48_MAX_AREA = 12.0
P48_MIN_WIDTH = 2.0
P48_MIN_HEIGHT = 3.6
P48_MAX_HEIGHT = 5.8

# Frozen P4.6 filter for non-canonical path.
P46_LOW_AREA = 4.15
P46_HIGH_AREA = 9.80
P46_MIN_WIDTH = 2.00
P46_MAX_HEIGHT = 6.10
P46_LOW_SPACING = 12.00
P46_MIN_HEIGHT_LOW_SPACING = 5.00


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


def p46_keep(c: Dict[str, Any]) -> bool:
    area = float(c["areaInStaffSpacesSquared"])
    width = float(c["widthInStaffSpaces"])
    height = float(c["heightInStaffSpaces"])
    spacing = float(c["staffSpacing"])
    if area < P46_LOW_AREA or area > P46_HIGH_AREA:
        return False
    if width < P46_MIN_WIDTH:
        return False
    if height > P46_MAX_HEIGHT:
        return False
    if spacing < P46_LOW_SPACING and height < P46_MIN_HEIGHT_LOW_SPACING:
        return False
    return True


def p48_keep(c: Dict[str, Any]) -> bool:
    area = float(c["areaInStaffSpacesSquared"])
    width = float(c["widthInStaffSpaces"])
    height = float(c["heightInStaffSpaces"])
    return (
        P48_MIN_AREA <= area <= P48_MAX_AREA
        and width >= P48_MIN_WIDTH
        and P48_MIN_HEIGHT <= height <= P48_MAX_HEIGHT
    )


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


def teacher_xyxy(box: Dict[str, Any], scale: float) -> List[float]:
    x = float(box["x"]) * scale
    y = float(box["y"]) * scale
    w = float(box.get("width", box.get("w"))) * scale
    h = float(box.get("height", box.get("h"))) * scale
    return [x, y, x + w, y + h]


def greedy_match(candidates: Sequence[Dict[str, Any]], teacher_boxes: Sequence[Dict[str, Any]], scale: float):
    edges: List[Tuple[float, int, int]] = []
    for ci, candidate in enumerate(candidates):
        for ti, teacher_box in enumerate(teacher_boxes):
            score = box_iou(candidate["bbox"], teacher_xyxy(teacher_box, scale))
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
        matches.append((ci, ti, score))
    return matches


def metric(tp: int, fp: int, fn: int) -> Dict[str, float | int]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def main() -> None:
    for path, expected in (
        (ORIG_PATH, EXPECTED_ORIG_SHA256),
        (CANON_PATH, EXPECTED_CANON_SHA256),
        (TEACHER_PATH, EXPECTED_TEACHER_SHA256),
    ):
        if not path.is_file():
            raise RuntimeError(f"Required artifact missing: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"SHA mismatch for {path.name}: {actual}")

    original = json.loads(ORIG_PATH.read_text(encoding="utf-8"))
    canonical = json.loads(CANON_PATH.read_text(encoding="utf-8"))
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))

    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("boxCount") != EXPECTED_TEACHER_BOXES:
        raise RuntimeError("Teacher artifact is not the frozen 29-page / 71-box development set")
    if original.get("p4_7HoldoutAccessed") is not False or canonical.get("p4_7HoldoutAccessed") is not False:
        raise RuntimeError("Unsafe provenance: holdout access flag is not false")

    result_by_variant: Dict[str, Any] = {}

    for variant_name in sorted(original["variants"]):
        ov = original["variants"][variant_name]
        cv = canonical["variants"][variant_name]
        input_scale = float(ov["scale"])
        pooled_tp = pooled_fp = pooled_fn = 0
        subtype_total = Counter()
        subtype_tp = Counter()
        canonicalized_pages = 0
        preserved_pages = 0
        per_page: Dict[str, Any] = {}

        for page_id, op in ov["pages"].items():
            cp = cv["pages"][page_id]
            pre_spacing = float(cp["preCanonicalMedianStaffSpacing"])
            use_canonical = pre_spacing < CANONICALIZE_BELOW_STAFF_SPACING_PX

            if use_canonical:
                candidates = [c for c in cp["candidates"] if p48_keep(c)]
                teacher_scale = input_scale * float(cp["canonicalFactor"])
                path_name = "canonical_p48"
                canonicalized_pages += 1
            else:
                candidates = [c for c in op["candidates"] if p46_keep(c)]
                teacher_scale = input_scale
                path_name = "original_p46"
                preserved_pages += 1

            teacher_boxes = teacher["pages"][page_id]["boxes"]
            for box in teacher_boxes:
                subtype_total[box["label"]] += 1

            matches = greedy_match(candidates, teacher_boxes, teacher_scale)
            matched_teacher = {ti for _, ti, _ in matches}
            tp = len(matches)
            fp = len(candidates) - tp
            fn = len(teacher_boxes) - tp
            pooled_tp += tp
            pooled_fp += fp
            pooled_fn += fn
            for ti in matched_teacher:
                subtype_tp[teacher_boxes[ti]["label"]] += 1

            per_page[page_id] = {
                "path": path_name,
                "preCanonicalMedianStaffSpacing": pre_spacing,
                "acceptedCandidateCount": len(candidates),
                "teacherBoxCount": len(teacher_boxes),
                "metrics": metric(tp, fp, fn),
            }

        pooled = metric(pooled_tp, pooled_fp, pooled_fn)
        subtype = {
            label: {
                "teacherBoxes": int(subtype_total[label]),
                "tp": int(subtype_tp[label]),
                "fn": int(subtype_total[label] - subtype_tp[label]),
                "recall": (subtype_tp[label] / subtype_total[label]) if subtype_total[label] else 0.0,
            }
            for label in ("C1", "C3", "C4")
        }
        result_by_variant[variant_name] = {
            "canonicalizedPageCount": canonicalized_pages,
            "preservedOriginalPageCount": preserved_pages,
            "pooled": pooled,
            "subtype": subtype,
            "perPage": per_page,
        }

    payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_8-adaptive-scale-filter-diagnostic.v1",
        "status": "COMPLETE",
        "developmentOnly": True,
        "p4_7HoldoutAccessed": False,
        "sourceArtifacts": {
            "originalCandidatesSha256": EXPECTED_ORIG_SHA256,
            "canonicalCandidatesSha256": EXPECTED_CANON_SHA256,
            "teacherSha256": EXPECTED_TEACHER_SHA256,
        },
        "adaptivePolicy": {
            "canonicalizeBelowStaffSpacingPx": CANONICALIZE_BELOW_STAFF_SPACING_PX,
            "otherwisePreserveFrozenP4_6Path": True,
            "canonicalFilter": {
                "minimumAreaInStaffSpacesSquared": P48_MIN_AREA,
                "maximumAreaInStaffSpacesSquared": P48_MAX_AREA,
                "minimumWidthInStaffSpaces": P48_MIN_WIDTH,
                "minimumHeightInStaffSpaces": P48_MIN_HEIGHT,
                "maximumHeightInStaffSpaces": P48_MAX_HEIGHT,
            },
        },
        "variants": result_by_variant,
        "decisionBoundary": {
            "detectorQualified": False,
            "productionInferenceAuthorized": False,
            "overallStage11PassAuthorized": False,
            "newIndependentHoldoutRequiredAfterFreeze": True,
        },
    }

    atomic_json(RESULT_PATH, payload)

    print("=" * 72)
    print("P4.8 ADAPTIVE SCALE/FILTER DIAGNOSTIC COMPLETE")
    print("P4.7 holdout: NOT READ")
    print("=" * 72)
    for name, data in result_by_variant.items():
        print(name)
        print("  canonicalizedPages:", data["canonicalizedPageCount"])
        print("  preservedOriginalPages:", data["preservedOriginalPageCount"])
        print("  POOLED:", data["pooled"])
        print("  SUBTYPE:", data["subtype"])
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", sha256_file(RESULT_PATH))
    print("detectorQualified: False — development diagnostic only")


if __name__ == "__main__":
    main()
