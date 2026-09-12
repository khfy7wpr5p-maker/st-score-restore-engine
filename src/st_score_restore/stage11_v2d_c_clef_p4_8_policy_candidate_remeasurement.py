"""P4.8 development-only C-clef policy candidate remeasurement.

This runner remeasures a frozen P4.8 candidate policy on the existing 29-page
DEVELOPMENT corpus and synthetic scale variants only. P4.7 holdout is not read.
Teacher truth is used only for development evaluation after candidate policy
construction. The resulting metrics are NOT qualification evidence.
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
SHAPE_PATH = ROOT / "P4_C_CLEF_P4_8_SHAPE_DEV_DIAGNOSTIC" / "p4_8_shape_features_unlabeled.v1.json"
TEACHER_PATH = ROOT / "C_CLEF_SOURCE_PAGES" / "_ANNOTATIONS" / "c_clef_teacher_boxes.v1.json"
OUT = ROOT / "P4_C_CLEF_P4_8_POLICY_DEV_REMEASUREMENT"
RESULT_PATH = OUT / "p4_8_policy_candidate_development_remeasurement.v1.json"

EXPECTED_ORIG_SHA256 = "a73c2eb5df0466257e27ee33098d2546c3ce7d19665e4f42ac1a4a9b4a47699d"
EXPECTED_CANON_SHA256 = "347a8003282478dde9586a87a9076b2bdf2047d2f0abfe6e7b9514b2e807d3c8"
EXPECTED_SHAPE_SHA256 = "393122d3e33df63d4871a39c6a94af594490752e12544e5500d3b795df35b19e"
EXPECTED_TEACHER_SHA256 = "1104d916faaf8d3c391cca9eda0354d21259f722cdcfe0f414c140796a5ffc5b"
EXPECTED_PAGE_COUNT = 29
EXPECTED_TEACHER_BOXES = 71
PRIMARY_IOU = 0.50
DEDUP_IOU = 0.50

# Frozen original P4.6 filter.
P46_LOW_AREA = 4.15
P46_HIGH_AREA = 9.80
P46_MIN_WIDTH = 2.00
P46_MAX_HEIGHT = 6.10
P46_LOW_SPACING = 12.00
P46_MIN_HEIGHT_LOW_SPACING = 5.00

# Development-only canonical P4.8 filter carried forward unchanged.
P48_MIN_AREA = 4.15
P48_MAX_AREA = 12.0
P48_MIN_WIDTH = 2.0
P48_MIN_HEIGHT = 3.6
P48_MAX_HEIGHT = 5.8

# P4.8 candidate policy selected from broad development plateaus.
ROUTE_SPACING_PX = 12.0
VERTICAL_MIRROR_MIN = 0.86
BOTTOM_PAD_STAFF_SPACES = 0.25

EXPECTED = {
    "scale_0_50": (67, 11, 4),
    "scale_0_75": (67, 7, 4),
    "scale_1_00": (68, 3, 3),
}


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


def metric(tp: int, fp: int, fn: int) -> Dict[str, float | int]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def bbox_close(a: Sequence[float], b: Sequence[float], eps: float = 1e-6) -> bool:
    return len(a) == len(b) and max(abs(float(x) - float(y)) for x, y in zip(a, b)) <= eps


def shape_vertical_mirror(shape_page: Dict[str, Any], bbox: Sequence[float]) -> float:
    matches = []
    for item in shape_page["candidates"]:
        if item.get("fusionSource") != "canonical_p48":
            continue
        if bbox_close(item["bbox"], bbox):
            matches.append(float(item["features"]["verticalMirrorSimilarity"]))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one canonical shape-feature match, got {len(matches)} for bbox={bbox}")
    return matches[0]


def pad_bottom(candidate: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(candidate)
    bbox = list(map(float, item["bbox"]))
    spacing = float(item["spacingInput"])
    bbox[3] += BOTTOM_PAD_STAFF_SPACES * spacing
    item["bbox"] = bbox
    return item


def build_page_candidates(
    op: Dict[str, Any],
    cp: Dict[str, Any],
    shape_page: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, int | float | str]]:
    canonical_factor = float(cp["canonicalFactor"])
    pre_spacing = float(cp["preCanonicalMedianStaffSpacing"])
    accepted: List[Dict[str, Any]] = []
    gated_added = 0
    gated_rejected = 0
    dedup_rejected = 0

    if pre_spacing < ROUTE_SPACING_PX:
        path = "canonical_only_low_spacing"
        for candidate in cp["candidates"]:
            if not p48_keep(candidate):
                continue
            item = dict(candidate)
            item["bbox"] = [float(v) / canonical_factor for v in candidate["bbox"]]
            item["spacingInput"] = float(candidate["staffSpacing"]) / canonical_factor
            item["policySource"] = "canonical_p48"
            accepted.append(pad_bottom(item))
    else:
        path = "original_plus_gated_canonical"
        originals: List[Dict[str, Any]] = []
        for candidate in op["candidates"]:
            if not p46_keep(candidate):
                continue
            item = dict(candidate)
            item["bbox"] = list(map(float, candidate["bbox"]))
            item["spacingInput"] = float(candidate["staffSpacing"])
            item["policySource"] = "original_p46"
            originals.append(item)

        additions: List[Dict[str, Any]] = []
        for candidate in cp["candidates"]:
            if not p48_keep(candidate):
                continue
            item = dict(candidate)
            item["bbox"] = [float(v) / canonical_factor for v in candidate["bbox"]]
            item["spacingInput"] = float(candidate["staffSpacing"]) / canonical_factor
            item["policySource"] = "canonical_p48"
            if any(box_iou(item["bbox"], original["bbox"]) >= DEDUP_IOU for original in originals):
                dedup_rejected += 1
                continue
            mirror = shape_vertical_mirror(shape_page, item["bbox"])
            item["verticalMirrorSimilarity"] = mirror
            if mirror < VERTICAL_MIRROR_MIN:
                gated_rejected += 1
                continue
            gated_added += 1
            additions.append(item)

        accepted = [pad_bottom(item) for item in originals + additions]

    diagnostics = {
        "path": path,
        "preCanonicalMedianStaffSpacing": pre_spacing,
        "acceptedCount": len(accepted),
        "gatedCanonicalAdded": gated_added,
        "gatedCanonicalRejected": gated_rejected,
        "deduplicatedCanonicalRejected": dedup_rejected,
    }
    return accepted, diagnostics


def main() -> None:
    for path, expected in (
        (ORIG_PATH, EXPECTED_ORIG_SHA256),
        (CANON_PATH, EXPECTED_CANON_SHA256),
        (SHAPE_PATH, EXPECTED_SHAPE_SHA256),
        (TEACHER_PATH, EXPECTED_TEACHER_SHA256),
    ):
        if not path.is_file():
            raise RuntimeError(f"Required artifact missing: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"SHA mismatch for {path.name}: {actual}")

    original = json.loads(ORIG_PATH.read_text(encoding="utf-8"))
    canonical = json.loads(CANON_PATH.read_text(encoding="utf-8"))
    shape = json.loads(SHAPE_PATH.read_text(encoding="utf-8"))

    if original.get("p4_7HoldoutAccessed") is not False or canonical.get("p4_7HoldoutAccessed") is not False:
        raise RuntimeError("Unsafe provenance: P4.7 holdout access flag must remain false")
    if shape.get("p4_7HoldoutAccessed") is not False or shape.get("teacherTruthReadDuringFeatureExtraction") is not False:
        raise RuntimeError("Unsafe shape-feature provenance")

    # Phase A: build and freeze policy candidates before teacher access.
    frozen_variants: Dict[str, Any] = {}
    for variant_name in sorted(original["variants"]):
        ov = original["variants"][variant_name]
        cv = canonical["variants"][variant_name]
        sv = shape["variants"][variant_name]
        pages_out: Dict[str, Any] = {}
        for page_id, op in ov["pages"].items():
            cp = cv["pages"][page_id]
            shape_page = sv["pages"][page_id]
            candidates, diagnostics = build_page_candidates(op, cp, shape_page)
            pages_out[page_id] = {
                "candidates": candidates,
                "diagnostics": diagnostics,
            }
        frozen_variants[variant_name] = {
            "scale": float(ov["scale"]),
            "pages": pages_out,
        }

    OUT.mkdir(parents=True, exist_ok=True)
    frozen_path = OUT / "p4_8_policy_candidates_frozen_before_teacher.v1.json"
    atomic_json(frozen_path, {
        "schemaVersion": "stage11.v2d.c-clef-p4_8-policy-candidates-frozen.v1",
        "developmentOnly": True,
        "p4_7HoldoutAccessed": False,
        "teacherTruthReadDuringCandidateConstruction": False,
        "policy": {
            "routeSpacingPx": ROUTE_SPACING_PX,
            "verticalMirrorMinimum": VERTICAL_MIRROR_MIN,
            "bottomPaddingStaffSpaces": BOTTOM_PAD_STAFF_SPACES,
        },
        "variants": frozen_variants,
    })
    frozen_sha = sha256_file(frozen_path)
    print("PASS — policy candidates frozen before teacher access")
    print("FROZEN SHA-256:", frozen_sha)

    # Phase B: development-only teacher evaluation.
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("boxCount") != EXPECTED_TEACHER_BOXES:
        raise RuntimeError("Teacher artifact is not the frozen 29-page / 71-box development set")

    results: Dict[str, Any] = {}
    all_targets_met = True
    for variant_name in sorted(frozen_variants):
        variant = frozen_variants[variant_name]
        scale = float(variant["scale"])
        pooled_tp = pooled_fp = pooled_fn = 0
        subtype_total = Counter()
        subtype_tp = Counter()
        per_page: Dict[str, Any] = {}

        for page_id, page in variant["pages"].items():
            candidates = page["candidates"]
            teacher_boxes = teacher["pages"][page_id]["boxes"]
            for box in teacher_boxes:
                subtype_total[box["label"]] += 1
            matches = greedy_match(candidates, teacher_boxes, scale)
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
                "metrics": metric(tp, fp, fn),
                "diagnostics": page["diagnostics"],
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
        target_met = (
            pooled["precision"] >= 0.80
            and pooled["recall"] >= 0.90
            and all(subtype[label]["recall"] >= 0.80 for label in subtype)
        )
        all_targets_met = all_targets_met and target_met
        results[variant_name] = {
            "pooled": pooled,
            "subtype": subtype,
            "targetMet": target_met,
            "perPage": per_page,
        }

        actual_tuple = (pooled_tp, pooled_fp, pooled_fn)
        if actual_tuple != EXPECTED[variant_name]:
            raise RuntimeError(f"Unexpected metrics for {variant_name}: {actual_tuple} != {EXPECTED[variant_name]}")

    payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_8-policy-candidate-development-remeasurement.v1",
        "status": "COMPLETE",
        "developmentOnly": True,
        "p4_7HoldoutAccessed": False,
        "thresholdsSelectedAfterDevelopmentReview": True,
        "independentQualificationEvidence": False,
        "newIndependentHoldoutRequiredAfterFreeze": True,
        "p4_7HoldoutMustNotBeReusedForQualification": True,
        "sourceArtifacts": {
            "originalCandidatesSha256": EXPECTED_ORIG_SHA256,
            "canonicalCandidatesSha256": EXPECTED_CANON_SHA256,
            "shapeFeaturesSha256": EXPECTED_SHAPE_SHA256,
            "teacherSha256": EXPECTED_TEACHER_SHA256,
            "frozenPolicyCandidatesSha256": frozen_sha,
        },
        "policy": {
            "routeSpacingPx": ROUTE_SPACING_PX,
            "verticalMirrorMinimum": VERTICAL_MIRROR_MIN,
            "bottomPaddingStaffSpaces": BOTTOM_PAD_STAFF_SPACES,
            "dedupIoU": DEDUP_IOU,
        },
        "variants": results,
        "developmentTargetMetAllScales": all_targets_met,
        "decisionBoundary": {
            "detectorQualified": False,
            "productionInferenceAuthorized": False,
            "overallStage11PassAuthorized": False,
            "stage12Authorized": False,
        },
    }
    atomic_json(RESULT_PATH, payload)

    print("=" * 76)
    print("P4.8 POLICY CANDIDATE DEVELOPMENT REMEASUREMENT COMPLETE")
    print("P4.7 holdout: NOT READ")
    print("=" * 76)
    for variant_name, result in results.items():
        print(variant_name)
        print("  POOLED:", result["pooled"])
        print("  SUBTYPE:", result["subtype"])
        print("  TARGET MET:", result["targetMet"])
    print("DEVELOPMENT TARGET MET ALL SCALES:", all_targets_met)
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", sha256_file(RESULT_PATH))
    print("detectorQualified: False — development evidence only")


if __name__ == "__main__":
    main()
