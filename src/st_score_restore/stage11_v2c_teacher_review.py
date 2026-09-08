"""Stage 11 V2c teacher-review ingestion for independent expected-class evidence."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .stage11_v2c_semantic_preservation import (
    CONTRACT_ID,
    EXPECTED_STATES,
    SEMANTIC_CLASSES,
    Stage11V2cSemanticPreservationError,
    validate_expected_class_manifest,
)

OVERLAY_SCHEMA_VERSION = "stage11.v2c.teacher-review-overlay.v1"
EXPECTED_REVIEW_PDF_SHA256 = "ad083a7ac30f466ec9718d896273a3ce7b4811e248ad859071d49bbf77ef3a0a"
EXPECTED_REVIEW_PDF_SIZE_BYTES = 30_385_082
EXPECTED_REVIEW_PDF_PAGE_COUNT = 21
EXPECTED_REVIEW_PAGE_COUNT = 20
EXPECTED_RESPONSE_COUNT = EXPECTED_REVIEW_PAGE_COUNT * len(SEMANTIC_CLASSES)
EVIDENCE_REF = "evidence/stage11/v2c/v2c-teacher-review-overlay.v1.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2cSemanticPreservationError(message)


def materialize_teacher_review_manifest(
    base_manifest: Mapping[str, Any], overlay: Mapping[str, Any]
) -> dict[str, Any]:
    """Apply source-only teacher review to a copy of the base manifest, fail-closed."""
    _require(overlay.get("schemaVersion") == OVERLAY_SCHEMA_VERSION, "teacher-review overlay schema mismatch")
    _require(overlay.get("contractId") == CONTRACT_ID, "teacher-review overlay contract mismatch")

    source_pdf = overlay.get("sourceReviewPdf") or {}
    _require(source_pdf.get("sha256") == EXPECTED_REVIEW_PDF_SHA256, "teacher-review PDF SHA mismatch")
    _require(int(source_pdf.get("byteSize", 0)) == EXPECTED_REVIEW_PDF_SIZE_BYTES, "teacher-review PDF size mismatch")
    _require(int(source_pdf.get("pageCount", 0)) == EXPECTED_REVIEW_PDF_PAGE_COUNT, "teacher-review PDF page count mismatch")
    _require(int(source_pdf.get("semanticResponseFieldCount", 0)) == EXPECTED_RESPONSE_COUNT, "teacher-review response field count mismatch")
    _require(bool(str(source_pdf.get("reviewerName") or "").strip()), "teacher reviewer name required")
    _require(bool(str(source_pdf.get("reviewDate") or "").strip()), "teacher review date required")

    independence = overlay.get("independenceBoundary") or {}
    _require(independence.get("reviewBasis") == "source_page_only", "teacher review must be source-only")
    _require(independence.get("modelOutputShown") is False, "model output must remain hidden during teacher review")
    _require(independence.get("detectorOutputUsedAsGroundTruth") is False, "detector output cannot be teacher ground truth")
    _require(tuple(overlay.get("semanticClassOrder") or ()) == tuple(SEMANTIC_CLASSES), "teacher-review class order mismatch")

    base_validation = validate_expected_class_manifest(base_manifest)
    _require(base_validation["pageCount"] == EXPECTED_REVIEW_PAGE_COUNT, "base manifest page count mismatch")
    materialized = deepcopy(dict(base_manifest))
    base_pages = {str(page["pageId"]): page for page in materialized.get("pages") or []}

    review_pages = overlay.get("pages")
    _require(isinstance(review_pages, list) and len(review_pages) == EXPECTED_REVIEW_PAGE_COUNT, "teacher-review pages incomplete")
    review_map: dict[str, Mapping[str, Any]] = {}
    for page in review_pages:
        _require(isinstance(page, Mapping), "teacher-review page must be object")
        page_id = str(page.get("pageId") or "")
        _require(page_id and page_id not in review_map, "teacher-review pageId missing/duplicate")
        _require(page_id in base_pages, "teacher-review page not in base manifest")
        states = page.get("states")
        _require(isinstance(states, list) and len(states) == len(SEMANTIC_CLASSES), "teacher-review state vector incomplete")
        _require(all(state in EXPECTED_STATES for state in states), "teacher-review state invalid")
        review_map[page_id] = page
    _require(set(review_map) == set(base_pages), "teacher-review/base page set mismatch")

    conflict_map: dict[tuple[str, str], Mapping[str, Any]] = {}
    conflicts = overlay.get("conflicts") or []
    _require(isinstance(conflicts, list), "teacher-review conflicts must be list")
    for conflict in conflicts:
        _require(isinstance(conflict, Mapping), "teacher-review conflict must be object")
        page_id = str(conflict.get("pageId") or "")
        class_id = str(conflict.get("classId") or "")
        key = (page_id, class_id)
        _require(page_id in review_map and class_id in SEMANTIC_CLASSES and key not in conflict_map, "teacher-review conflict invalid/duplicate")
        class_index = SEMANTIC_CLASSES.index(class_id)
        _require(review_map[page_id]["states"][class_index] == conflict.get("reviewerSelectedState"), "teacher-review conflict does not match submitted field")
        _require(conflict.get("effectiveState") == "unknown_review_required", "teacher-review conflict must fail closed")
        _require(bool(str(conflict.get("reason") or "").strip()), "teacher-review conflict reason required")
        conflict_map[key] = conflict

    state_counts = {state: 0 for state in EXPECTED_STATES}
    for page_id, base_page in base_pages.items():
        review_page = review_map[page_id]
        base_page["annotationStatus"] = "teacher_annotation_ingested_conflicts_pending" if any(key[0] == page_id for key in conflict_map) else "teacher_annotation_ingested"
        if review_page.get("note"):
            base_page["reviewerNote"] = str(review_page["note"])
        for index, class_id in enumerate(SEMANTIC_CLASSES):
            submitted_state = str(review_page["states"][index])
            conflict = conflict_map.get((page_id, class_id))
            effective_state = str(conflict["effectiveState"]) if conflict else submitted_state
            record: dict[str, Any] = {
                "state": effective_state,
                "provenance": {
                    "type": "teacher_annotation",
                    "evidenceRef": f"{EVIDENCE_REF}#pages/{page_id}/{class_id}",
                },
            }
            if conflict:
                record["reviewConflict"] = {
                    "reviewerSelected": submitted_state,
                    "reason": str(conflict["reason"]),
                    "resolutionRequired": True,
                }
            base_page["classes"][class_id] = record
            state_counts[effective_state] += 1

    total = sum(state_counts.values())
    _require(total == EXPECTED_RESPONSE_COUNT, "teacher-review effective response count mismatch")
    independently_annotated = state_counts["present"] + state_counts["absent"]
    total_applicable = independently_annotated + state_counts["unknown_review_required"]
    annotation_coverage = independently_annotated / max(1, total_applicable)

    summary = overlay.get("effectiveSummary") or {}
    _require(int(summary.get("expectedResponseCount", 0)) == EXPECTED_RESPONSE_COUNT, "teacher-review summary expected count mismatch")
    _require(int(summary.get("receivedResponseCount", 0)) == EXPECTED_RESPONSE_COUNT, "teacher-review summary received count mismatch")
    _require(int(summary.get("acceptedResponseCount", -1)) == EXPECTED_RESPONSE_COUNT - len(conflict_map), "teacher-review accepted count mismatch")
    _require(int(summary.get("unresolvedConflictCount", -1)) == len(conflict_map), "teacher-review conflict count mismatch")
    _require(summary.get("effectiveStateCounts") == state_counts, "teacher-review state-count summary mismatch")
    _require(int(summary.get("independentlyAnnotatedPresentOrAbsentClassCount", -1)) == independently_annotated, "teacher-review independent annotation count mismatch")
    _require(abs(float(summary.get("annotationCoverage", -1.0)) - annotation_coverage) < 1e-12, "teacher-review annotation coverage mismatch")
    _require(summary.get("completeFormSubmission") is True, "teacher-review submission must be complete")

    claim = overlay.get("claimBoundary") or {}
    _require(claim.get("teacherLabelsIngested") is True, "teacher-review ingestion flag missing")
    _require(claim.get("semanticPreservationEstablished") is False, "teacher review cannot establish semantic preservation by itself")
    _require(claim.get("productionPromotionAuthorized") is False, "teacher review cannot authorize production")
    _require(claim.get("stage12EntryAuthorized") is False, "teacher review cannot authorize Stage 12")

    materialized["status"] = "teacher_annotation_ingested_with_conflicts_pending_resolution"
    validation = validate_expected_class_manifest(materialized)
    return {
        "manifest": materialized,
        "validation": validation,
        "conflictCount": len(conflict_map),
        "acceptedResponseCount": EXPECTED_RESPONSE_COUNT - len(conflict_map),
        "sourceReviewPdfSha256": EXPECTED_REVIEW_PDF_SHA256,
    }
