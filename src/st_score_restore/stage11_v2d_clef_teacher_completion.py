"""Fail-closed validation for Stage 11 V2d independent clef teacher truth.

The pristine spatial package stays unchanged. Soprano C clef is admitted only by a
separate versioned taxonomy amendment. Clef completion cannot imply staff-line,
detector, preservation, production, or Stage 12 completion.
"""
from __future__ import annotations

from typing import Any, Mapping

from .stage11_v2c_semantic_preservation import Stage11V2cSemanticPreservationError
from .stage11_v2d_spatial_teacher_review import CONTRACT_ID, EXPECTED_PAGES

COMPLETION_SCHEMA = "stage11.v2d.clef-box-teacher-review-completion.v1"
AMENDMENT_SCHEMA = "stage11.v2d.clef-teacher-taxonomy-amendment.v1"
BINDING_SCHEMA = "stage11.v2d.clef-box-teacher-completion-binding.v1"
BASE_CLEF_TYPES = ("treble", "bass", "alto", "tenor", "percussion", "tab", "other", "unknown")
EFFECTIVE_CLEF_TYPES = frozenset((*BASE_CLEF_TYPES, "soprano"))
SOURCE_BUNDLE = {
    "filename": "ST_SCORE_RESTORE_STAGE11_V2D_SPATIAL_TEACHER_REVIEW_PACKAGE_2026-09-09.zip",
    "byteSize": 18175904,
    "sha256": "e5609d2f79139c209618a0fa8d61145ab55a6e548c0124e4664bb59d87366559",
    "pageCount": 18,
}
COMPLETION_IDENTITY = {
    "filename": "clef_box_teacher_completion.v1.json",
    "driveFileId": "1zd48RNvW5htuFj2w4oTjiBMa1OFgYH6j",
    "driveFolderId": "11JIiEupmBx7KOa29pjMNdBry59j8g58B",
    "byteSize": 70465,
    "sha256": "68df771d5ace9f0b968452ff532fa2693fa2cd3405477d91fa3a98eccb190d54",
    "schemaVersion": COMPLETION_SCHEMA,
    "reviewerName": "Önder",
    "reviewDate": "2026-09-09",
}
EXPECTED_TYPE_COUNTS = {"treble": 165, "bass": 34, "tab": 12, "soprano": 2}
DOWNSTREAM_FALSE = (
    "detectorQualified",
    "semanticPreservationEstablished",
    "overallStage11PassAuthorized",
    "productionReady",
    "productionPromotionAuthorized",
    "stage12EntryAuthorized",
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2cSemanticPreservationError(message)


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def validate_clef_taxonomy_amendment(amendment: Mapping[str, Any]) -> dict[str, Any]:
    _require(amendment.get("schemaVersion") == AMENDMENT_SCHEMA, "taxonomy amendment schema mismatch")
    _require(amendment.get("contractId") == CONTRACT_ID, "taxonomy amendment contract mismatch")
    work = amendment.get("workPackage") or {}
    _require(work.get("path") == "evidence/stage11/v2d/v2d-spatial-teacher-review-work-package.v1.json", "work-package path mismatch")
    _require(work.get("schemaVersion") == "stage11.v2d.spatial-teacher-review-work-package.v1", "work-package schema mismatch")
    _require(tuple(work.get("baseAllowedClefTypes") or ()) == BASE_CLEF_TYPES, "base clef taxonomy mismatch")
    _require(work.get("mutated") is False, "pristine work package cannot be mutated")
    change = amendment.get("amendment") or {}
    additions = change.get("addedClefTypes")
    _require(isinstance(additions, list) and len(additions) == 1, "exactly one taxonomy addition required")
    addition = additions[0]
    _require(isinstance(addition, Mapping) and addition.get("clefType") == "soprano", "taxonomy addition must be soprano")
    _require(addition.get("semanticName") == "Soprano C clef", "soprano semantic name mismatch")
    _require(addition.get("displayLabelTr") == "Soprano Do anahtarı", "soprano display label mismatch")
    _require(set(change.get("effectiveAllowedClefTypes") or ()) == EFFECTIVE_CLEF_TYPES, "effective clef taxonomy mismatch")
    _require(change.get("appliesToCompletionSchema") == COMPLETION_SCHEMA, "taxonomy completion schema mismatch")
    for key in ("modelOutputUsed", "detectorOutputUsed", "trainingPerformed"):
        _require(change.get(key) is False, f"taxonomy boundary must remain false: {key}")
    boundary = amendment.get("claimBoundary") or {}
    _require(boundary.get("teacherSpatialLabelsComplete") is False, "taxonomy cannot complete spatial truth")
    for key in DOWNSTREAM_FALSE:
        _require(boundary.get(key) is False, f"taxonomy claim must remain false: {key}")
    return {"status": "pass", "addedClefType": "soprano"}


def validate_clef_teacher_completion(completion: Mapping[str, Any], amendment: Mapping[str, Any]) -> dict[str, Any]:
    validate_clef_taxonomy_amendment(amendment)
    _require(completion.get("schemaVersion") == COMPLETION_SCHEMA, "clef completion schema mismatch")
    _require(completion.get("contractId") == CONTRACT_ID, "clef completion contract mismatch")
    _require(isinstance(completion.get("reviewerName"), str) and bool(completion["reviewerName"].strip()), "reviewerName required")
    _require(isinstance(completion.get("reviewDate"), str) and len(completion["reviewDate"]) == 10, "reviewDate required")
    _require(completion.get("sourceReviewBundle") == SOURCE_BUNDLE, "source review bundle mismatch")
    independence = completion.get("independenceBoundary") or {}
    _require(independence == {
        "reviewBasis": "source_page_only",
        "modelOutputShown": False,
        "restoredOutputShown": False,
        "detectorOutputUsedAsGroundTruth": False,
    }, "independence boundary mismatch")
    pages = completion.get("pages")
    _require(isinstance(pages, list) and len(pages) == len(EXPECTED_PAGES), "exactly 18 review pages required")
    box_ids: set[str] = set()
    type_counts: dict[str, int] = {}
    total = ambiguous = truncated = 0
    for page, (page_id, _source_id, _source_page_number) in zip(pages, EXPECTED_PAGES):
        _require(isinstance(page, Mapping) and page.get("pageId") == page_id, f"page order/identity mismatch: {page_id}")
        _require(page.get("teacherState") == "present", f"teacherState must be present: {page_id}")
        _require(page.get("reviewerStatus") == "completed", f"reviewerStatus must be completed: {page_id}")
        image = page.get("reviewImage") or {}
        _require(image.get("path") == f"source-pages/{page_id}.png", f"review image path mismatch: {page_id}")
        _require(_integer(image.get("byteSize")) and image["byteSize"] > 0, f"review image byte size invalid: {page_id}")
        _require(_sha256(image.get("sha256")), f"review image sha256 invalid: {page_id}")
        _require(_integer(image.get("width")) and image["width"] > 0, f"review image width invalid: {page_id}")
        _require(_integer(image.get("height")) and image["height"] > 0, f"review image height invalid: {page_id}")
        boxes = page.get("clefBoxes")
        _require(isinstance(boxes, list) and boxes, f"teacher-present page requires clef boxes: {page_id}")
        for box in boxes:
            _require(isinstance(box, Mapping), f"clef box must be object: {page_id}")
            _require(set(box) == {"boxId", "xMin", "yMin", "xMaxExclusive", "yMaxExclusive", "clefType", "truncated", "ambiguous"}, f"clef box fields mismatch: {page_id}")
            box_id = box.get("boxId")
            _require(isinstance(box_id, str) and box_id.startswith(f"{page_id}-clef-"), f"clef boxId invalid: {page_id}")
            _require(box_id not in box_ids, f"duplicate clef boxId: {box_id}")
            box_ids.add(box_id)
            coords = [box.get(k) for k in ("xMin", "yMin", "xMaxExclusive", "yMaxExclusive")]
            _require(all(_integer(v) for v in coords), f"clef coordinates must be integers: {box_id}")
            x1, y1, x2, y2 = coords
            _require(0 <= x1 < x2 <= image["width"] and 0 <= y1 < y2 <= image["height"], f"clef box out of bounds: {box_id}")
            clef_type = box.get("clefType")
            _require(clef_type in EFFECTIVE_CLEF_TYPES, f"clef type not authorized: {clef_type}")
            _require(isinstance(box.get("truncated"), bool) and isinstance(box.get("ambiguous"), bool), f"clef flags must be boolean: {box_id}")
            total += 1
            type_counts[str(clef_type)] = type_counts.get(str(clef_type), 0) + 1
            truncated += int(box["truncated"])
            ambiguous += int(box["ambiguous"])
    summary = completion.get("summary") or {}
    _require(summary.get("reviewPageCount") == 18 and summary.get("completedPageCount") == 18, "completion page summary mismatch")
    _require(summary.get("clefBoxCount") == total, "clef box summary mismatch")
    _require(summary.get("clefBoxLabelsComplete") is True, "clef labels must be complete")
    _require(summary.get("staffLineLabelsComplete") is False, "clef-only artifact cannot complete staff lines")
    boundary = completion.get("claimBoundary") or {}
    _require(boundary.get("clefBoxLabelsComplete") is True, "clef completion claim must be true")
    _require(boundary.get("teacherSpatialLabelsComplete") is False, "whole spatial review is incomplete")
    _require(boundary.get("newColabRunRequiredNow") is False, "completion cannot self-authorize Colab")
    for key in DOWNSTREAM_FALSE:
        _require(boundary.get(key) is False, f"clef completion claim must remain false: {key}")
    return {"status": "pass", "reviewPageCount": 18, "clefBoxCount": total, "clefTypeCounts": dict(sorted(type_counts.items())), "ambiguousBoxCount": ambiguous, "truncatedBoxCount": truncated}


def validate_clef_teacher_completion_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    _require(binding.get("schemaVersion") == BINDING_SCHEMA, "clef completion binding schema mismatch")
    _require(binding.get("contractId") == CONTRACT_ID, "clef completion binding contract mismatch")
    record = binding.get("completion") or {}
    _require(record == COMPLETION_IDENTITY, "clef completion identity mismatch")
    _require(binding.get("sourceReviewBundle") == SOURCE_BUNDLE, "binding source review bundle mismatch")
    _require(binding.get("taxonomyAmendmentPath") == "evidence/stage11/v2d/v2d-clef-teacher-taxonomy-amendment.v1.json", "taxonomy amendment path mismatch")
    _require(binding.get("independenceBoundary") == {"reviewBasis": "source_page_only", "modelOutputShown": False, "restoredOutputShown": False, "detectorOutputUsedAsGroundTruth": False}, "binding independence mismatch")
    summary = binding.get("validatedSummary") or {}
    _require(summary.get("reviewPageCount") == 18 and summary.get("completedPageCount") == 18, "binding page summary mismatch")
    _require(summary.get("clefBoxCount") == 213, "binding clef count mismatch")
    _require(summary.get("clefTypeCounts") == EXPECTED_TYPE_COUNTS, "binding clef type counts mismatch")
    for key in ("duplicateBoxIdCount", "outOfBoundsBoxCount", "ambiguousBoxCount", "truncatedBoxCount"):
        _require(summary.get(key) == 0, f"binding {key} must be zero")
    _require(summary.get("clefBoxLabelsComplete") is True and summary.get("staffLineLabelsComplete") is False, "binding completion flags mismatch")
    decision = binding.get("ingestionDecision") or {}
    _require(decision == {"clefTeacherTruthAccepted": True, "staffLineTeacherTruthAccepted": False, "teacherSpatialLabelsComplete": False, "nextStep": "P4_SOURCE_ONLY_CLEF_DETECTOR_QUALIFICATION"}, "ingestion decision mismatch")
    boundary = binding.get("claimBoundary") or {}
    for key in DOWNSTREAM_FALSE:
        _require(boundary.get(key) is False, f"binding claim must remain false: {key}")
    return {"status": "pass", "clefTeacherTruthAccepted": True, "clefBoxCount": 213, "artifactSha256": COMPLETION_IDENTITY["sha256"]}
