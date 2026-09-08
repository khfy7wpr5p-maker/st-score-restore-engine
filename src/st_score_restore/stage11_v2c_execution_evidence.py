"""Validation for Stage 11 V2c exact frozen-package repeat evidence.

This is evidence validation only.  It cannot authorize training, held-out access,
production inference/promotion, or Stage 12.
"""
from __future__ import annotations

from typing import Any, Mapping

from .stage11_v2c_semantic_preservation import (
    CANONICAL_CPU_PROFILE,
    EXPECTED_PACKAGE_SHA256,
    EXPECTED_PACKAGE_SIZE_BYTES,
    Stage11V2cSemanticPreservationError,
)

BARLEY_DATASET_ITEM_ID = "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1"
BARLEY_SOURCE_FAMILY_ID = "source.family.barley-mnoah-your-face-your-tongue-your-wit.v1"
BARLEY_SOURCE_SHA256 = "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e"
BARLEY_SOURCE_BYTE_SIZE = 84_689
EVIDENCE_SCHEMA_VERSION = "stage11.v2c.barley-repeat-execution.v1"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2cSemanticPreservationError(message)


def _digest(value: Any, label: str) -> str:
    digest = str(value or "")
    _require(len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest), f"invalid {label}")
    return digest


def validate_barley_repeat_execution(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(payload, Mapping), "V2c Barley evidence must be an object")
    _require(payload.get("schemaVersion") == EVIDENCE_SCHEMA_VERSION, "V2c Barley evidence schema mismatch")
    _require(payload.get("sourceDatasetItemId") == BARLEY_DATASET_ITEM_ID, "V2c Barley dataset item mismatch")
    _require(payload.get("sourceFamilyId") == BARLEY_SOURCE_FAMILY_ID, "V2c Barley source family mismatch")
    _require(payload.get("sourcePdfSha256") == BARLEY_SOURCE_SHA256, "V2c Barley source SHA mismatch")
    _require(int(payload.get("sourcePdfByteSize", 0)) == BARLEY_SOURCE_BYTE_SIZE, "V2c Barley source size mismatch")
    _require(int(payload.get("renderDpi", 0)) == 72, "V2c Barley render DPI mismatch")
    _require(payload.get("renderer") == "pdfium-via-render_pdf.py", "V2c Barley renderer mismatch")
    _require(payload.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "V2c package SHA mismatch")
    _require(int(payload.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "V2c package size mismatch")
    _require(int(payload.get("repeatCount", 0)) >= 2, "V2c repeat count insufficient")

    runtime = payload.get("runtime") or {}
    for key in ("device", "torch", "intraopThreads", "interopThreads", "deterministicAlgorithms"):
        _require(runtime.get(key) == CANONICAL_CPU_PROFILE[key], f"V2c canonical runtime mismatch: {key}")
    method = payload.get("executionMethod") or {}
    _require(method.get("profileAppliedBeforePackageLoad") is True, "V2c CPU profile must be applied before package load")

    pages = payload.get("pages")
    _require(isinstance(pages, list) and len(pages) == 2, "V2c Barley evidence requires exactly two pages")
    seen_pages: set[int] = set()
    for page in pages:
        _require(isinstance(page, Mapping), "V2c Barley page record must be an object")
        page_index = int(page.get("pageIndex", -1))
        _require(page_index in {0, 1} and page_index not in seen_pages, "V2c Barley page index invalid/duplicate")
        seen_pages.add(page_index)
        shape = page.get("shape")
        _require(shape == [792, 612], "V2c Barley rendered page shape mismatch")
        _digest(page.get("renderedSourceSha256"), "rendered source SHA")
        _digest(page.get("sourceDecodedPixelSha256"), "source decoded-pixel SHA")
        repeats = page.get("repeats")
        _require(isinstance(repeats, list) and len(repeats) == int(payload.get("repeatCount")), "V2c Barley repeat records incomplete")
        output_hashes: set[str] = set()
        decoded_hashes: set[str] = set()
        for repeat in repeats:
            _require(isinstance(repeat, Mapping), "V2c repeat record must be an object")
            output_hashes.add(_digest(repeat.get("outputSha256"), "repeat output SHA"))
            decoded_hashes.add(_digest(repeat.get("decodedPixelSha256"), "repeat decoded-pixel SHA"))
            _require(int(repeat.get("outputBytes", 0)) > 0, "V2c repeat output bytes missing")
            _require(int(repeat.get("tileCount", 0)) == 4, "V2c Barley tile count mismatch")
            _require(0.0 <= float(repeat.get("outputMin", -1.0)) <= 1.0, "V2c outputMin outside [0,1]")
            _require(0.0 <= float(repeat.get("outputMax", 2.0)) <= 1.0, "V2c outputMax outside [0,1]")
        _require(len(output_hashes) == 1, "V2c repeat output bytes are not stable")
        _require(len(decoded_hashes) == 1, "V2c repeat decoded pixels are not stable")
        repeatability = page.get("repeatability") or {}
        _require(repeatability.get("outputBytesStable") is True, "V2c output byte stability flag missing")
        _require(repeatability.get("decodedPixelsStable") is True, "V2c decoded-pixel stability flag missing")
        _require(int(repeatability.get("changedPixelsAcrossRepeats", -1)) == 0, "V2c changed pixels across repeats must be zero")
        _require(float(repeatability.get("maxAbsDiffAcrossRepeats", -1.0)) == 0.0, "V2c max repeat difference must be zero")

    aggregate = payload.get("aggregate") or {}
    _require(int(aggregate.get("pageCount", 0)) == 2, "V2c Barley aggregate page count mismatch")
    _require(aggregate.get("allOutputBytesStable") is True, "V2c aggregate byte stability failed")
    _require(aggregate.get("allDecodedPixelsStable") is True, "V2c aggregate pixel stability failed")
    _require(int(aggregate.get("changedPixelsAcrossRepeats", -1)) == 0, "V2c aggregate changed pixels must be zero")
    _require(float(aggregate.get("maxAbsDiffAcrossRepeats", -1.0)) == 0.0, "V2c aggregate max diff must be zero")

    _require(payload.get("semanticDisposition") == "BLOCKED_INDEPENDENT_EXPECTED_CLASS_ANNOTATION_AND_CORPUS_TARGET_INSUFFICIENT", "V2c Barley semantic disposition must remain blocked")
    _require((payload.get("claimBoundary") or {}).get("semanticPreservation") == "NOT_ESTABLISHED", "V2c semantic preservation cannot be claimed")
    _require((payload.get("claimBoundary") or {}).get("rawPixelDriftIsNotMusicalTruth") is True, "V2c raw-pixel claim boundary missing")
    for key in (
        "heldoutAccessed",
        "trainingPerformed",
        "weightsMutated",
        "productionInferenceAuthorized",
        "productionPromotionAuthorized",
        "stage12EntryAuthorized",
    ):
        _require(payload.get(key) is False, f"V2c safety flag must remain false: {key}")

    return {
        "status": "pass",
        "sourceFamilyId": BARLEY_SOURCE_FAMILY_ID,
        "pageCount": 2,
        "determinism": "PASS_FOR_BARLEY_CANONICAL_RUNTIME_AND_TWO_PAGE_SOURCE",
        "semanticPreservation": "NOT_ESTABLISHED",
        "productionPromotionAuthorized": False,
        "stage12EntryAuthorized": False,
    }
