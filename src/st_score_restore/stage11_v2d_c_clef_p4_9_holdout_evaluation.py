"""P4.9 one-shot independent holdout evaluation for the frozen P4.8 C-clef policy.

Safety contract:
- P4.8 policy is frozen before this holdout is evaluated.
- Candidate generation reads only the P4.9 prepared page manifest/images.
- Teacher truth is not opened until the final candidate artifact is frozen.
- P4.8 thresholds/policy are never changed in this runner.
- P4.7 holdout is not read.
- A passing C-clef result does not authorize overall Stage 11 PASS, production,
  or Stage 12 entry.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import statistics
import tempfile
import types
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import cv2
import numpy as np

ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/P4_C_CLEF_HOLDOUT_P4_9")
PREPARED = ROOT / "_PREPARED"
MANIFEST_PATH = PREPARED / "c_clef_p4_9_holdout_source_page_manifest.v1.json"
TEACHER_PATH = ROOT / "_ANNOTATIONS" / "c_clef_p4_9_holdout_teacher_boxes.v1.json"
OUT = ROOT / "_RESULT"
FROZEN_CANDIDATES_PATH = OUT / "p4_9_p4_8_policy_candidates_frozen_before_teacher.v1.json"
RESULT_PATH = OUT / "p4_9_p4_8_holdout_evaluation_result.v1.json"

EXPECTED_MANIFEST_SHA256 = "8db0cf576137ec8cfd8458dd5b9cead73f49b4b2910bf6436e31e1e3737a7ece"
EXPECTED_TEACHER_SHA256 = "8ce56115b519df0429ec37964de9e694c44a0fdf081b74c9bff0484bf248f095"
EXPECTED_PAGE_COUNT = 11
EXPECTED_TEACHER_BOX_COUNT = 38
EXPECTED_LABEL_COUNTS = {"C1": 12, "C3": 21, "C4": 5, "AMBIGUOUS": 0}

P45_COMMIT = "7130bdf94bcf9247a0b33e9342db22746b46f289"
P45_EXPECTED_SOURCE_SHA256 = "0bd631e0863f084204cb3927aa19c1da715e30c81371250a50b4ad97f107c426"
P45_URL = (
    "https://raw.githubusercontent.com/khfy7wpr5p-maker/st-score-restore-engine/"
    + P45_COMMIT
    + "/src/st_score_restore/stage11_v2d_c_clef_p4_5_source_image_localizer.py"
)

# Frozen P4.6 original-path filter.
P46_LOW_AREA = 4.15
P46_HIGH_AREA = 9.80
P46_MIN_WIDTH = 2.00
P46_MAX_HEIGHT = 6.10
P46_LOW_SPACING = 12.00
P46_MIN_HEIGHT_LOW_SPACING = 5.00

# Frozen P4.8 canonical-path filter.
P48_MIN_AREA = 4.15
P48_MAX_AREA = 12.0
P48_MIN_WIDTH = 2.0
P48_MIN_HEIGHT = 3.6
P48_MAX_HEIGHT = 5.8

# Frozen P4.8 policy.
CANONICAL_STAFF_SPACING_PX = 15.0
MIN_CANONICAL_FACTOR = 0.60
MAX_CANONICAL_FACTOR = 3.00
ROUTE_SPACING_PX = 12.0
VERTICAL_MIRROR_MIN = 0.86
BOTTOM_PAD_STAFF_SPACES = 0.25
PRIMARY_IOU = 0.50
DEDUP_IOU = 0.50

# Frozen qualification target inherited from the P4.8 development contract.
MIN_PRECISION = 0.80
MIN_RECALL = 0.90
MIN_SUBTYPE_RECALL = 0.80


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
        raise RuntimeError(f"Frozen P4.5 module SHA mismatch: {actual}")
    module = types.ModuleType("p45_frozen_p49")
    module.__file__ = "stage11_v2d_c_clef_p4_5_source_image_localizer.py"
    exec(compile(data.decode("utf-8"), module.__file__, "exec"), module.__dict__)
    return module


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


def vertical_mirror_similarity(gray: np.ndarray, bbox: Sequence[float], spacing: float) -> float:
    """Exact verticalMirrorSimilarity feature used by the frozen P4.8 gate."""
    h, w = gray.shape[:2]
    x1, y1, x2, y2 = map(float, bbox)
    margin = max(2.0, 0.35 * float(spacing))
    xa = max(0, int(math.floor(x1 - margin)))
    ya = max(0, int(math.floor(y1 - margin)))
    xb = min(w, int(math.ceil(x2 + margin)))
    yb = min(h, int(math.ceil(y2 + margin)))
    if xb <= xa or yb <= ya:
        raise RuntimeError("Invalid candidate crop for mirror feature")

    crop = gray[ya:yb, xa:xb]
    _, ink = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    line_width = max(5, int(round(1.50 * float(spacing))))
    horizontal = cv2.morphologyEx(
        ink,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (line_width, 1)),
    )
    removal = cv2.dilate(horizontal, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3)))
    clean = ink.copy()
    clean[removal > 0] = 0
    norm = cv2.resize((clean > 0).astype(np.uint8), (64, 96), interpolation=cv2.INTER_NEAREST)
    upper = norm[:48, :]
    lower = np.flipud(norm[48:, :])
    return 1.0 - float(np.mean(np.abs(upper.astype(np.float32) - lower.astype(np.float32))))


def pad_bottom(candidate: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(candidate)
    bbox = list(map(float, item["bbox"]))
    spacing = float(item["spacingInput"])
    bbox[3] += BOTTOM_PAD_STAFF_SPACES * spacing
    item["bbox"] = bbox
    return item


def build_policy_candidates(
    gray: np.ndarray,
    original_candidates: Sequence[Dict[str, Any]],
    canonical_candidates: Sequence[Dict[str, Any]],
    canonical_factor: float,
    pre_spacing: float | None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if pre_spacing is None:
        return [], {
            "path": "no_staffs_detected",
            "preCanonicalMedianStaffSpacing": None,
            "acceptedCount": 0,
            "gatedCanonicalAdded": 0,
            "gatedCanonicalRejected": 0,
            "deduplicatedCanonicalRejected": 0,
        }

    accepted: List[Dict[str, Any]] = []
    gated_added = 0
    gated_rejected = 0
    dedup_rejected = 0

    if pre_spacing < ROUTE_SPACING_PX:
        path = "canonical_only_low_spacing"
        for candidate in canonical_candidates:
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
        for candidate in original_candidates:
            if not p46_keep(candidate):
                continue
            item = dict(candidate)
            item["bbox"] = list(map(float, candidate["bbox"]))
            item["spacingInput"] = float(candidate["staffSpacing"])
            item["policySource"] = "original_p46"
            originals.append(item)

        additions: List[Dict[str, Any]] = []
        for candidate in canonical_candidates:
            if not p48_keep(candidate):
                continue
            item = dict(candidate)
            item["bbox"] = [float(v) / canonical_factor for v in candidate["bbox"]]
            item["spacingInput"] = float(candidate["staffSpacing"]) / canonical_factor
            item["policySource"] = "canonical_p48"
            if any(box_iou(item["bbox"], original["bbox"]) >= DEDUP_IOU for original in originals):
                dedup_rejected += 1
                continue
            mirror = vertical_mirror_similarity(gray, item["bbox"], float(item["spacingInput"]))
            item["verticalMirrorSimilarity"] = mirror
            if mirror < VERTICAL_MIRROR_MIN:
                gated_rejected += 1
                continue
            gated_added += 1
            additions.append(item)

        accepted = [pad_bottom(item) for item in originals + additions]

    return accepted, {
        "path": path,
        "preCanonicalMedianStaffSpacing": float(pre_spacing),
        "canonicalFactor": float(canonical_factor),
        "originalRawCandidateCount": len(original_candidates),
        "canonicalRawCandidateCount": len(canonical_candidates),
        "acceptedCount": len(accepted),
        "gatedCanonicalAdded": gated_added,
        "gatedCanonicalRejected": gated_rejected,
        "deduplicatedCanonicalRejected": dedup_rejected,
    }


def teacher_xyxy(box: Dict[str, Any]) -> List[float]:
    x = float(box["x"])
    y = float(box["y"])
    w = float(box.get("w", box.get("width")))
    h = float(box.get("h", box.get("height")))
    return [x, y, x + w, y + h]


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


def metric(tp: int, fp: int, fn: int) -> Dict[str, float | int]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def evaluate(frozen_pages: Dict[str, Any], teacher: Dict[str, Any]) -> Dict[str, Any]:
    total_tp = total_fp = total_fn = 0
    subtype_total = Counter()
    subtype_tp = Counter()
    per_page: Dict[str, Any] = {}

    for page_id, page in frozen_pages.items():
        candidates = page["candidates"]
        teacher_boxes = teacher["pages"][page_id]["boxes"]
        for box in teacher_boxes:
            subtype_total[box["label"]] += 1

        matches = greedy_match(candidates, teacher_boxes)
        matched_teacher = {ti for _, ti, _ in matches}
        tp = len(matches)
        fp = len(candidates) - tp
        fn = len(teacher_boxes) - tp
        total_tp += tp
        total_fp += fp
        total_fn += fn

        for ti in matched_teacher:
            subtype_tp[teacher_boxes[ti]["label"]] += 1

        per_page[page_id] = {
            "sourcePdfName": teacher["pages"][page_id]["sourcePdfName"],
            "sourcePageNumber": teacher["pages"][page_id]["sourcePageNumber"],
            "candidateCount": len(candidates),
            "teacherBoxCount": len(teacher_boxes),
            "metrics": metric(tp, fp, fn),
            "matches": [
                {
                    "candidateIndex": ci,
                    "teacherIndex": ti,
                    "teacherLabel": teacher_boxes[ti]["label"],
                    "iou": score,
                }
                for ci, ti, score in matches
            ],
            "unmatchedTeacher": [
                {"teacherIndex": ti, "label": box["label"], "bbox": teacher_xyxy(box)}
                for ti, box in enumerate(teacher_boxes)
                if ti not in matched_teacher
            ],
        }

    subtype = {}
    for label in ("C1", "C3", "C4"):
        total = int(subtype_total[label])
        tp = int(subtype_tp[label])
        subtype[label] = {
            "teacherBoxes": total,
            "tp": tp,
            "fn": total - tp,
            "recall": tp / total if total else 0.0,
        }

    pooled = metric(total_tp, total_fp, total_fn)
    target_met = (
        pooled["precision"] >= MIN_PRECISION
        and pooled["recall"] >= MIN_RECALL
        and all(subtype[label]["recall"] >= MIN_SUBTYPE_RECALL for label in ("C1", "C3", "C4"))
    )
    return {
        "pooled": pooled,
        "perTeacherSubtype": subtype,
        "perPage": per_page,
        "qualificationTarget": {
            "precisionAtLeast": MIN_PRECISION,
            "recallAtLeast": MIN_RECALL,
            "eachSubtypeRecallAtLeast": MIN_SUBTYPE_RECALL,
            "met": bool(target_met),
        },
    }


def main() -> None:
    if RESULT_PATH.exists():
        raise RuntimeError(
            "P4.9 final result already exists. This holdout is one-shot; do not rerun or retune. "
            + str(RESULT_PATH)
        )

    if not MANIFEST_PATH.is_file():
        raise RuntimeError("P4.9 prepared manifest missing")
    manifest_sha = sha256_file(MANIFEST_PATH)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("P4.9 manifest SHA mismatch: " + manifest_sha)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    pages = manifest.get("pages", [])
    if manifest.get("pageCount") != EXPECTED_PAGE_COUNT or len(pages) != EXPECTED_PAGE_COUNT:
        raise RuntimeError("P4.9 manifest is not the frozen 11-page artifact")
    if manifest.get("detectorOutputsAccessed") is not False:
        raise RuntimeError("Unsafe P4.9 manifest provenance")

    p45 = load_frozen_p45()

    print("=" * 76)
    print("P4.9 INDEPENDENT HOLDOUT — FROZEN P4.8 POLICY")
    print("P4.7 holdout: NOT READ")
    print("Teacher truth: NOT READ during Phase A")
    print("P4.8 policy: FROZEN / NO RETUNING")
    print("=" * 76)

    frozen_pages: Dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="p49_canonical_") as temp_dir:
        temp_root = Path(temp_dir)
        for page_index, page in enumerate(pages, start=1):
            page_id = page["pageId"]
            image_path = PREPARED / page["imagePath"]
            if not image_path.is_file():
                raise RuntimeError("Prepared image missing: " + page_id)
            image_sha = sha256_file(image_path)
            if image_sha != page["imageSha256"]:
                raise RuntimeError("Prepared image SHA mismatch: " + page_id)

            gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if gray is None:
                raise RuntimeError("Unreadable P4.9 image: " + page_id)
            if int(gray.shape[1]) != int(page["width"]) or int(gray.shape[0]) != int(page["height"]):
                raise RuntimeError("Prepared image dimensions mismatch: " + page_id)

            original_candidates, original_diag = p45.generate_page_candidates(image_path)
            pre_staffs = p45.detect_staffs(gray)

            if pre_staffs:
                pre_spacing = float(statistics.median(float(staff["spacing"]) for staff in pre_staffs))
                canonical_factor = CANONICAL_STAFF_SPACING_PX / pre_spacing
                canonical_factor = min(MAX_CANONICAL_FACTOR, max(MIN_CANONICAL_FACTOR, canonical_factor))
                interp = cv2.INTER_CUBIC if canonical_factor >= 1.0 else cv2.INTER_AREA
                canonical_gray = cv2.resize(
                    gray,
                    None,
                    fx=canonical_factor,
                    fy=canonical_factor,
                    interpolation=interp,
                )
                canonical_path = temp_root / f"{page_id}.png"
                if not cv2.imwrite(str(canonical_path), canonical_gray):
                    raise RuntimeError("Could not write canonical temp image: " + page_id)
                canonical_candidates, canonical_diag = p45.generate_page_candidates(canonical_path)
            else:
                pre_spacing = None
                canonical_factor = 1.0
                canonical_candidates = []
                canonical_diag = {
                    "detectedStaffCount": 0,
                    "candidateCount": 0,
                    "imageWidth": int(gray.shape[1]),
                    "imageHeight": int(gray.shape[0]),
                }

            candidates, policy_diag = build_policy_candidates(
                gray,
                original_candidates,
                canonical_candidates,
                canonical_factor,
                pre_spacing,
            )
            frozen_pages[page_id] = {
                "pageId": page_id,
                "sourcePdfName": page["sourcePdfName"],
                "sourcePageNumber": page["sourcePageNumber"],
                "sourceImageSha256": image_sha,
                "originalDiagnostics": original_diag,
                "canonicalDiagnostics": canonical_diag,
                "policyDiagnostics": policy_diag,
                "candidates": candidates,
            }
            print(
                f"P4.9 GENERATED {page_index:02d}/{EXPECTED_PAGE_COUNT} {page_id} "
                f"preStaffs={len(pre_staffs)} accepted={len(candidates)} path={policy_diag['path']}"
            )

    frozen_payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_9-p4_8-policy-candidates-frozen.v1",
        "status": "PHASE_A_FROZEN_BEFORE_TEACHER_ACCESS",
        "holdout": "P4.9 independent",
        "p4_7HoldoutAccessed": False,
        "teacherTruthReadDuringCandidateGeneration": False,
        "sourceManifestSha256": manifest_sha,
        "pageCount": EXPECTED_PAGE_COUNT,
        "p4_5FrozenCommit": P45_COMMIT,
        "policy": {
            "routeSpacingPx": ROUTE_SPACING_PX,
            "canonicalStaffSpacingPx": CANONICAL_STAFF_SPACING_PX,
            "canonicalFactorClamp": [MIN_CANONICAL_FACTOR, MAX_CANONICAL_FACTOR],
            "verticalMirrorMinimum": VERTICAL_MIRROR_MIN,
            "bottomPaddingStaffSpaces": BOTTOM_PAD_STAFF_SPACES,
            "primaryIou": PRIMARY_IOU,
            "dedupIou": DEDUP_IOU,
        },
        "pages": frozen_pages,
    }
    atomic_json(FROZEN_CANDIDATES_PATH, frozen_payload)
    frozen_sha = sha256_file(FROZEN_CANDIDATES_PATH)
    print("PASS — P4.9 policy candidates frozen before teacher access")
    print("FROZEN CANDIDATES SHA-256:", frozen_sha)

    # Phase B begins only now.
    if not TEACHER_PATH.is_file():
        raise RuntimeError("P4.9 frozen teacher truth missing")
    teacher_sha = sha256_file(TEACHER_PATH)
    if teacher_sha != EXPECTED_TEACHER_SHA256:
        raise RuntimeError("P4.9 teacher truth SHA mismatch: " + teacher_sha)
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if teacher.get("sourceManifestSha256") != manifest_sha:
        raise RuntimeError("Teacher truth is not bound to the frozen P4.9 manifest")
    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("completedPageCount") != EXPECTED_PAGE_COUNT:
        raise RuntimeError("Teacher truth is not complete 11/11")
    if teacher.get("boxCount") != EXPECTED_TEACHER_BOX_COUNT:
        raise RuntimeError("Teacher box count changed")
    if teacher.get("labelCounts") != EXPECTED_LABEL_COUNTS:
        raise RuntimeError("Teacher label counts changed")
    if teacher.get("detectorOutputsAccessed") is not False:
        raise RuntimeError("Teacher annotation provenance violation")
    if set(teacher.get("pages", {})) != set(frozen_pages):
        raise RuntimeError("Teacher/manifest page IDs differ")

    measurement = evaluate(frozen_pages, teacher)
    target_met = bool(measurement["qualificationTarget"]["met"])

    result = {
        "schemaVersion": "stage11.v2d.c-clef-p4_9-holdout-evaluation.v1",
        "status": "COMPLETE",
        "holdout": "P4.9 independent",
        "oneShotQualificationRun": True,
        "p4_7HoldoutAccessed": False,
        "policyRetunedAfterHoldoutAccess": False,
        "teacherTruthReadDuringCandidateGeneration": False,
        "sourceManifestSha256": manifest_sha,
        "teacherTruthSha256": teacher_sha,
        "frozenCandidateArtifact": {
            "path": str(FROZEN_CANDIDATES_PATH),
            "sha256": frozen_sha,
        },
        "pageCount": EXPECTED_PAGE_COUNT,
        "teacherBoxCount": EXPECTED_TEACHER_BOX_COUNT,
        "measurement": measurement,
        "cClefDetectorQualifiedOnP4_9": target_met,
        "decisionBoundary": {
            "overallStage11PassAuthorized": False,
            "productionReady": False,
            "stage12EntryAuthorized": False,
            "noRetuningOnP4_9AfterResult": True,
        },
    }
    atomic_json(RESULT_PATH, result)
    result_sha = sha256_file(RESULT_PATH)

    print()
    print("=" * 76)
    print("P4.9 INDEPENDENT HOLDOUT COMPLETE")
    print("=" * 76)
    print("POOLED:", measurement["pooled"])
    print("SUBTYPE RECALL:", {k: v["recall"] for k, v in measurement["perTeacherSubtype"].items()})
    print("HOLDOUT TARGET MET:", target_met)
    print("cClefDetectorQualifiedOnP4_9:", target_met)
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", result_sha)
    print("NO RETUNING ON P4.9 HOLDOUT")


if __name__ == "__main__":
    main()
