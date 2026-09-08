"""Fail-closed validation for Stage 11 V2c full 20-page repeat evidence."""
from __future__ import annotations

from typing import Any, Mapping

from .stage11_v2c_semantic_preservation import (
    CONTRACT_ID,
    EXPECTED_PACKAGE_SHA256,
    EXPECTED_PACKAGE_SIZE_BYTES,
    Stage11V2cSemanticPreservationError,
)

SCHEMA_VERSION = "stage11.v2c.full20-repeat-execution.v1"
DETERMINISM_RESULT = "PASS_FOR_CANONICAL_RUNTIME_AND_FULL_20_PAGE_DEVELOPMENT_CORPUS"
SEMANTIC_BLOCKED_DISPOSITION = "BLOCKED_INDEPENDENT_EXPECTED_CLASS_ANNOTATION_AND_TRUSTED_CLASS_COVERAGE_INSUFFICIENT"
EXPECTED_FAMILIES = {
    "source.family.imslp799143-beethoven-op48-no3.v1",
    "source.family.wikimedia-guitar-technical-exercise-no1.v1",
    "source.family.barley-mnoah-your-face-your-tongue-your-wit.v1",
    "source.family.imslp675596-carulli-recueil-morceaux-faciles.v1",
    "source.family.imslp865937-bach-anna-magdalena.v1",
}
EXPECTED_SOURCES = {
    "beethoven": ("c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c", 1182561),
    "wikimedia": ("36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb", 34636),
    "barley": ("6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e", 84689),
    "carulli": ("db20e9ce755aa56dd9dbb0436a37a48545442e7961e471f813cde7aaa8fc0f22", 4662523),
    "bach": ("692d4317375048b9d520b4d756c3ce992e96ca82b10c3026a5925f1a878fc959", 3235494),
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2cSemanticPreservationError(message)


def _digest(value: Any, label: str) -> str:
    digest = str(value or "")
    _require(len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest), f"invalid {label}")
    return digest


