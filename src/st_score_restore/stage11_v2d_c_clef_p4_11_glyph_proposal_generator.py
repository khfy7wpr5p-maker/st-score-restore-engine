"""P4.11 development-only C-clef source-glyph proposal generator.

This stage does not classify or qualify C-clefs. It consumes the frozen v3.2
source-only candidate artifact only to recover staff geometry, then derives a
smaller set of source-image component-centred proposals. Teacher truth is not
opened until all proposals have been frozen to disk.

P4.9 is spent qualification evidence and may be used only as development data.
Any policy selected here requires a new independent holdout after freeze.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
from typing import Any, Dict, List, Sequence, Tuple

import cv2
import numpy as np

ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/P4_C_CLEF_HOLDOUT_P4_9")
PREPARED = ROOT / "_PREPARED"
MANIFEST_PATH = PREPARED / "c_clef_p4_9_holdout_source_page_manifest.v1.json"
TEACHER_PATH = ROOT / "_ANNOTATIONS" / "c_clef_p4_9_holdout_teacher_boxes.v1.json"
V32_RAW_PATH = (
    ROOT
    / "_P4_10_LOCALIZER_V3_2_DEV_DIAGNOSTIC"
    / "p4_10_localizer_v3_2_candidates_before_teacher.v1.json"
)
OUT = ROOT / "_P4_11_GLYPH_PROPOSAL_DEV"
PROPOSAL_PATH = OUT / "p4_11_source_glyph_proposals_before_teacher.v1.json"
RESULT_PATH = OUT / "p4_11_source_glyph_proposal_result.v1.json"

EXPECTED_MANIFEST_SHA256 = "8db0cf576137ec8cfd8458dd5b9cead73f49b4b2910bf6436e31e1e3737a7ece"
EXPECTED_TEACHER_SHA256 = "8ce56115b519df0429ec37964de9e694c44a0fdf081b74c9bff0484bf248f095"
EXPECTED_V32_RAW_SHA256 = "ec2e855a044d009b895dc02ea2e8d5132a58359e5d880abd7cfb11a6bf9c0897"
EXPECTED_PAGE_COUNT = 11
EXPECTED_TEACHER_BOX_COUNT = 38
EXPECTED_LABEL_COUNTS = {"C1": 12, "C3": 21, "C4": 5, "AMBIGUOUS": 0}
V32_RAW_CANDIDATE_COUNT = 95778
PRIMARY_IOU = 0.50
MIN_POOLED_RECALL = 0.90
MIN_SUBTYPE_RECALL = 0.80
MIN_CANDIDATE_REDUCTION = 0.70

# Development-selected proposal policy. Selection used only spent P4.9 data.
# Values were chosen from broad source-only plateaus, not from a new holdout.
BAND_MARGIN_SPACES = 2.8
HLINE_KERNEL_SPACES = 2.2
HLINE_REMOVAL_VERTICAL_SPACES = 0.18
CLOSE_WIDTH_SPACES = 0.12
CLOSE_HEIGHT_SPACES = 0.35
FRAGMENT_MIN_WIDTH_SPACES = 0.15
FRAGMENT_MAX_WIDTH_SPACES = 5.0
FRAGMENT_MIN_HEIGHT_SPACES = 0.50
FRAGMENT_MAX_HEIGHT_SPACES = 7.5
FRAGMENT_MIN_AREA_SPACES2 = 0.40
FRAGMENT_MAX_AREA_SPACES2 = 20.0
X_GROUP_GAP_SPACES = 0.80
MAX_PROPOSAL_X_FRACTION = 0.45
SECOND_ANCHOR_MAX_DISTANCE_SPACES = 1.40
X_OFFSET_HYPOTHESES_SPACES = (-2.0, -1.0, 0.0, 1.25)

ANCHOR_LINE_INDEX = {"C1": 4, "C3": 2, "C4": 1}
ANCHOR_DEFS = ((4, "C1"), (2, "C3"), (1, "C4"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
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
    edges: List[Tuple[float, int, int]] = []
    for ci, candidate in enumerate(candidates):
        for ti, teacher_box in enumerate(teacher_boxes):
            score = box_iou(candidate["bbox"], teacher_xyxy(teacher_box))
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


def reconstruct_staffs_from_frozen_candidates(page: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Recover five-line staff geometry from the frozen source-only v3.2 artifact."""
    grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for candidate in page.get("candidates", []):
        grouped[int(candidate["staffIndex"])].append(candidate)

    staffs: List[Dict[str, Any]] = []
    for staff_index in sorted(grouped):
        candidates = grouped[staff_index]
        spacings = [float(item["staffSpacing"]) for item in candidates]
        spacing = float(statistics.median(spacings))
        if not math.isfinite(spacing) or spacing <= 0.0:
            raise RuntimeError(f"Invalid frozen staff spacing on staff {staff_index}")

        y0_estimates: List[float] = []
        source_counts: Counter[str] = Counter()
        for item in candidates:
            anchor = str(item["anchor"])
            if anchor not in ANCHOR_LINE_INDEX:
                continue
            bbox = list(map(float, item["bbox"]))
            y_center = 0.5 * (bbox[1] + bbox[3])
            y0_estimates.append(y_center - ANCHOR_LINE_INDEX[anchor] * spacing)
            source_counts[str(item.get("staffSource", "unknown"))] += 1
        if not y0_estimates:
            raise RuntimeError(f"Cannot reconstruct frozen staff {staff_index}")

        y0 = float(statistics.median(y0_estimates))
        source = source_counts.most_common(1)[0][0] if source_counts else "unknown"
        staffs.append(
            {
                "staffIndex": int(staff_index),
                "staffSpacing": spacing,
                "staffLines": [float(y0 + k * spacing) for k in range(5)],
                "staffSource": source,
            }
        )
    return staffs


