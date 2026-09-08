"""Fail-closed preservation review for the frozen Stage 11 V2a shadow candidate.

This boundary reuses the deterministic music/TAB safety validator on exact non-held-out
shadow outputs. It can block further promotion, but it cannot train, tune, select for
production, or enter Stage 12. Semantic per-class identity (for example notehead vs stem)
is deliberately not claimed by this structural review.
"""
from __future__ import annotations

import hashlib
from typing import Any, Iterable, Mapping

import numpy as np

from .music_safety_validator import validate_candidate
from .safe_restoration import restore_bytes
from .stage11_v2a_shadow_corpus import (
    DEFAULT_RENDER_DPI,
    GEOMETRY_LOCKED_PRIMARY_CONFIG,
    SOURCE_DATA_KIND,
    _source_pages,
)
from .stage11_v2a_shadow_handoff import Stage11V2aShadowObserver
from .stage11_v2a_staging_api import EXPECTED_PACKAGE_SHA256, EXPECTED_PACKAGE_SIZE_BYTES

CONTRACT_ID = "stage11.v2a.shadow-preservation-review.nonheldout.v1"
EVIDENCE_TYPE = "stage11_v2a_nonheldout_shadow_preservation_review_execution"
EVIDENCE_SCHEMA_VERSION = "stage11.v2a.shadow-preservation-review-execution.v1"
EXPECTED_DATASET_ITEMS = {
    "dataset.item.imslp799143-beethoven-op48-no3.v1": "source.family.imslp799143-beethoven-op48-no3.v1",
    "dataset.item.wikimedia-guitar-technical-exercise-no1.v1": "source.family.wikimedia-guitar-technical-exercise-no1.v1",
}
EXPECTED_PAGE_COUNT = 5
EXPECTED_SOURCE_FAMILY_COUNT = 2


class Stage11V2aShadowPreservationReviewError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aShadowPreservationReviewError(message)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def preservation_review_contract() -> dict[str, Any]:
    return {
        "contractId": CONTRACT_ID,
        "candidate": {
            "packageSha256": EXPECTED_PACKAGE_SHA256,
            "packageSizeBytes": EXPECTED_PACKAGE_SIZE_BYTES,
            "frozen": True,
        },
        "scope": {
            "sourceDataKind": SOURCE_DATA_KIND,
            "nonheldoutOnly": True,
            "structuralMusicTabPreservation": True,
            "staffTabGeometryAssessed": True,
            "nonLineSymbolInkAssessed": True,
            "thinComponentPreservationAssessed": True,
            "semanticPerClassIdentityClaimed": False,
        },
        "decision": {
            "pageRejectBlocksBoundary": True,
            "pageReviewRequiredKeepsBoundaryInReview": True,
            "allPagePassMayOnlyPassThisShadowReview": True,
            "automaticApprovalAllowed": False,
            "automaticPromotionAllowed": False,
        },
        "authorization": {
            "preservationReviewAuthorized": True,
            "trainingAuthorized": False,
            "tuningAuthorized": False,
            "productionInferenceAuthorized": False,
            "productionPromotionAuthorized": False,
            "realUserRolloutAuthorized": False,
            "finalProductionModelSelectionAuthorized": False,
            "stage12EntryAuthorized": False,
        },
    }


