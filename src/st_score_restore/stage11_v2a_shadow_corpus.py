"""Fail-closed non-held-out corpus observation for the frozen Stage 11 V2a candidate.

This boundary is development/evaluation only. It consumes already-approved Stage 1
open-corpus items from the development split, compares the frozen V2a output with a
shape-locked OpenCV primary candidate, and emits observation evidence. It cannot train,
tune, select, promote, register a network route, use held-out data, or enter Stage 12.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable, Mapping

import cv2
import numpy as np

from .pdf_pipeline import PdfPipelineConfig, process_pdf_bytes
from .safe_restoration import restore_bytes
from .stage11_v2a_shadow_handoff import Stage11V2aShadowObserver
from .stage11_v2a_staging_api import (
    EXPECTED_PACKAGE_SHA256,
    EXPECTED_PACKAGE_SIZE_BYTES,
    encode_grayscale_png,
)

CONTRACT_ID = "stage11.v2a.shadow-corpus.approved-nonheldout.v1"
EVIDENCE_TYPE = "stage11_v2a_nonheldout_shadow_corpus_execution"
EVIDENCE_SCHEMA_VERSION = "stage11.v2a.shadow-corpus-execution.v1"
SOURCE_DATA_KIND = "nonheldout_test_only"
SUPPORTED_INPUT_KINDS = frozenset({"png", "scanned_pdf"})
SUPPORTED_MEDIA_TYPES = frozenset({"image/png", "application/pdf"})
DEFAULT_RENDER_DPI = 72

# First exact-byte real-corpus acceptance item. It is public-domain/open-corpus,
# quality_evaluation-granted, and assigned to development in catalog.v2.
FIRST_REAL_DATASET_ITEM_ID = "dataset.item.imslp799143-beethoven-op48-no3.v1"
FIRST_REAL_SOURCE_FAMILY_ID = "source.family.imslp799143-beethoven-op48-no3.v1"
FIRST_REAL_SOURCE_SHA256 = "c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c"
FIRST_REAL_SOURCE_BYTES = 1_182_561
FIRST_REAL_PAGE_COUNT = 4

GEOMETRY_LOCKED_PRIMARY_CONFIG = {
    "orientation_enabled": False,
    "deskew_enabled": False,
    "perspective_enabled": False,
    "crop_enabled": False,
}


class Stage11V2aShadowCorpusError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aShadowCorpusError(message)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _hex_digest(value: Any, label: str) -> str:
    digest = str(value or "")
    _require(len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest), f"invalid {label}")
    return digest


def shadow_corpus_contract() -> dict[str, Any]:
    return {
        "contractId": CONTRACT_ID,
        "candidate": {
            "packageSha256": EXPECTED_PACKAGE_SHA256,
            "packageSizeBytes": EXPECTED_PACKAGE_SIZE_BYTES,
            "frozen": True,
        },
        "admission": {
            "eligibilityClass": "open_corpus",
            "split": "development",
            "requiredPermission": "quality_evaluation",
            "requiredPermissionStatus": "granted",
            "requiredReviewStatus": "approved",
            "requiredRevocationStatus": "not_revoked",
            "requiredPrivacyClassification": "none",
            "allowedSourceKinds": ["public_domain"],
            "supportedInputKinds": sorted(SUPPORTED_INPUT_KINDS),
            "supportedMediaTypes": sorted(SUPPORTED_MEDIA_TYPES),
            "heldOutForbidden": True,
        },
        "transport": {
            "pdfPolicy": "raster_only_pages",
            "defaultRenderDpi": DEFAULT_RENDER_DPI,
            "grayscaleTransportRequired": True,
            "normalizedDerivativeBecomesDatasetItem": False,
            "sourceBytesModified": False,
        },
        "primaryComparator": {
            "engine": "opencv_safe_baseline",
            "geometryLockedForShadowComparison": True,
            "configuration": dict(GEOMETRY_LOCKED_PRIMARY_CONFIG),
            "selectable": False,
        },
        "comparison": {
            "purpose": "observational_only",
            "metrics": [
                "meanAbsDiff",
                "maxAbsDiff",
                "changedPixelFraction",
                "sourceToPrimaryMeanAbsDiff",
                "sourceToShadowMeanAbsDiff",
            ],
            "qualityDecisionAllowed": False,
            "tuningAllowed": False,
            "automaticPromotionAllowed": False,
        },
        "authorization": {
            "shadowCorpusObservationAuthorized": True,
            "trainingAuthorized": False,
            "tuningAuthorized": False,
            "productionInferenceAuthorized": False,
            "productionPromotionAuthorized": False,
            "realUserRolloutAuthorized": False,
            "finalProductionModelSelectionAuthorized": False,
            "stage12EntryAuthorized": False,
        },
    }


def eligible_shadow_corpus_items(catalog: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return only Stage 1 items that are safe for this observation boundary."""

    _require(isinstance(catalog, Mapping), "Stage 1 catalog must be an object")
    items = catalog.get("items")
    _require(isinstance(items, list), "Stage 1 catalog items must be a list")
    eligible: list[dict[str, Any]] = []
    for raw in items:
        if not isinstance(raw, Mapping):
            continue
        item = dict(raw)
        artifact = item.get("artifact") or {}
        provenance = item.get("provenance") or {}
        privacy = item.get("privacy") or {}
        permissions = item.get("permissions") or {}
        quality = permissions.get("quality_evaluation") or {}
        review = item.get("review") or {}
        revocation = item.get("revocation") or {}
        input_meta = item.get("input") or {}
        rights_review = provenance.get("rightsReview") or {}
        if not (
            item.get("eligibilityClass") == "open_corpus"
            and item.get("split") == "development"
            and artifact.get("state") == "external_available"
            and provenance.get("sourceKind") == "public_domain"
            and rights_review.get("status") == "approved"
            and privacy.get("classification") == "none"
            and quality.get("status") == "granted"
            and review.get("status") == "approved"
            and revocation.get("status") == "not_revoked"
            and input_meta.get("kind") in SUPPORTED_INPUT_KINDS
            and input_meta.get("mediaType") in SUPPORTED_MEDIA_TYPES
        ):
            continue
        try:
            _hex_digest(artifact.get("sha256"), "eligible artifact SHA")
            _require(int(artifact.get("byteSize", 0)) > 0, "eligible artifact byte size missing")
        except (Stage11V2aShadowCorpusError, TypeError, ValueError):
            continue
        eligible.append(item)
    return sorted(eligible, key=lambda item: str(item.get("datasetItemId") or ""))


