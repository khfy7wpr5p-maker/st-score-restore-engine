"""P4.10 diagnostic for the failed P4.9 independent C-clef holdout.

This is NOT a qualification run and MUST NOT retune the frozen P4.8 policy.
P4.9 is spent holdout evidence. It is read here only to classify the failure
mechanisms that produced the frozen P4.9 result. Any future detector revision
requires a brand-new independent holdout for qualification.
"""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import tempfile
import types
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import cv2

ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/P4_C_CLEF_HOLDOUT_P4_9")
PREPARED = ROOT / "_PREPARED"
MANIFEST_PATH = PREPARED / "c_clef_p4_9_holdout_source_page_manifest.v1.json"
TEACHER_PATH = ROOT / "_ANNOTATIONS" / "c_clef_p4_9_holdout_teacher_boxes.v1.json"
P49_RESULT_DIR = ROOT / "_RESULT"
FROZEN_CANDIDATES_PATH = P49_RESULT_DIR / "p4_9_p4_8_policy_candidates_frozen_before_teacher.v1.json"
P49_RESULT_PATH = P49_RESULT_DIR / "p4_9_p4_8_holdout_evaluation_result.v1.json"
OUT = ROOT / "_P4_10_DIAGNOSTIC"
RESULT_PATH = OUT / "p4_10_p4_9_failure_root_cause_diagnostic.v1.json"

EXPECTED_MANIFEST_SHA256 = "8db0cf576137ec8cfd8458dd5b9cead73f49b4b2910bf6436e31e1e3737a7ece"
EXPECTED_TEACHER_SHA256 = "8ce56115b519df0429ec37964de9e694c44a0fdf081b74c9bff0484bf248f095"
EXPECTED_FROZEN_CANDIDATES_SHA256 = "5ddd472575019d7f502834f1e551daa1562757f88b3c634c2a19e139dfad9e8c"
EXPECTED_P49_RESULT_SHA256 = "102c3b56299436cb4a8f8be6aa059dd39e1ab1e361775626ef54c7802c048dea"
EXPECTED_PAGE_COUNT = 11
EXPECTED_BOX_COUNT = 38
EXPECTED_LABEL_COUNTS = {"C1": 12, "C3": 21, "C4": 5, "AMBIGUOUS": 0}
EXPECTED_POOLED = (7, 13, 31)

P49_COMMIT = "ac8e2bf2b29cd50d2395535a128485a49277ceb7"
P49_URL = (
    "https://raw.githubusercontent.com/khfy7wpr5p-maker/st-score-restore-engine/"
    + P49_COMMIT
    + "/src/st_score_restore/stage11_v2d_c_clef_p4_9_holdout_evaluation.py"
)

IOU_NEAR_MISS = 0.30
IOU_MATCH = 0.50


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


def load_p49_module():
    data = urllib.request.urlopen(P49_URL, timeout=60).read()
    module = types.ModuleType("p49_frozen_for_p410_diagnostic")
    module.__file__ = "stage11_v2d_c_clef_p4_9_holdout_evaluation.py"
    exec(compile(data.decode("utf-8"), module.__file__, "exec"), module.__dict__)
    return module, sha256_bytes(data)


def mapped_canonical(candidate: Dict[str, Any], factor: float) -> Dict[str, Any]:
    item = dict(candidate)
    item["bbox"] = [float(v) / factor for v in candidate["bbox"]]
    item["spacingInput"] = float(candidate["staffSpacing"]) / factor
    return item


def max_iou(p49, candidates: Sequence[Dict[str, Any]], teacher_bbox: Sequence[float]) -> float:
    if not candidates:
        return 0.0
    return max(float(p49.box_iou(c["bbox"], teacher_bbox)) for c in candidates)


def matching_candidates(p49, candidates: Sequence[Dict[str, Any]], teacher_bbox: Sequence[float], threshold: float) -> List[Dict[str, Any]]:
    out = []
    for candidate in candidates:
        score = float(p49.box_iou(candidate["bbox"], teacher_bbox))
        if score >= threshold:
            out.append({"candidate": candidate, "iou": score})
    out.sort(key=lambda x: x["iou"], reverse=True)
    return out


