"""Validation for the Stage 11 V2a non-held-out shadow-corpus source-family expansion.

This layer accepts a second independently approved development source family while keeping
all shadow observations read-only and non-selectable. It does not train, tune, promote,
register production inference, consume held-out data, or authorize Stage 12.
"""
from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from .stage11_v2a_shadow_corpus import (
    CONTRACT_ID,
    EVIDENCE_SCHEMA_VERSION,
    EVIDENCE_TYPE,
    FIRST_REAL_DATASET_ITEM_ID,
    FIRST_REAL_PAGE_COUNT,
    FIRST_REAL_SOURCE_BYTES,
    FIRST_REAL_SOURCE_FAMILY_ID,
    FIRST_REAL_SOURCE_SHA256,
    SOURCE_DATA_KIND,
    shadow_corpus_contract,
)
from .stage11_v2a_staging_api import EXPECTED_PACKAGE_SHA256, EXPECTED_PACKAGE_SIZE_BYTES

EXPANDED_PAGE_COUNT = 5
EXPANDED_SOURCE_FAMILY_COUNT = 2
SECOND_DATASET_ITEM_ID = "dataset.item.wikimedia-guitar-technical-exercise-no1.v1"
SECOND_SOURCE_FAMILY_ID = "source.family.wikimedia-guitar-technical-exercise-no1.v1"
SECOND_SOURCE_SHA256 = "36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb"
SECOND_SOURCE_BYTES = 34_636
SECOND_PAGE_COUNT = 1
SECOND_INPUT_KIND = "png"


class Stage11V2aShadowCorpusExpansionError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aShadowCorpusExpansionError(message)


def _hex_digest(value: Any, label: str) -> str:
    digest = str(value or "")
    _require(len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest), f"invalid {label}")
    return digest


def _validate_page(page: Mapping[str, Any]) -> tuple[float, float]:
    shape = page.get("shape")
    _require(isinstance(shape, list) and len(shape) == 2 and all(int(v) > 0 for v in shape), "expanded shadow page shape invalid")
    for key in ("normalizedGrayscaleSha256", "primaryCandidateSha256", "shadowCandidateSha256"):
        _hex_digest(page.get(key), key)
    rendered = page.get("renderedPageSha256")
    if rendered is not None:
        _hex_digest(rendered, "renderedPageSha256")
    _require(int(page.get("tileCount", 0)) > 0, "expanded shadow page tile count missing")
    comparison = page.get("comparison") or {}
    mean = float(comparison.get("meanAbsDiff", -1.0))
    maximum = float(comparison.get("maxAbsDiff", -1.0))
    changed = float(comparison.get("changedPixelFraction", -1.0))
    _require(mean >= 0.0 and maximum >= 0.0, "expanded shadow comparison missing")
    _require(0.0 <= changed <= 1.0, "expanded shadow changed-pixel fraction invalid")
    _require(float(comparison.get("sourceToPrimaryMeanAbsDiff", -1.0)) >= 0.0, "source-to-primary metric missing")
    _require(float(comparison.get("sourceToShadowMeanAbsDiff", -1.0)) >= 0.0, "source-to-shadow metric missing")
    _require(comparison.get("qualityDecisionMade") is False, "expanded shadow observation cannot decide quality")
    _require(comparison.get("automaticPromotionPerformed") is False, "expanded shadow observation cannot promote")
    return mean, changed