def build_shadow_corpus_plan(
    catalog: Mapping[str, Any],
    dataset_item_ids: Iterable[str],
) -> list[dict[str, Any]]:
    requested = [str(value) for value in dataset_item_ids]
    _require(requested, "at least one non-held-out dataset item is required")
    _require(len(requested) == len(set(requested)), "duplicate shadow corpus dataset item")
    by_id = {
        str(item.get("datasetItemId")): item
        for item in eligible_shadow_corpus_items(catalog)
    }
    missing = [item_id for item_id in requested if item_id not in by_id]
    _require(not missing, f"requested item is not eligible for non-held-out shadow observation: {missing}")
    return [by_id[item_id] for item_id in requested]


def _native_grayscale_png(raw: bytes, *, label: str) -> bytes:
    _require(isinstance(raw, bytes) and bool(raw), f"{label} bytes required")
    encoded = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_UNCHANGED)
    _require(image is not None, f"{label} decode failed")
    _require(image.ndim == 2 and image.dtype == np.uint8, f"{label} must be native 8-bit grayscale PNG")
    return encode_grayscale_png(image)


def _render_scanned_pdf_pages(raw: bytes, *, source_name: str, render_dpi: int) -> list[tuple[int, bytes, str]]:
    result = process_pdf_bytes(
        raw,
        source_name=source_name,
        config=PdfPipelineConfig(render_dpi=render_dpi),
    )
    manifest = dict(result.manifest)
    _require(manifest.get("sourceBytesModified") is False, "PDF source bytes must remain immutable")
    _require(manifest.get("vectorPagesRasterized") is False, "vector pages may not be rasterized for shadow corpus")
    _require(int(manifest.get("renderedPageCount", 0)) == int(manifest.get("pageCount", -1)), "all selected scanned-PDF pages must be raster-only and rendered")
    pages: list[tuple[int, bytes, str]] = []
    for page_record in manifest.get("pages") or []:
        page_index = int(page_record["pageIndex"])
        rendered = result.page_bytes(page_index)
        _require(rendered is not None, "rendered PDF page bytes missing")
        image = cv2.imdecode(np.frombuffer(rendered, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        _require(image is not None and image.ndim == 2, "rendered PDF page grayscale normalization failed")
        normalized = encode_grayscale_png(image)
        render_meta = page_record.get("render") or {}
        rendered_sha = _hex_digest(render_meta.get("sha256"), "rendered page SHA")
        pages.append((page_index, normalized, rendered_sha))
    _require(pages, "selected scanned PDF produced no observable raster pages")
    return pages


def _source_pages(item: Mapping[str, Any], raw: bytes, *, render_dpi: int) -> list[tuple[int, bytes, str | None]]:
    input_meta = item.get("input") or {}
    kind = input_meta.get("kind")
    if kind == "png":
        return [(0, _native_grayscale_png(raw, label="shadow corpus PNG"), None)]
    if kind == "scanned_pdf":
        return _render_scanned_pdf_pages(
            raw,
            source_name=f"{item.get('datasetItemId')}.pdf",
            render_dpi=render_dpi,
        )
    raise Stage11V2aShadowCorpusError("unsupported shadow corpus input kind")


def run_nonheldout_shadow_corpus(
    plan: Iterable[Mapping[str, Any]],
    source_bytes_by_item_id: Mapping[str, bytes],
    observer: Stage11V2aShadowObserver,
    *,
    render_dpi: int = DEFAULT_RENDER_DPI,
) -> dict[str, Any]:
    """Execute a read-only corpus comparison over approved development items."""

    selected = [dict(item) for item in plan]
    _require(selected, "shadow corpus plan cannot be empty")
    _require(isinstance(source_bytes_by_item_id, Mapping), "source byte map must be an object")
    _require(isinstance(observer, Stage11V2aShadowObserver), "observer must be Stage11V2aShadowObserver")
    _require(72 <= int(render_dpi) <= 300, "shadow corpus render DPI outside approved PDF range")

    corpus_records: list[dict[str, Any]] = []
    all_page_metrics: list[dict[str, float]] = []
    for item in selected:
        item_id = str(item.get("datasetItemId") or "")
        _require(item.get("split") == "development", "held-out item reached shadow corpus runner")
        _require(item.get("eligibilityClass") == "open_corpus", "shadow corpus item is not open-corpus")
        artifact = item.get("artifact") or {}
        expected_sha = _hex_digest(artifact.get("sha256"), "source artifact SHA")
        expected_size = int(artifact.get("byteSize", 0))
        raw = source_bytes_by_item_id.get(item_id)
        _require(isinstance(raw, bytes) and bool(raw), f"exact bytes missing for {item_id}")
        _require(len(raw) == expected_size, f"source byte-size mismatch for {item_id}")
        _require(_sha256(raw) == expected_sha, f"source SHA mismatch for {item_id}")

        page_records: list[dict[str, Any]] = []
        for page_index, source_png, rendered_sha in _source_pages(item, raw, render_dpi=int(render_dpi)):
            primary = restore_bytes(
                source_png,
                source_name=f"shadow-corpus-{expected_sha[:12]}-page-{page_index + 1}.png",
                config=GEOMETRY_LOCKED_PRIMARY_CONFIG,
                output_format="png",
                candidate_name=f"shadow-corpus-{expected_sha[:12]}-page-{page_index + 1}.primary.png",
            )
            source_image = cv2.imdecode(np.frombuffer(source_png, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
            primary_image = cv2.imdecode(np.frombuffer(primary.output_bytes, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
            _require(source_image is not None and primary_image is not None, "shadow corpus comparator decode failed")
            _require(source_image.shape == primary_image.shape, "shape-locked primary comparator changed geometry")

            request_id = f"shadow-corpus:{expected_sha[:16]}:{page_index + 1}"
            shadow_bytes, observation = observer.observe(
                source_png,
                primary.output_bytes,
                request_id=request_id,
                source_data_kind=SOURCE_DATA_KIND,
            )
            shadow_image = cv2.imdecode(np.frombuffer(shadow_bytes, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
            _require(shadow_image is not None and shadow_image.shape == source_image.shape, "shadow corpus output geometry mismatch")

            source_float = source_image.astype(np.float32) / 255.0
            primary_float = primary_image.astype(np.float32) / 255.0
            shadow_float = shadow_image.astype(np.float32) / 255.0
            source_to_primary = np.abs(source_float - primary_float)
            source_to_shadow = np.abs(source_float - shadow_float)
            comparison = dict(observation["comparison"])
            comparison.update(
                {
                    "sourceToPrimaryMeanAbsDiff": float(source_to_primary.mean()),
                    "sourceToShadowMeanAbsDiff": float(source_to_shadow.mean()),
                }
            )
            metrics = {
                "meanAbsDiff": float(comparison["meanAbsDiff"]),
                "maxAbsDiff": float(comparison["maxAbsDiff"]),
                "changedPixelFraction": float(comparison["changedPixelFraction"]),
                "sourceToPrimaryMeanAbsDiff": float(comparison["sourceToPrimaryMeanAbsDiff"]),
                "sourceToShadowMeanAbsDiff": float(comparison["sourceToShadowMeanAbsDiff"]),
            }
            all_page_metrics.append(metrics)
            page_records.append(
                {
                    "pageIndex": page_index,
                    "shape": list(source_image.shape),
                    "renderedPageSha256": rendered_sha,
                    "normalizedGrayscaleSha256": _sha256(source_png),
                    "primaryCandidateSha256": _sha256(primary.output_bytes),
                    "shadowCandidateSha256": _sha256(shadow_bytes),
                    "tileCount": int(observation["transport"]["tileCount"]),
                    "comparison": {**comparison, "qualityDecisionMade": False, "automaticPromotionPerformed": False},
                }
            )
        corpus_records.append(
            {
                "datasetItemId": item_id,
                "sourceFamilyId": str(item.get("sourceFamilyId") or ""),
                "sourceSha256": expected_sha,
                "sourceByteSize": expected_size,
                "split": "development",
                "eligibilityClass": "open_corpus",
                "purpose": "quality_evaluation",
                "inputKind": (item.get("input") or {}).get("kind"),
                "pageCount": len(page_records),
                "pages": page_records,
            }
        )

    means = [m["meanAbsDiff"] for m in all_page_metrics]
    changed = [m["changedPixelFraction"] for m in all_page_metrics]
    _require(means, "shadow corpus execution produced no page observations")
    return {
        "artifactType": EVIDENCE_TYPE,
        "schemaVersion": EVIDENCE_SCHEMA_VERSION,
        "status": "completed",
        "contractId": CONTRACT_ID,
        "sourceDataKind": SOURCE_DATA_KIND,
        "packageSha256": EXPECTED_PACKAGE_SHA256,
        "packageSizeBytes": EXPECTED_PACKAGE_SIZE_BYTES,
        "transportNormalization": {
            "pdfRenderer": "pdfium/pypdfium2",
            "dpi": int(render_dpi),
            "pagePolicy": "raster_only_pages",
            "grayscaleConversion": "opencv_imread_grayscale_to_native_png",
            "normalizedDerivativePersistedAsDatasetItem": False,
            "trainingDataCreated": False,
        },
        "primaryComparator": {
            "engine": "opencv_safe_baseline",
            "configuration": "current_default_photometric_with_geometry_locked_for_shadow_comparison",
            "sourceBytesModified": False,
        },
        "corpus": corpus_records,
        "pageObservationCount": len(all_page_metrics),
        "aggregate": {
            "meanOfPageMeanAbsDiff": float(np.mean(means)),
            "maxPageMeanAbsDiff": float(np.max(means)),
            "minPageMeanAbsDiff": float(np.min(means)),
            "meanChangedPixelFraction": float(np.mean(changed)),
            "maxChangedPixelFraction": float(np.max(changed)),
            "minChangedPixelFraction": float(np.min(changed)),
            "qualityDecisionMade": False,
            "automaticPromotionPerformed": False,
        },
        "safety": {
            "heldOutAccessed": False,
            "optimizerCreated": False,
            "backpropagationExecuted": False,
            "weightsMutated": False,
            "realUserDataUsed": False,
            "studentDataUsed": False,
            "trainingPerformed": False,
            "tuningPerformed": False,
            "shadowSelectable": False,
        },
        "authorization": shadow_corpus_contract()["authorization"],
        "contract": shadow_corpus_contract(),
    }


def validate_shadow_corpus_execution_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate committed first-real-corpus evidence without touching source bytes."""

    _require(payload.get("artifactType") == EVIDENCE_TYPE, "shadow corpus evidence type mismatch")
    _require(payload.get("schemaVersion") == EVIDENCE_SCHEMA_VERSION, "shadow corpus evidence schema mismatch")
    _require(payload.get("status") == "completed", "shadow corpus evidence must be completed")
    _require(payload.get("sourceDataKind") == SOURCE_DATA_KIND, "shadow corpus sourceDataKind mismatch")
    _require(payload.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "shadow corpus package SHA mismatch")
    _require(int(payload.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "shadow corpus package size mismatch")
    if payload.get("pageObservationCount") is not None:
        _require(int(payload.get("pageObservationCount", 0)) == FIRST_REAL_PAGE_COUNT, "shadow corpus page observation count mismatch")

    # The imported acceptance evidence intentionally uses the first exact-byte real public
    # development item only. Broader source-family coverage is a later boundary.
    if "corpus" in payload:
        corpus = payload.get("corpus")
        _require(isinstance(corpus, list) and len(corpus) == 1, "first real shadow corpus evidence must contain one source item")
        item = corpus[0]
    else:
        item = payload
    _require(item.get("datasetItemId") == FIRST_REAL_DATASET_ITEM_ID, "shadow corpus dataset item mismatch")
    _require(item.get("sourceFamilyId") == FIRST_REAL_SOURCE_FAMILY_ID, "shadow corpus source family mismatch")
    _require(item.get("sourceSha256") == FIRST_REAL_SOURCE_SHA256, "shadow corpus source SHA mismatch")
    _require(int(item.get("sourceByteSize", 0)) == FIRST_REAL_SOURCE_BYTES, "shadow corpus source size mismatch")
    _require(item.get("split") == "development", "shadow corpus must not use held-out split")
    _require(item.get("eligibilityClass") == "open_corpus", "shadow corpus eligibility mismatch")
    _require(item.get("purpose") == "quality_evaluation", "shadow corpus purpose mismatch")
    pages = item.get("pages")
    _require(isinstance(pages, list) and len(pages) == FIRST_REAL_PAGE_COUNT, "shadow corpus page set mismatch")
    _require([int(page.get("pageIndex", -1)) for page in pages] == list(range(FIRST_REAL_PAGE_COUNT)), "shadow corpus page order mismatch")

    means: list[float] = []
    changed_values: list[float] = []
    for page in pages:
        shape = page.get("shape")
        _require(isinstance(shape, list) and len(shape) == 2 and all(int(v) > 0 for v in shape), "shadow corpus page shape invalid")
        for key in ("normalizedGrayscaleSha256", "primaryCandidateSha256", "shadowCandidateSha256"):
            _hex_digest(page.get(key), key)
        rendered = page.get("renderedPageSha256")
        if rendered is not None:
            _hex_digest(rendered, "rendered page SHA")
        _require(int(page.get("tileCount", 0)) > 0, "shadow corpus tile count missing")
        comparison = page.get("comparison") or {}
        mean = float(comparison.get("meanAbsDiff", -1.0))
        maximum = float(comparison.get("maxAbsDiff", -1.0))
        changed = float(comparison.get("changedPixelFraction", -1.0))
        _require(mean >= 0.0 and maximum >= 0.0, "shadow corpus comparison missing")
        _require(0.0 <= changed <= 1.0, "shadow corpus changed-pixel fraction invalid")
        _require(float(comparison.get("sourceToPrimaryMeanAbsDiff", -1.0)) >= 0.0, "source-to-primary metric missing")
        _require(float(comparison.get("sourceToShadowMeanAbsDiff", -1.0)) >= 0.0, "source-to-shadow metric missing")
        _require(comparison.get("qualityDecisionMade") is False, "shadow corpus cannot make a quality decision")
        _require(comparison.get("automaticPromotionPerformed") is False, "shadow corpus cannot promote")
        means.append(mean)
        changed_values.append(changed)

    aggregate = payload.get("aggregate") or {}
    expected = {
        "meanOfPageMeanAbsDiff": float(np.mean(means)),
        "maxPageMeanAbsDiff": float(np.max(means)),
        "minPageMeanAbsDiff": float(np.min(means)),
        "meanChangedPixelFraction": float(np.mean(changed_values)),
        "maxChangedPixelFraction": float(np.max(changed_values)),
        "minChangedPixelFraction": float(np.min(changed_values)),
    }
    for key, value in expected.items():
        _require(abs(float(aggregate.get(key, -1.0)) - value) <= 1e-12, f"shadow corpus aggregate mismatch: {key}")
    _require(aggregate.get("qualityDecisionMade") is False, "aggregate cannot make a quality decision")
    _require(aggregate.get("automaticPromotionPerformed") is False, "aggregate cannot promote")

    transport = payload.get("transportNormalization") or {}
    _require(transport.get("pagePolicy") == "raster_only_pages", "shadow corpus PDF page policy mismatch")
    _require(int(transport.get("dpi", 0)) == DEFAULT_RENDER_DPI, "shadow corpus acceptance DPI mismatch")
    _require(transport.get("normalizedDerivativePersistedAsDatasetItem") is False, "transport derivative cannot become a dataset item")
    _require(transport.get("trainingDataCreated") is False, "transport cannot create training data")
    comparator = payload.get("primaryComparator") or {}
    _require(comparator.get("engine") == "opencv_safe_baseline", "shadow corpus primary comparator mismatch")
    _require(comparator.get("sourceBytesModified") is False, "primary comparator cannot modify source bytes")

    safety = payload.get("safety") or {}
    for key in (
        "heldOutAccessed",
        "optimizerCreated",
        "backpropagationExecuted",
        "weightsMutated",
        "realUserDataUsed",
        "studentDataUsed",
        "trainingPerformed",
        "tuningPerformed",
        "shadowSelectable",
    ):
        _require(safety.get(key) is False, f"shadow corpus safety flag must be false: {key}")
    authorization = payload.get("authorization") or {}
    _require(authorization.get("shadowCorpusObservationAuthorized") is True, "shadow corpus authorization missing")
    for key in (
        "trainingAuthorized",
        "tuningAuthorized",
        "productionInferenceAuthorized",
        "productionPromotionAuthorized",
        "realUserRolloutAuthorized",
        "finalProductionModelSelectionAuthorized",
        "stage12EntryAuthorized",
    ):
        _require(authorization.get(key) is False, f"shadow corpus authorization must remain false: {key}")
    _require(payload.get("contractId") == CONTRACT_ID, "shadow corpus contract ID mismatch")
    _require(payload.get("contract") == shadow_corpus_contract(), "shadow corpus contract snapshot mismatch")
    return {
        "status": "pass",
        "realNonheldoutCorpusObserved": True,
        "pageObservationCount": FIRST_REAL_PAGE_COUNT,
        "sourceFamilyCount": 1,
        "productionInferenceAuthorized": False,
        "realUserRolloutAuthorized": False,
        "stage12EntryAuthorized": False,
    }


__all__ = [
    "CONTRACT_ID",
    "DEFAULT_RENDER_DPI",
    "EVIDENCE_SCHEMA_VERSION",
    "EVIDENCE_TYPE",
    "FIRST_REAL_DATASET_ITEM_ID",
    "FIRST_REAL_SOURCE_FAMILY_ID",
    "FIRST_REAL_SOURCE_SHA256",
    "SOURCE_DATA_KIND",
    "Stage11V2aShadowCorpusError",
    "build_shadow_corpus_plan",
    "eligible_shadow_corpus_items",
    "run_nonheldout_shadow_corpus",
    "shadow_corpus_contract",
    "validate_shadow_corpus_execution_evidence",
]
