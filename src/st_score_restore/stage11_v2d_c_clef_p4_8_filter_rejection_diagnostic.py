"""P4.8 development-only diagnostic for P4.6 rejection causes.

Consumes only the already-frozen P4.8 development scale candidate artifact and
frozen development teacher truth. It never reads the P4.7 holdout. It does not
change any detector/filter threshold. The purpose is to identify which frozen
P4.6 rule rejects raw true-positive candidates as synthetic scale decreases.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Sequence, Tuple

ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL")
DEV_ROOT = ROOT / "C_CLEF_SOURCE_PAGES"
RAW_PATH = ROOT / "P4_C_CLEF_P4_8_DEV_DIAGNOSTIC" / "p4_8_development_scale_candidates.v1.json"
TEACHER_PATH = DEV_ROOT / "_ANNOTATIONS" / "c_clef_teacher_boxes.v1.json"
OUT_PATH = ROOT / "P4_C_CLEF_P4_8_DEV_DIAGNOSTIC" / "p4_8_filter_rejection_diagnostic.v1.json"

EXPECTED_RAW_SHA256 = "a73c2eb5df0466257e27ee33098d2546c3ce7d19665e4f42ac1a4a9b4a47699d"
EXPECTED_TEACHER_SHA256 = "1104d916faaf8d3c391cca9eda0354d21259f722cdcfe0f414c140796a5ffc5b"
EXPECTED_PAGE_COUNT = 29
EXPECTED_TEACHER_BOX_COUNT = 71
PRIMARY_IOU = 0.50

# Frozen P4.6 v1 rules. DO NOT RETUNE HERE.
LOW_AREA = 4.15
HIGH_AREA = 9.80
MIN_WIDTH = 2.00
MAX_HEIGHT = 6.10
LOW_SPACING = 12.00
MIN_HEIGHT_LOW_SPACING = 5.00


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
        matches.append((ci, ti, float(score)))
    return matches


def rejection_reasons(candidate: Dict[str, Any]) -> List[str]:
    area = float(candidate["areaInStaffSpacesSquared"])
    width = float(candidate["widthInStaffSpaces"])
    height = float(candidate["heightInStaffSpaces"])
    spacing = float(candidate["staffSpacing"])
    reasons: List[str] = []
    if area < LOW_AREA:
        reasons.append("area_below_4_15")
    if area > HIGH_AREA:
        reasons.append("area_above_9_80")
    if width < MIN_WIDTH:
        reasons.append("width_below_2_00_staff_spaces")
    if height > MAX_HEIGHT:
        reasons.append("height_above_6_10_staff_spaces")
    if spacing < LOW_SPACING and height < MIN_HEIGHT_LOW_SPACING:
        reasons.append("low_spacing_requires_height_at_least_5_00")
    return reasons


def feature_summary(values: List[float]) -> Dict[str, float | None]:
    if not values:
        return {"min": None, "median": None, "max": None}
    return {"min": min(values), "median": median(values), "max": max(values)}


def main() -> None:
    if not RAW_PATH.is_file():
        raise RuntimeError("P4.8 raw development artifact missing")
    if not TEACHER_PATH.is_file():
        raise RuntimeError("Development teacher truth missing")
    raw_sha = sha256_file(RAW_PATH)
    teacher_sha = sha256_file(TEACHER_PATH)
    if raw_sha != EXPECTED_RAW_SHA256:
        raise RuntimeError("P4.8 raw artifact SHA mismatch: " + raw_sha)
    if teacher_sha != EXPECTED_TEACHER_SHA256:
        raise RuntimeError("Development teacher SHA mismatch: " + teacher_sha)

    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if raw.get("p4_7HoldoutAccessed") is not False:
        raise RuntimeError("Unsafe provenance: P4.7 holdout access flag is not false")
    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("boxCount") != EXPECTED_TEACHER_BOX_COUNT:
        raise RuntimeError("Development teacher artifact changed")

    print("=" * 72)
    print("P4.8 DEVELOPMENT FILTER REJECTION DIAGNOSTIC")
    print("P4.7 holdout: NOT READ")
    print("P4.6 thresholds: FROZEN / NOT CHANGED")
    print("=" * 72)

    variants_out: Dict[str, Any] = {}
    for variant_name, variant in raw["variants"].items():
        scale = float(variant["scale"])
        matched_total = 0
        matched_kept = 0
        reason_counts = Counter()
        combo_counts = Counter()
        by_label = defaultdict(lambda: {"matched": 0, "kept": 0, "rejected": 0, "reasons": Counter()})
        features = defaultdict(list)
        rejected_examples = []

        for page_id, page in variant["pages"].items():
            candidates = page["candidates"]
            teacher_boxes = teacher["pages"][page_id]["boxes"]
            matches = greedy_match(candidates, teacher_boxes, scale)
            for ci, ti, iou in matches:
                candidate = candidates[ci]
                label = teacher_boxes[ti]["label"]
                matched_total += 1
                by_label[label]["matched"] += 1
                reasons = rejection_reasons(candidate)
                features["staffSpacing"].append(float(candidate["staffSpacing"]))
                features["area"].append(float(candidate["areaInStaffSpacesSquared"]))
                features["width"].append(float(candidate["widthInStaffSpaces"]))
                features["height"].append(float(candidate["heightInStaffSpaces"]))
                if not reasons:
                    matched_kept += 1
                    by_label[label]["kept"] += 1
                else:
                    by_label[label]["rejected"] += 1
                    reason_counts.update(reasons)
                    combo_counts["+".join(sorted(reasons))] += 1
                    by_label[label]["reasons"].update(reasons)
                    if len(rejected_examples) < 20:
                        rejected_examples.append({
                            "pageId": page_id,
                            "label": label,
                            "iou": iou,
                            "reasons": reasons,
                            "staffSpacing": float(candidate["staffSpacing"]),
                            "areaInStaffSpacesSquared": float(candidate["areaInStaffSpacesSquared"]),
                            "widthInStaffSpaces": float(candidate["widthInStaffSpaces"]),
                            "heightInStaffSpaces": float(candidate["heightInStaffSpaces"]),
                        })

        by_label_out = {}
        for label in ("C1", "C3", "C4"):
            item = by_label[label]
            by_label_out[label] = {
                "matchedRawTP": item["matched"],
                "keptByP4_6": item["kept"],
                "rejectedByP4_6": item["rejected"],
                "rejectionReasons": dict(item["reasons"]),
            }

        variants_out[variant_name] = {
            "scale": scale,
            "matchedRawTP": matched_total,
            "keptMatchedTP": matched_kept,
            "rejectedMatchedTP": matched_total - matched_kept,
            "matchedTPKeepRate": matched_kept / matched_total if matched_total else 0.0,
            "rejectionReasonCounts": dict(reason_counts),
            "rejectionReasonCombinations": dict(combo_counts),
            "perSubtype": by_label_out,
            "matchedTPFeatureSummary": {key: feature_summary(vals) for key, vals in features.items()},
            "rejectedExamples": rejected_examples,
        }

        print()
        print(variant_name, "scale=", scale)
        print("  raw matched TP:", matched_total)
        print("  kept by P4.6:", matched_kept)
        print("  rejected matched TP:", matched_total - matched_kept)
        print("  reasons:", dict(reason_counts))
        print("  per subtype:", by_label_out)
        print("  staffSpacing:", feature_summary(features["staffSpacing"]))

    result = {
        "schemaVersion": "stage11.v2d.c-clef-p4_8-filter-rejection-diagnostic.v1",
        "status": "COMPLETE",
        "developmentOnly": True,
        "p4_7HoldoutAccessed": False,
        "thresholdsChanged": False,
        "sourceRawCandidateSha256": raw_sha,
        "teacherTruthSha256": teacher_sha,
        "frozenP4_6Rules": {
            "minimumAreaInStaffSpacesSquared": LOW_AREA,
            "maximumAreaInStaffSpacesSquared": HIGH_AREA,
            "minimumWidthInStaffSpaces": MIN_WIDTH,
            "maximumHeightInStaffSpaces": MAX_HEIGHT,
            "lowStaffSpacingThreshold": LOW_SPACING,
            "minimumHeightWhenLowStaffSpacing": MIN_HEIGHT_LOW_SPACING,
        },
        "variants": variants_out,
        "interpretationBoundary": {
            "diagnosticOnly": True,
            "detectorQualified": False,
            "productionInferenceAuthorized": False,
            "newIndependentHoldoutRequiredAfterAnyNewFilterFreeze": True,
        },
    }
    atomic_json(OUT_PATH, result)
    print()
    print("SAVED:", OUT_PATH)
    print("SHA-256:", sha256_file(OUT_PATH))
    print("detectorQualified: False — development diagnostic only")


if __name__ == "__main__":
    main()