def summarize_music_safety_report(report: Mapping[str, Any]) -> dict[str, Any]:
    _require(report.get("status") == "completed", "music safety report must be completed")
    verdict = str(report.get("verdict") or "")
    _require(verdict in {"pass", "review_required", "reject"}, "unsupported music safety verdict")
    _require(report.get("automaticApproval") is False, "music safety report cannot auto-approve")
    geometry = report.get("geometry") or {}
    metrics = report.get("metrics") or {}
    symbols = metrics.get("symbols") or {}
    components = metrics.get("components") or {}
    decision = report.get("decision") or {}
    registration = report.get("registration") or {}
    return {
        "verdict": verdict,
        "riskScore": float(metrics.get("riskScore", 100.0)),
        "registration": {
            "reliable": bool(registration.get("reliable")),
            "translationX": float(registration.get("translationX", 0.0)),
            "translationY": float(registration.get("translationY", 0.0)),
            "response": float(registration.get("response", 0.0)),
        },
        "geometry": {
            "staff": dict(geometry.get("staff") or {}),
            "tab": dict(geometry.get("tab") or {}),
            "unknownSystems": dict(geometry.get("unknownSystems") or {}),
        },
        "nonLineSymbols": {
            "sourceDarkPixels": int(symbols.get("sourceDarkPixels", 0)),
            "candidateDarkPixels": int(symbols.get("candidateDarkPixels", 0)),
            "lostDarkPixels": int(symbols.get("lostDarkPixels", 0)),
            "inventedDarkPixels": int(symbols.get("inventedDarkPixels", 0)),
            "lossFraction": float(symbols.get("lossFraction", 1.0)),
            "inventionFraction": float(symbols.get("inventionFraction", 1.0)),
            "inkRecall": 1.0 - float(symbols.get("lossFraction", 1.0)),
        },
        "components": {
            "sourceComponentCount": int(components.get("sourceComponentCount", 0)),
            "candidateComponentCount": int(components.get("candidateComponentCount", 0)),
            "lostComponentCount": int(components.get("lostComponentCount", 0)),
            "inventedComponentCount": int(components.get("inventedComponentCount", 0)),
            "lossFraction": float(components.get("lossFraction", 1.0)),
            "inventionFraction": float(components.get("inventionFraction", 1.0)),
            "componentRecall": 1.0 - float(components.get("lossFraction", 1.0)),
            "maxMatchedShiftPixels": float(components.get("maxMatchedShiftPixels", 0.0)),
            "meanMatchedShiftPixels": float(components.get("meanMatchedShiftPixels", 0.0)),
        },
        "rejectReasons": sorted(str(value) for value in decision.get("rejectReasons") or []),
        "reviewRequiredReasons": sorted(str(value) for value in decision.get("reviewRequiredReasons") or []),
        "semanticClassAttribution": "not_claimed",
        "automaticApproval": False,
        "automaticPromotionPerformed": False,
    }


def _disposition(verdicts: Iterable[str]) -> str:
    values = list(verdicts)
    _require(bool(values), "preservation review requires at least one page")
    if "reject" in values:
        return "blocked"
    if "review_required" in values:
        return "review_required"
    return "shadow_review_pass"


