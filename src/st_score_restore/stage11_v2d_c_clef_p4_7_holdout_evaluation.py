"""P4.7 independent holdout evaluation for the frozen C-clef detector.

The runner uses the exact frozen P4.5 source-image localizer and P4.6 geometric
filter. Candidate generation and filtering complete and are persisted before
teacher truth is opened. No threshold tuning is permitted after this run.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

FROZEN_P45_COMMIT = "7130bdf94bcf9247a0b33e9342db22746b46f289"
FROZEN_P46_COMMIT = "76caac8a7c76606bf09051ae5cd1704e32ef29dd"
P45_PATH = "src/st_score_restore/stage11_v2d_c_clef_p4_5_source_image_localizer.py"
P46_PATH = "src/st_score_restore/stage11_v2d_c_clef_p4_6_offline_filter.py"
REPO = "khfy7wpr5p-maker/st-score-restore-engine"

ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/P4_C_CLEF_HOLDOUT")
PREPARED = ROOT / "_PREPARED"
ANNOTATIONS = ROOT / "_ANNOTATIONS"
MANIFEST_PATH = PREPARED / "c_clef_holdout_source_page_manifest.v1.json"
TEACHER_PATH = ANNOTATIONS / "c_clef_holdout_teacher_boxes.v1.json"
OUT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/P4_C_CLEF_HOLDOUT_P4_7_RESULT")
RAW_PATH = OUT / "p4_7_holdout_raw_candidates.v1.json"
FILTERED_PATH = OUT / "p4_7_holdout_filtered_candidates.v1.json"
RESULT_PATH = OUT / "p4_7_holdout_evaluation_result.v1.json"

EXPECTED_MANIFEST_SHA256 = "4a9d525c467961e4fe6c7e1720a5bc6ec619946093bbb5ca8da337aac40dca25"
EXPECTED_TEACHER_SHA256 = "309bdd3858e71b5770d97f2f9f150075a9694ce4c75590fb22958ff2be24e4c0"
EXPECTED_PAGE_COUNT = 15
EXPECTED_TEACHER_BOXES = 25
EXPECTED_LABEL_COUNTS = {"C1": 10, "C3": 10, "C4": 5, "AMBIGUOUS": 0}
PRIMARY_IOU = 0.50

TARGET_POOLED_PRECISION = 0.80
TARGET_POOLED_RECALL = 0.90
TARGET_SUBTYPE_RECALL = 0.80
TARGET_GROUP_PRECISION = 0.80
TARGET_GROUP_RECALL = 0.80


def fail(message: str) -> None:
    raise RuntimeError("P4.7 HOLDOUT BLOCKED: " + message)


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


def raw_url(commit: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{REPO}/{commit}/{path}"


def load_pinned_module(name: str, commit: str, path: str, workdir: Path):
    workdir.mkdir(parents=True, exist_ok=True)
    target = workdir / f"{name}.py"
    source = urllib.request.urlopen(raw_url(commit, path), timeout=60).read()
    target.write_bytes(source)
    spec = importlib.util.spec_from_file_location(name, target)
    if spec is None or spec.loader is None:
        fail("Cannot load frozen module: " + name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, hashlib.sha256(source).hexdigest()


def metric(tp: int, fp: int, fn: int) -> Dict[str, Any]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def teacher_xyxy(box: Dict[str, Any]) -> List[float]:
    x = float(box["x"])
    y = float(box["y"])
    w = float(box["w"])
    h = float(box["h"])
    return [x, y, x + w, y + h]


def greedy_match(p45, accepted_items: Sequence[Dict[str, Any]], teacher_boxes: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges: List[Tuple[float, int, int]] = []
    for accepted_index, item in enumerate(accepted_items):
        candidate = item["candidate"]
        for teacher_index, teacher_box in enumerate(teacher_boxes):
            score = p45.box_iou(candidate["bbox"], teacher_xyxy(teacher_box))
            if score >= PRIMARY_IOU:
                edges.append((float(score), accepted_index, teacher_index))
    edges.sort(key=lambda row: row[0], reverse=True)

    used_candidates = set()
    used_teacher = set()
    matches: List[Dict[str, Any]] = []
    for score, accepted_index, teacher_index in edges:
        if accepted_index in used_candidates or teacher_index in used_teacher:
            continue
        used_candidates.add(accepted_index)
        used_teacher.add(teacher_index)
        item = accepted_items[accepted_index]
        teacher_box = teacher_boxes[teacher_index]
        matches.append({
            "iou": score,
            "acceptedIndex": accepted_index,
            "originalCandidateIndex": int(item["candidateIndex"]),
            "teacherIndex": teacher_index,
            "teacherLabel": teacher_box["label"],
            "teacherBox": teacher_xyxy(teacher_box),
        })
    return matches


def main() -> None:
    started = time.time()
    print("=" * 76)
    print("ST SCORE RESTORE — P4.7 INDEPENDENT C-CLEF HOLDOUT")
    print("Frozen P4.5 localizer + frozen P4.6 filter")
    print("No EOMER / No ONNX / No GPU / No model inference")
    print("No post-holdout tuning permitted")
    print("=" * 76)

    if not MANIFEST_PATH.is_file():
        fail("Holdout manifest missing")
    manifest_sha = sha256_file(MANIFEST_PATH)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        fail("Holdout manifest SHA mismatch: " + manifest_sha)

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    pages = manifest.get("pages")
    if manifest.get("pageCount") != EXPECTED_PAGE_COUNT or not isinstance(pages, list) or len(pages) != EXPECTED_PAGE_COUNT:
        fail("Holdout manifest is not the frozen 15-page artifact")
    if manifest.get("labelCounts") != {"C1": 5, "C3": 5, "C4": 5}:
        fail("Holdout manifest page-group counts changed")
    page_ids = [page.get("pageId") for page in pages]
    if len(set(page_ids)) != EXPECTED_PAGE_COUNT:
        fail("Holdout page IDs are not unique")

    module_dir = OUT / "_frozen_modules"
    p45, p45_source_sha = load_pinned_module("p4_5_frozen", FROZEN_P45_COMMIT, P45_PATH, module_dir)
    p46, p46_source_sha = load_pinned_module("p4_6_frozen", FROZEN_P46_COMMIT, P46_PATH, module_dir)

    if float(p45.PRIMARY_IOU) != PRIMARY_IOU:
        fail("Frozen P4.5 IoU drift")
    if p46.FILTER_ID != "source-image-c-clef-geometric-filter.p4_6.v1":
        fail("Frozen P4.6 filter ID drift")
    expected_thresholds = (4.15, 9.80, 2.00, 6.10, 12.00, 5.00)
    actual_thresholds = (
        float(p46.LOW_AREA), float(p46.HIGH_AREA), float(p46.MIN_WIDTH),
        float(p46.MAX_HEIGHT), float(p46.LOW_SPACING), float(p46.MIN_HEIGHT_LOW_SPACING),
    )
    if actual_thresholds != expected_thresholds:
        fail("Frozen P4.6 threshold drift: " + repr(actual_thresholds))

    # ------------------------------------------------------------------
    # PHASE A — source-only candidate generation. Teacher truth is not read.
    # ------------------------------------------------------------------
    raw_pages: Dict[str, Any] = {}
    manifest_meta: Dict[str, Dict[str, Any]] = {}
    for page_index, page in enumerate(pages, start=1):
        page_id = page["pageId"]
        image_path = (PREPARED / page["imagePath"]).resolve()
        if image_path != PREPARED and PREPARED not in image_path.parents:
            fail("Unsafe holdout imagePath: " + page_id)
        if not image_path.is_file():
            fail("Holdout image missing: " + page_id)
        actual_image_sha = sha256_file(image_path)
        if actual_image_sha != page["imageSha256"]:
            fail("Holdout image SHA mismatch: " + page_id)

        candidates, diagnostics = p45.generate_page_candidates(image_path)
        raw_pages[page_id] = {
            "pageId": page_id,
            "sourceImageSha256": actual_image_sha,
            "diagnostics": diagnostics,
            "candidates": candidates,
        }
        manifest_meta[page_id] = {
            "labelHint": page.get("labelHint"),
            "sourceFamily": page.get("sourceFamily"),
            "sourcePdfName": page.get("sourcePdfName"),
        }
        print(
            f"P4.7 GENERATED {page_index:02d}/{EXPECTED_PAGE_COUNT} {page_id} "
            f"| staffs={diagnostics['detectedStaffCount']} candidates={diagnostics['candidateCount']}"
        )

    raw_payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_7-holdout-raw-candidates.v1",
        "status": "FROZEN_BEFORE_TEACHER_EVALUATION",
        "heldOut": True,
        "sourceOnly": True,
        "sourceManifestSha256": manifest_sha,
        "pageCount": EXPECTED_PAGE_COUNT,
        "teacherTruthReadDuringCandidateGeneration": False,
        "p4_5Commit": FROZEN_P45_COMMIT,
        "p4_5SourceSha256": p45_source_sha,
        "eomerUsed": False,
        "onnxUsed": False,
        "gpuUsed": False,
        "pages": raw_pages,
    }
    atomic_json(RAW_PATH, raw_payload)
    raw_sha = sha256_file(RAW_PATH)
    print("PASS — holdout raw candidates frozen before teacher access")
    print("RAW SHA-256:", raw_sha)

    # ------------------------------------------------------------------
    # PHASE B — frozen P4.6 geometry filter. Teacher truth is still unread.
    # ------------------------------------------------------------------
    filtered_pages: Dict[str, Any] = {}
    accepted_total = 0
    rejected_total = 0
    rejection_totals = Counter()
    for page_id, page in raw_pages.items():
        accepted = []
        rejected = []
        for candidate_index, candidate in enumerate(page["candidates"]):
            keep, reasons = p46.filter_candidate(candidate)
            item = {"candidateIndex": candidate_index, "candidate": candidate}
            if keep:
                accepted.append(item)
                accepted_total += 1
            else:
                rejected.append({**item, "reasons": reasons})
                rejected_total += 1
                rejection_totals.update(reasons)
        filtered_pages[page_id] = {
            "pageId": page_id,
            "accepted": accepted,
            "rejected": rejected,
        }

    filtered_payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_7-holdout-filtered-candidates.v1",
        "status": "FROZEN_BEFORE_TEACHER_EVALUATION",
        "heldOut": True,
        "teacherTruthReadDuringFiltering": False,
        "pageIdUsedByFilter": False,
        "sourceGroupUsedByFilter": False,
        "filterId": p46.FILTER_ID,
        "p4_6Commit": FROZEN_P46_COMMIT,
        "p4_6SourceSha256": p46_source_sha,
        "sourceRawCandidateSha256": raw_sha,
        "acceptedCandidateCount": accepted_total,
        "rejectedCandidateCount": rejected_total,
        "rejectionReasonTotals": dict(rejection_totals),
        "thresholds": {
            "minimumAreaInStaffSpacesSquared": p46.LOW_AREA,
            "maximumAreaInStaffSpacesSquared": p46.HIGH_AREA,
            "minimumWidthInStaffSpaces": p46.MIN_WIDTH,
            "maximumHeightInStaffSpaces": p46.MAX_HEIGHT,
            "lowStaffSpacingThreshold": p46.LOW_SPACING,
            "minimumHeightWhenLowStaffSpacing": p46.MIN_HEIGHT_LOW_SPACING,
        },
        "pages": filtered_pages,
    }
    atomic_json(FILTERED_PATH, filtered_payload)
    filtered_sha = sha256_file(FILTERED_PATH)
    print(f"PASS — frozen P4.6 filter complete: {accepted_total} accepted / {rejected_total} rejected")
    print("FILTERED SHA-256:", filtered_sha)

    # ------------------------------------------------------------------
    # PHASE C — first teacher access and one-shot holdout evaluation.
    # ------------------------------------------------------------------
    if not TEACHER_PATH.is_file():
        fail("Frozen holdout teacher truth missing")
    teacher_sha = sha256_file(TEACHER_PATH)
    if teacher_sha != EXPECTED_TEACHER_SHA256:
        fail("Holdout teacher SHA mismatch: " + teacher_sha)
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if teacher.get("sourceManifestSha256") != manifest_sha:
        fail("Teacher truth is not bound to frozen holdout manifest")
    if teacher.get("pageCount") != EXPECTED_PAGE_COUNT or teacher.get("completedPageCount") != EXPECTED_PAGE_COUNT:
        fail("Holdout teacher annotation is incomplete")
    if teacher.get("boxCount") != EXPECTED_TEACHER_BOXES:
        fail("Holdout teacher box count changed")
    if teacher.get("labelCounts") != EXPECTED_LABEL_COUNTS:
        fail("Holdout teacher label counts changed")
    if set(teacher.get("pages", {})) != set(page_ids):
        fail("Holdout teacher page IDs differ from manifest")

    pooled_tp = pooled_fp = pooled_fn = 0
    subtype_teacher = Counter()
    subtype_tp = Counter()
    group_teacher = Counter()
    group_tp = Counter()
    group_fp = Counter()
    per_page: Dict[str, Any] = {}

    for page_id in page_ids:
        accepted = filtered_pages[page_id]["accepted"]
        teacher_boxes = teacher["pages"][page_id]["boxes"]
        matches = greedy_match(p45, accepted, teacher_boxes)
        matched_teacher = {m["teacherIndex"] for m in matches}

        tp = len(matches)
        fp = len(accepted) - tp
        fn = len(teacher_boxes) - tp
        pooled_tp += tp
        pooled_fp += fp
        pooled_fn += fn

        for teacher_index, box in enumerate(teacher_boxes):
            label = box["label"]
            if label in ("C1", "C3", "C4"):
                subtype_teacher[label] += 1
                if teacher_index in matched_teacher:
                    subtype_tp[label] += 1

        group = manifest_meta[page_id]["labelHint"]
        group_teacher[group] += len(teacher_boxes)
        group_tp[group] += tp
        group_fp[group] += fp

        per_page[page_id] = {
            "manifestGroup": group,
            "sourceFamily": manifest_meta[page_id]["sourceFamily"],
            "sourcePdfName": manifest_meta[page_id]["sourcePdfName"],
            "teacherBoxCount": len(teacher_boxes),
            "acceptedCandidateCount": len(accepted),
            "metrics": metric(tp, fp, fn),
            "matches": matches,
            "unmatchedTeacherBoxes": [
                {"teacherIndex": i, "label": box["label"], "bbox": teacher_xyxy(box)}
                for i, box in enumerate(teacher_boxes)
                if i not in matched_teacher
            ],
        }

    pooled = metric(pooled_tp, pooled_fp, pooled_fn)
    subtype = {}
    for label in ("C1", "C3", "C4"):
        total = int(subtype_teacher[label])
        tp = int(subtype_tp[label])
        subtype[label] = {
            "teacherBoxes": total,
            "tp": tp,
            "fn": total - tp,
            "recall": tp / total if total else 0.0,
        }

    groups = {}
    for group in sorted(group_teacher):
        total = int(group_teacher[group])
        tp = int(group_tp[group])
        fp = int(group_fp[group])
        groups[group] = metric(tp, fp, total - tp)
        groups[group]["teacherBoxes"] = total

    target_met = (
        pooled["precision"] >= TARGET_POOLED_PRECISION
        and pooled["recall"] >= TARGET_POOLED_RECALL
        and all(v["recall"] >= TARGET_SUBTYPE_RECALL for v in subtype.values())
        and all(
            v["precision"] >= TARGET_GROUP_PRECISION and v["recall"] >= TARGET_GROUP_RECALL
            for v in groups.values()
        )
    )

    result = {
        "schemaVersion": "stage11.v2d.c-clef-p4_7-independent-holdout-result.v1",
        "status": "COMPLETE",
        "heldOut": True,
        "qualificationEvidence": True,
        "firstTeacherAccessAfterCandidateAndFilterFreeze": True,
        "postHoldoutRetuningAllowed": False,
        "sourceManifestSha256": manifest_sha,
        "teacherTruthSha256": teacher_sha,
        "rawCandidateSha256": raw_sha,
        "filteredCandidateSha256": filtered_sha,
        "frozenImplementation": {
            "p4_5Commit": FROZEN_P45_COMMIT,
            "p4_5SourceSha256": p45_source_sha,
            "p4_6Commit": FROZEN_P46_COMMIT,
            "p4_6SourceSha256": p46_source_sha,
            "filterId": p46.FILTER_ID,
            "primaryIoU": PRIMARY_IOU,
        },
        "pageCount": EXPECTED_PAGE_COUNT,
        "teacherBoxCount": EXPECTED_TEACHER_BOXES,
        "pooled": pooled,
        "perTeacherSubtype": subtype,
        "perManifestGroup": groups,
        "perPage": per_page,
        "predeclaredTargets": {
            "pooledPrecisionMinimum": TARGET_POOLED_PRECISION,
            "pooledRecallMinimum": TARGET_POOLED_RECALL,
            "eachTeacherSubtypeRecallMinimum": TARGET_SUBTYPE_RECALL,
            "eachManifestGroupPrecisionMinimum": TARGET_GROUP_PRECISION,
            "eachManifestGroupRecallMinimum": TARGET_GROUP_RECALL,
        },
        "decision": {
            "holdoutTargetMet": bool(target_met),
            "detectorQualified": bool(target_met),
            "productionInferenceAuthorized": False,
            "overallStage11PassAuthorized": False,
            "stage12EntryAuthorized": False,
            "nextSafeAction": (
                "Record P4.7 as independent holdout PASS; retain frozen P4.6 without retuning."
                if target_met
                else "Record P4.7 as holdout FAIL. Do not retune P4.6 on this holdout; create a new detector version using development data only."
            ),
        },
        "runtimeSeconds": time.time() - started,
    }
    atomic_json(RESULT_PATH, result)
    result_sha = sha256_file(RESULT_PATH)

    print()
    print("=" * 76)
    print("P4.7 INDEPENDENT HOLDOUT COMPLETE")
    print("=" * 76)
    print("POOLED:", pooled)
    print("SUBTYPE RECALL:", {k: v["recall"] for k, v in subtype.items()})
    print("GROUP METRICS:", groups)
    print("HOLDOUT TARGET MET:", target_met)
    print("detectorQualified:", bool(target_met))
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", result_sha)
    print("NO RETUNING ON THIS HOLDOUT")


if __name__ == "__main__":
    main()