def validate_full20_repeat_execution(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(payload, Mapping), "V2c full20 evidence must be an object")
    _require(payload.get("schemaVersion") == SCHEMA_VERSION, "V2c full20 schema mismatch")
    _require(payload.get("contractId") == CONTRACT_ID, "V2c full20 contract mismatch")

    scope = payload.get("scope") or {}
    _require(scope.get("developmentOnly") is True, "V2c full20 must remain development-only")
    for key in ("heldOutAccessed", "trainingPerformed", "weightsMutated", "productionPromotionAuthorized", "stage12EntryAuthorized"):
        _require(scope.get(key) is False, f"V2c full20 safety flag must remain false: {key}")

    candidate = payload.get("candidate") or {}
    _require(candidate.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "V2c full20 package SHA mismatch")
    _require(int(candidate.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "V2c full20 package size mismatch")
    _require(candidate.get("weightsFrozen") is True, "V2c full20 package must remain frozen")

    runtime = payload.get("canonicalCpuProfile") or {}
    _require(runtime.get("device") == "CPU", "V2c full20 device mismatch")
    _require(runtime.get("torch") == "2.10.0+cpu", "V2c full20 torch mismatch")
    _require(int(runtime.get("intraopThreads", 0)) == 5, "V2c full20 intraop mismatch")
    _require(int(runtime.get("interopThreads", 0)) == 1, "V2c full20 interop mismatch")
    _require(runtime.get("deterministicAlgorithms") is False, "V2c full20 deterministicAlgorithms mismatch")
    _require(runtime.get("applyBeforePackageLoad") is True, "V2c full20 profile timing mismatch")

    render = payload.get("render") or {}
    _require(render.get("engine") == "pdftoppm", "V2c full20 renderer mismatch")
    _require(int(render.get("dpi", 0)) == 72, "V2c full20 render DPI mismatch")

    exact = payload.get("sourceExactBytes") or {}
    _require(set(exact) == set(EXPECTED_SOURCES), "V2c full20 exact-source inventory mismatch")
    for key, (expected_sha, expected_size) in EXPECTED_SOURCES.items():
        record = exact[key]
        _require(record.get("sha256") == expected_sha, f"V2c full20 source SHA mismatch: {key}")
        _require(int(record.get("byteSize", 0)) == expected_size, f"V2c full20 source size mismatch: {key}")

    corpus = payload.get("corpus") or {}
    _require(int(corpus.get("sourceFamilyCount", 0)) == 5, "V2c full20 family count mismatch")
    _require(int(corpus.get("pageCount", 0)) == 20, "V2c full20 page count mismatch")
    page_ids = corpus.get("pageIds")
    _require(isinstance(page_ids, list) and len(page_ids) == 20 and len(set(page_ids)) == 20, "V2c full20 corpus page IDs invalid")

    pages = payload.get("pages")
    _require(isinstance(pages, list) and len(pages) == 20, "V2c full20 requires exactly 20 page records")
    seen: set[str] = set()
    families: set[str] = set()
    for page in pages:
        _require(isinstance(page, Mapping), "V2c full20 page record invalid")
        page_id = str(page.get("pageId") or "")
        _require(page_id and page_id not in seen, "V2c full20 page ID missing/duplicate")
        seen.add(page_id)
        family = str(page.get("sourceFamilyId") or "")
        _require(family in EXPECTED_FAMILIES, "V2c full20 unexpected source family")
        families.add(family)
        _digest(page.get("sourceRenderSha256"), "source render SHA")
        _digest(page.get("sourcePixelSha256"), "source pixel SHA")
        _digest(page.get("outputSha256"), "output SHA")
        _digest(page.get("decodedPixelSha256"), "decoded pixel SHA")
        _require(int(page.get("repeatCount", 0)) == 2, "V2c full20 repeat count mismatch")
        _require(int(page.get("outputByteSize", 0)) > 0, "V2c full20 output byte size missing")
        _require(int(page.get("tileCount", 0)) > 0, "V2c full20 tile count missing")
        _require(page.get("outputBytesStable") is True, "V2c full20 output bytes unstable")
        _require(page.get("decodedPixelsStable") is True, "V2c full20 decoded pixels unstable")
        _require(int(page.get("changedPixelCount", -1)) == 0, "V2c full20 changed pixels must be zero")
        _require(int(page.get("maxAbsDiff", -1)) == 0, "V2c full20 max diff must be zero")
    _require(seen == set(page_ids), "V2c full20 page record/catalog mismatch")
    _require(families == EXPECTED_FAMILIES, "V2c full20 family coverage mismatch")

    aggregate = payload.get("aggregate") or {}
    _require(int(aggregate.get("repeatCountPerPage", 0)) == 2, "V2c full20 aggregate repeat count mismatch")
    _require(aggregate.get("allOutputBytesStable") is True, "V2c full20 aggregate byte stability failed")
    _require(aggregate.get("allDecodedPixelsStable") is True, "V2c full20 aggregate pixel stability failed")
    _require(int(aggregate.get("changedPixelsAcrossRepeats", -1)) == 0, "V2c full20 aggregate changed pixels must be zero")
    _require(int(aggregate.get("maxAbsDiffAcrossRepeats", -1)) == 0, "V2c full20 aggregate max diff must be zero")
    _require(aggregate.get("determinismResult") == DETERMINISM_RESULT, "V2c full20 determinism claim mismatch")
    _require(aggregate.get("semanticPreservationEstablished") is False, "V2c full20 semantic preservation cannot be established here")
    _require(aggregate.get("semanticDisposition") == SEMANTIC_BLOCKED_DISPOSITION, "V2c full20 semantic disposition must remain blocked")

    claim = payload.get("claimBoundary") or {}
    _require(claim.get("semanticPreservation") == "NOT_ESTABLISHED", "V2c full20 semantic success claim forbidden")
    _require(claim.get("rawPixelDriftIsNotMusicalTruth") is True, "V2c full20 raw-pixel claim boundary missing")
    _require(claim.get("productionPromotionAuthorized") is False, "V2c full20 production promotion forbidden")
    _require(claim.get("stage12EntryAuthorized") is False, "V2c full20 Stage 12 authorization forbidden")

    return {
        "status": "pass",
        "sourceFamilyCount": 5,
        "pageCount": 20,
        "determinism": DETERMINISM_RESULT,
        "semanticPreservation": "NOT_ESTABLISHED",
        "stage12EntryAuthorized": False,
    }