def build_preservation_review_evidence(
    page_records: Iterable[Mapping[str, Any]],
    *,
    environment: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    pages = [dict(item) for item in page_records]
    _require(bool(pages), "preservation review page set is empty")
    verdicts = [str(page.get("review", {}).get("verdict") or "") for page in pages]
    disposition = _disposition(verdicts)
    ink_recalls = [float(page["review"]["nonLineSymbols"]["inkRecall"]) for page in pages]
    component_recalls = [float(page["review"]["components"]["componentRecall"]) for page in pages]
    risk_scores = [float(page["review"]["riskScore"]) for page in pages]
    verdict_counts = {key: verdicts.count(key) for key in ("pass", "review_required", "reject")}
    source_families = sorted({str(page.get("sourceFamilyId") or "") for page in pages})
    return {
        "artifactType": EVIDENCE_TYPE,
        "schemaVersion": EVIDENCE_SCHEMA_VERSION,
        "status": "completed",
        "contractId": CONTRACT_ID,
        "sourceDataKind": SOURCE_DATA_KIND,
        "packageSha256": EXPECTED_PACKAGE_SHA256,
        "packageSizeBytes": EXPECTED_PACKAGE_SIZE_BYTES,
        "reviewScope": "nonheldout_structural_preservation",
        "pages": pages,
        "aggregate": {
            "pageCount": len(pages),
            "sourceFamilyCount": len(source_families),
            "sourceFamilies": source_families,
            "verdictCounts": verdict_counts,
            "meanNonLineInkRecall": float(np.mean(ink_recalls)),
            "minNonLineInkRecall": float(np.min(ink_recalls)),
            "meanComponentRecall": float(np.mean(component_recalls)),
            "minComponentRecall": float(np.min(component_recalls)),
            "meanRiskScore": float(np.mean(risk_scores)),
            "maxRiskScore": float(np.max(risk_scores)),
            "preservationDisposition": disposition,
            "automaticPromotionPerformed": False,
        },
        "interpretation": {
            "staffAndTabGeometryAssessed": True,
            "nonLineSymbolInkAssessed": True,
            "thinComponentPreservationAssessed": True,
            "semanticPerClassNoteheadStemBeamDigitClassificationAssessed": False,
            "semanticClassAttribution": "not_claimed",
        },
        "safety": {
            "heldOutAccessed": False,
            "optimizerCreated": False,
            "backpropagationExecuted": False,
            "weightsMutated": False,
            "trainingPerformed": False,
            "tuningPerformed": False,
            "realUserDataUsed": False,
            "studentDataUsed": False,
            "candidateSelectable": False,
            "automaticPromotionPerformed": False,
        },
        "authorization": preservation_review_contract()["authorization"],
        "contract": preservation_review_contract(),
        "environment": dict(environment or {}),
    }


def run_preservation_review(
    plan: Iterable[Mapping[str, Any]],
    source_bytes_by_item_id: Mapping[str, bytes],
    observer: Stage11V2aShadowObserver,
    *,
    render_dpi: int = DEFAULT_RENDER_DPI,
    environment: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute the structural preservation review against exact non-held-out source bytes."""
    selected = [dict(item) for item in plan]
    _require(selected, "preservation review plan is empty")
    records: list[dict[str, Any]] = []
    for item in selected:
        item_id = str(item.get("datasetItemId") or "")
        family_id = str(item.get("sourceFamilyId") or "")
        _require(item.get("split") == "development", "held-out item reached preservation review")
        artifact = item.get("artifact") or {}
        expected_sha = str(artifact.get("sha256") or "")
        expected_size = int(artifact.get("byteSize", 0))
        raw = source_bytes_by_item_id.get(item_id)
        _require(isinstance(raw, bytes) and bool(raw), f"exact source bytes missing: {item_id}")
        _require(len(raw) == expected_size, f"source size mismatch: {item_id}")
        _require(_sha256(raw) == expected_sha, f"source SHA mismatch: {item_id}")
        for page_index, source_png, _rendered_sha in _source_pages(item, raw, render_dpi=int(render_dpi)):
            primary = restore_bytes(
                source_png,
                source_name=f"preservation-review-{expected_sha[:12]}-{page_index + 1}.png",
                config=GEOMETRY_LOCKED_PRIMARY_CONFIG,
                output_format="png",
                candidate_name=f"preservation-review-{expected_sha[:12]}-{page_index + 1}.primary.png",
            )
            shadow_bytes, observation = observer.observe(
                source_png,
                primary.output_bytes,
                request_id=f"preservation-review:{expected_sha[:16]}:{page_index + 1}",
                source_data_kind=SOURCE_DATA_KIND,
            )
            report = validate_candidate(
                source_png,
                shadow_bytes,
                source_name=f"{item_id}.page-{page_index + 1}.source.png",
                candidate_name=f"{item_id}.page-{page_index + 1}.v2a-shadow.png",
            )
            records.append({
                "datasetItemId": item_id,
                "sourceFamilyId": family_id,
                "pageIndex": int(page_index),
                "sourceSha256": _sha256(source_png),
                "shadowCandidateSha256": _sha256(shadow_bytes),
                "tileCount": int((observation.get("transport") or {}).get("tileCount", 0)),
                "review": summarize_music_safety_report(report),
            })
    return build_preservation_review_evidence(records, environment=environment)


def validate_preservation_review_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == EVIDENCE_TYPE, "preservation evidence type mismatch")
    _require(payload.get("schemaVersion") == EVIDENCE_SCHEMA_VERSION, "preservation evidence schema mismatch")
    _require(payload.get("status") == "completed", "preservation evidence must be completed")
    _require(payload.get("contractId") == CONTRACT_ID, "preservation contract mismatch")
    _require(payload.get("sourceDataKind") == SOURCE_DATA_KIND, "preservation sourceDataKind mismatch")
    _require(payload.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "preservation package SHA mismatch")
    _require(int(payload.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "preservation package size mismatch")
    pages = payload.get("pages")
    _require(isinstance(pages, list) and len(pages) == EXPECTED_PAGE_COUNT, "exact five-page review set required")
    seen: set[tuple[str, int]] = set()
    families: set[str] = set()
    verdicts: list[str] = []
    ink_recalls: list[float] = []
    component_recalls: list[float] = []
    risk_scores: list[float] = []
    for page in pages:
        _require(isinstance(page, Mapping), "preservation page must be an object")
        item_id = str(page.get("datasetItemId") or "")
        family_id = str(page.get("sourceFamilyId") or "")
        _require(EXPECTED_DATASET_ITEMS.get(item_id) == family_id, "unexpected preservation source family")
        page_index = int(page.get("pageIndex", -1))
        key = (item_id, page_index)
        _require(key not in seen, "duplicate preservation page")
        seen.add(key)
        families.add(family_id)
        review = page.get("review") or {}
        verdict = str(review.get("verdict") or "")
        _require(verdict in {"pass", "review_required", "reject"}, "invalid preservation page verdict")
        _require(review.get("semanticClassAttribution") == "not_claimed", "semantic class identity may not be claimed")
        _require(review.get("automaticApproval") is False, "preservation review cannot auto-approve")
        _require(review.get("automaticPromotionPerformed") is False, "preservation review cannot auto-promote")
        symbols = review.get("nonLineSymbols") or {}
        components = review.get("components") or {}
        ink_recall = float(symbols.get("inkRecall", -1.0))
        component_recall = float(components.get("componentRecall", -1.0))
        risk = float(review.get("riskScore", -1.0))
        _require(0.0 <= ink_recall <= 1.0, "invalid non-line ink recall")
        _require(0.0 <= component_recall <= 1.0, "invalid component recall")
        _require(0.0 <= risk <= 100.0, "invalid preservation risk score")
        verdicts.append(verdict)
        ink_recalls.append(ink_recall)
        component_recalls.append(component_recall)
        risk_scores.append(risk)
    _require(len(families) == EXPECTED_SOURCE_FAMILY_COUNT, "two independent source families required")
    _require(("dataset.item.imslp799143-beethoven-op48-no3.v1", 0) in seen, "Beethoven review missing")
    _require(("dataset.item.wikimedia-guitar-technical-exercise-no1.v1", 0) in seen, "Wikimedia/TAB review missing")
    aggregate = payload.get("aggregate") or {}
    _require(int(aggregate.get("pageCount", 0)) == EXPECTED_PAGE_COUNT, "aggregate page count mismatch")
    _require(int(aggregate.get("sourceFamilyCount", 0)) == EXPECTED_SOURCE_FAMILY_COUNT, "aggregate source-family count mismatch")
    expected_counts = {key: verdicts.count(key) for key in ("pass", "review_required", "reject")}
    _require(aggregate.get("verdictCounts") == expected_counts, "aggregate verdict counts mismatch")
    expected_disposition = _disposition(verdicts)
    _require(aggregate.get("preservationDisposition") == expected_disposition, "preservation disposition mismatch")
    for key, value in {
        "meanNonLineInkRecall": float(np.mean(ink_recalls)),
        "minNonLineInkRecall": float(np.min(ink_recalls)),
        "meanComponentRecall": float(np.mean(component_recalls)),
        "minComponentRecall": float(np.min(component_recalls)),
        "meanRiskScore": float(np.mean(risk_scores)),
        "maxRiskScore": float(np.max(risk_scores)),
    }.items():
        _require(abs(float(aggregate.get(key, -999.0)) - value) <= 1e-9, f"aggregate mismatch: {key}")
    _require(aggregate.get("automaticPromotionPerformed") is False, "aggregate cannot auto-promote")
    safety = payload.get("safety") or {}
    for key in (
        "heldOutAccessed", "optimizerCreated", "backpropagationExecuted", "weightsMutated",
        "trainingPerformed", "tuningPerformed", "realUserDataUsed", "studentDataUsed",
        "candidateSelectable", "automaticPromotionPerformed",
    ):
        _require(safety.get(key) is False, f"preservation safety flag must be false: {key}")
    authorization = payload.get("authorization") or {}
    _require(authorization.get("preservationReviewAuthorized") is True, "preservation review authorization missing")
    for key in (
        "trainingAuthorized", "tuningAuthorized", "productionInferenceAuthorized", "productionPromotionAuthorized",
        "realUserRolloutAuthorized", "finalProductionModelSelectionAuthorized", "stage12EntryAuthorized",
    ):
        _require(authorization.get(key) is False, f"authorization must remain false: {key}")
    _require(payload.get("contract") == preservation_review_contract(), "preservation contract snapshot mismatch")
    return {
        "status": "pass",
        "preservationEvidenceValidated": True,
        "preservationDisposition": expected_disposition,
        "pageCount": EXPECTED_PAGE_COUNT,
        "sourceFamilyCount": EXPECTED_SOURCE_FAMILY_COUNT,
        "productionPromotionAuthorized": False,
        "stage12EntryAuthorized": False,
    }


__all__ = [
    "CONTRACT_ID",
    "EVIDENCE_SCHEMA_VERSION",
    "EVIDENCE_TYPE",
    "Stage11V2aShadowPreservationReviewError",
    "build_preservation_review_evidence",
    "preservation_review_contract",
    "run_preservation_review",
    "summarize_music_safety_report",
    "validate_preservation_review_evidence",
]