def _component_groups(gray: np.ndarray, staff: Dict[str, Any]) -> List[Dict[str, float]]:
    """Extract source-pixel x/y groups without teacher data or synthetic sliding windows."""
    height, width = gray.shape[:2]
    spacing = float(staff["staffSpacing"])
    lines = np.asarray(staff["staffLines"], dtype=float)
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    y0 = max(0, int(math.floor(lines[0] - BAND_MARGIN_SPACES * spacing)))
    y1 = min(height, int(math.ceil(lines[-1] + BAND_MARGIN_SPACES * spacing)))
    if y1 <= y0:
        return []
    roi = ink[y0:y1, :].copy()

    line_width = max(7, int(round(HLINE_KERNEL_SPACES * spacing)))
    horizontal = cv2.morphologyEx(
        roi,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (line_width, 1)),
    )
    removal = cv2.dilate(
        horizontal,
        cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (1, max(1, int(round(HLINE_REMOVAL_VERTICAL_SPACES * spacing)))),
        ),
    )
    clean = roi.copy()
    clean[removal > 0] = 0

    close_width = max(1, int(round(CLOSE_WIDTH_SPACES * spacing)))
    close_height = max(1, int(round(CLOSE_HEIGHT_SPACES * spacing)))
    closed = cv2.morphologyEx(
        clean,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (close_width, close_height)),
    )

    count, _, stats, _ = cv2.connectedComponentsWithStats(
        (closed > 0).astype(np.uint8), connectivity=8
    )
    fragments: List[Dict[str, float]] = []
    for component_id in range(1, count):
        x = int(stats[component_id, cv2.CC_STAT_LEFT])
        y = int(stats[component_id, cv2.CC_STAT_TOP])
        w = int(stats[component_id, cv2.CC_STAT_WIDTH])
        h = int(stats[component_id, cv2.CC_STAT_HEIGHT])
        area = int(stats[component_id, cv2.CC_STAT_AREA])
        width_sp = w / spacing
        height_sp = h / spacing
        area_sp2 = area / (spacing * spacing)
        if not (FRAGMENT_MIN_WIDTH_SPACES <= width_sp <= FRAGMENT_MAX_WIDTH_SPACES):
            continue
        if not (FRAGMENT_MIN_HEIGHT_SPACES <= height_sp <= FRAGMENT_MAX_HEIGHT_SPACES):
            continue
        if not (FRAGMENT_MIN_AREA_SPACES2 <= area_sp2 <= FRAGMENT_MAX_AREA_SPACES2):
            continue
        fragments.append(
            {
                "xCenter": float(x + 0.5 * w),
                "yCenter": float(y0 + y + 0.5 * h),
                "areaSpaces2": float(area_sp2),
            }
        )

    fragments.sort(key=lambda item: item["xCenter"])
    groups: List[List[Dict[str, float]]] = []
    for fragment in fragments:
        if (
            groups
            and fragment["xCenter"] - groups[-1][-1]["xCenter"]
            <= X_GROUP_GAP_SPACES * spacing
        ):
            groups[-1].append(fragment)
        else:
            groups.append([fragment])

    out: List[Dict[str, float]] = []
    for group_index, group in enumerate(groups):
        weights = [max(1e-9, item["areaSpaces2"]) for item in group]
        weight_sum = float(sum(weights))
        x_center = sum(item["xCenter"] * weight for item, weight in zip(group, weights)) / weight_sum
        y_center = sum(item["yCenter"] * weight for item, weight in zip(group, weights)) / weight_sum
        if x_center > MAX_PROPOSAL_X_FRACTION * width:
            continue
        out.append(
            {
                "groupIndex": int(group_index),
                "xCenter": float(x_center),
                "yCenter": float(y_center),
                "fragmentCount": int(len(group)),
                "areaSpaces2": float(weight_sum),
            }
        )
    return out


