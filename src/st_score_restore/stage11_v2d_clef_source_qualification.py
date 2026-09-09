"""Stage 11 V2d source-only clef detector qualification primitives.

The primary IoU threshold is preregistered at 0.50. Measurement is against
independent teacher boxes on source images only and never auto-qualifies a detector.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from .stage11_v2c_semantic_preservation import Stage11V2cSemanticPreservationError
from .stage11_v2d_spatial_teacher_review import CONTRACT_ID, EXPECTED_PAGES

QUALIFICATION_CONTRACT_SCHEMA = "stage11.v2d.clef-source-qualification-contract.v1"
QUALIFICATION_RESULT_SCHEMA = "stage11.v2d.clef-source-qualification-result.v1"
PRIMARY_IOU_THRESHOLD = 0.50
EXPECTED_CLEF_BOX_COUNT = 213
OEMER_COMMIT = "dbe2a933d630d0f74805d717960eb259473f5978"
OEMER_CHECKPOINTS = {
    "unet_big/model.onnx": "37512e858731096439746f60b377c049f07055b4a23ec6eb9a178ce92cfba174",
    "seg_net/model.onnx": "ed2e1a86ea75712ee6cdc740e96f7a36753543cf9bb980227c071c9256d9d82e",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2cSemanticPreservationError(message)


def box_iou(a: Sequence[float], b: Sequence[float]) -> float:
    _require(len(a) == 4 and len(b) == 4, "IoU boxes must contain four coordinates")
    ax1, ay1, ax2, ay2 = map(float, a)
    bx1, by1, bx2, by2 = map(float, b)
    _require(ax1 < ax2 and ay1 < ay2 and bx1 < bx2 and by1 < by2, "IoU boxes must have positive area")
    iw = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    ih = max(0.0, min(ay2, by2) - max(ay1, by1))
    if iw == 0.0 or ih == 0.0:
        return 0.0
    inter = iw * ih
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union


def greedy_one_to_one_match(
    teacher_boxes: Sequence[Sequence[float]],
    detector_boxes: Sequence[Sequence[float]],
    *,
    iou_threshold: float = PRIMARY_IOU_THRESHOLD,
) -> dict[str, Any]:
    _require(0.0 < iou_threshold <= 1.0, "IoU threshold must be in (0, 1]")
    candidates: list[tuple[float, int, int]] = []
    for teacher_index, teacher in enumerate(teacher_boxes):
        for detector_index, detector in enumerate(detector_boxes):
            score = box_iou(teacher, detector)
            if score >= iou_threshold:
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
        matches.append({"teacherIndex": teacher_index, "detectorIndex": detector_index, "iou": score})
    tp = len(matches)
    fn = len(teacher_boxes) - tp
    fp = len(detector_boxes) - tp
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1, "matches": matches}


def _aggregate(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    records = list(records)
    tp = sum(int(r["tp"]) for r in records)
    fp = sum(int(r["fp"]) for r in records)
    fn = sum(int(r["fn"]) for r in records)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def validate_clef_source_qualification_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    _require(contract.get("schemaVersion") == QUALIFICATION_CONTRACT_SCHEMA, "clef source qualification contract schema mismatch")
    _require(contract.get("contractId") == CONTRACT_ID, "clef source qualification contract id mismatch")
    _require(contract.get("teacherTruthBindingPath") == "evidence/stage11/v2d/v2d-clef-box-teacher-completion-binding.v1.json", "teacher truth binding path mismatch")
    scope = contract.get("scope") or {}
    _require(scope.get("developmentOnly") is True, "qualification must remain development-only")
    _require(scope.get("sourceImagesOnly") is True, "qualification must be source-only")
    _require(scope.get("restoredImagesEvaluated") is False, "restored images are forbidden in P4")
    _require(scope.get("heldOutAccessed") is False, "held-out access is forbidden")
    _require(scope.get("trainingAuthorized") is False, "training is forbidden")
    _require(scope.get("detectorOutputUsedAsGroundTruth") is False, "detector output cannot become teacher truth")
    _require(scope.get("teacherClefBoxCount") == EXPECTED_CLEF_BOX_COUNT, "teacher clef box count mismatch")
    _require(scope.get("reviewPageCount") == len(EXPECTED_PAGES), "review page count mismatch")
    _require(scope.get("sourceFamilyCount") == 5, "source family count mismatch")
    detector = contract.get("detector") or {}
    _require(detector.get("candidateId") == "oemer-onnx-segmentation-dbe2a933", "detector candidate mismatch")
    _require(detector.get("upstreamCommit") == OEMER_COMMIT, "Oemer commit mismatch")
    _require(detector.get("checkpointSha256") == OEMER_CHECKPOINTS, "Oemer checkpoint binding mismatch")
    _require(detector.get("clefSubtypeClassificationEvaluated") is False, "current detector does not classify clef subtypes")
    matching = contract.get("matching") or {}
    _require(matching.get("method") == "greedy_one_to_one_descending_iou", "matching method mismatch")
    _require(matching.get("primaryIouThreshold") == PRIMARY_IOU_THRESHOLD, "primary IoU threshold mismatch")
    _require(matching.get("thresholdPreregistered") is True, "IoU threshold must be preregistered")
    _require(matching.get("thresholdMayChangeAfterSeeingResult") is False, "IoU threshold cannot drift after measurement")
    _require(contract.get("requiredMetrics") == ["tp", "fp", "fn", "precision", "recall", "f1"], "required metrics mismatch")
    _require(contract.get("aggregation") == ["page", "source_family", "pooled"], "aggregation contract mismatch")
    decision = contract.get("decisionBoundary") or {}
    _require(decision.get("measurementDoesNotAutoQualifyDetector") is True, "measurement cannot auto-qualify detector")
    _require(decision.get("qualificationThresholdsPrecommitted") is False, "qualification thresholds are not precommitted")
    _require(decision.get("detectorQualified") is False, "detector is not yet qualified")
    _require(decision.get("preservationMeasurementAuthorizedByThisArtifact") is False, "P4 contract cannot authorize preservation measurement")
    boundary = contract.get("claimBoundary") or {}
    for key in ("semanticPreservationEstablished", "overallStage11PassAuthorized", "productionReady", "productionPromotionAuthorized", "stage12EntryAuthorized"):
        _require(boundary.get(key) is False, f"qualification contract claim must remain false: {key}")
    return {"status": "pass", "primaryIouThreshold": PRIMARY_IOU_THRESHOLD}


def build_clef_source_qualification_measurement(page_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    expected_ids = [page_id for page_id, _source_id, _page_number in EXPECTED_PAGES]
    _require(len(page_records) == len(expected_ids), "exactly 18 page measurements required")
    _require([r.get("pageId") for r in page_records] == expected_ids, "qualification page order/identity mismatch")
    teacher_total = sum(int(r.get("teacherBoxCount", -1)) for r in page_records)
    _require(teacher_total == EXPECTED_CLEF_BOX_COUNT, "qualification teacher box total mismatch")
    for record in page_records:
        _require(record.get("sourceOnly") is True, f"page measurement must be source-only: {record.get('pageId')}")
        for key in ("tp", "fp", "fn"):
            _require(isinstance(record.get(key), int) and record[key] >= 0, f"invalid page metric: {record.get('pageId')}.{key}")
        _require(record["tp"] + record["fn"] == record["teacherBoxCount"], f"teacher count does not reconcile: {record.get('pageId')}")
    family_groups: dict[str, list[Mapping[str, Any]]] = {}
    for record, (_page_id, source_id, _page_number) in zip(page_records, EXPECTED_PAGES):
        _require(record.get("sourceFamily") == source_id, f"source family mismatch: {record.get('pageId')}")
        family_groups.setdefault(source_id, []).append(record)
    return {
        "schemaVersion": QUALIFICATION_RESULT_SCHEMA,
        "contractId": CONTRACT_ID,
        "scope": {"sourceImagesOnly": True, "restoredImagesEvaluated": False, "teacherClefBoxCount": EXPECTED_CLEF_BOX_COUNT, "reviewPageCount": len(EXPECTED_PAGES)},
        "matching": {"method": "greedy_one_to_one_descending_iou", "primaryIouThreshold": PRIMARY_IOU_THRESHOLD},
        "pageMetrics": list(page_records),
        "sourceFamilyMetrics": {family: _aggregate(records) for family, records in family_groups.items()},
        "pooledMetrics": _aggregate(page_records),
        "decisionBoundary": {"measurementComplete": True, "detectorQualified": False, "qualificationDecisionRequired": True, "semanticPreservationEstablished": False},
    }