def validate_shadow_corpus_expansion_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == EVIDENCE_TYPE, "expanded shadow evidence type mismatch")
    _require(payload.get("schemaVersion") == EVIDENCE_SCHEMA_VERSION, "expanded shadow evidence schema mismatch")
    _require(payload.get("status") == "completed", "expanded shadow evidence must be completed")
    _require(payload.get("contractId") == CONTRACT_ID, "expanded shadow contract mismatch")
    _require(payload.get("sourceDataKind") == SOURCE_DATA_KIND, "expanded shadow sourceDataKind mismatch")
    _require(payload.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "expanded shadow package SHA mismatch")
    _require(int(payload.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "expanded shadow package size mismatch")
    _require(int(payload.get("pageObservationCount", 0)) == EXPANDED_PAGE_COUNT, "expanded shadow page count mismatch")

    corpus = payload.get("corpus")
    _require(isinstance(corpus, list) and len(corpus) == 2, "expanded shadow corpus must contain exactly two source items")
    expected = [
        {
            "datasetItemId": FIRST_REAL_DATASET_ITEM_ID,
            "sourceFamilyId": FIRST_REAL_SOURCE_FAMILY_ID,
            "sourceSha256": FIRST_REAL_SOURCE_SHA256,
            "sourceByteSize": FIRST_REAL_SOURCE_BYTES,
            "pageCount": FIRST_REAL_PAGE_COUNT,
            "inputKind": "scanned_pdf",
        },
        {
            "datasetItemId": SECOND_DATASET_ITEM_ID,
            "sourceFamilyId": SECOND_SOURCE_FAMILY_ID,
            "sourceSha256": SECOND_SOURCE_SHA256,
            "sourceByteSize": SECOND_SOURCE_BYTES,
            "pageCount": SECOND_PAGE_COUNT,
            "inputKind": SECOND_INPUT_KIND,
        },
    ]

    means: list[float] = []
    changed_values: list[float] = []
    families: set[str] = set()
    for item, spec in zip(corpus, expected):
        _require(isinstance(item, Mapping), "expanded shadow corpus item must be an object")
        for key in ("datasetItemId", "sourceFamilyId", "sourceSha256", "sourceByteSize", "pageCount", "inputKind"):
            _require(item.get(key) == spec[key], f"expanded shadow item mismatch: {key}")
        _require(item.get("split") == "development", "expanded shadow corpus must remain development-only")
        _require(item.get("eligibilityClass") == "open_corpus", "expanded shadow corpus must remain open-corpus")
        _require(item.get("purpose") == "quality_evaluation", "expanded shadow purpose mismatch")
        families.add(str(item["sourceFamilyId"]))
        pages = item.get("pages")
        _require(isinstance(pages, list) and len(pages) == int(spec["pageCount"]), "expanded shadow page set mismatch")
        _require([int(page.get("pageIndex", -1)) for page in pages] == list(range(int(spec["pageCount"]))), "expanded shadow page order mismatch")
        for page in pages:
            mean, changed = _validate_page(page)
            means.append(mean)
            changed_values.append(changed)

    _require(len(families) == EXPANDED_SOURCE_FAMILY_COUNT, "expanded shadow source families are not independent")
    _require(SECOND_SOURCE_FAMILY_ID != FIRST_REAL_SOURCE_FAMILY_ID, "second source family must be independent")

    aggregate = payload.get("aggregate") or {}
    expected_aggregate = {
        "meanOfPageMeanAbsDiff": float(np.mean(means)),
        "maxPageMeanAbsDiff": float(np.max(means)),
        "minPageMeanAbsDiff": float(np.min(means)),
        "meanChangedPixelFraction": float(np.mean(changed_values)),
        "maxChangedPixelFraction": float(np.max(changed_values)),
        "minChangedPixelFraction": float(np.min(changed_values)),
    }
    for key, value in expected_aggregate.items():
        _require(abs(float(aggregate.get(key, -1.0)) - value) <= 1e-12, f"expanded shadow aggregate mismatch: {key}")
    _require(aggregate.get("qualityDecisionMade") is False, "expanded aggregate cannot decide quality")
    _require(aggregate.get("automaticPromotionPerformed") is False, "expanded aggregate cannot promote")

    source = payload.get("executionSource") or {}
    _require(source.get("kind") == "exact-byte-approved-development-custody", "expanded execution source mismatch")
    _require(source.get("frozenPackageSha256Verified") is True, "expanded package identity not verified")
    _require(source.get("sourceArtifactSha256Verified") is True, "expanded source identity not verified")
    _require(int(source.get("sourceFamilyCount", 0)) == EXPANDED_SOURCE_FAMILY_COUNT, "expanded source-family count mismatch")
    _require(source.get("independentSourceFamiliesVerified") is True, "expanded source-family independence not verified")

    transport = payload.get("transportNormalization") or {}
    _require(transport.get("pagePolicy") == "raster_only_pages", "expanded PDF page policy mismatch")
    _require(int(transport.get("dpi", 0)) == 72, "expanded acceptance DPI mismatch")
    _require(transport.get("normalizedDerivativePersistedAsDatasetItem") is False, "expanded normalized derivative cannot become dataset item")
    _require(transport.get("trainingDataCreated") is False, "expanded transport cannot create training data")

    comparator = payload.get("primaryComparator") or {}
    _require(comparator.get("engine") == "opencv_safe_baseline", "expanded primary comparator mismatch")
    _require(comparator.get("sourceBytesModified") is False, "expanded comparator cannot modify source bytes")

    safety = payload.get("safety") or {}
    for key in (
        "heldOutAccessed", "optimizerCreated", "backpropagationExecuted", "weightsMutated",
        "realUserDataUsed", "studentDataUsed", "trainingPerformed", "tuningPerformed", "shadowSelectable",
    ):
        _require(safety.get(key) is False, f"expanded shadow safety flag must remain false: {key}")

    authorization = payload.get("authorization") or {}
    _require(authorization.get("shadowCorpusObservationAuthorized") is True, "expanded shadow authorization missing")
    for key in (
        "trainingAuthorized", "tuningAuthorized", "productionInferenceAuthorized", "productionPromotionAuthorized",
        "realUserRolloutAuthorized", "finalProductionModelSelectionAuthorized", "stage12EntryAuthorized",
    ):
        _require(authorization.get(key) is False, f"expanded shadow authorization must remain false: {key}")
    _require(payload.get("contract") == shadow_corpus_contract(), "expanded shadow contract snapshot mismatch")

    return {
        "status": "pass",
        "expandedNonheldoutCorpusObserved": True,
        "pageObservationCount": EXPANDED_PAGE_COUNT,
        "sourceFamilyCount": EXPANDED_SOURCE_FAMILY_COUNT,
        "productionInferenceAuthorized": False,
        "realUserRolloutAuthorized": False,
        "stage12EntryAuthorized": False,
    }


__all__ = [
    "EXPANDED_PAGE_COUNT",
    "EXPANDED_SOURCE_FAMILY_COUNT",
    "SECOND_DATASET_ITEM_ID",
    "SECOND_SOURCE_FAMILY_ID",
    "SECOND_SOURCE_SHA256",
    "Stage11V2aShadowCorpusExpansionError",
    "validate_shadow_corpus_expansion_evidence",
]