def classify_fn(
    p49,
    gray,
    teacher_bbox: Sequence[float],
    pre_staffs: Sequence[Dict[str, Any]],
    pre_spacing: float | None,
    canonical_factor: float,
    original_raw: Sequence[Dict[str, Any]],
    canonical_raw_source: Sequence[Dict[str, Any]],
    original_p46: Sequence[Dict[str, Any]],
    canonical_p48: Sequence[Dict[str, Any]],
    final_candidates: Sequence[Dict[str, Any]],
) -> Tuple[str, Dict[str, Any]]:
    best = {
        "originalRaw": max_iou(p49, original_raw, teacher_bbox),
        "canonicalRaw": max_iou(p49, canonical_raw_source, teacher_bbox),
        "originalP46": max_iou(p49, original_p46, teacher_bbox),
        "canonicalP48": max_iou(p49, canonical_p48, teacher_bbox),
        "finalPolicy": max_iou(p49, final_candidates, teacher_bbox),
    }

    details: Dict[str, Any] = {
        "preStaffCount": len(pre_staffs),
        "preCanonicalMedianStaffSpacing": pre_spacing,
        "canonicalFactor": canonical_factor,
        "maxIoUByStage": best,
    }

    if not pre_staffs:
        return "STAFF_DETECTION_FAILURE", details

    # If a final candidate geometrically covers the teacher box but greedy matching
    # assigned it elsewhere, this is an assignment conflict rather than a detector miss.
    if best["finalPolicy"] >= IOU_MATCH:
        return "GREEDY_MATCH_ASSIGNMENT_CONFLICT", details

    best_raw = max(best["originalRaw"], best["canonicalRaw"])
    if best_raw < IOU_NEAR_MISS:
        return "LOCALIZER_MISS", details
    if best_raw < IOU_MATCH:
        return "LOCALIZER_GEOMETRY_NEAR_MISS", details

    low_spacing_route = pre_spacing is not None and pre_spacing < float(p49.ROUTE_SPACING_PX)

    # Frozen low-spacing route discards original path entirely.
    if low_spacing_route:
        if best["canonicalRaw"] < IOU_MATCH and best["originalRaw"] >= IOU_MATCH:
            return "ROUTING_CANONICAL_ONLY_LOST_ORIGINAL_MATCH", details
        if best["canonicalRaw"] >= IOU_MATCH and best["canonicalP48"] < IOU_MATCH:
            return "CANONICAL_FILTER_REJECTION", details
        if best["canonicalP48"] >= IOU_MATCH and best["finalPolicy"] < IOU_MATCH:
            return "BBOX_PADDING_OR_FINAL_GEOMETRY_FAILURE", details
        return "LOW_SPACING_PATH_UNRESOLVED", details

    # Normal route: frozen P4.6 originals first, then gated canonical additions.
    if best["originalRaw"] >= IOU_MATCH:
        if best["originalP46"] < IOU_MATCH:
            return "ORIGINAL_P46_FILTER_REJECTION", details
        if best["finalPolicy"] < IOU_MATCH:
            return "BBOX_PADDING_OR_FINAL_GEOMETRY_FAILURE", details

    if best["canonicalRaw"] >= IOU_MATCH:
        if best["canonicalP48"] < IOU_MATCH:
            return "CANONICAL_P48_FILTER_REJECTION", details

        canon_matches = matching_candidates(p49, canonical_p48, teacher_bbox, IOU_MATCH)
        dedup_hits = 0
        mirror_rejects = 0
        mirror_values: List[float] = []
        for row in canon_matches:
            c = row["candidate"]
            if any(p49.box_iou(c["bbox"], o["bbox"]) >= float(p49.DEDUP_IOU) for o in original_p46):
                dedup_hits += 1
                continue
            mirror = float(p49.vertical_mirror_similarity(gray, c["bbox"], float(c["spacingInput"])))
            mirror_values.append(mirror)
            if mirror < float(p49.VERTICAL_MIRROR_MIN):
                mirror_rejects += 1

        details["matchingCanonicalP48Count"] = len(canon_matches)
        details["matchingCanonicalDedupHits"] = dedup_hits
        details["matchingCanonicalMirrorValues"] = mirror_values
        details["matchingCanonicalMirrorRejects"] = mirror_rejects

        if canon_matches and dedup_hits == len(canon_matches):
            return "CANONICAL_DEDUP_SUPPRESSION", details
        if mirror_rejects > 0 and mirror_rejects + dedup_hits == len(canon_matches):
            return "SHAPE_MIRROR_GATE_REJECTION", details
        if best["finalPolicy"] < IOU_MATCH:
            return "BBOX_PADDING_OR_FINAL_GEOMETRY_FAILURE", details

    return "UNRESOLVED_POLICY_FAILURE", details


