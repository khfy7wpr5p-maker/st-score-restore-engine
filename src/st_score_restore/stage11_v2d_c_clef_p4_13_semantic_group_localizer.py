"""P4.13 development-only C-clef semantic grouping and source-ink localization.

P4.12 retained 7,204 broad source-semantic proposals while preserving 38/38
localization recall on the already-spent P4.9 development set. P4.13 collapses
only proposal variants that originate from the same P4.11 source component
group. Every variant receives a deterministic source-only semantic score before
a representative is selected; no first-wins or arbitrary NMS is used.

The representative is then localized to nearby source ink after staff-line
suppression. Phase A freezes all groups, scores, and refined boxes before any
teacher truth is read. Phase B may use the already-spent P4.9 teacher boxes only
for development diagnostics. Scores are heuristic and explicitly uncalibrated.
This stage is not qualification evidence and must not open a new holdout.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import cv2
import numpy as np

from st_score_restore.stage11_v2d_c_clef_p4_11_glyph_proposal_generator import (
    EXPECTED_MANIFEST_SHA256,
    EXPECTED_PAGE_COUNT,
    EXPECTED_TEACHER_BOX_COUNT,
    EXPECTED_TEACHER_SHA256,
    EXPECTED_V32_RAW_SHA256,
    PREPARED,
    ROOT,
    TEACHER_PATH,
    V32_RAW_CANDIDATE_COUNT,
    V32_RAW_PATH,
    atomic_json,
    generate_page_proposals,
    greedy_match,
    reconstruct_staffs_from_frozen_candidates,
    sha256_file,
)
from st_score_restore.stage11_v2d_c_clef_p4_12_semantic_sieve import (
    semantic_features,
    sieve_keep,
)

OUT = ROOT / "_P4_13_SEMANTIC_GROUP_LOCALIZER_DEV"
SOURCE_GROUP_PATH = OUT / "p4_13_source_group_localizations_before_teacher.v1.json"
RESULT_PATH = OUT / "p4_13_semantic_group_localizer_result.v1.json"

EXPECTED_P4_11_PROPOSAL_COUNT = 26732
EXPECTED_P4_12_RETAINED_COUNT = 7204
PRIMARY_IOU = 0.50

# Source-only localization constants. They are frozen by this P4.13 runner and
# are not qualification thresholds.
REFINE_MARGIN_SPACES = 0.20
REFINE_PAD_SPACES = 0.12
REFINE_HLINE_KERNEL_SPACES = 1.50
REFINE_HLINE_REMOVAL_PX = 3
MIN_COMPONENT_AREA_SPACES2 = 0.01
MAX_SEED_DISTANCE_SPACES = 2.50
MERGE_GAP_SPACES = 0.55

# Explicit semantic-score weights. The score ranks variants inside one exact
# source component group only. It is not a calibrated C-clef probability.
SCORE_WEIGHTS = {
    "leftVerticalRunP90": 0.22,
    "leftVerticalRunMax": 0.13,
    "anchorInkBalance": 0.15,
    "leftLobeBalance": 0.12,
    "cleanInkDensity": 0.12,
    "rawInkDensity": 0.08,
    "nonStaffInkRetention": 0.08,
    "xOffsetAlignment": 0.06,
    "anchorRankPrior": 0.04,
}


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _feature_scale(value: float, reference: float) -> float:
    if reference <= 0.0:
        raise ValueError("reference must be positive")
    return clamp01(float(value) / float(reference))


def semantic_confidence_score(features: Dict[str, Any], proposal: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """Return deterministic [0,1] source-only ranking score and components.

    This score is deliberately not fitted or calibrated against teacher labels.
    It only ranks alternative boxes/anchors generated from one exact source
    component group, so no cross-component detection decision is made here.
    """
    raw_density = max(0.0, float(features["inkDensity"]))
    clean_density = max(0.0, float(features["cleanInkDensity"]))
    left_mid = max(0.0, float(features["leftMidDensity"]))
    left_bottom = max(0.0, float(features["leftBottomDensity"]))
    lobe_hi = max(left_mid, left_bottom)
    lobe_balance = min(left_mid, left_bottom) / lobe_hi if lobe_hi > 1e-12 else 0.0
    retention = clean_density / raw_density if raw_density > 1e-12 else 0.0
    offset = abs(float(proposal.get("xOffsetStaffSpaces", 0.0)))
    anchor_rank = int(proposal.get("anchorRank", 1))

    parts = {
        "leftVerticalRunP90": _feature_scale(float(features["leftVerticalRunP90"]), 0.45),
        "leftVerticalRunMax": _feature_scale(float(features["leftVerticalRunMax"]), 0.75),
        "anchorInkBalance": clamp01(float(features["anchorInkBalance"])),
        "leftLobeBalance": clamp01(lobe_balance),
        "cleanInkDensity": _feature_scale(clean_density, 0.35),
        "rawInkDensity": _feature_scale(raw_density, 0.50),
        "nonStaffInkRetention": clamp01(retention),
        "xOffsetAlignment": float(math.exp(-offset / 1.50)),
        "anchorRankPrior": 1.0 if anchor_rank == 1 else 0.75,
    }
    score = sum(SCORE_WEIGHTS[name] * parts[name] for name in SCORE_WEIGHTS)
    return clamp01(score), parts


def _bbox_gap(a: Sequence[float], b: Sequence[float]) -> float:
    ax1, ay1, ax2, ay2 = map(float, a)
    bx1, by1, bx2, by2 = map(float, b)
    dx = max(0.0, bx1 - ax2, ax1 - bx2)
    dy = max(0.0, by1 - ay2, ay1 - by2)
    return float(math.hypot(dx, dy))


def _union_bbox(boxes: Sequence[Sequence[float]]) -> List[float]:
    if not boxes:
        raise ValueError("boxes must not be empty")
    return [
        min(float(box[0]) for box in boxes),
        min(float(box[1]) for box in boxes),
        max(float(box[2]) for box in boxes),
        max(float(box[3]) for box in boxes),
    ]


def refine_bbox_to_source_ink(
    gray: np.ndarray,
    proposal: Dict[str, Any],
    staff: Dict[str, Any],
) -> Dict[str, Any]:
    """Tighten one representative box to nearby non-staff source ink.

    Connected components are seeded by proximity to the P4.11 source component
    centre and then expanded only through nearby source-ink fragments. No
    teacher coordinates, subtype labels, restored image, or detector output are
    consulted.
    """
    height, width = gray.shape[:2]
    spacing = float(proposal["staffSpacing"])
    if spacing <= 0.0 or not math.isfinite(spacing):
        raise RuntimeError("Invalid proposal staff spacing")

    x1, y1, x2, y2 = map(float, proposal["bbox"])
    margin = max(2.0, REFINE_MARGIN_SPACES * spacing)
    xa = max(0, int(math.floor(x1 - margin)))
    ya = max(0, int(math.floor(y1 - margin)))
    xb = min(width, int(math.ceil(x2 + margin)))
    yb = min(height, int(math.ceil(y2 + margin)))
    if xb <= xa or yb <= ya:
        raise RuntimeError("Invalid refinement crop")

    crop = gray[ya:yb, xa:xb]
    _, ink = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    line_width = max(5, int(round(REFINE_HLINE_KERNEL_SPACES * spacing)))
    horizontal = cv2.morphologyEx(
        ink,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (line_width, 1)),
    )
    removal = cv2.dilate(
        horizontal,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, REFINE_HLINE_REMOVAL_PX)),
    )
    clean = ink.copy()
    clean[removal > 0] = 0

    count, _, stats, _ = cv2.connectedComponentsWithStats((clean > 0).astype(np.uint8), connectivity=8)
    min_area = max(2.0, MIN_COMPONENT_AREA_SPACES2 * spacing * spacing)
    components: List[Dict[str, Any]] = []
    for component_id in range(1, count):
        area = float(stats[component_id, cv2.CC_STAT_AREA])
        if area < min_area:
            continue
        lx = float(stats[component_id, cv2.CC_STAT_LEFT])
        ly = float(stats[component_id, cv2.CC_STAT_TOP])
        lw = float(stats[component_id, cv2.CC_STAT_WIDTH])
        lh = float(stats[component_id, cv2.CC_STAT_HEIGHT])
        box = [float(xa) + lx, float(ya) + ly, float(xa) + lx + lw, float(ya) + ly + lh]
        components.append({"bbox": box, "area": area})

    if not components:
        return {
            "bbox": [x1, y1, x2, y2],
            "supportFound": False,
            "selectedComponentCount": 0,
            "supportPixelArea": 0,
            "reason": "NO_NON_STAFF_COMPONENT",
        }

    target_x = float(proposal["componentGroupXCenter"])
    target_y = float(proposal["componentGroupYCenter"])

    def center_distance(item: Dict[str, Any]) -> float:
        bx1, by1, bx2, by2 = item["bbox"]
        cx = 0.5 * (bx1 + bx2)
        cy = 0.5 * (by1 + by2)
        return float(math.hypot(cx - target_x, cy - target_y))

    seed_index = min(range(len(components)), key=lambda index: (center_distance(components[index]), index))
    seed_distance = center_distance(components[seed_index]) / spacing
    if seed_distance > MAX_SEED_DISTANCE_SPACES:
        return {
            "bbox": [x1, y1, x2, y2],
            "supportFound": False,
            "selectedComponentCount": 0,
            "supportPixelArea": 0,
            "reason": "NO_COMPONENT_NEAR_SOURCE_GROUP_CENTER",
            "nearestDistanceSpaces": float(seed_distance),
        }

    selected = {seed_index}
    union = list(components[seed_index]["bbox"])
    max_gap = MERGE_GAP_SPACES * spacing
    changed = True
    while changed:
        changed = False
        for index, item in enumerate(components):
            if index in selected:
                continue
            if _bbox_gap(union, item["bbox"]) <= max_gap:
                selected.add(index)
                union = _union_bbox([union, item["bbox"]])
                changed = True

    pad = max(1.0, REFINE_PAD_SPACES * spacing)
    refined = [
        max(0.0, union[0] - pad),
        max(0.0, union[1] - pad),
        min(float(width), union[2] + pad),
        min(float(height), union[3] + pad),
    ]
    pixel_area = int(sum(components[index]["area"] for index in selected))
    return {
        "bbox": [float(value) for value in refined],
        "supportFound": True,
        "selectedComponentCount": int(len(selected)),
        "supportPixelArea": pixel_area,
        "supportAreaSpaces2": float(pixel_area / (spacing * spacing)),
        "nearestDistanceSpaces": float(seed_distance),
        "reason": "SOURCE_INK_REFINED",
    }


def group_page_records(
    gray: np.ndarray,
    retained_records: Sequence[Dict[str, Any]],
    staff_by_index: Dict[int, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Rank then collapse variants sharing one exact P4.11 source component group."""
    buckets: Dict[Tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)
    for record in retained_records:
        key = (int(record["staffIndex"]), int(record["componentGroupIndex"]))
        buckets[key].append(record)

    groups: List[Dict[str, Any]] = []
    for group_index, key in enumerate(sorted(buckets)):
        members = buckets[key]
        scored: List[Tuple[float, float, int, int, Dict[str, Any], Dict[str, float]]] = []
        for record in members:
            score, parts = semantic_confidence_score(record["features"], record)
            scored.append(
                (
                    score,
                    -abs(float(record["xOffsetStaffSpaces"])),
                    -int(record["anchorRank"]),
                    -int(record["proposalIndex"]),
                    record,
                    parts,
                )
            )
        scored.sort(key=lambda item: item[:4], reverse=True)
        score, _, _, _, representative, score_parts = scored[0]
        staff = staff_by_index[int(representative["staffIndex"])]
        refinement = refine_bbox_to_source_ink(gray, representative, staff)
        groups.append(
            {
                "groupIndex": int(group_index),
                "staffIndex": int(key[0]),
                "componentGroupIndex": int(key[1]),
                "componentGroupXCenter": float(representative["componentGroupXCenter"]),
                "componentGroupYCenter": float(representative["componentGroupYCenter"]),
                "memberCount": int(len(members)),
                "memberProposalIndexes": sorted(int(item["proposalIndex"]) for item in members),
                "memberAnchors": sorted({str(item["anchor"]) for item in members}),
                "semanticConfidenceScore": float(score),
                "semanticConfidenceCalibrated": False,
                "scoreComponents": score_parts,
                "representative": {
                    "proposalIndex": int(representative["proposalIndex"]),
                    "bbox": [float(value) for value in representative["bbox"]],
                    "anchor": str(representative["anchor"]),
                    "anchorRank": int(representative["anchorRank"]),
                    "sizeTag": str(representative["sizeTag"]),
                    "xOffsetStaffSpaces": float(representative["xOffsetStaffSpaces"]),
                },
                "refinement": refinement,
                "bbox": [float(value) for value in refinement["bbox"]],
            }
        )
    return groups


