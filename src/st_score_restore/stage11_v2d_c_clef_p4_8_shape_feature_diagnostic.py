"""P4.8 development-only C-clef image-shape feature diagnostic.

Purpose:
- preserve the existing frozen original P4.6 path and the development-only
  canonical P4.8 path;
- build the same dual-path fused candidate set used by the prior diagnostic;
- extract image-shape features from candidate crops BEFORE teacher truth is read;
- only after the unlabeled feature artifact is frozen, read development teacher
  truth and compare TP/FP feature distributions.

P4.7 holdout is never read. No threshold is selected in this diagnostic.
No production/qualification/Stage11/Stage12 authorization is implied.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import cv2
import numpy as np

ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL")
SOURCE_ROOT = ROOT / "C_CLEF_SOURCE_PAGES"
ORIG_PATH = ROOT / "P4_C_CLEF_P4_8_DEV_DIAGNOSTIC" / "p4_8_development_scale_candidates.v1.json"
CANON_PATH = ROOT / "P4_C_CLEF_P4_8_CANONICAL_DEV_DIAGNOSTIC" / "p4_8_canonical_scale_candidates.v1.json"
TEACHER_PATH = SOURCE_ROOT / "_ANNOTATIONS" / "c_clef_teacher_boxes.v1.json"
OUT = ROOT / "P4_C_CLEF_P4_8_SHAPE_DEV_DIAGNOSTIC"
UNLABELED_PATH = OUT / "p4_8_shape_features_unlabeled.v1.json"
RESULT_PATH = OUT / "p4_8_shape_feature_diagnostic.v1.json"

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

# Development-only canonical-path filter carried forward unchanged.
P48_MIN_AREA = 4.15
P48_MAX_AREA = 12.0
P48_MIN_WIDTH = 2.0
P48_MIN_HEIGHT = 3.6
P48_MAX_HEIGHT = 5.8

FEATURE_NAMES = (
    "inkDensity",
    "cleanInkDensity",
    "largestComponentFraction",
    "largestContourSolidity",
    "largestContourExtent",
    "componentCount",
    "holeCount",
    "topThirdDensity",
    "middleThirdDensity",
    "bottomThirdDensity",
    "topBottomBalance",
    "middleToOuterDensityRatio",
    "verticalMirrorSimilarity",
    "leftRightBalance",
    "rowPeakCount",
    "columnPeakCount",
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
    return inter / union if union > 0.0 else 0.0


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
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    return cv2.resize(gray, (nw, nh), interpolation=interp)


def density(mask: np.ndarray) -> float:
    return float(np.count_nonzero(mask)) / float(mask.size) if mask.size else 0.0


def balance(a: float, b: float) -> float:
    hi = max(a, b)
    return min(a, b) / hi if hi > 1e-12 else 1.0


def projection_peak_count(values: np.ndarray) -> int:
    if values.size < 5:
        return 0
    x = values.astype(np.float32)
    kernel = np.ones(5, dtype=np.float32) / 5.0
    smoothed = np.convolve(x, kernel, mode="same")
    threshold = float(np.mean(smoothed) + 0.35 * np.std(smoothed))
    count = 0
    for i in range(1, len(smoothed) - 1):
        if smoothed[i] >= threshold and smoothed[i] > smoothed[i - 1] and smoothed[i] >= smoothed[i + 1]:
            count += 1
    return int(count)


def shape_features(gray: np.ndarray, bbox: Sequence[float], spacing: float) -> Dict[str, float | int]:
    h, w = gray.shape[:2]
    x1, y1, x2, y2 = map(float, bbox)
    margin = max(2.0, 0.35 * float(spacing))
    xa = max(0, int(math.floor(x1 - margin)))
    ya = max(0, int(math.floor(y1 - margin)))
    xb = min(w, int(math.ceil(x2 + margin)))
    yb = min(h, int(math.ceil(y2 + margin)))
    if xb <= xa or yb <= ya:
        raise RuntimeError("Invalid candidate crop")

    crop = gray[ya:yb, xa:xb]
    _, ink = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Remove long horizontal staff-line fragments without using teacher truth.
    line_width = max(5, int(round(1.50 * float(spacing))))
    horizontal = cv2.morphologyEx(
        ink,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (line_width, 1)),
    )
    removal = cv2.dilate(horizontal, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3)))
    clean = ink.copy()
    clean[removal > 0] = 0

    # Normalize only for shape statistics; candidate geometry itself is unchanged.
    norm = cv2.resize((clean > 0).astype(np.uint8), (64, 96), interpolation=cv2.INTER_NEAREST)
    raw_norm = cv2.resize((ink > 0).astype(np.uint8), (64, 96), interpolation=cv2.INTER_NEAREST)

    top = density(norm[:32, :])
    middle = density(norm[32:64, :])
    bottom = density(norm[64:, :])
    left = density(norm[:, :32])
    right = density(norm[:, 32:])
    outer = 0.5 * (top + bottom)

    upper = norm[:48, :]
    lower = np.flipud(norm[48:, :])
    vertical_similarity = 1.0 - float(np.mean(np.abs(upper.astype(np.float32) - lower.astype(np.float32))))

    count, _, stats, _ = cv2.connectedComponentsWithStats(norm.astype(np.uint8), connectivity=8)
    component_areas = [int(stats[i, cv2.CC_STAT_AREA]) for i in range(1, count)]
    largest_component_fraction = (max(component_areas) / float(np.count_nonzero(norm))) if component_areas and np.count_nonzero(norm) else 0.0

    contours, hierarchy = cv2.findContours((norm * 255).astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    hole_count = 0
    largest_solidity = 0.0
    largest_extent = 0.0
    largest_area = 0.0
    if hierarchy is not None and contours:
        hierarchy = hierarchy[0]
        hole_count = int(sum(1 for item in hierarchy if int(item[3]) >= 0))
        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area <= largest_area:
                continue
            largest_area = area
            hull = cv2.convexHull(contour)
            hull_area = float(cv2.contourArea(hull))
            x, y, cw, ch = cv2.boundingRect(contour)
            largest_solidity = area / hull_area if hull_area > 0 else 0.0
            largest_extent = area / float(cw * ch) if cw > 0 and ch > 0 else 0.0

    row_projection = np.sum(norm, axis=1)
    col_projection = np.sum(norm, axis=0)

    return {
        "inkDensity": density(raw_norm),
        "cleanInkDensity": density(norm),
        "largestComponentFraction": float(largest_component_fraction),
        "largestContourSolidity": float(largest_solidity),
        "largestContourExtent": float(largest_extent),
        "componentCount": int(max(0, count - 1)),
        "holeCount": int(hole_count),
        "topThirdDensity": float(top),
        "middleThirdDensity": float(middle),
        "bottomThirdDensity": float(bottom),
        "topBottomBalance": float(balance(top, bottom)),
        "middleToOuterDensityRatio": float(middle / outer) if outer > 1e-12 else 0.0,
        "verticalMirrorSimilarity": float(vertical_similarity),
        "leftRightBalance": float(balance(left, right)),
        "rowPeakCount": int(projection_peak_count(row_projection)),
        "columnPeakCount": int(projection_peak_count(col_projection)),
    }


def percentile(values: Sequence[float], q: float) -> float:
    if not values:
        return 0.0
    return float(np.percentile(np.asarray(values, dtype=float), q))


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

    # Phase A: teacher truth is NOT opened here.
    original = json.loads(ORIG_PATH.read_text(encoding="utf-8"))
    canonical = json.loads(CANON_PATH.read_text(encoding="utf-8"))
    if original.get("p4_7HoldoutAccessed") is not False or canonical.get("p4_7HoldoutAccessed") is not False:
        raise RuntimeError("Unsafe provenance: holdout access flag is not false")

    variants_unlabeled: Dict[str, Any] = {}

    for variant_name in sorted(original["variants"]):
        ov = original["variants"][variant_name]
        cv = canonical["variants"][variant_name]
        scale = float(ov["scale"])
        pages_out: Dict[str, Any] = {}

        for page_id, op in ov["pages"].items():
            cp = cv["pages"][page_id]
            factor = float(cp["canonicalFactor"])
            fused: List[Dict[str, Any]] = []

            for candidate in op["candidates"]:
                if not p46_keep(candidate):
                    continue
                item = dict(candidate)
                item["fusionSource"] = "original_p46"
                item["featureSpacing"] = float(candidate["staffSpacing"])
                fused.append(item)

            for candidate in cp["candidates"]:
                if not p48_keep(candidate):
                    continue
                item = dict(candidate)
                item["bbox"] = [float(v) / factor for v in candidate["bbox"]]
                item["fusionSource"] = "canonical_p48"
                item["featureSpacing"] = float(candidate["staffSpacing"]) / factor
                if any(box_iou(item["bbox"], kept["bbox"]) >= DEDUP_IOU for kept in fused):
                    continue
                fused.append(item)

            source_path = source_image_for_page(page_id)
            gray = cv2.imread(str(source_path), cv2.IMREAD_GRAYSCALE)
            if gray is None:
                raise RuntimeError("Unreadable source image: " + str(source_path))
            scaled = resize_for_scale(gray, scale)

            candidate_rows = []
            for index, candidate in enumerate(fused):
                candidate_rows.append({
                    "candidateIndex": int(index),
                    "bbox": [float(v) for v in candidate["bbox"]],
                    "fusionSource": candidate["fusionSource"],
                    "features": shape_features(scaled, candidate["bbox"], float(candidate["featureSpacing"])),
                })

            pages_out[page_id] = {
                "candidateCount": len(candidate_rows),
                "sourceImageSha256": sha256_file(source_path),
                "candidates": candidate_rows,
            }
            print(f"FEATURES {variant_name} {page_id}: {len(candidate_rows)}")

        variants_unlabeled[variant_name] = {"scale": scale, "pages": pages_out}

    unlabeled = {
        "schemaVersion": "stage11.v2d.c-clef-p4_8-shape-features-unlabeled.v1",
        "status": "PHASE_A_COMPLETE",
        "developmentOnly": True,
        "p4_7HoldoutAccessed": False,
        "teacherTruthReadDuringFeatureExtraction": False,
        "featureNames": list(FEATURE_NAMES),
        "variants": variants_unlabeled,
    }
    atomic_json(UNLABELED_PATH, unlabeled)
    unlabeled_sha = sha256_file(UNLABELED_PATH)
    print("PASS — Phase A image features frozen before teacher access")
    print("UNLABELED SHA-256:", unlabeled_sha)

    # Phase B: development teacher truth is opened only after Phase A is frozen.
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("boxCount") != EXPECTED_TEACHER_BOXES:
        raise RuntimeError("Teacher artifact is not frozen 29-page / 71-box development truth")

    variants_labeled: Dict[str, Any] = {}
    overall_tp: Dict[str, List[float]] = {name: [] for name in FEATURE_NAMES}
    overall_fp: Dict[str, List[float]] = {name: [] for name in FEATURE_NAMES}

    for variant_name, variant in variants_unlabeled.items():
        scale = float(variant["scale"])
        tp_values: Dict[str, List[float]] = {name: [] for name in FEATURE_NAMES}
        fp_values: Dict[str, List[float]] = {name: [] for name in FEATURE_NAMES}
        labels_by_source = Counter()
        page_labels: Dict[str, Any] = {}

        for page_id, page in variant["pages"].items():
            candidates = page["candidates"]
            teacher_boxes = teacher["pages"][page_id]["boxes"]
            matches = greedy_match(candidates, teacher_boxes, scale)
            match_by_candidate = {ci: (ti, score) for ci, ti, score in matches}
            labeled_candidates = []

            for ci, candidate in enumerate(candidates):
                is_tp = ci in match_by_candidate
                label = "TP" if is_tp else "FP"
                labels_by_source[label + "_" + candidate["fusionSource"]] += 1
                if is_tp:
                    teacher_index, iou = match_by_candidate[ci]
                    subtype = teacher_boxes[teacher_index]["label"]
                else:
                    iou = 0.0
                    subtype = None

                for name in FEATURE_NAMES:
                    value = float(candidate["features"][name])
                    target = tp_values if is_tp else fp_values
                    target[name].append(value)
                    (overall_tp if is_tp else overall_fp)[name].append(value)

                labeled_candidates.append({
                    "candidateIndex": ci,
                    "label": label,
                    "subtype": subtype,
                    "matchIoU": float(iou),
                    "fusionSource": candidate["fusionSource"],
                })

            page_labels[page_id] = {"candidates": labeled_candidates}

        summaries = {}
        for name in FEATURE_NAMES:
            summaries[name] = {
                "tp": stats(tp_values[name]),
                "fp": stats(fp_values[name]),
                "separation": directional_auc(tp_values[name], fp_values[name]),
            }
        ranked = sorted(
            ({"feature": name, **summaries[name]["separation"]} for name in FEATURE_NAMES),
            key=lambda item: item["separation"],
            reverse=True,
        )
        variants_labeled[variant_name] = {
            "labelCountsBySource": dict(labels_by_source),
            "featureSummaries": summaries,
            "rankedFeatures": ranked,
            "pages": page_labels,
        }

    overall = {}
    for name in FEATURE_NAMES:
        overall[name] = {
            "tp": stats(overall_tp[name]),
            "fp": stats(overall_fp[name]),
            "separation": directional_auc(overall_tp[name], overall_fp[name]),
        }
    overall_ranked = sorted(
        ({"feature": name, **overall[name]["separation"]} for name in FEATURE_NAMES),
        key=lambda item: item["separation"],
        reverse=True,
    )

    result = {
        "schemaVersion": "stage11.v2d.c-clef-p4_8-shape-feature-diagnostic.v1",
        "status": "COMPLETE",
        "developmentOnly": True,
        "p4_7HoldoutAccessed": False,
        "teacherTruthReadDuringFeatureExtraction": False,
        "unlabeledFeatureArtifactSha256": unlabeled_sha,
        "teacherSha256": EXPECTED_TEACHER_SHA256,
        "thresholdSelected": False,
        "featureNames": list(FEATURE_NAMES),
        "variants": variants_labeled,
        "overallFeatureSummaries": overall,
        "overallRankedFeatures": overall_ranked,
        "decisionBoundary": {
            "detectorQualified": False,
            "productionInferenceAuthorized": False,
            "overallStage11PassAuthorized": False,
            "newIndependentHoldoutRequiredAfterAnyFutureP4_8Freeze": True,
        },
    }
    atomic_json(RESULT_PATH, result)

    print("=" * 72)
    print("P4.8 C-CLEF SHAPE FEATURE DIAGNOSTIC COMPLETE")
    print("P4.7 holdout: NOT READ")
    print("thresholdSelected: False")
    print("=" * 72)
    print("TOP OVERALL FEATURES:")
    for item in overall_ranked[:8]:
        print(" ", item)
    for variant_name, payload in variants_labeled.items():
        print(variant_name, "TOP FEATURES:", payload["rankedFeatures"][:6])
        print("  labels:", payload["labelCountsBySource"])
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", sha256_file(RESULT_PATH))
    print("detectorQualified: False — development diagnostic only")


if __name__ == "__main__":
    main()
