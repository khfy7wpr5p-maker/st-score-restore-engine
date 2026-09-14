"""Stage 11 V2c development-only semantic-preservation evidence layer.

This module is intentionally fail-closed.  It does not replace the shared music-safety
validator, does not modify the HTTP/job-service path, and cannot train, tune, promote,
access held-out data, or authorize Stage 12.  Its purpose is to make semantic-preservation
measurement class-aware, provenance-aware, and non-circular for the already-frozen V2a
candidate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Callable, Iterable, Mapping, Sequence

import cv2
import numpy as np

EXPECTED_PACKAGE_SHA256 = "7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234"
EXPECTED_PACKAGE_SIZE_BYTES = 7_817_857
CONTRACT_ID = "stage11.v2c.semantic-preservation.nonheldout.v1"
MANIFEST_SCHEMA_VERSION = "stage11.v2c.expected-class-manifest.v1"
CURRENT_TRUTH_SCHEMA_VERSION = "stage11.v2c.current-truth.v1"

CANONICAL_CPU_PROFILE = {
    "device": "CPU",
    "torch": "2.10.0+cpu",
    "intraopThreads": 5,
    "interopThreads": 1,
    "deterministicAlgorithms": False,
    "applyBeforePackageLoad": True,
}

SEMANTIC_CLASSES = (
    "staff_line",
    "tab_line",
    "notehead",
    "stem",
    "beam_or_flag",
    "rest",
    "accidental",
    "clef",
    "barline",
    "tie_or_slur",
    "tab_digit",
    "tab_string",
)
EXPECTED_STATES = frozenset({"present", "absent", "not_applicable", "unknown_review_required"})
INDEPENDENT_PROVENANCE_TYPES = frozenset({"public_ground_truth", "teacher_annotation", "independent_review"})


class Stage11V2cSemanticPreservationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2cSemanticPreservationError(message)


def _bbox(value: Sequence[float]) -> tuple[float, float, float, float]:
    _require(len(value) == 4, "bbox must contain x1,y1,x2,y2")
    x1, y1, x2, y2 = (float(v) for v in value)
    _require(all(math.isfinite(v) for v in (x1, y1, x2, y2)), "bbox must be finite")
    _require(x2 > x1 and y2 > y1, "bbox must have positive area")
    return x1, y1, x2, y2


@dataclass(frozen=True)
class SemanticDetection:
    class_id: str
    bbox: tuple[float, float, float, float]
    confidence: float
    provenance: str
    detector_version: str
    abstention_reason: str | None = None

    def __post_init__(self) -> None:
        _require(self.class_id in SEMANTIC_CLASSES, f"unknown semantic class: {self.class_id}")
        object.__setattr__(self, "bbox", _bbox(self.bbox))
        _require(0.0 <= float(self.confidence) <= 1.0, "confidence outside [0,1]")
        _require(bool(self.provenance), "detection provenance required")
        _require(bool(self.detector_version), "detector version required")
        if self.abstention_reason is not None:
            _require(bool(str(self.abstention_reason).strip()), "blank abstention reason")

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["bbox"] = list(self.bbox)
        return payload


def semantic_preservation_contract() -> dict[str, Any]:
    return {
        "contractId": CONTRACT_ID,
        "candidate": {
            "packageSha256": EXPECTED_PACKAGE_SHA256,
            "packageSizeBytes": EXPECTED_PACKAGE_SIZE_BYTES,
            "weightsFrozen": True,
        },
        "runtime": dict(CANONICAL_CPU_PROFILE),
        "semanticClasses": list(SEMANTIC_CLASSES),
        "expectedClassStates": sorted(EXPECTED_STATES),
        "measurement": {
            "expectedPresenceMustBeIndependentOfEvaluatedDetector": True,
            "presentClassesAreDetectorCoverageDenominator": True,
            "absentClassesAreNotSourceRecallFailures": True,
            "unknownClassesCannotCreateAutomaticPassEvidence": True,
            "detectorFailureIsAbstention": True,
            "sameClassOneToOneMatching": True,
            "crossClassMatchingForbidden": True,
        },
        "scope": {
            "nonHeldOutOnly": True,
            "developmentOnly": True,
            "sharedMusicSafetyValidatorModified": False,
            "httpApiModified": False,
            "openApiModified": False,
            "normalJobServiceModified": False,
        },
        "authorization": {
            "trainingAuthorized": False,
            "fineTuningAuthorized": False,
            "tuningAuthorized": False,
            "heldOutAccessAuthorized": False,
            "productionInferenceAuthorized": False,
            "productionPromotionAuthorized": False,
            "stage12EntryAuthorized": False,
        },
    }


def validate_expected_class_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    _require(manifest.get("schemaVersion") == MANIFEST_SCHEMA_VERSION, "expected-class manifest schema mismatch")
    _require(manifest.get("contractId") == CONTRACT_ID, "expected-class manifest contract mismatch")
    pages = manifest.get("pages")
    _require(isinstance(pages, list), "expected-class manifest pages must be a list")
    seen: set[str] = set()
    state_counts = {state: 0 for state in EXPECTED_STATES}
    eligible_present = 0
    independently_annotated = 0

    for page in pages:
        _require(isinstance(page, Mapping), "expected-class page must be an object")
        page_id = str(page.get("pageId") or "")
        _require(page_id and page_id not in seen, "expected-class pageId missing or duplicated")
        seen.add(page_id)
        _require(bool(page.get("sourceFamilyId")), "expected-class sourceFamilyId required")
        _require(page.get("split") == "development", "held-out/non-development page forbidden")
        classes = page.get("classes")
        _require(isinstance(classes, Mapping), "expected-class classes must be an object")
        _require(set(classes) == set(SEMANTIC_CLASSES), "expected-class page must enumerate every semantic class")
        for class_id in SEMANTIC_CLASSES:
            record = classes[class_id]
            _require(isinstance(record, Mapping), f"expected-class record must be object: {class_id}")
            state = record.get("state")
            _require(state in EXPECTED_STATES, f"invalid expected-class state: {class_id}")
            state_counts[str(state)] += 1
            provenance = record.get("provenance") or {}
            provenance_type = provenance.get("type")
            if state in {"present", "absent"}:
                _require(provenance_type in INDEPENDENT_PROVENANCE_TYPES, f"independent provenance required: {class_id}")
                _require(bool(provenance.get("evidenceRef")), f"expected-class evidenceRef required: {class_id}")
                independently_annotated += 1
            elif provenance_type is not None:
                _require(provenance_type in INDEPENDENT_PROVENANCE_TYPES, f"invalid expected-class provenance: {class_id}")
            if state == "present":
                eligible_present += 1

    total_applicable = state_counts["present"] + state_counts["absent"] + state_counts["unknown_review_required"]
    annotation_coverage = independently_annotated / max(1, total_applicable)
    return {
        "status": "pass",
        "pageCount": len(pages),
        "stateCounts": state_counts,
        "eligiblePresentClassCount": eligible_present,
        "independentlyAnnotatedClassCount": independently_annotated,
        "annotationCoverage": annotation_coverage,
    }


def _iou(a: SemanticDetection, b: SemanticDetection) -> float:
    ax1, ay1, ax2, ay2 = a.bbox
    bx1, by1, bx2, by2 = b.bbox
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    intersection = iw * ih
    if intersection <= 0:
        return 0.0
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - intersection
    return intersection / max(union, 1e-12)


def suppress_duplicate_detections(
    detections: Iterable[SemanticDetection], *, iou_threshold: float = 0.8
) -> list[SemanticDetection]:
    _require(0.0 <= float(iou_threshold) <= 1.0, "duplicate IoU threshold outside [0,1]")
    ordered = sorted(detections, key=lambda item: (-item.confidence, item.class_id, item.bbox))
    kept: list[SemanticDetection] = []
    for detection in ordered:
        duplicate = any(
            existing.class_id == detection.class_id and _iou(existing, detection) >= float(iou_threshold)
            for existing in kept
        )
        if not duplicate:
            kept.append(detection)
    return kept


def match_same_class_one_to_one(
    source: Iterable[SemanticDetection],
    candidate: Iterable[SemanticDetection],
    *,
    class_id: str,
    confidence_threshold: float = 0.5,
    match_iou_threshold: float = 0.3,
) -> dict[str, Any]:
    _require(class_id in SEMANTIC_CLASSES, "invalid match class")
    _require(0.0 <= float(confidence_threshold) <= 1.0, "confidence threshold outside [0,1]")
    _require(0.0 <= float(match_iou_threshold) <= 1.0, "match IoU threshold outside [0,1]")
    source_items = suppress_duplicate_detections(
        item for item in source if item.class_id == class_id and item.confidence >= float(confidence_threshold)
    )
    candidate_items = suppress_duplicate_detections(
        item for item in candidate if item.class_id == class_id and item.confidence >= float(confidence_threshold)
    )
    pairs: list[tuple[float, int, int]] = []
    for source_index, source_item in enumerate(source_items):
        for candidate_index, candidate_item in enumerate(candidate_items):
            overlap = _iou(source_item, candidate_item)
            if overlap >= float(match_iou_threshold):
                pairs.append((overlap, source_index, candidate_index))
    pairs.sort(reverse=True)
    used_source: set[int] = set()
    used_candidate: set[int] = set()
    matches: list[dict[str, Any]] = []
    for overlap, source_index, candidate_index in pairs:
        if source_index in used_source or candidate_index in used_candidate:
            continue
        used_source.add(source_index)
        used_candidate.add(candidate_index)
        matches.append({"sourceIndex": source_index, "candidateIndex": candidate_index, "iou": overlap})
    matched = len(matches)
    return {
        "classId": class_id,
        "sourceCount": len(source_items),
        "candidateCount": len(candidate_items),
        "matchedCount": matched,
        "sourceRecall": matched / max(1, len(source_items)),
        "candidateOnlyCount": max(0, len(candidate_items) - matched),
        "candidateOnlyRate": max(0, len(candidate_items) - matched) / max(1, len(candidate_items)),
        "matches": matches,
        "crossClassMatchingAllowed": False,
    }


def detector_coverage_from_manifest(
    manifest: Mapping[str, Any],
    confidently_evaluated_present: Mapping[str, Iterable[str]],
    confidently_evaluated_absent: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, Any]:
    validation = validate_expected_class_manifest(manifest)
    absent_map = confidently_evaluated_absent or {}
    eligible_present = 0
    covered_present = 0
    eligible_absent = 0
    covered_absent = 0
    unknown_count = 0
    page_results: list[dict[str, Any]] = []
    for page in manifest.get("pages") or []:
        page_id = str(page["pageId"])
        evaluated_present = set(confidently_evaluated_present.get(page_id) or ())
        evaluated_absent = set(absent_map.get(page_id) or ())
        _require(evaluated_present <= set(SEMANTIC_CLASSES), "unknown evaluated present class")
        _require(evaluated_absent <= set(SEMANTIC_CLASSES), "unknown evaluated absent class")
        page_eligible_present = 0
        page_covered_present = 0
        for class_id, record in page["classes"].items():
            state = record["state"]
            if state == "present":
                eligible_present += 1
                page_eligible_present += 1
                if class_id in evaluated_present:
                    covered_present += 1
                    page_covered_present += 1
            elif state == "absent":
                eligible_absent += 1
                if class_id in evaluated_absent:
                    covered_absent += 1
            elif state == "unknown_review_required":
                unknown_count += 1
        page_results.append(
            {
                "pageId": page_id,
                "eligiblePresentClassCount": page_eligible_present,
                "coveredPresentClassCount": page_covered_present,
                "applicableClassDetectorCoverage": page_covered_present / max(1, page_eligible_present),
            }
        )
    return {
        "annotationCoverage": validation["annotationCoverage"],
        "eligiblePresentClassCount": eligible_present,
        "coveredPresentClassCount": covered_present,
        "applicableClassDetectorCoverage": covered_present / max(1, eligible_present),
        "eligibleAbsentClassCount": eligible_absent,
        "coveredAbsentClassCount": covered_absent,
        "absenceEvaluationCoverage": covered_absent / max(1, eligible_absent),
        "unknownReviewRequiredClassCount": unknown_count,
        "pages": page_results,
    }


def run_detector_safely(
    detector: Callable[[np.ndarray], Iterable[SemanticDetection]], image: np.ndarray, *, detector_name: str
) -> dict[str, Any]:
    _require(isinstance(image, np.ndarray) and image.ndim == 2 and image.size > 0, "detector image must be non-empty grayscale")
    try:
        detections = list(detector(image))
        _require(all(isinstance(item, SemanticDetection) for item in detections), "detector returned invalid item")
        return {"detections": [item.as_dict() for item in detections], "abstentions": []}
    except Exception as exc:  # fail closed by design at this evidence-only boundary
        return {
            "detections": [],
            "abstentions": [
                {
                    "classId": "*",
                    "detector": detector_name,
                    "reason": f"detector_failure:{type(exc).__name__}",
                }
            ],
        }


def conservative_line_system_detector(image: np.ndarray) -> list[SemanticDetection]:
    """Detect only high-confidence 5-line staff or 6-line TAB systems; otherwise abstain.

    This is deliberately narrow.  It does not claim note, pitch, rhythm, or TAB-digit
    identity. Unsupported semantic classes remain abstentions until a separately trusted
    inference-only detector is admitted.
    """
    _require(isinstance(image, np.ndarray) and image.ndim == 2, "line detector expects grayscale image")
    gray = image.astype(np.uint8, copy=False)
    dark = gray < 128
    occupancy = dark.mean(axis=1)
    candidate_rows = np.flatnonzero(occupancy >= 0.35)
    if candidate_rows.size == 0:
        return []
    groups: list[list[int]] = []
    for row in candidate_rows.tolist():
        if not groups or row > groups[-1][-1] + 1:
            groups.append([row])
        else:
            groups[-1].append(row)
    centers = [int(round(sum(group) / len(group))) for group in groups]
    detections: list[SemanticDetection] = []
    width = float(gray.shape[1])
    for start in range(len(centers)):
        for count, class_id in ((6, "tab_line"), (5, "staff_line")):
            subset = centers[start : start + count]
            if len(subset) != count:
                continue
            spacings = np.diff(np.asarray(subset, dtype=np.float64))
            if spacings.size == 0:
                continue
            median = float(np.median(spacings))
            if median < 3.0 or median > 64.0:
                continue
            if float(np.max(np.abs(spacings - median))) > max(1.5, median * 0.18):
                continue
            confidence = min(0.99, 0.82 + float(np.min(occupancy[subset])) * 0.15)
            for row in subset:
                detections.append(
                    SemanticDetection(
                        class_id=class_id,
                        bbox=(0.0, max(0.0, row - 1.0), width, min(float(gray.shape[0]), row + 2.0)),
                        confidence=confidence,
                        provenance="rule:horizontal-system-spacing",
                        detector_version="stage11-v2c-line-system.v1",
                    )
                )
            return detections
    return []


def validate_corpus_plan(plan: Mapping[str, Any], *, minimum_families: int = 5, minimum_pages: int = 20) -> dict[str, Any]:
    items = plan.get("items")
    _require(isinstance(items, list), "corpus plan items must be a list")
    families: set[str] = set()
    page_count = 0
    for item in items:
        _require(isinstance(item, Mapping), "corpus plan item must be object")
        _require(item.get("eligibilityClass") == "open_corpus", "non-open corpus item forbidden")
        _require(item.get("split") == "development", "held-out/non-development corpus item forbidden")
        _require(item.get("qualityEvaluationStatus") == "granted", "quality_evaluation grant required")
        _require(item.get("rightsReviewStatus") == "approved", "rights approval required")
        _require(item.get("privacyClassification") == "none", "privacy must be none")
        _require(item.get("revocationStatus") == "not_revoked", "revoked corpus item forbidden")
        family = str(item.get("sourceFamilyId") or "")
        _require(bool(family), "source family required")
        families.add(family)
        pages = int(item.get("pageCount", 0))
        _require(pages > 0, "positive corpus page count required")
        page_count += pages
        sha = str(item.get("sourceSha256") or "")
        _require(len(sha) == 64 and all(ch in "0123456789abcdef" for ch in sha), "valid source SHA-256 required")
        _require(int(item.get("sourceByteSize", 0)) > 0, "source byte size required")
        _require(bool(item.get("rightsEvidenceRef")), "rights evidence reference required")
    family_count = len(families)
    passed = family_count >= int(minimum_families) and page_count >= int(minimum_pages)
    return {
        "status": "pass" if passed else "blocked",
        "sourceFamilyCount": family_count,
        "pageCount": page_count,
        "minimumSourceFamilies": int(minimum_families),
        "minimumPages": int(minimum_pages),
        "familyShortage": max(0, int(minimum_families) - family_count),
        "pageShortage": max(0, int(minimum_pages) - page_count),
    }


def decide_v2c_disposition(
    *,
    determinism_passed: bool,
    corpus_gate_passed: bool,
    provenance_gate_passed: bool,
    semantic_evidence_sufficient: bool,
    teacher_review_required: bool,
    systematic_deletion_evidenced: bool = False,
    systematic_invention_evidenced: bool = False,
) -> dict[str, Any]:
    blockers: list[str] = []
    if not determinism_passed:
        blockers.append("determinism_insufficient")
    if not corpus_gate_passed:
        blockers.append("approved_corpus_insufficient")
    if not provenance_gate_passed:
        blockers.append("semantic_provenance_insufficient")
    if not semantic_evidence_sufficient:
        blockers.append("semantic_detector_coverage_insufficient")
    if systematic_deletion_evidenced:
        blockers.append("systematic_music_symbol_deletion")
    if systematic_invention_evidenced:
        blockers.append("systematic_music_symbol_invention")
    hard = systematic_deletion_evidenced or systematic_invention_evidenced
    if blockers:
        disposition = "blocked"
    elif teacher_review_required:
        disposition = "review_required"
    else:
        disposition = "review_complete"
    return {
        "disposition": disposition,
        "blockers": sorted(set(blockers)),
        "hardBlocker": hard,
        "automaticPromotionAuthorized": False,
        "stage12EntryAuthorized": False,
    }


def validate_current_truth(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("schemaVersion") == CURRENT_TRUTH_SCHEMA_VERSION, "V2c current-truth schema mismatch")
    _require(payload.get("contractId") == CONTRACT_ID, "V2c current-truth contract mismatch")
    candidate = payload.get("candidate") or {}
    _require(candidate.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "V2c package SHA mismatch")
    _require(int(candidate.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "V2c package size mismatch")
    _require(candidate.get("weightsFrozen") is True, "V2c weights must remain frozen")
    authorization = payload.get("authorization") or {}
    for key in (
        "trainingAuthorized",
        "heldOutAccessAuthorized",
        "productionInferenceAuthorized",
        "productionPromotionAuthorized",
        "stage12EntryAuthorized",
    ):
        _require(authorization.get(key) is False, f"V2c authorization must remain false: {key}")
    _require((payload.get("productionBoundaries") or {}).get("sharedMusicSafetyValidatorModified") is False, "shared validator modification forbidden")
    _require((payload.get("productionBoundaries") or {}).get("httpApiModified") is False, "HTTP API modification forbidden")
    return {"status": "pass", "state": payload.get("state"), "stage12EntryAuthorized": False}