def metric(tp: int, fp: int, fn: int) -> Dict[str, float | int]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def _evaluate_candidates(
    candidates: Sequence[Dict[str, Any]],
    teacher_boxes: Sequence[Dict[str, Any]],
) -> Tuple[Dict[str, float | int], List[Tuple[int, int, float]]]:
    matches = greedy_match(candidates, teacher_boxes)
    return metric(len(matches), len(candidates) - len(matches), len(teacher_boxes) - len(matches)), matches


def main() -> None:
    manifest_path = PREPARED / "c_clef_p4_9_holdout_source_page_manifest.v1.json"
    for path, expected in (
        (manifest_path, EXPECTED_MANIFEST_SHA256),
        (V32_RAW_PATH, EXPECTED_V32_RAW_SHA256),
    ):
        if not path.is_file():
            raise RuntimeError(f"Required frozen artifact missing: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"SHA mismatch for {path.name}: {actual}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frozen_v32 = json.loads(V32_RAW_PATH.read_text(encoding="utf-8"))
    if manifest.get("pageCount") != EXPECTED_PAGE_COUNT or len(manifest.get("pages", [])) != EXPECTED_PAGE_COUNT:
        raise RuntimeError("Expected frozen 11-page P4.9 manifest")
    if manifest.get("detectorOutputsAccessed") is not False:
        raise RuntimeError("Unsafe source manifest provenance")
    if frozen_v32.get("teacherTruthReadDuringCandidateGeneration") is not False:
        raise RuntimeError("Unsafe v3.2 candidate provenance")
    if int(frozen_v32.get("candidateCountTotal", -1)) != V32_RAW_CANDIDATE_COUNT:
        raise RuntimeError("Unexpected v3.2 frozen candidate count")

    print("=" * 76)
    print("P4.13 C-CLEF SEMANTIC GROUP LOCALIZER — DEVELOPMENT ONLY")
    print("Phase A: source only; semantic score before exact-group collapse; teacher CLOSED")
    print("=" * 76)

    manifest_pages = {str(page["pageId"]): page for page in manifest["pages"]}
    v32_pages = frozen_v32.get("pages", {})
    pages_out: Dict[str, Any] = {}
    proposal_total = retained_total = group_total = 0

    for page_id in sorted(manifest_pages):
        page = manifest_pages[page_id]
        if page_id not in v32_pages:
            raise RuntimeError(f"v3.2 page missing: {page_id}")
        image_path = PREPARED / str(page["imagePath"])
        if not image_path.is_file():
            raise RuntimeError(f"Source image missing: {image_path}")
        expected_image_sha = str(page["imageSha256"])
        actual_image_sha = sha256_file(image_path)
        if actual_image_sha != expected_image_sha:
            raise RuntimeError(f"Source image SHA mismatch for {page_id}: {actual_image_sha}")
        if str(v32_pages[page_id].get("sourceImageSha256")) != expected_image_sha:
            raise RuntimeError(f"v3.2/source-manifest image identity mismatch for {page_id}")

        gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            raise RuntimeError(f"Unreadable source image: {image_path}")
        staffs = reconstruct_staffs_from_frozen_candidates(v32_pages[page_id])
        staff_by_index = {int(item["staffIndex"]): item for item in staffs}
        proposals, diagnostics = generate_page_proposals(gray, staffs)

        retained_records: List[Dict[str, Any]] = []
        for proposal_index, proposal in enumerate(proposals):
            staff = staff_by_index[int(proposal["staffIndex"])]
            features = semantic_features(gray, proposal, staff)
            if not sieve_keep(features):
                continue
            retained_records.append(
                {
                    "proposalIndex": int(proposal_index),
                    "bbox": [float(value) for value in proposal["bbox"]],
                    "staffIndex": int(proposal["staffIndex"]),
                    "staffSpacing": float(proposal["staffSpacing"]),
                    "anchor": str(proposal["anchor"]),
                    "anchorRank": int(proposal["anchorRank"]),
                    "sizeTag": str(proposal["sizeTag"]),
                    "xOffsetStaffSpaces": float(proposal["xOffsetStaffSpaces"]),
                    "componentGroupIndex": int(proposal["componentGroupIndex"]),
                    "componentGroupXCenter": float(proposal["componentGroupXCenter"]),
                    "componentGroupYCenter": float(proposal["componentGroupYCenter"]),
                    "features": features,
                }
            )

        groups = group_page_records(gray, retained_records, staff_by_index)
        proposal_total += len(proposals)
        retained_total += len(retained_records)
        group_total += len(groups)
        pages_out[page_id] = {
            "pageId": page_id,
            "sourceImageSha256": expected_image_sha,
            "p4_11Diagnostics": diagnostics,
            "p4_11ProposalCount": len(proposals),
            "p4_12RetainedCount": len(retained_records),
            "p4_13GroupCount": len(groups),
            "groups": groups,
        }
        print(f"{page_id}: p4.11={len(proposals)} p4.12={len(retained_records)} groups={len(groups)}")

    if proposal_total != EXPECTED_P4_11_PROPOSAL_COUNT:
        raise RuntimeError(f"P4.11 proposal identity drift: {proposal_total}")
    if retained_total != EXPECTED_P4_12_RETAINED_COUNT:
        raise RuntimeError(f"P4.12 retained identity drift: {retained_total}")

    source_payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_13-source-group-localizations-before-teacher.v1",
        "status": "FROZEN_BEFORE_TEACHER_EVALUATION",
        "developmentOnly": True,
        "qualificationEvidence": False,
        "p4_9SpentHoldoutReclassifiedForDevelopmentDiagnostic": True,
        "sourceManifestSha256": EXPECTED_MANIFEST_SHA256,
        "v32SourceOnlyCandidateArtifactSha256": EXPECTED_V32_RAW_SHA256,
        "teacherTruthReadDuringScoringGroupingOrRefinement": False,
        "restoredImagesAccessed": False,
        "newIndependentHoldoutAccessed": False,
        "semanticScoreCalibratedProbability": False,
        "p4_11ProposalCount": proposal_total,
        "p4_12RetainedProposalCount": retained_total,
        "p4_13ExactComponentGroupCount": group_total,
        "proposalCollapseFraction": 1.0 - (group_total / float(retained_total)) if retained_total else 0.0,
        "groupingPolicy": "exact (staffIndex, componentGroupIndex) identity only; score before representative selection; no cross-group NMS",
        "scoreWeights": SCORE_WEIGHTS,
        "pages": pages_out,
    }
    atomic_json(SOURCE_GROUP_PATH, source_payload)
    source_sha = sha256_file(SOURCE_GROUP_PATH)
    print("PASS — P4.13 source grouping/localization frozen before teacher access")
    print("SOURCE GROUP SHA-256:", source_sha)

    # Phase B: teacher truth is opened only after the source-only artifact exists.
    if not TEACHER_PATH.is_file():
        raise RuntimeError(f"Teacher truth missing: {TEACHER_PATH}")
    teacher_sha = sha256_file(TEACHER_PATH)
    if teacher_sha != EXPECTED_TEACHER_SHA256:
        raise RuntimeError(f"Teacher SHA mismatch: {teacher_sha}")
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("boxCount") != EXPECTED_TEACHER_BOX_COUNT:
        raise RuntimeError("Teacher truth is not frozen 11-page / 38-box P4.9")

    pooled_refined = Counter(tp=0, fp=0, fn=0)
    pooled_original = Counter(tp=0, fp=0, fn=0)
    subtype_total: Counter[str] = Counter()
    subtype_refined_tp: Counter[str] = Counter()
    per_page: Dict[str, Any] = {}

    for page_id in sorted(pages_out):
        groups = pages_out[page_id]["groups"]
        refined_candidates = [{"bbox": group["bbox"]} for group in groups]
        original_candidates = [{"bbox": group["representative"]["bbox"]} for group in groups]
        teacher_boxes = teacher["pages"][page_id]["boxes"]
        refined_metric, refined_matches = _evaluate_candidates(refined_candidates, teacher_boxes)
        original_metric, _ = _evaluate_candidates(original_candidates, teacher_boxes)
        for key in ("tp", "fp", "fn"):
            pooled_refined[key] += int(refined_metric[key])
            pooled_original[key] += int(original_metric[key])
        matched_teacher = {teacher_index for _, teacher_index, _ in refined_matches}
        for teacher_index, box in enumerate(teacher_boxes):
            label = str(box["label"])
            subtype_total[label] += 1
            if teacher_index in matched_teacher:
                subtype_refined_tp[label] += 1
        per_page[page_id] = {
            "groupCount": len(groups),
            "teacherBoxCount": len(teacher_boxes),
            "originalRepresentative": original_metric,
            "sourceInkRefined": refined_metric,
        }

    pooled_refined_metric = metric(pooled_refined["tp"], pooled_refined["fp"], pooled_refined["fn"])
    pooled_original_metric = metric(pooled_original["tp"], pooled_original["fp"], pooled_original["fn"])
    subtype = {
        label: {
            "teacherBoxes": int(total),
            "matched": int(subtype_refined_tp[label]),
            "recall": subtype_refined_tp[label] / total if total else 1.0,
        }
        for label, total in sorted(subtype_total.items())
        if label != "AMBIGUOUS"
    }

    result = {
        "schemaVersion": "stage11.v2d.c-clef-p4_13-semantic-group-localizer-result.v1",
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "developmentOnly": True,
        "qualificationEvidence": False,
        "p4_9SpentHoldoutReclassifiedForDevelopmentDiagnostic": True,
        "selectionDisclosure": {
            "policyDesignedWithSpentDevelopmentContext": True,
            "teacherTruthReadDuringScoringGroupingOrRefinement": False,
            "teacherTruthOpenedOnlyAfterSourceArtifactFrozen": True,
            "semanticScoreCalibratedProbability": False,
            "newIndependentHoldoutAccessed": False,
        },
        "sourceArtifact": {
            "path": str(SOURCE_GROUP_PATH),
            "sha256": source_sha,
            "p4_11ProposalCount": proposal_total,
            "p4_12RetainedProposalCount": retained_total,
            "p4_13ExactComponentGroupCount": group_total,
            "proposalCollapseFraction": 1.0 - (group_total / float(retained_total)) if retained_total else 0.0,
        },
        "developmentDiagnostic": {
            "originalRepresentative": pooled_original_metric,
            "sourceInkRefined": pooled_refined_metric,
            "perSubtypeSourceInkRefined": subtype,
            "perPage": per_page,
        },
        "decisionBoundary": {
            "groupingPolicyFrozenForThisDevelopmentRun": True,
            "finalPrecisionPolicyFrozen": False,
            "semanticConfidenceCalibrated": False,
            "detectorQualified": False,
            "overallStage11PassAuthorized": False,
            "productionReady": False,
            "productionPromotionAuthorized": False,
            "stage12EntryAuthorized": False,
            "newIndependentHoldoutMustRemainClosed": True,
        },
        "nextSafeAction": "Review P4.13 source-group collapse and source-ink localization diagnostics. If geometry remains recall-safe, preregister a final cross-group precision/ranking policy before opening any new independent holdout.",
    }
    atomic_json(RESULT_PATH, result)

    print()
    print("=" * 76)
    print("P4.13 DEVELOPMENT GROUP LOCALIZER COMPLETE")
    print("=" * 76)
    print("P4.12 retained proposals:", retained_total)
    print("Exact source component groups:", group_total)
    print("Original representative:", pooled_original_metric)
    print("Source-ink refined:", pooled_refined_metric)
    print("Subtype refined recall:", {key: value["recall"] for key, value in subtype.items()})
    print("RESULT SHA-256:", sha256_file(RESULT_PATH))
    print("detectorQualified: False — development-only grouping/localization diagnostic")


if __name__ == "__main__":
    main()
