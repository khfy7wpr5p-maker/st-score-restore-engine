"""P4.8 development-only dual-path C-clef fusion diagnostic.

Uses only frozen development artifacts. P4.7 holdout is never read.
The diagnostic preserves frozen P4.6 accepted original candidates, maps accepted
canonical-path candidates back to the input-variant coordinate system, and adds
only canonical candidates that do not overlap an already-kept original candidate
at IoU >= 0.50. Teacher truth is used only for development evaluation.

This is diagnostic evidence only. It does not qualify the detector or authorize
production/Stage11/Stage12 progression.
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
OUT = ROOT / "P4_C_CLEF_P4_8_FUSION_DEV_DIAGNOSTIC"
RESULT_PATH = OUT / "p4_8_dual_path_fusion_diagnostic.v1.json"

EXPECTED_ORIG_SHA256 = "a73c2eb5df0466257e27ee33098d2546c3ce7d19665e4f42ac1a4a9b4a47699d"
EXPECTED_CANON_SHA256 = "347a8003282478dde9586a87a9076b2bdf2047d2f0abfe6e7b9514b2e807d3c8"
EXPECTED_TEACHER_SHA256 = "1104d916faaf8d3c391cca9eda0354d21259f722cdcfe0f414c140796a5ffc5b"
EXPECTED_PAGE_COUNT = 29
EXPECTED_TEACHER_BOXES = 71
PRIMARY_IOU = 0.50
DEDUP_IOU = 0.50

# Frozen P4.6 original-path filter.
P46_LOW_AREA = 4.15
P46_HIGH_AREA = 9.80
P46_MIN_WIDTH = 2.00
P46_MAX_HEIGHT = 6.10
P46_LOW_SPACING = 12.00
P46_MIN_HEIGHT_LOW_SPACING = 5.00

# Development-only P4.8 canonical-path filter already evaluated in the prior
# adaptive diagnostic. No new threshold tuning is performed in this script.
P48_MIN_AREA = 4.15
P48_MAX_AREA = 12.0
P48_MIN_WIDTH = 2.0
P48_MIN_HEIGHT = 3.6
P48_MAX_HEIGHT = 5.8


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

    variants_out: Dict[str, Any] = {}

    for variant_name in sorted(original["variants"]):
        ov = original["variants"][variant_name]
        cv = canonical["variants"][variant_name]
        input_scale = float(ov["scale"])
        pooled_tp = pooled_fp = pooled_fn = 0
        subtype_total = Counter()
        subtype_tp = Counter()
        original_count = added_canonical_count = dedup_rejected_count = 0
        per_page: Dict[str, Any] = {}

        for page_id, op in ov["pages"].items():
            cp = cv["pages"][page_id]
            canonical_factor = float(cp["canonicalFactor"])

            fused: List[Dict[str, Any]] = []
            for candidate in op["candidates"]:
                if not p46_keep(candidate):
                    continue
                item = dict(candidate)
                item["fusionSource"] = "original_p46"
                fused.append(item)
                original_count += 1

            page_added = 0
            page_dedup = 0
            for candidate in cp["candidates"]:
                if not p48_keep(candidate):
                    continue
                item = dict(candidate)
                item["bbox"] = [float(v) / canonical_factor for v in candidate["bbox"]]
                item["fusionSource"] = "canonical_p48"
                if any(box_iou(item["bbox"], kept["bbox"]) >= DEDUP_IOU for kept in fused):
                    dedup_rejected_count += 1
                    page_dedup += 1
                    continue
                fused.append(item)
                added_canonical_count += 1
                page_added += 1

            teacher_boxes = teacher["pages"][page_id]["boxes"]
            for box in teacher_boxes:
                subtype_total[box["label"]] += 1

            matches = greedy_match(fused, teacher_boxes, input_scale)
            matched_teacher = {ti for _, ti, _ in matches}
            tp = len(matches)
            fp = len(fused) - tp
            fn = len(teacher_boxes) - tp
            pooled_tp += tp
            pooled_fp += fp
            pooled_fn += fn
            for ti in matched_teacher:
                subtype_tp[teacher_boxes[ti]["label"]] += 1

            per_page[page_id] = {
                "acceptedOriginalCandidateCount": sum(1 for c in fused if c["fusionSource"] == "original_p46"),
                "addedCanonicalCandidateCount": page_added,
                "deduplicatedCanonicalCandidateCount": page_dedup,
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
        variants_out[variant_name] = {
            "acceptedOriginalCandidateCount": original_count,
            "addedCanonicalCandidateCount": added_canonical_count,
            "deduplicatedCanonicalCandidateCount": dedup_rejected_count,
            "pooled": pooled,
            "subtype": subtype,
            "perPage": per_page,
        }

    payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_8-dual-path-fusion-diagnostic.v1",
        "status": "COMPLETE",
        "developmentOnly": True,
        "p4_7HoldoutAccessed": False,
        "sourceArtifacts": {
            "originalCandidatesSha256": EXPECTED_ORIG_SHA256,
            "canonicalCandidatesSha256": EXPECTED_CANON_SHA256,
            "teacherSha256": EXPECTED_TEACHER_SHA256,
        },
        "fusionPolicy": {
            "originalPath": "frozen_p4_6",
            "canonicalPath": "p4_8_normalized_geometry_filter",
            "canonicalBBoxMappedBackByCanonicalFactor": True,
            "preferOriginalWhenOverlap": True,
            "dedupIoU": DEDUP_IOU,
            "dedupThresholdTunedOnTeacher": False,
        },
        "variants": variants_out,
        "decisionBoundary": {
            "detectorQualified": False,
            "productionInferenceAuthorized": False,
            "overallStage11PassAuthorized": False,
            "newIndependentHoldoutRequiredAfterAnyP4_8Freeze": True,
        },
    }
    atomic_json(RESULT_PATH, payload)

    print("=" * 72)
    print("P4.8 DUAL-PATH FUSION DIAGNOSTIC COMPLETE")
    print("P4.7 holdout: NOT READ")
    print("=" * 72)
    for variant_name, result in variants_out.items():
        print(variant_name)
        print("  originalAccepted:", result["acceptedOriginalCandidateCount"])
        print("  canonicalAdded:", result["addedCanonicalCandidateCount"])
        print("  canonicalDeduped:", result["deduplicatedCanonicalCandidateCount"])
        print("  POOLED:", result["pooled"])
        print("  SUBTYPE:", result["subtype"])
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", sha256_file(RESULT_PATH))
    print("detectorQualified: False — development diagnostic only")


if __name__ == "__main__":
    main()