def main() -> None:
    required = (
        (MANIFEST_PATH, EXPECTED_MANIFEST_SHA256),
        (TEACHER_PATH, EXPECTED_TEACHER_SHA256),
        (FROZEN_CANDIDATES_PATH, EXPECTED_FROZEN_CANDIDATES_SHA256),
        (P49_RESULT_PATH, EXPECTED_P49_RESULT_SHA256),
    )
    for path, expected in required:
        if not path.is_file():
            raise RuntimeError(f"Required P4.9 artifact missing: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"P4.9 artifact SHA mismatch for {path.name}: {actual}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    frozen = json.loads(FROZEN_CANDIDATES_PATH.read_text(encoding="utf-8"))
    p49_result = json.loads(P49_RESULT_PATH.read_text(encoding="utf-8"))

    if manifest.get("pageCount") != EXPECTED_PAGE_COUNT:
        raise RuntimeError("Unexpected P4.9 manifest page count")
    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("boxCount") != EXPECTED_BOX_COUNT:
        raise RuntimeError("Unexpected frozen P4.9 teacher dimensions")
    if teacher.get("labelCounts") != EXPECTED_LABEL_COUNTS:
        raise RuntimeError("P4.9 teacher label counts changed")
    if frozen.get("teacherTruthReadDuringCandidateGeneration") is not False:
        raise RuntimeError("Unsafe P4.9 candidate provenance")

    pooled = p49_result["measurement"]["pooled"] if "measurement" in p49_result else p49_result["pooled"]
    observed = (int(pooled["tp"]), int(pooled["fp"]), int(pooled["fn"]))
    if observed != EXPECTED_POOLED:
        raise RuntimeError(f"P4.9 result no longer matches frozen 7/13/31 result: {observed}")

    p49, p49_source_sha = load_p49_module()
    p45 = p49.load_frozen_p45()

    # Re-evaluate frozen candidates as an integrity assertion before diagnosis.
    replay = p49.evaluate(frozen["pages"], teacher)
    replay_pooled = replay["pooled"]
    replay_tuple = (int(replay_pooled["tp"]), int(replay_pooled["fp"]), int(replay_pooled["fn"]))
    if replay_tuple != EXPECTED_POOLED:
        raise RuntimeError(f"Frozen P4.9 replay mismatch: {replay_tuple}")

    print("=" * 78)
    print("P4.10 P4.9 FAILURE ROOT-CAUSE DIAGNOSTIC")
    print("P4.9 qualification status: SPENT / FAILED")
    print("Policy retuning in this runner: FORBIDDEN")
    print("Frozen replay:", replay_tuple)
    print("=" * 78)

    per_fn: List[Dict[str, Any]] = []
    categories = Counter()
    categories_by_subtype: Dict[str, Counter] = defaultdict(Counter)
    per_page_summary: Dict[str, Any] = {}

    with tempfile.TemporaryDirectory(prefix="p410_diag_") as td:
        temp_root = Path(td)
        for page_index, page in enumerate(manifest["pages"], start=1):
            page_id = page["pageId"]
            image_path = PREPARED / page["imagePath"]
            if not image_path.is_file() or sha256_file(image_path) != page["imageSha256"]:
                raise RuntimeError("Prepared image integrity failure: " + page_id)
            gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if gray is None:
                raise RuntimeError("Unreadable prepared image: " + page_id)

            original_raw, original_diag = p45.generate_page_candidates(image_path)
            pre_staffs = p45.detect_staffs(gray)
            if pre_staffs:
                pre_spacing = float(statistics.median(float(s["spacing"]) for s in pre_staffs))
                factor = float(p49.CANONICAL_STAFF_SPACING_PX) / pre_spacing
                factor = min(float(p49.MAX_CANONICAL_FACTOR), max(float(p49.MIN_CANONICAL_FACTOR), factor))
                interpolation = cv2.INTER_CUBIC if factor >= 1.0 else cv2.INTER_AREA
                canonical_gray = cv2.resize(gray, None, fx=factor, fy=factor, interpolation=interpolation)
                canonical_path = temp_root / f"{page_id}.png"
                if not cv2.imwrite(str(canonical_path), canonical_gray):
                    raise RuntimeError("Could not write diagnostic canonical image")
                canonical_raw_native, canonical_diag = p45.generate_page_candidates(canonical_path)
                canonical_raw_source = [mapped_canonical(c, factor) for c in canonical_raw_native]
            else:
                pre_spacing = None
                factor = 1.0
                canonical_raw_source = []
                canonical_diag = {"detectedStaffCount": 0, "candidateCount": 0}

            original_p46 = []
            for c in original_raw:
                if p49.p46_keep(c):
                    item = dict(c)
                    item["bbox"] = list(map(float, c["bbox"]))
                    item["spacingInput"] = float(c["staffSpacing"])
                    original_p46.append(item)

            canonical_p48 = []
            for c in canonical_raw_source:
                # p48_keep is scale-invariant because normalized geometry remains unchanged.
                if p49.p48_keep(c):
                    canonical_p48.append(dict(c))

            final_candidates = frozen["pages"][page_id]["candidates"]
            teacher_boxes = teacher["pages"][page_id]["boxes"]
            final_matches = p49.greedy_match(final_candidates, teacher_boxes)
            matched_teacher = {ti for _, ti, _ in final_matches}

            page_counter = Counter()
            for ti, box in enumerate(teacher_boxes):
                if ti in matched_teacher:
                    continue
                teacher_bbox = p49.teacher_xyxy(box)
                category, details = classify_fn(
                    p49,
                    gray,
                    teacher_bbox,
                    pre_staffs,
                    pre_spacing,
                    factor,
                    original_raw,
                    canonical_raw_source,
                    original_p46,
                    canonical_p48,
                    final_candidates,
                )
                label = str(box["label"])
                categories[category] += 1
                categories_by_subtype[label][category] += 1
                page_counter[category] += 1
                per_fn.append({
                    "pageId": page_id,
                    "sourcePdfName": teacher["pages"][page_id]["sourcePdfName"],
                    "sourcePageNumber": teacher["pages"][page_id]["sourcePageNumber"],
                    "teacherIndex": ti,
                    "label": label,
                    "teacherBbox": teacher_bbox,
                    "rootCause": category,
                    "diagnostics": details,
                })

            per_page_summary[page_id] = {
                "teacherBoxes": len(teacher_boxes),
                "finalMatches": len(final_matches),
                "falseNegatives": len(teacher_boxes) - len(final_matches),
                "preStaffCount": len(pre_staffs),
                "originalRawCandidates": len(original_raw),
                "canonicalRawCandidates": len(canonical_raw_source),
                "originalP46Candidates": len(original_p46),
                "canonicalP48Candidates": len(canonical_p48),
                "finalPolicyCandidates": len(final_candidates),
                "rootCauseCounts": dict(page_counter),
                "originalDiagnostics": original_diag,
                "canonicalDiagnostics": canonical_diag,
            }
            print(
                f"P4.10 {page_index:02d}/{EXPECTED_PAGE_COUNT} {page_id} | "
                f"staffs={len(pre_staffs)} finalTP={len(final_matches)} FN={len(teacher_boxes)-len(final_matches)}"
            )

    if len(per_fn) != EXPECTED_POOLED[2]:
        raise RuntimeError(f"Expected 31 diagnosed FNs, got {len(per_fn)}")

    payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_10-p4_9-failure-root-cause.v1",
        "status": "DIAGNOSTIC_COMPLETE",
        "diagnosticOnly": True,
        "p4_9HoldoutStatus": "SPENT_FAILED_HOLDOUT",
        "p4_9UsedForQualificationRetuning": False,
        "futureQualificationRequiresBrandNewIndependentHoldout": True,
        "p4_8PolicyChanged": False,
        "p4_9RunnerCommit": P49_COMMIT,
        "p4_9RunnerSourceSha256Observed": p49_source_sha,
        "frozenInputs": {
            "manifestSha256": EXPECTED_MANIFEST_SHA256,
            "teacherSha256": EXPECTED_TEACHER_SHA256,
            "frozenCandidatesSha256": EXPECTED_FROZEN_CANDIDATES_SHA256,
            "p4_9ResultSha256": EXPECTED_P49_RESULT_SHA256,
            "expectedPooled": {"tp": 7, "fp": 13, "fn": 31},
        },
        "rootCauseCounts": dict(categories),
        "rootCauseCountsBySubtype": {k: dict(v) for k, v in categories_by_subtype.items()},
        "perPage": per_page_summary,
        "falseNegatives": per_fn,
        "decisionBoundary": {
            "detectorQualified": False,
            "productionInferenceAuthorized": False,
            "overallStage11PassAuthorized": False,
            "stage12Authorized": False,
        },
    }
    atomic_json(RESULT_PATH, payload)

    print("=" * 78)
    print("P4.10 ROOT-CAUSE DIAGNOSTIC COMPLETE")
    print("Diagnosed FN:", len(per_fn))
    print("ROOT CAUSES:")
    for name, count in categories.most_common():
        print(f"  {name}: {count}")
    print("BY SUBTYPE:")
    for subtype in ("C1", "C3", "C4"):
        print(" ", subtype, dict(categories_by_subtype[subtype]))
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", sha256_file(RESULT_PATH))
    print("P4.8 policy changed: False")
    print("NEXT: use diagnosis to design P4.10 development work; P4.9 cannot qualify it")


if __name__ == "__main__":
    main()
