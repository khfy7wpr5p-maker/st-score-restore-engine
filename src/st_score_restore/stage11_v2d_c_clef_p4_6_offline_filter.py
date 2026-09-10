"""P4.6 offline false-positive filter for frozen P4.5 C-clef candidates.

Development-only. No EOMER/ONNX/GPU/model inference. The filter consumes only
candidate geometry. Teacher-derived P4.5 match data is loaded only after the
filter output has been materialized, for development remeasurement.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL")
P45 = ROOT / "P4_C_CLEF_SOURCE_LOCALIZER_P4_5"
CANDIDATE_PATH = P45 / "p4_5_source_image_candidates.v1.json"
MEASUREMENT_PATH = P45 / "p4_5_source_image_localizer_result.v1.json"
OUT = ROOT / "P4_C_CLEF_FILTER_P4_6"
FILTERED_PATH = OUT / "p4_6_filtered_candidates.v1.json"
RESULT_PATH = OUT / "p4_6_development_filter_result.v1.json"

EXPECTED_CANDIDATE_SHA256 = "0c1c921d0c0f19849a9eb36efabe4f1dc658ca4d7a3d3aa904f1c42d97157832"
EXPECTED_MEASUREMENT_SHA256 = "e2a046fdbba52ff1394b3676c1e103f26518da7ff5306d68ee1026eff5de2e45"
EXPECTED_PAGE_COUNT = 29
EXPECTED_TEACHER_BOXES = 71
FILTER_ID = "source-image-c-clef-geometric-filter.p4_6.v1"

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


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def filter_candidate(candidate: dict) -> tuple[bool, list[str]]:
    """Pure candidate-geometry filter. No teacher/page/source-group input."""
    area = float(candidate["areaInStaffSpacesSquared"])
    width = float(candidate["widthInStaffSpaces"])
    height = float(candidate["heightInStaffSpaces"])
    spacing = float(candidate["staffSpacing"])
    reasons: list[str] = []

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
    return not reasons, reasons


def metric(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def main() -> None:
    print("=" * 72)
    print("ST SCORE RESTORE — P4.6 OFFLINE C-CLEF FILTER")
    print("No EOMER / No ONNX / No GPU / No model inference")
    print("=" * 72)

    for path in (CANDIDATE_PATH, MEASUREMENT_PATH):
        if not path.is_file():
            raise RuntimeError(f"Required P4.5 artifact missing: {path}")

    csha = sha256_file(CANDIDATE_PATH)
    msha = sha256_file(MEASUREMENT_PATH)
    if csha != EXPECTED_CANDIDATE_SHA256:
        raise RuntimeError(f"P4.5 candidate SHA mismatch: {csha}")
    if msha != EXPECTED_MEASUREMENT_SHA256:
        raise RuntimeError(f"P4.5 measurement SHA mismatch: {msha}")

    candidates = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    if candidates.get("pageCount") != EXPECTED_PAGE_COUNT:
        raise RuntimeError("P4.5 candidate artifact is not the frozen 29-page artifact")
    if candidates.get("teacherTruthReadDuringCandidateGeneration") is not False:
        raise RuntimeError("P4.5 candidate-generation provenance is unsafe")

    # Phase A: filtering. Do not read measurement/teacher-derived match data here.
    pages_out = {}
    rejection_totals = Counter()
    accepted_count = 0
    original_count = 0

    for page_id, page in candidates["pages"].items():
        accepted = []
        rejected = []
        for candidate_index, candidate in enumerate(page["candidates"]):
            original_count += 1
            keep, reasons = filter_candidate(candidate)
            item = {"candidateIndex": candidate_index, "candidate": candidate}
            if keep:
                accepted.append(item)
                accepted_count += 1
            else:
                item["reasons"] = reasons
                rejected.append(item)
                rejection_totals.update(reasons)
        pages_out[page_id] = {
            "pageId": page_id,
            "sourceGroup": page["sourceGroup"],
            "accepted": accepted,
            "rejected": rejected,
        }

    filtered = {
        "schemaVersion": "stage11.v2d.c-clef-p4_6-filtered-candidates.v1",
        "status": "COMPLETE",
        "filterId": FILTER_ID,
        "developmentOnly": True,
        "teacherTruthReadDuringFiltering": False,
        "pageIdUsedByFilter": False,
        "sourceGroupUsedByFilter": False,
        "eomerUsed": False,
        "onnxUsed": False,
        "gpuUsed": False,
        "sourceCandidateArtifact": {
            "sha256": csha,
            "candidateCount": original_count,
        },
        "thresholds": {
            "minimumAreaInStaffSpacesSquared": LOW_AREA,
            "maximumAreaInStaffSpacesSquared": HIGH_AREA,
            "minimumWidthInStaffSpaces": MIN_WIDTH,
            "maximumHeightInStaffSpaces": MAX_HEIGHT,
            "lowStaffSpacingThreshold": LOW_SPACING,
            "minimumHeightWhenLowStaffSpacing": MIN_HEIGHT_LOW_SPACING,
        },
        "acceptedCandidateCount": accepted_count,
        "rejectedCandidateCount": original_count - accepted_count,
        "rejectionReasonTotals": dict(rejection_totals),
        "pages": pages_out,
    }
    atomic_json(FILTERED_PATH, filtered)
    filtered_sha = sha256_file(FILTERED_PATH)
    print(f"PASS — Phase A filter complete: {accepted_count}/{original_count} candidates retained")
    print(f"PASS — filtered artifact SHA-256: {filtered_sha}")

    # Phase B: development evaluation. Teacher-derived matches enter only now.
    measurement = json.loads(MEASUREMENT_PATH.read_text(encoding="utf-8"))
    if measurement.get("pageCount") != EXPECTED_PAGE_COUNT or measurement.get("teacherBoxCount") != EXPECTED_TEACHER_BOXES:
        raise RuntimeError("P4.5 measurement is not the frozen 29-page / 71-box result")

    per_page_source = measurement["primaryMeasurement"]["perPage"]
    subtype_totals = {"C1": 20, "C3": 36, "C4": 15}
    subtype_tp = Counter()
    group_teacher = Counter()
    group_tp = Counter()
    group_fp = Counter()
    per_page_result = {}
    pooled_tp = 0
    pooled_fp = 0

    for page_id, filtered_page in pages_out.items():
        source_page = per_page_source[page_id]
        match_by_index = {int(m["candidateIndex"]): m for m in source_page["matches"]}
        accepted_indices = {int(item["candidateIndex"]) for item in filtered_page["accepted"]}

        retained_matches = [match_by_index[i] for i in sorted(accepted_indices & set(match_by_index))]
        tp = len(retained_matches)
        fp = len(accepted_indices) - tp
        teacher_count = int(source_page["teacherBoxCount"])
        fn = teacher_count - tp
        pooled_tp += tp
        pooled_fp += fp

        group = filtered_page["sourceGroup"]
        group_teacher[group] += teacher_count
        group_tp[group] += tp
        group_fp[group] += fp
        for match in retained_matches:
            subtype_tp[match["teacherLabel"]] += 1

        per_page_result[page_id] = {
            "teacherBoxCount": teacher_count,
            "acceptedCandidateCount": len(accepted_indices),
            "metrics": metric(tp, fp, fn),
            "retainedMatches": retained_matches,
        }

    pooled_fn = EXPECTED_TEACHER_BOXES - pooled_tp
    pooled = metric(pooled_tp, pooled_fp, pooled_fn)
    subtype = {
        label: {
            "teacherBoxes": total,
            "tp": int(subtype_tp[label]),
            "fn": total - int(subtype_tp[label]),
            "recall": int(subtype_tp[label]) / total,
        }
        for label, total in subtype_totals.items()
    }
    by_group = {}
    for group, teacher_count in sorted(group_teacher.items()):
        tp = int(group_tp[group])
        fp = int(group_fp[group])
        by_group[group] = metric(tp, fp, teacher_count - tp)
        by_group[group]["teacherBoxes"] = teacher_count

    result = {
        "schemaVersion": "stage11.v2d.c-clef-p4_6-development-filter-result.v1",
        "status": "COMPLETE",
        "developmentOnly": True,
        "developmentThresholdsSelectedAfterReviewingP4_5Labels": True,
        "qualificationEvidence": False,
        "heldOutAccessed": False,
        "filterId": FILTER_ID,
        "sourceArtifacts": {
            "candidateSha256": csha,
            "measurementSha256": msha,
            "filteredCandidateSha256": filtered_sha,
        },
        "pooled": pooled,
        "perTeacherSubtype": subtype,
        "perSourceGroup": by_group,
        "perPage": per_page_result,
        "decision": {
            "developmentFilterTargetMet": (
                pooled["precision"] >= 0.80
                and pooled["recall"] >= 0.90
                and all(v["recall"] >= 0.80 for v in subtype.values())
                and all(v["precision"] >= 0.80 and v["recall"] >= 0.80 for v in by_group.values())
            ),
            "detectorQualified": False,
            "productionInferenceAuthorized": False,
            "overallStage11PassAuthorized": False,
            "nextSafeAction": "Freeze this P4.6 filter and evaluate it once on an independent held-out C-clef set. Do not retune after holdout access.",
        },
    }

    # Fail closed if current artifacts do not reproduce the development result used to freeze v1.
    expected = (66, 5, 5)
    actual = (pooled["tp"], pooled["fp"], pooled["fn"])
    if actual != expected:
        raise RuntimeError(f"P4.6 reproducibility drift: expected TP/FP/FN={expected}, got {actual}")
    if not result["decision"]["developmentFilterTargetMet"]:
        raise RuntimeError("P4.6 development target unexpectedly failed")

    atomic_json(RESULT_PATH, result)
    result_sha = sha256_file(RESULT_PATH)

    print()
    print("=" * 72)
    print("P4.6 OFFLINE FILTER COMPLETE")
    print("=" * 72)
    print("POOLED:", pooled)
    print("SUBTYPES:", subtype)
    print("SOURCE GROUPS:", by_group)
    print("DEVELOPMENT FILTER TARGET MET:", result["decision"]["developmentFilterTargetMet"])
    print("detectorQualified: False — independent holdout still required")
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", result_sha)


if __name__ == "__main__":
    main()
