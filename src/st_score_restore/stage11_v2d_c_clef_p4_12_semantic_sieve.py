"""P4.12 development-only C-clef source-semantic proposal sieve.

P4.11 reduced the v3.2 C-clef hypothesis surface from 95,778 geometric
candidates to 26,732 source-component-centred proposals while preserving 38/38
C-clef localization recall on the already-spent P4.9 development set.

P4.12 does not classify/qualify C-clefs and does not open a new holdout. Phase A
regenerates the frozen P4.11 proposal policy from source pixels + frozen v3.2
staff geometry, extracts source-only semantic/shape features, applies a broad
recall-preserving sieve, and freezes the unlabeled feature artifact. Only then
may Phase B open the already-spent P4.9 teacher truth for development-only
measurement.

The selected sieve is intentionally broad. Its purpose is hypothesis reduction,
not final precision. A later precision/localization policy still requires a new
independent holdout after freeze.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Sequence

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
    generate_page_proposals,
    greedy_match,
    reconstruct_staffs_from_frozen_candidates,
)

OUT = ROOT / "_P4_12_SEMANTIC_SIEVE_DEV"
FEATURE_PATH = OUT / "p4_12_semantic_features_before_teacher.v1.json"
RESULT_PATH = OUT / "p4_12_semantic_sieve_result.v1.json"

EXPECTED_P4_11_PROPOSAL_COUNT = 26732
PRIMARY_IOU = 0.50

# Development-selected broad plateau. These values are not qualification
# thresholds. P4.9 is already spent and is explicitly development-only here.
MAX_COMPONENT_X_FRACTION = 0.40
MIN_RAW_INK_DENSITY = 0.22
MIN_LEFT_VERTICAL_RUN_P90 = 0.08

MIN_POOLED_RECALL = 0.95
MIN_SUBTYPE_RECALL = 0.80
MAX_RETAINED_PROPOSALS = 8000

NORMALIZED_WIDTH = 64
NORMALIZED_HEIGHT = 96
LEFT_STRUCTURE_COLUMNS = 24
CROP_MARGIN_SPACES = 0.35
STAFF_LINE_KERNEL_SPACES = 1.50
STAFF_LINE_REMOVAL_PX = 3


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


def density(mask: np.ndarray) -> float:
    return float(np.count_nonzero(mask)) / float(mask.size) if mask.size else 0.0


def balance(a: float, b: float) -> float:
    hi = max(float(a), float(b))
    return min(float(a), float(b)) / hi if hi > 1e-12 else 1.0


def longest_vertical_runs(mask: np.ndarray) -> np.ndarray:
    """Return longest contiguous foreground run per column, normalized by height."""
    binary = (mask > 0).astype(np.int8)
    height, width = binary.shape[:2]
    out = np.zeros(width, dtype=np.float32)
    if height <= 0 or width <= 0:
        return out
    for x in range(width):
        column = binary[:, x]
        if not np.any(column):
            continue
        transitions = np.diff(np.concatenate(([0], column, [0])).astype(np.int16))
        starts = np.flatnonzero(transitions == 1)
        ends = np.flatnonzero(transitions == -1)
        if starts.size and ends.size:
            out[x] = float(np.max(ends - starts)) / float(height)
    return out


def semantic_features(
    gray: np.ndarray,
    proposal: Dict[str, Any],
    staff: Dict[str, Any],
) -> Dict[str, float | int]:
    """Extract teacher-independent C-clef structure features from one proposal."""
    height, width = gray.shape[:2]
    spacing = float(proposal["staffSpacing"])
    if spacing <= 0.0 or not math.isfinite(spacing):
        raise RuntimeError("Invalid proposal staff spacing")

    x1, y1, x2, y2 = map(float, proposal["bbox"])
    margin = max(2.0, CROP_MARGIN_SPACES * spacing)
    xa = max(0, int(math.floor(x1 - margin)))
    ya = max(0, int(math.floor(y1 - margin)))
    xb = min(width, int(math.ceil(x2 + margin)))
    yb = min(height, int(math.ceil(y2 + margin)))
    if xb <= xa or yb <= ya:
        raise RuntimeError("Invalid proposal crop")

    crop = gray[ya:yb, xa:xb]
    _, ink = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Remove long horizontal staff fragments before semantic shape measurement.
    line_width = max(5, int(round(STAFF_LINE_KERNEL_SPACES * spacing)))
    horizontal = cv2.morphologyEx(
        ink,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (line_width, 1)),
    )
    removal = cv2.dilate(
        horizontal,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, STAFF_LINE_REMOVAL_PX)),
    )
    clean = ink.copy()
    clean[removal > 0] = 0

    raw_norm = cv2.resize(
        (ink > 0).astype(np.uint8),
        (NORMALIZED_WIDTH, NORMALIZED_HEIGHT),
        interpolation=cv2.INTER_NEAREST,
    )
    norm = cv2.resize(
        (clean > 0).astype(np.uint8),
        (NORMALIZED_WIDTH, NORMALIZED_HEIGHT),
        interpolation=cv2.INTER_NEAREST,
    )

    top = density(norm[:32, :])
    middle = density(norm[32:64, :])
    bottom = density(norm[64:, :])
    left = norm[:, :LEFT_STRUCTURE_COLUMNS]
    left_middle = density(norm[32:64, :LEFT_STRUCTURE_COLUMNS])
    left_bottom = density(norm[64:, :LEFT_STRUCTURE_COLUMNS])

    vertical_runs = longest_vertical_runs(norm)
    left_runs = longest_vertical_runs(left)
    left_p90 = float(np.percentile(left_runs, 90)) if left_runs.size else 0.0
    left_max = float(np.max(left_runs)) if left_runs.size else 0.0
    stem_x_fraction = (
        float(np.argmax(vertical_runs)) / float(max(1, NORMALIZED_WIDTH - 1))
        if vertical_runs.size and float(np.max(vertical_runs)) > 0.0
        else 1.0
    )

    rows, cols = np.nonzero(norm)
    ink_centroid_x = (
        float(np.mean(cols)) / float(max(1, NORMALIZED_WIDTH - 1))
        if cols.size
        else 1.0
    )

    # Measure upper/lower ink balance around the proposal's geometric anchor line.
    staff_lines = np.asarray(staff["staffLines"], dtype=float)
    anchor_line_index = {"C1": 4, "C3": 2, "C4": 1}.get(str(proposal["anchor"]))
    anchor_balance = 0.0
    if anchor_line_index is not None and staff_lines.size == 5:
        cy = int(round(float(staff_lines[anchor_line_index]) - ya))
        half_span = max(2, int(round(1.75 * spacing)))
        center_half = max(1, int(round(0.22 * spacing)))
        top0, top1 = max(0, cy - half_span), max(0, cy - center_half)
        bot0, bot1 = min(clean.shape[0], cy + center_half + 1), min(clean.shape[0], cy + half_span + 1)
        if top1 > top0 and bot1 > bot0:
            top_band = (clean[top0:top1, :] > 0).astype(np.uint8)
            bottom_band = (clean[bot0:bot1, :] > 0).astype(np.uint8)
            shared = min(top_band.shape[0], bottom_band.shape[0])
            if shared > 0:
                anchor_balance = balance(density(top_band[-shared:, :]), density(bottom_band[:shared, :]))

    component_x_fraction = float(proposal["componentGroupXCenter"]) / float(max(1, width))
    return {
        "inkDensity": density(raw_norm),
        "cleanInkDensity": density(norm),
        "topThirdDensity": top,
        "middleThirdDensity": middle,
        "bottomThirdDensity": bottom,
        "leftMidDensity": left_middle,
        "leftBottomDensity": left_bottom,
        "leftVerticalRunP90": left_p90,
        "leftVerticalRunMax": left_max,
        "stemXFraction": stem_x_fraction,
        "inkCentroidX": ink_centroid_x,
        "anchorInkBalance": float(anchor_balance),
        "componentGroupXFraction": component_x_fraction,
        "componentFragmentCount": int(proposal["componentFragmentCount"]),
    }


def sieve_keep(features: Dict[str, Any]) -> bool:
    """Broad source-only development sieve; not a C-clef qualification decision."""
    return (
        float(features["componentGroupXFraction"]) <= MAX_COMPONENT_X_FRACTION
        and float(features["inkDensity"]) >= MIN_RAW_INK_DENSITY
        and float(features["leftVerticalRunP90"]) >= MIN_LEFT_VERTICAL_RUN_P90
    )


def metric(tp: int, fp: int, fn: int) -> Dict[str, float | int]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def main() -> None:
    for path, expected in (
        (PREPARED / "c_clef_p4_9_holdout_source_page_manifest.v1.json", EXPECTED_MANIFEST_SHA256),
        (V32_RAW_PATH, EXPECTED_V32_RAW_SHA256),
    ):
        if not path.is_file():
            raise RuntimeError(f"Required frozen artifact missing: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"SHA mismatch for {path.name}: {actual}")

    manifest_path = PREPARED / "c_clef_p4_9_holdout_source_page_manifest.v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frozen_v32 = json.loads(V32_RAW_PATH.read_text(encoding="utf-8"))
    if manifest.get("pageCount") != EXPECTED_PAGE_COUNT or len(manifest.get("pages", [])) != EXPECTED_PAGE_COUNT:
        raise RuntimeError("Expected frozen 11-page P4.9 manifest")
    if manifest.get("detectorOutputsAccessed") is not False:
        raise RuntimeError("Unsafe source manifest provenance")
    if frozen_v32.get("teacherTruthReadDuringCandidateGeneration") is not False:
        raise RuntimeError("Unsafe v3.2 candidate provenance")
    if int(frozen_v32.get("candidateCountTotal", -1)) != V32_RAW_CANDIDATE_COUNT:
        raise RuntimeError("Unexpected v3.2 candidate count")

    print("=" * 76)
    print("P4.12 C-CLEF SOURCE-SEMANTIC SIEVE — DEVELOPMENT ONLY")
    print("Phase A: source pixels + frozen v3.2 staff geometry; teacher CLOSED")
    print("=" * 76)

    manifest_pages = {str(page["pageId"]): page for page in manifest["pages"]}
    v32_pages = frozen_v32.get("pages", {})
    pages_out: Dict[str, Any] = {}
    proposal_total = retained_total = 0

    for page_id in sorted(manifest_pages):
        page = manifest_pages[page_id]
        image_path = PREPARED / str(page["imagePath"])
        if not image_path.is_file():
            raise RuntimeError(f"Source image missing: {image_path}")
        expected_image_sha = str(page["imageSha256"])
        actual_image_sha = sha256_file(image_path)
        if actual_image_sha != expected_image_sha:
            raise RuntimeError(f"Source image SHA mismatch for {page_id}: {actual_image_sha}")
        if page_id not in v32_pages:
            raise RuntimeError(f"v3.2 page missing: {page_id}")
        if str(v32_pages[page_id].get("sourceImageSha256")) != expected_image_sha:
            raise RuntimeError(f"v3.2/source-manifest identity mismatch for {page_id}")

        gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            raise RuntimeError(f"Unreadable source image: {image_path}")
        staffs = reconstruct_staffs_from_frozen_candidates(v32_pages[page_id])
        staff_by_index = {int(item["staffIndex"]): item for item in staffs}
        proposals, diagnostics = generate_page_proposals(gray, staffs)

        records: List[Dict[str, Any]] = []
        for proposal_index, proposal in enumerate(proposals):
            staff = staff_by_index[int(proposal["staffIndex"])]
            features = semantic_features(gray, proposal, staff)
            keep = sieve_keep(features)
            records.append(
                {
                    "proposalIndex": int(proposal_index),
                    "bbox": [float(v) for v in proposal["bbox"]],
                    "staffIndex": int(proposal["staffIndex"]),
                    "anchor": str(proposal["anchor"]),
                    "anchorRank": int(proposal["anchorRank"]),
                    "sizeTag": str(proposal["sizeTag"]),
                    "xOffsetStaffSpaces": float(proposal["xOffsetStaffSpaces"]),
                    "componentGroupIndex": int(proposal["componentGroupIndex"]),
                    "componentGroupXCenter": float(proposal["componentGroupXCenter"]),
                    "componentGroupYCenter": float(proposal["componentGroupYCenter"]),
                    "features": features,
                    "sieveKeep": bool(keep),
                }
            )

        kept = sum(1 for item in records if item["sieveKeep"])
        proposal_total += len(records)
        retained_total += kept
        pages_out[page_id] = {
            "pageId": page_id,
            "sourceImageSha256": expected_image_sha,
            "staffs": staffs,
            "p4_11Diagnostics": diagnostics,
            "proposalCount": len(records),
            "retainedCount": kept,
            "records": records,
        }
        print(f"{page_id}: proposals={len(records)} retained={kept}")

    if proposal_total != EXPECTED_P4_11_PROPOSAL_COUNT:
        raise RuntimeError(f"P4.11 proposal identity drift: {proposal_total}")

    policy = {
        "maxComponentGroupXFraction": MAX_COMPONENT_X_FRACTION,
        "minRawInkDensity": MIN_RAW_INK_DENSITY,
        "minLeftVerticalRunP90": MIN_LEFT_VERTICAL_RUN_P90,
        "purpose": "broad recall-preserving source-semantic hypothesis reduction; not final precision",
    }
    feature_payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_12-semantic-features-before-teacher.v1",
        "status": "FROZEN_BEFORE_TEACHER_EVALUATION",
        "developmentOnly": True,
        "qualificationEvidence": False,
        "p4_9SpentHoldoutReclassifiedForDevelopmentDiagnostic": True,
        "sourceManifestSha256": EXPECTED_MANIFEST_SHA256,
        "v32SourceOnlyCandidateArtifactSha256": EXPECTED_V32_RAW_SHA256,
        "teacherTruthReadDuringFeatureExtraction": False,
        "p4_11ProposalCount": proposal_total,
        "retainedCount": retained_total,
        "policy": policy,
        "pages": pages_out,
    }
    atomic_json(FEATURE_PATH, feature_payload)
    feature_sha = sha256_file(FEATURE_PATH)
    print("PASS — semantic feature artifact frozen before teacher access")
    print("FEATURE SHA-256:", feature_sha)

    # Phase B: P4.9 is already spent, so teacher truth may now be used only for
    # development evaluation of the already-frozen source-only sieve.
    if not TEACHER_PATH.is_file():
        raise RuntimeError(f"Teacher truth missing: {TEACHER_PATH}")
    teacher_sha = sha256_file(TEACHER_PATH)
    if teacher_sha != EXPECTED_TEACHER_SHA256:
        raise RuntimeError(f"Teacher SHA mismatch: {teacher_sha}")
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("boxCount") != EXPECTED_TEACHER_BOX_COUNT:
        raise RuntimeError("Teacher truth is not frozen 11-page / 38-box P4.9")

    pooled_tp = pooled_fp = pooled_fn = 0
    subtype_total: Counter[str] = Counter()
    subtype_tp: Counter[str] = Counter()
    per_page: Dict[str, Any] = {}

    for page_id in sorted(pages_out):
        retained = [
            {
                "bbox": item["bbox"],
                "proposalIndex": item["proposalIndex"],
                "anchor": item["anchor"],
            }
            for item in pages_out[page_id]["records"]
            if item["sieveKeep"]
        ]
        teacher_boxes = teacher["pages"][page_id]["boxes"]
        for box in teacher_boxes:
            subtype_total[str(box["label"])] += 1
        matches = greedy_match(retained, teacher_boxes)
        matched_teacher = {ti for _, ti, _ in matches}
        tp = len(matches)
        fp = len(retained) - tp
        fn = len(teacher_boxes) - tp
        pooled_tp += tp
        pooled_fp += fp
        pooled_fn += fn
        for ti in matched_teacher:
            subtype_tp[str(teacher_boxes[ti]["label"])] += 1
        per_page[page_id] = {
            "retainedCount": len(retained),
            "teacherBoxCount": len(teacher_boxes),
            "matchedTeacherCount": tp,
            "recall": tp / len(teacher_boxes) if teacher_boxes else 1.0,
        }

    pooled = metric(pooled_tp, pooled_fp, pooled_fn)
    subtype = {
        label: {
            "teacherBoxes": int(total),
            "matched": int(subtype_tp[label]),
            "recall": subtype_tp[label] / total if total else 1.0,
        }
        for label, total in sorted(subtype_total.items())
        if label != "AMBIGUOUS"
    }
    reduction_from_p411 = 1.0 - (retained_total / float(proposal_total))
    reduction_from_v32 = 1.0 - (retained_total / float(V32_RAW_CANDIDATE_COUNT))
    target_met = (
        pooled["recall"] >= MIN_POOLED_RECALL
        and all(item["recall"] >= MIN_SUBTYPE_RECALL for item in subtype.values())
        and retained_total <= MAX_RETAINED_PROPOSALS
    )

    result = {
        "schemaVersion": "stage11.v2d.c-clef-p4_12-semantic-sieve-result.v1",
        "status": "DEVELOPMENT_SIEVE_TARGET_MET" if target_met else "DEVELOPMENT_SIEVE_TARGET_NOT_MET",
        "developmentOnly": True,
        "qualificationEvidence": False,
        "p4_9SpentHoldoutReclassifiedForDevelopmentDiagnostic": True,
        "selectionDisclosure": {
            "thresholdsSelectedAfterDevelopmentReview": True,
            "independentQualificationEvidence": False,
            "newIndependentHoldoutAccessed": False,
            "newIndependentHoldoutRequiredAfterFinalPrecisionPolicyFreeze": True,
        },
        "featureArtifact": {
            "path": str(FEATURE_PATH),
            "sha256": feature_sha,
            "p4_11ProposalCount": proposal_total,
            "retainedCount": retained_total,
            "reductionFromP4_11": reduction_from_p411,
            "reductionFromV32": reduction_from_v32,
        },
        "policy": policy,
        "pooled": pooled,
        "perSubtype": subtype,
        "perPage": per_page,
        "developmentSieveTarget": {
            "pooledRecallAtLeast": MIN_POOLED_RECALL,
            "eachSubtypeRecallAtLeast": MIN_SUBTYPE_RECALL,
            "retainedAtMost": MAX_RETAINED_PROPOSALS,
            "met": bool(target_met),
        },
        "decisionBoundary": {
            "semanticSieveDevelopmentCandidateAccepted": bool(target_met),
            "precisionSolved": False,
            "precisionGateFrozen": False,
            "detectorQualified": False,
            "overallStage11PassAuthorized": False,
            "productionReady": False,
            "stage12EntryAuthorized": False,
            "newIndependentHoldoutMustRemainClosed": True,
        },
        "nextSafeAction": "Score and localize the reduced source-semantic proposal groups without arbitrary NMS; freeze a final precision/localization policy before opening any new independent holdout.",
    }
    atomic_json(RESULT_PATH, result)

    print()
    print("=" * 76)
    print("P4.12 DEVELOPMENT SEMANTIC SIEVE COMPLETE")
    print("=" * 76)
    print("P4.11 proposals:", proposal_total)
    print("Retained:", retained_total)
    print("Reduction from P4.11:", reduction_from_p411)
    print("Reduction from v3.2:", reduction_from_v32)
    print("Pooled:", pooled)
    print("Subtype recall:", {key: value["recall"] for key, value in subtype.items()})
    print("TARGET MET:", target_met)
    print("RESULT SHA-256:", sha256_file(RESULT_PATH))
    print("detectorQualified: False — development semantic sieve only")


if __name__ == "__main__":
    main()