def generate_page_proposals(gray: np.ndarray, staffs: Sequence[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    height, width = gray.shape[:2]
    proposals: List[Dict[str, Any]] = []
    group_count = 0

    for staff in staffs:
        spacing = float(staff["staffSpacing"])
        lines = np.asarray(staff["staffLines"], dtype=float)
        groups = _component_groups(gray, staff)
        group_count += len(groups)

        sizes = [(3.2, 5.2, "base")]
        if spacing < 10.0:
            sizes.append((3.0, 4.8, "small_spacing"))
        if spacing < 9.0 and (float(width) / spacing) > 180.0:
            sizes.append((3.4, 5.4, "dense_wide_page"))

        for group in groups:
            ranked = sorted(
                (
                    abs(float(lines[line_index]) - float(group["yCenter"])) / spacing,
                    line_index,
                    anchor,
                )
                for line_index, anchor in ANCHOR_DEFS
            )
            selected = [ranked[0]]
            if ranked[1][0] <= SECOND_ANCHOR_MAX_DISTANCE_SPACES:
                selected.append(ranked[1])

            for x_offset in X_OFFSET_HYPOTHESES_SPACES:
                x_center = float(group["xCenter"]) + x_offset * spacing
                for anchor_rank, (_, line_index, anchor) in enumerate(selected, start=1):
                    y_center = float(lines[line_index])
                    for width_sp, height_sp, size_tag in sizes:
                        x1 = max(0.0, x_center - 0.5 * width_sp * spacing)
                        x2 = min(float(width), x_center + 0.5 * width_sp * spacing)
                        y1 = max(0.0, y_center - 0.5 * height_sp * spacing)
                        y2 = min(float(height), y_center + 0.5 * height_sp * spacing)
                        if x2 <= x1 or y2 <= y1:
                            continue
                        proposals.append(
                            {
                                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                                "staffIndex": int(staff["staffIndex"]),
                                "staffSource": str(staff.get("staffSource", "unknown")),
                                "staffSpacing": spacing,
                                "anchor": anchor,
                                "anchorRank": int(anchor_rank),
                                "sizeTag": size_tag,
                                "xOffsetStaffSpaces": float(x_offset),
                                "componentGroupIndex": int(group["groupIndex"]),
                                "componentGroupXCenter": float(group["xCenter"]),
                                "componentGroupYCenter": float(group["yCenter"]),
                                "componentFragmentCount": int(group["fragmentCount"]),
                                "proposalSource": "source_component_center_nominal_geometry",
                            }
                        )

    return proposals, {"staffCount": len(staffs), "componentGroupCount": group_count, "proposalCount": len(proposals)}


def metric(tp: int, fp: int, fn: int) -> Dict[str, float | int]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def main() -> None:
    for path, expected in (
        (MANIFEST_PATH, EXPECTED_MANIFEST_SHA256),
        (V32_RAW_PATH, EXPECTED_V32_RAW_SHA256),
    ):
        if not path.is_file():
            raise RuntimeError(f"Required frozen artifact missing: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"SHA mismatch for {path.name}: {actual}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
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
    print("P4.11 C-CLEF SOURCE-GLYPH PROPOSAL GENERATOR — DEVELOPMENT ONLY")
    print("Phase A: source images + frozen source-only v3.2 staff geometry")
    print("Teacher truth: NOT READ until proposal artifact is frozen")
    print("=" * 76)

    pages_out: Dict[str, Any] = {}
    proposal_total = 0
    manifest_pages = {str(page["pageId"]): page for page in manifest["pages"]}
    v32_pages = frozen_v32.get("pages", {})

    for page_id in sorted(manifest_pages):
        page = manifest_pages[page_id]
        if page_id not in v32_pages:
            raise RuntimeError(f"v3.2 page missing: {page_id}")
        image_path = PREPARED / str(page["imagePath"])
        if not image_path.is_file():
            raise RuntimeError(f"Source image missing: {image_path}")
        actual_image_sha = sha256_file(image_path)
        expected_image_sha = str(page["imageSha256"])
        if actual_image_sha != expected_image_sha:
            raise RuntimeError(f"Source image SHA mismatch for {page_id}: {actual_image_sha}")
        if str(v32_pages[page_id].get("sourceImageSha256")) != expected_image_sha:
            raise RuntimeError(f"v3.2/source-manifest image identity mismatch for {page_id}")

        gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            raise RuntimeError(f"Unreadable source image: {image_path}")
        staffs = reconstruct_staffs_from_frozen_candidates(v32_pages[page_id])
        proposals, diagnostics = generate_page_proposals(gray, staffs)
        proposal_total += len(proposals)
        pages_out[page_id] = {
            "pageId": page_id,
            "sourceImageSha256": expected_image_sha,
            "sourcePdfName": page.get("sourcePdfName"),
            "sourcePageNumber": page.get("sourcePageNumber"),
            "staffs": staffs,
            "diagnostics": diagnostics,
            "proposals": proposals,
        }
        print(f"{page_id}: staffs={len(staffs)} groups={diagnostics['componentGroupCount']} proposals={len(proposals)}")

    policy = {
        "bandMarginSpaces": BAND_MARGIN_SPACES,
        "horizontalLineKernelSpaces": HLINE_KERNEL_SPACES,
        "horizontalRemovalVerticalSpaces": HLINE_REMOVAL_VERTICAL_SPACES,
        "closeWidthSpaces": CLOSE_WIDTH_SPACES,
        "closeHeightSpaces": CLOSE_HEIGHT_SPACES,
        "fragmentWidthSpaces": [FRAGMENT_MIN_WIDTH_SPACES, FRAGMENT_MAX_WIDTH_SPACES],
        "fragmentHeightSpaces": [FRAGMENT_MIN_HEIGHT_SPACES, FRAGMENT_MAX_HEIGHT_SPACES],
        "fragmentAreaSpaces2": [FRAGMENT_MIN_AREA_SPACES2, FRAGMENT_MAX_AREA_SPACES2],
        "xGroupGapSpaces": X_GROUP_GAP_SPACES,
        "maxProposalXFraction": MAX_PROPOSAL_X_FRACTION,
        "secondAnchorMaxDistanceSpaces": SECOND_ANCHOR_MAX_DISTANCE_SPACES,
        "xOffsetHypothesesSpaces": list(X_OFFSET_HYPOTHESES_SPACES),
        "anchorSemantics": "geometric hypotheses only; not predicted C-clef subtype",
    }
    frozen_payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_11-source-glyph-proposals.v1",
        "status": "FROZEN_BEFORE_TEACHER_EVALUATION",
        "developmentOnly": True,
        "p4_9SpentHoldoutReclassifiedForDevelopmentDiagnostic": True,
        "sourceManifestSha256": EXPECTED_MANIFEST_SHA256,
        "v32SourceOnlyCandidateArtifactSha256": EXPECTED_V32_RAW_SHA256,
        "teacherTruthReadDuringCandidateGeneration": False,
        "policy": policy,
        "pageCount": EXPECTED_PAGE_COUNT,
        "proposalCountTotal": proposal_total,
        "pages": pages_out,
    }
    atomic_json(PROPOSAL_PATH, frozen_payload)
    proposal_sha = sha256_file(PROPOSAL_PATH)
    print("PASS — proposal artifact frozen before teacher access")
    print("PROPOSAL SHA-256:", proposal_sha)

    # Phase B: development-only evaluation. P4.9 is already spent.
    if not TEACHER_PATH.is_file():
        raise RuntimeError(f"Teacher truth missing: {TEACHER_PATH}")
    teacher_sha = sha256_file(TEACHER_PATH)
    if teacher_sha != EXPECTED_TEACHER_SHA256:
        raise RuntimeError(f"Teacher SHA mismatch: {teacher_sha}")
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("boxCount") != EXPECTED_TEACHER_BOX_COUNT:
        raise RuntimeError("Teacher truth is not the frozen 11-page / 38-box P4.9 set")
    if teacher.get("labelCounts") != EXPECTED_LABEL_COUNTS:
        raise RuntimeError("Teacher label counts changed")

    pooled_tp = pooled_fp = pooled_fn = 0
    subtype_total: Counter[str] = Counter()
    subtype_tp: Counter[str] = Counter()
    per_page: Dict[str, Any] = {}
    for page_id in sorted(pages_out):
        proposals = pages_out[page_id]["proposals"]
        teacher_boxes = teacher["pages"][page_id]["boxes"]
        for box in teacher_boxes:
            subtype_total[str(box["label"])] += 1
        matches = greedy_match(proposals, teacher_boxes)
        matched_teacher = {ti for _, ti, _ in matches}
        tp = len(matches)
        fp = len(proposals) - tp
        fn = len(teacher_boxes) - tp
        pooled_tp += tp
        pooled_fp += fp
        pooled_fn += fn
        for ti in matched_teacher:
            subtype_tp[str(teacher_boxes[ti]["label"])] += 1
        per_page[page_id] = {
            "proposalCount": len(proposals),
            "teacherBoxCount": len(teacher_boxes),
            "matchedTeacherCount": tp,
            "proposalRecall": tp / len(teacher_boxes) if teacher_boxes else 1.0,
            "matches": [
                {
                    "proposalIndex": int(ci),
                    "teacherIndex": int(ti),
                    "teacherLabel": str(teacher_boxes[ti]["label"]),
                    "iou": float(score),
                }
                for ci, ti, score in matches
            ],
        }

    pooled = metric(pooled_tp, pooled_fp, pooled_fn)
    subtype = {
        label: {
            "teacherBoxes": int(total),
            "matched": int(subtype_tp[label]),
            "proposalRecall": subtype_tp[label] / total if total else 1.0,
        }
        for label, total in sorted(subtype_total.items())
        if label != "AMBIGUOUS"
    }
    reduction = 1.0 - (proposal_total / float(V32_RAW_CANDIDATE_COUNT))
    target_met = (
        pooled["recall"] >= MIN_POOLED_RECALL
        and all(item["proposalRecall"] >= MIN_SUBTYPE_RECALL for item in subtype.values())
        and reduction >= MIN_CANDIDATE_REDUCTION
    )

    result = {
        "schemaVersion": "stage11.v2d.c-clef-p4_11-source-glyph-proposal-result.v1",
        "status": "DEVELOPMENT_PROPOSAL_TARGET_MET" if target_met else "DEVELOPMENT_PROPOSAL_TARGET_NOT_MET",
        "developmentOnly": True,
        "qualificationEvidence": False,
        "p4_9SpentHoldoutReclassifiedForDevelopmentDiagnostic": True,
        "selectionDisclosure": {
            "policySelectedAfterDevelopmentReview": True,
            "independentQualificationEvidence": False,
            "newIndependentHoldoutRequiredAfterPrecisionPolicyFreeze": True,
        },
        "proposalArtifact": {
            "path": str(PROPOSAL_PATH),
            "sha256": proposal_sha,
            "proposalCountTotal": proposal_total,
            "v32RawCandidateCount": V32_RAW_CANDIDATE_COUNT,
            "candidateReduction": reduction,
        },
        "policy": policy,
        "pooledProposalMetrics": pooled,
        "perSubtype": subtype,
        "perPage": per_page,
        "developmentProposalTarget": {
            "pooledRecallAtLeast": MIN_POOLED_RECALL,
            "eachSubtypeRecallAtLeast": MIN_SUBTYPE_RECALL,
            "candidateReductionAtLeast": MIN_CANDIDATE_REDUCTION,
            "met": target_met,
        },
        "decisionBoundary": {
            "proposalGeneratorDevelopmentFrozen": bool(target_met),
            "precisionGateFrozen": False,
            "detectorQualified": False,
            "overallStage11PassAuthorized": False,
            "productionReady": False,
            "stage12EntryAuthorized": False,
            "next": "Score the reduced source-glyph proposal set with source-image semantic features; do not open a new independent holdout until the precision policy is frozen.",
        },
    }
    atomic_json(RESULT_PATH, result)

    print()
    print("=" * 76)
    print("P4.11 SOURCE-GLYPH PROPOSAL DEVELOPMENT RESULT")
    print("=" * 76)
    print("PROPOSALS:", proposal_total, "FROM V3.2 RAW:", V32_RAW_CANDIDATE_COUNT)
    print("REDUCTION:", reduction)
    print("POOLED:", pooled)
    print("SUBTYPE:", {k: v["proposalRecall"] for k, v in subtype.items()})
    print("TARGET MET:", target_met)
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", sha256_file(RESULT_PATH))
    print("detectorQualified: False — proposal generation only")


if __name__ == "__main__":
    main()
