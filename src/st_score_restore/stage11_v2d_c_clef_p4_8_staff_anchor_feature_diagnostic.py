"""P4.8 development-only C-clef staff-anchor feature diagnostic.

Measures staff-line-relative semantic features for the existing dual-path fused
candidate set. P4.7 holdout is never read. No threshold is selected here.
Feature extraction is completed and frozen before development teacher truth is
opened for TP/FP comparison.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import cv2
import numpy as np

ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL")
SOURCE_ROOT = ROOT / "C_CLEF_SOURCE_PAGES"
ORIG_PATH = ROOT / "P4_C_CLEF_P4_8_DEV_DIAGNOSTIC" / "p4_8_development_scale_candidates.v1.json"
CANON_PATH = ROOT / "P4_C_CLEF_P4_8_CANONICAL_DEV_DIAGNOSTIC" / "p4_8_canonical_scale_candidates.v1.json"
TEACHER_PATH = SOURCE_ROOT / "_ANNOTATIONS" / "c_clef_teacher_boxes.v1.json"
OUT = ROOT / "P4_C_CLEF_P4_8_STAFF_ANCHOR_DEV_DIAGNOSTIC"
UNLABELED_PATH = OUT / "p4_8_staff_anchor_features_unlabeled.v1.json"
RESULT_PATH = OUT / "p4_8_staff_anchor_feature_diagnostic.v1.json"

EXPECTED_ORIG_SHA256 = "a73c2eb5df0466257e27ee33098d2546c3ce7d19665e4f42ac1a4a9b4a47699d"
EXPECTED_CANON_SHA256 = "347a8003282478dde9586a87a9076b2bdf2047d2f0abfe6e7b9514b2e807d3c8"
EXPECTED_TEACHER_SHA256 = "1104d916faaf8d3c391cca9eda0354d21259f722cdcfe0f414c140796a5ffc5b"
EXPECTED_PAGE_COUNT = 29
EXPECTED_TEACHER_BOXES = 71
PRIMARY_IOU = 0.50
DEDUP_IOU = 0.50

P46_LOW_AREA = 4.15
P46_HIGH_AREA = 9.80
P46_MIN_WIDTH = 2.00
P46_MAX_HEIGHT = 6.10
P46_LOW_SPACING = 12.00
P46_MIN_HEIGHT_LOW_SPACING = 5.00

P48_MIN_AREA = 4.15
P48_MAX_AREA = 12.0
P48_MIN_WIDTH = 2.0
P48_MIN_HEIGHT = 3.6
P48_MAX_HEIGHT = 5.8

FEATURE_NAMES = (
    "bboxCenterNearestStaffLineDistanceSpaces",
    "bestStaffLineMirrorSimilarity",
    "bestStaffLineInkBalance",
    "bestStaffLineCenterBandDensity",
    "bestStaffLineOuterToCenterRatio",
    "bestStaffLineSemanticScore",
    "bestStaffLineIndex",
    "bestStaffLineDistanceFromBBoxCenterSpaces",
)


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
    if inter <= 0.0:
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


def source_image_for_page(page_id: str) -> Path:
    matches = list(SOURCE_ROOT.rglob(page_id + ".png"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one source PNG for {page_id}, found {len(matches)}")
    return matches[0]


def resize_for_scale(gray: np.ndarray, scale: float) -> np.ndarray:
    if abs(scale - 1.0) < 1e-12:
        return gray
    h, w = gray.shape[:2]
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    return cv2.resize(gray, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC)


def balance(a: float, b: float) -> float:
    hi = max(a, b)
    return min(a, b) / hi if hi > 1e-12 else 1.0


def semantic_anchor_features(gray: np.ndarray, candidate: Dict[str, Any]) -> Dict[str, float | int]:
    bbox = [float(v) for v in candidate["bbox"]]
    staff_lines = np.asarray(candidate["staffLines"], dtype=float)
    spacing = float(candidate["staffSpacing"])
    if spacing <= 0 or staff_lines.size != 5:
        raise RuntimeError("Invalid staff geometry")

    h, w = gray.shape[:2]
    x1, y1, x2, y2 = bbox
    margin_x = 0.25 * spacing
    margin_y = 2.25 * spacing
    xa = max(0, int(math.floor(x1 - margin_x)))
    xb = min(w, int(math.ceil(x2 + margin_x)))
    ya = max(0, int(math.floor(min(y1 - margin_y, staff_lines[0] - 2.0 * spacing))))
    yb = min(h, int(math.ceil(max(y2 + margin_y, staff_lines[-1] + 2.0 * spacing))))
    if xb <= xa or yb <= ya:
        raise RuntimeError("Invalid anchor crop")

    crop = gray[ya:yb, xa:xb]
    _, ink = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Remove horizontal staff fragments before measuring glyph symmetry.
    line_width = max(5, int(round(1.5 * spacing)))
    horizontal = cv2.morphologyEx(
        ink,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (line_width, 1)),
    )
    removal = cv2.dilate(horizontal, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3)))
    clean = (ink > 0).astype(np.uint8)
    clean[removal > 0] = 0

    center_y = 0.5 * (y1 + y2)
    nearest_distance = float(np.min(np.abs(staff_lines - center_y)) / spacing)

    line_metrics: List[Dict[str, float | int]] = []
    half_span = max(2, int(round(1.75 * spacing)))
    center_half = max(1, int(round(0.22 * spacing)))

    for line_index, line_y_abs in enumerate(staff_lines, start=1):
        line_y = float(line_y_abs) - ya
        cy = int(round(line_y))
        top0 = max(0, cy - half_span)
        top1 = max(0, cy - center_half)
        bot0 = min(clean.shape[0], cy + center_half + 1)
        bot1 = min(clean.shape[0], cy + half_span + 1)
        if top1 <= top0 or bot1 <= bot0:
            continue

        top = clean[top0:top1, :]
        bottom = clean[bot0:bot1, :]
        mh = min(top.shape[0], bottom.shape[0])
        if mh <= 0:
            continue
        top_cmp = top[-mh:, :]
        bottom_cmp = np.flipud(bottom[:mh, :])
        mirror = 1.0 - float(np.mean(np.abs(top_cmp.astype(np.float32) - bottom_cmp.astype(np.float32))))

        top_density = float(np.mean(top_cmp))
        bottom_density = float(np.mean(bottom_cmp))
        ink_balance = balance(top_density, bottom_density)

        c0 = max(0, cy - center_half)
        c1 = min(clean.shape[0], cy + center_half + 1)
        center_density = float(np.mean(clean[c0:c1, :])) if c1 > c0 else 0.0
        outer_density = 0.5 * (top_density + bottom_density)
        outer_to_center = outer_density / max(center_density, 1e-6)

        # Semantic score is measurement only; not an acceptance threshold.
        # C-clef should have balanced upper/lower glyph structure around its anchor line.
        score = 0.55 * mirror + 0.45 * ink_balance
        line_metrics.append({
            "lineIndex": line_index,
            "mirrorSimilarity": mirror,
            "inkBalance": ink_balance,
            "centerBandDensity": center_density,
            "outerToCenterRatio": outer_to_center,
            "semanticScore": score,
            "distanceFromBBoxCenterSpaces": abs(float(line_y_abs) - center_y) / spacing,
        })

    if not line_metrics:
        return {
            "bboxCenterNearestStaffLineDistanceSpaces": nearest_distance,
            "bestStaffLineMirrorSimilarity": 0.0,
            "bestStaffLineInkBalance": 0.0,
            "bestStaffLineCenterBandDensity": 0.0,
            "bestStaffLineOuterToCenterRatio": 0.0,
            "bestStaffLineSemanticScore": 0.0,
            "bestStaffLineIndex": 0,
            "bestStaffLineDistanceFromBBoxCenterSpaces": 99.0,
        }

    best = max(line_metrics, key=lambda item: (item["semanticScore"], -item["distanceFromBBoxCenterSpaces"]))
    return {
        "bboxCenterNearestStaffLineDistanceSpaces": nearest_distance,
        "bestStaffLineMirrorSimilarity": float(best["mirrorSimilarity"]),
        "bestStaffLineInkBalance": float(best["inkBalance"]),
        "bestStaffLineCenterBandDensity": float(best["centerBandDensity"]),
        "bestStaffLineOuterToCenterRatio": float(best["outerToCenterRatio"]),
        "bestStaffLineSemanticScore": float(best["semanticScore"]),
        "bestStaffLineIndex": int(best["lineIndex"]),
        "bestStaffLineDistanceFromBBoxCenterSpaces": float(best["distanceFromBBoxCenterSpaces"]),
    }


def percentile(values: Sequence[float], q: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=float), q)) if values else 0.0


def stats(values: Sequence[float]) -> Dict[str, float | int]:
    if not values:
        return {"count": 0, "mean": 0.0, "p10": 0.0, "median": 0.0, "p90": 0.0}
    arr = np.asarray(values, dtype=float)
    return {
        "count": int(arr.size),
        "mean": float(np.mean(arr)),
        "p10": percentile(values, 10),
        "median": percentile(values, 50),
        "p90": percentile(values, 90),
    }


def directional_auc(tp_values: Sequence[float], fp_values: Sequence[float]) -> Dict[str, Any]:
    if not tp_values or not fp_values:
        return {"auc": 0.5, "separation": 0.5, "direction": "none"}
    wins = ties = total = 0
    for t in tp_values:
        for f in fp_values:
            total += 1
            if t > f:
                wins += 1
            elif t == f:
                ties += 1
    auc = (wins + 0.5 * ties) / total if total else 0.5
    if auc >= 0.5:
        return {"auc": float(auc), "separation": float(auc), "direction": "TP_HIGHER"}
    return {"auc": float(auc), "separation": float(1.0 - auc), "direction": "TP_LOWER"}


def main() -> None:
    for path, expected in ((ORIG_PATH, EXPECTED_ORIG_SHA256), (CANON_PATH, EXPECTED_CANON_SHA256), (TEACHER_PATH, EXPECTED_TEACHER_SHA256)):
        if not path.is_file():
            raise RuntimeError(f"Required artifact missing: {path}")
        if sha256_file(path) != expected:
            raise RuntimeError(f"SHA mismatch for {path.name}: {sha256_file(path)}")

    original = json.loads(ORIG_PATH.read_text(encoding="utf-8"))
    canonical = json.loads(CANON_PATH.read_text(encoding="utf-8"))
    if original.get("p4_7HoldoutAccessed") is not False or canonical.get("p4_7HoldoutAccessed") is not False:
        raise RuntimeError("Unsafe provenance: holdout access flag is not false")

    unlabeled: Dict[str, Any] = {
        "schemaVersion": "stage11.v2d.c-clef-p4_8-staff-anchor-features-unlabeled.v1",
        "status": "COMPLETE",
        "developmentOnly": True,
        "p4_7HoldoutAccessed": False,
        "teacherTruthReadDuringFeatureExtraction": False,
        "featureNames": list(FEATURE_NAMES),
        "variants": {},
    }

    fused_by_variant: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    # Phase A: no teacher truth read.
    for variant_name in sorted(original["variants"]):
        ov = original["variants"][variant_name]
        cv = canonical["variants"][variant_name]
        input_scale = float(ov["scale"])
        variant_pages: Dict[str, Any] = {}
        fused_by_variant[variant_name] = {}

        for page_id, op in ov["pages"].items():
            source = cv2.imread(str(source_image_for_page(page_id)), cv2.IMREAD_GRAYSCALE)
            if source is None:
                raise RuntimeError(f"Unreadable source image: {page_id}")
            gray = resize_for_scale(source, input_scale)
            cp = cv["pages"][page_id]
            factor = float(cp["canonicalFactor"])

            fused: List[Dict[str, Any]] = []
            for c in op["candidates"]:
                if not p46_keep(c):
                    continue
                item = dict(c)
                item["fusionSource"] = "original_p46"
                fused.append(item)

            for c in cp["candidates"]:
                if not p48_keep(c):
                    continue
                item = dict(c)
                item["bbox"] = [float(v) / factor for v in c["bbox"]]
                item["staffLines"] = [float(v) / factor for v in c["staffLines"]]
                item["staffSpacing"] = float(c["staffSpacing"]) / factor
                item["fusionSource"] = "canonical_p48"
                if any(box_iou(item["bbox"], kept["bbox"]) >= DEDUP_IOU for kept in fused):
                    continue
                fused.append(item)

            fused_by_variant[variant_name][page_id] = fused
            records = []
            for idx, candidate in enumerate(fused):
                records.append({
                    "candidateIndex": idx,
                    "fusionSource": candidate["fusionSource"],
                    "bbox": candidate["bbox"],
                    "features": semantic_anchor_features(gray, candidate),
                })
            variant_pages[page_id] = {"candidateCount": len(records), "candidates": records}

        unlabeled["variants"][variant_name] = {"scale": input_scale, "pages": variant_pages}

    atomic_json(UNLABELED_PATH, unlabeled)
    unlabeled_sha = sha256_file(UNLABELED_PATH)
    print("PASS — staff-anchor feature artifact frozen before teacher access")
    print("UNLABELED SHA-256:", unlabeled_sha)

    # Phase B: development labels only after Phase A is frozen.
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("boxCount") != EXPECTED_TEACHER_BOXES:
        raise RuntimeError("Teacher artifact is not the frozen 29-page / 71-box development set")

    result_variants: Dict[str, Any] = {}
    overall_tp: Dict[str, List[float]] = {f: [] for f in FEATURE_NAMES}
    overall_fp: Dict[str, List[float]] = {f: [] for f in FEATURE_NAMES}

    for variant_name in sorted(unlabeled["variants"]):
        v = unlabeled["variants"][variant_name]
        scale = float(v["scale"])
        feature_rows = v["pages"]
        tp_values: Dict[str, List[float]] = {f: [] for f in FEATURE_NAMES}
        fp_values: Dict[str, List[float]] = {f: [] for f in FEATURE_NAMES}
        label_counts = Counter()
        pages_out: Dict[str, Any] = {}

        for page_id, page_features in feature_rows.items():
            fused = fused_by_variant[variant_name][page_id]
            teacher_boxes = teacher["pages"][page_id]["boxes"]
            matches = greedy_match(fused, teacher_boxes, scale)
            matched = {ci: (ti, iou) for ci, ti, iou in matches}
            labeled = []
            for record in page_features["candidates"]:
                ci = int(record["candidateIndex"])
                label = "TP" if ci in matched else "FP"
                source = record["fusionSource"]
                label_counts[f"{label}_{source}"] += 1
                subtype = teacher_boxes[matched[ci][0]]["label"] if ci in matched else None
                labeled.append({
                    "candidateIndex": ci,
                    "fusionSource": source,
                    "label": label,
                    "subtype": subtype,
                    "matchIoU": float(matched[ci][1]) if ci in matched else 0.0,
                })
                for feature in FEATURE_NAMES:
                    value = float(record["features"][feature])
                    (tp_values if label == "TP" else fp_values)[feature].append(value)
                    (overall_tp if label == "TP" else overall_fp)[feature].append(value)
            pages_out[page_id] = {"candidates": labeled}

        summaries = {}
        ranked = []
        for feature in FEATURE_NAMES:
            sep = directional_auc(tp_values[feature], fp_values[feature])
            summaries[feature] = {"tp": stats(tp_values[feature]), "fp": stats(fp_values[feature]), **sep}
            ranked.append({"feature": feature, **sep})
        ranked.sort(key=lambda item: item["separation"], reverse=True)
        result_variants[variant_name] = {
            "labelCountsBySource": dict(label_counts),
            "featureSummaries": summaries,
            "rankedFeatures": ranked,
            "pages": pages_out,
        }

    overall_summaries = {}
    overall_ranked = []
    for feature in FEATURE_NAMES:
        sep = directional_auc(overall_tp[feature], overall_fp[feature])
        overall_summaries[feature] = {"tp": stats(overall_tp[feature]), "fp": stats(overall_fp[feature]), **sep}
        overall_ranked.append({"feature": feature, **sep})
    overall_ranked.sort(key=lambda item: item["separation"], reverse=True)

    payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_8-staff-anchor-feature-diagnostic.v1",
        "status": "COMPLETE",
        "developmentOnly": True,
        "p4_7HoldoutAccessed": False,
        "teacherTruthReadDuringFeatureExtraction": False,
        "thresholdSelected": False,
        "unlabeledFeatureArtifactSha256": unlabeled_sha,
        "featureNames": list(FEATURE_NAMES),
        "overallFeatureSummaries": overall_summaries,
        "overallRankedFeatures": overall_ranked,
        "variants": result_variants,
        "decisionBoundary": {
            "detectorQualified": False,
            "productionInferenceAuthorized": False,
            "overallStage11PassAuthorized": False,
            "newIndependentHoldoutRequiredAfterAnyP4_8Freeze": True,
        },
    }
    atomic_json(RESULT_PATH, payload)

    print("=" * 72)
    print("P4.8 STAFF-ANCHOR FEATURE DIAGNOSTIC COMPLETE")
    print("P4.7 holdout: NOT READ")
    print("thresholdSelected: False")
    print("=" * 72)
    print("TOP OVERALL FEATURES:")
    for item in overall_ranked:
        print(item)
    for variant_name in sorted(result_variants):
        print(variant_name, "TOP FEATURES:", result_variants[variant_name]["rankedFeatures"][:5])
        print("  labels:", result_variants[variant_name]["labelCountsBySource"])
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", sha256_file(RESULT_PATH))
    print("detectorQualified: False — development diagnostic only")


if __name__ == "__main__":
    main()
