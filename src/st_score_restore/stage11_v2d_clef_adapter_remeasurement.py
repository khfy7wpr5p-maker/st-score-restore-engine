"""Recompute P4.2 clef metrics from cached Oemer candidates and exact PNGs.

This command is intentionally offline: it never imports Oemer, opens ONNX
checkpoints, or reruns inference.  It applies the deterministic clef/key
geometry adapter to persisted components, detects explicit TAB markers from
the exact source PNGs, and measures the result against teacher completion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import cv2

from .stage11_v2d_clef_adapter import (
    ADAPTER_ID,
    adapter_parameters,
    detect_tab_clef_markers,
    resolve_oemer_clef_candidates,
    tab_adapter_parameters,
)
from .stage11_v2d_clef_source_qualification import (
    PRIMARY_IOU_THRESHOLD,
    box_iou,
    build_clef_source_qualification_measurement,
    greedy_one_to_one_match,
)


RESULT_SCHEMA = "stage11.v2d.clef-source-qualification-execution.p4_2-adapter.v1"
EXPECTED_INPUT_SCHEMA = "stage11.v2d.clef-source-qualification-execution.coordinate-corrected.v2"
POOLED_PRECISION_TARGET = 0.80
POOLED_RECALL_TARGET = 0.70
SUPPORTED_CLEF_TYPES = ("treble", "bass", "tab")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _teacher_page(page: Mapping[str, Any]) -> tuple[list[list[float]], list[str]]:
    boxes: list[list[float]] = []
    types: list[str] = []
    for item in page.get("clefBoxes", []):
        boxes.append(
            [
                float(item["xMin"]),
                float(item["yMin"]),
                float(item["xMaxExclusive"]),
                float(item["yMaxExclusive"]),
            ]
        )
        types.append(str(item["clefType"]))
    return boxes, types


def _typed_one_to_one_match(
    teacher_boxes: Sequence[Sequence[float]],
    teacher_types: Sequence[str],
    detector_boxes: Sequence[Sequence[float]],
    detector_types: Sequence[str],
) -> dict[str, Any]:
    if len(teacher_boxes) != len(teacher_types) or len(detector_boxes) != len(detector_types):
        raise ValueError("typed boxes and labels must align")
    candidates: list[tuple[float, int, int]] = []
    for teacher_index, (teacher_box, teacher_type) in enumerate(zip(teacher_boxes, teacher_types)):
        for detector_index, (detector_box, detector_type) in enumerate(zip(detector_boxes, detector_types)):
            if teacher_type != detector_type:
                continue
            score = box_iou(teacher_box, detector_box)
            if score >= PRIMARY_IOU_THRESHOLD:
                candidates.append((score, teacher_index, detector_index))
    candidates.sort(reverse=True)
    used_teacher: set[int] = set()
    used_detector: set[int] = set()
    matches: list[dict[str, Any]] = []
    for score, teacher_index, detector_index in candidates:
        if teacher_index in used_teacher or detector_index in used_detector:
            continue
        used_teacher.add(teacher_index)
        used_detector.add(detector_index)
        matches.append(
            {
                "teacherIndex": teacher_index,
                "detectorIndex": detector_index,
                "clefType": teacher_types[teacher_index],
                "iou": score,
            }
        )
    return {"matches": matches, "usedTeacher": used_teacher, "usedDetector": used_detector}


def _metrics(tp: int, fp: int, fn: int) -> dict[str, Any]:
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def recompute(
    corrected_result: Mapping[str, Any],
    teacher_completion: Mapping[str, Any],
    *,
    source_identity: Mapping[str, Any],
    source_page_dir: Path,
) -> dict[str, Any]:
    if corrected_result.get("schemaVersion") != EXPECTED_INPUT_SCHEMA:
        raise ValueError("coordinate-corrected P4 input schema mismatch")
    teacher_pages = {str(page["pageId"]): page for page in teacher_completion.get("pages", [])}
    page_records: list[dict[str, Any]] = []
    subtype_totals: Counter[str] = Counter()

    for prior in corrected_result.get("pageEvidence", []):
        page_id = str(prior["pageId"])
        if page_id not in teacher_pages:
            raise ValueError(f"teacher page missing: {page_id}")
        teacher_boxes, teacher_types = _teacher_page(teacher_pages[page_id])
        if teacher_boxes != prior.get("teacherBoxes"):
            raise ValueError(f"teacher box coordinates do not match corrected result: {page_id}")
        geometry = prior.get("coordinateNormalization") or {}
        source_width = float(geometry["sourceWidth"])
        source_height = float(geometry["sourceHeight"])
        source_path = source_page_dir / f"{page_id}.png"
        if not source_path.is_file():
            raise ValueError(f"exact source PNG missing: {page_id}")
        if sha256_file(source_path) != str(prior["sourceImage"]["sha256"]):
            raise ValueError(f"exact source PNG hash mismatch: {page_id}")
        source_image = cv2.imread(str(source_path), cv2.IMREAD_GRAYSCALE)
        if source_image is None:
            raise ValueError(f"cannot decode exact source PNG: {page_id}")
        if source_image.shape != (int(source_height), int(source_width)):
            raise ValueError(f"exact source PNG dimensions mismatch: {page_id}")
        raw_candidates = prior.get("detectorBoxes") or []
        resolved = resolve_oemer_clef_candidates(
            raw_candidates,
            source_width=source_width,
            source_height=source_height,
        )
        tab_resolved = detect_tab_clef_markers(source_image)
        detector_boxes = [list(map(float, box)) for box in resolved["clefBoxes"]]
        detector_boxes.extend([list(map(float, box)) for box in tab_resolved["clefBoxes"]])
        detector_types = [str(value) for value in resolved["clefTypes"]]
        detector_types.extend(str(value) for value in tab_resolved["clefTypes"])
        match = greedy_one_to_one_match(teacher_boxes, detector_boxes, iou_threshold=PRIMARY_IOU_THRESHOLD)
        typed = _typed_one_to_one_match(teacher_boxes, teacher_types, detector_boxes, detector_types)

        teacher_counts = Counter(teacher_types)
        detector_counts = Counter(detector_types)
        matched_counts = Counter(str(item["clefType"]) for item in typed["matches"])
        page_subtypes: dict[str, Any] = {}
        for clef_type in sorted(set(teacher_counts) | set(detector_counts)):
            values = _metrics(
                matched_counts[clef_type],
                detector_counts[clef_type] - matched_counts[clef_type],
                teacher_counts[clef_type] - matched_counts[clef_type],
            )
            page_subtypes[clef_type] = values
            for key in ("tp", "fp", "fn"):
                subtype_totals[f"{clef_type}.{key}"] += int(values[key])

        page_records.append(
            {
                "schemaVersion": "stage11.v2d.clef-source-qualification-page.p4_2.v1",
                "pageId": page_id,
                "sourceFamily": str(prior["sourceFamily"]),
                "sourceOnly": True,
                "sourceImage": dict(prior["sourceImage"]),
                "coordinateNormalization": dict(geometry),
                "teacherBoxCount": len(teacher_boxes),
                "teacherBoxes": teacher_boxes,
                "teacherClefTypes": teacher_types,
                "rawCombinedClefKeyCandidateCount": len(raw_candidates),
                "rawCombinedClefKeyCandidateBoxes": raw_candidates,
                "detectorBoxCount": len(detector_boxes),
                "detectorBoxes": detector_boxes,
                "detectorClefTypes": detector_types,
                "adapterSourceCandidateIndexes": resolved["sourceCandidateIndexes"],
                "tabClefDiagnostic": {
                    "adapterId": tab_resolved["adapterId"],
                    "detectionCount": len(tab_resolved["detections"]),
                    "detections": tab_resolved["detections"],
                    "abstentions": tab_resolved["abstentions"],
                },
                "keySignatureDiagnostic": {
                    "status": "unscored_partial_candidates",
                    "teacherTruthAvailable": False,
                    "candidateCount": len(resolved["keyCandidateBoxes"]),
                    "candidateBoxes": [list(map(float, box)) for box in resolved["keyCandidateBoxes"]],
                    "reason": "rejected components from the persisted broad Oemer clefs_keys candidate set only",
                },
                "matches": match["matches"],
                "typedMatches": typed["matches"],
                "subtypeMetrics": page_subtypes,
                **{key: match[key] for key in ("tp", "fp", "fn", "precision", "recall", "f1")},
            }
        )

    measurement = build_clef_source_qualification_measurement(page_records)
    subtype_metrics: dict[str, Any] = {}
    all_types = sorted({key.split(".", 1)[0] for key in subtype_totals})
    for clef_type in all_types:
        subtype_metrics[clef_type] = _metrics(
            subtype_totals[f"{clef_type}.tp"],
            subtype_totals[f"{clef_type}.fp"],
            subtype_totals[f"{clef_type}.fn"],
        )

    pooled = measurement["pooledMetrics"]
    pooled_target_met = pooled["precision"] >= POOLED_PRECISION_TARGET and pooled["recall"] >= POOLED_RECALL_TARGET
    family_diagnostic = {
        family: {
            **metrics,
            "targetMet": metrics["precision"] >= POOLED_PRECISION_TARGET and metrics["recall"] >= POOLED_RECALL_TARGET,
        }
        for family, metrics in measurement["sourceFamilyMetrics"].items()
    }
    all_family_targets_met = all(item["targetMet"] for item in family_diagnostic.values())
    key_candidate_count = sum(page["keySignatureDiagnostic"]["candidateCount"] for page in page_records)
    return {
        "schemaVersion": RESULT_SCHEMA,
        "contractId": str(corrected_result["contractId"]),
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "purpose": "P4_2_OFFLINE_CLEF_ADAPTER_REMEASUREMENT",
        "sourceOnly": True,
        "inferenceRerun": False,
        "trainingUsed": False,
        "sourceArtifact": dict(source_identity),
        "teacherTruth": dict(corrected_result["teacherTruth"]),
        "adapter": {
            **adapter_parameters(),
            **tab_adapter_parameters(),
            "inputCoordinateSpace": "original_source_image_pixels",
            "supportedClefTypes": list(SUPPORTED_CLEF_TYPES),
            "unsupportedClefTypes": ["soprano"],
            "teacherBoxesConsumedAtInference": False,
        },
        "matching": dict(corrected_result["matching"]),
        "developmentTarget": {
            "precisionMinimum": POOLED_PRECISION_TARGET,
            "recallMinimum": POOLED_RECALL_TARGET,
            "pooledTargetMet": pooled_target_met,
            "allSourceFamilyTargetsMet": all_family_targets_met,
        },
        "pageEvidence": page_records,
        "sourceFamilyMetrics": measurement["sourceFamilyMetrics"],
        "sourceFamilyRobustness": family_diagnostic,
        "pooledMetrics": pooled,
        "clefSubtypeMetrics": subtype_metrics,
        "keySignatureDiagnostic": {
            "status": "unscored_partial_candidates",
            "teacherTruthAvailable": False,
            "candidateCount": key_candidate_count,
            "keysMixedIntoClefScore": False,
        },
        "decisionBoundary": {
            "measurementComplete": True,
            "pooledDevelopmentTargetMet": pooled_target_met,
            "allSourceFamilyTargetsMet": all_family_targets_met,
            "detectorQualified": False,
            "qualificationDecisionRequired": True,
            "reason": "non-held-out adapter development; soprano support has insufficient evidence and independent holdout is pending",
            "semanticPreservationEstablished": False,
            "overallStage11PassAuthorized": False,
            "productionReady": False,
            "stage12EntryAuthorized": False,
        },
    }


def recompute_files(input_path: Path, completion_path: Path, source_page_dir: Path, output_path: Path) -> Path:
    result = recompute(
        _load_object(input_path),
        _load_object(completion_path),
        source_identity={
            "filename": input_path.name,
            "byteSize": input_path.stat().st_size,
            "sha256": sha256_file(input_path),
        },
        source_page_dir=source_page_dir,
    )
    _atomic_json(output_path, result)
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--completion", type=Path, required=True)
    parser.add_argument("--source-pages", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    output = recompute_files(args.input, args.completion, args.source_pages, args.output)
    payload = _load_object(output)
    print("P4.2 CLEF ADAPTER REMEASUREMENT PASS")
    print("POOLED:", payload["pooledMetrics"])
    print("SAVED:", output)
    print("SHA-256:", sha256_file(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
