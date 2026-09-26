"""Validate the pristine Stage 11 V2d clef/staff spatial review package.

This module validates preparation evidence only.  It deliberately rejects populated
human annotations so detector output or repository-authored data cannot be mistaken
for teacher ground truth.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .stage11_v2c_semantic_preservation import Stage11V2cSemanticPreservationError

SCHEMA_VERSION = "stage11.v2d.spatial-teacher-review-work-package.v1"
CONTRACT_ID = "stage11.v2c.semantic-preservation.nonheldout.v1"
EXPECTED_STATE = "awaiting_human_spatial_labels"
EXPECTED_CLASSES = ("clef", "staff_line")
EXPECTED_RENDER_PROFILE = "pdftoppm-72dpi-singlepage-or-source-png-copy.v1"
HUMAN_FIELDS = (
    "clefBoxes",
    "staffLineMaskPng",
    "staffSystems",
    "reviewerStatus",
    "reviewerNote",
)
FORBIDDEN_CLAIMS = (
    "teacherSpatialLabelsComplete",
    "detectorQualified",
    "semanticPreservationEstablished",
    "overallStage11PassAuthorized",
    "productionReady",
    "productionPromotionAuthorized",
    "stage12EntryAuthorized",
)

EXPECTED_SOURCES: dict[str, dict[str, Any]] = {
    "beethoven": {
        "driveFileId": "1F6Xp6mmwsjmpk64GkcDqw6t0XpH_1IGk",
        "filename": "beethoven-op48-no3.pdf",
        "byteSize": 1_182_561,
        "sha256": "c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c",
    },
    "wikimedia": {
        "driveFileId": "1JYyN_nk0lYarszlBlC9nqVfeJxB0FEmz",
        "filename": "wikimedia-guitar-technical-exercise-no1.png",
        "byteSize": 34_636,
        "sha256": "36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb",
    },
    "barley": {
        "driveFileId": "1TsmQFpcM4uv52MH37ilKFj1jYY4pyCrG",
        "filename": "barley-your-face-your-tongue-your-wit.pdf",
        "byteSize": 84_689,
        "sha256": "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e",
    },
    "carulli": {
        "driveFileId": "1TkE4FVRb16IhVkYH5q10WOs4wPRDdhmi",
        "filename": "carulli-morceaux-faciles.pdf",
        "byteSize": 4_662_523,
        "sha256": "db20e9ce755aa56dd9dbb0436a37a48545442e7961e471f813cde7aaa8fc0f22",
    },
    "bach": {
        "driveFileId": "1tgd9EEplOAwJmdurUGctvQ9Rzw6U4zvX",
        "filename": "bach-anna-magdalena.pdf",
        "byteSize": 3_235_494,
        "sha256": "692d4317375048b9d520b4d756c3ce992e96ca82b10c3026a5925f1a878fc959",
    },
}

EXPECTED_PAGES: tuple[tuple[str, str, int], ...] = (
    ("beethoven-op48-no3-p2", "beethoven", 2),
    ("beethoven-op48-no3-p3", "beethoven", 3),
    ("wikimedia-guitar-technical-exercise-no1-p1", "wikimedia", 1),
    ("barley-your-face-your-tongue-your-wit-p1", "barley", 1),
    ("barley-your-face-your-tongue-your-wit-p2", "barley", 2),
    ("carulli-morceaux-faciles-p2", "carulli", 2),
    ("carulli-morceaux-faciles-p3", "carulli", 3),
    ("carulli-morceaux-faciles-p4", "carulli", 4),
    ("carulli-morceaux-faciles-p5", "carulli", 5),
    ("carulli-morceaux-faciles-p6", "carulli", 6),
    ("carulli-morceaux-faciles-p7", "carulli", 7),
    ("carulli-morceaux-faciles-p8", "carulli", 8),
    ("carulli-morceaux-faciles-p9", "carulli", 9),
    ("carulli-morceaux-faciles-p10", "carulli", 10),
    ("bach-anna-magdalena-p4", "bach", 4),
    ("bach-anna-magdalena-p10", "bach", 10),
    ("bach-anna-magdalena-p24", "bach", 24),
    ("bach-anna-magdalena-p40", "bach", 40),
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2cSemanticPreservationError(message)


def _validate_sources(raw_sources: Any) -> None:
    _require(isinstance(raw_sources, list), "source assets must be a list")
    source_map: dict[str, Mapping[str, Any]] = {}
    for source in raw_sources:
        _require(isinstance(source, Mapping), "source asset must be an object")
        source_id = str(source.get("sourceId") or "")
        _require(source_id and source_id not in source_map, "sourceId missing or duplicate")
        source_map[source_id] = source
    _require(set(source_map) == set(EXPECTED_SOURCES), "source asset set mismatch")
    for source_id, expected in EXPECTED_SOURCES.items():
        actual = source_map[source_id]
        for key, value in expected.items():
            _require(actual.get(key) == value, f"source asset mismatch: {source_id}.{key}")


def validate_spatial_review_work_package(package: Mapping[str, Any]) -> dict[str, Any]:
    """Validate exact scope, annotation conventions, and null human fields."""
    _require(package.get("schemaVersion") == SCHEMA_VERSION, "spatial work-package schema mismatch")
    _require(package.get("contractId") == CONTRACT_ID, "spatial work-package contract mismatch")
    _require(package.get("state") == EXPECTED_STATE, "spatial work package must remain pristine")

    scope = package.get("scope") or {}
    _require(scope.get("developmentOnly") is True, "spatial review must remain development-only")
    _require(tuple(scope.get("semanticClasses") or ()) == EXPECTED_CLASSES, "spatial class scope mismatch")
    _require(scope.get("teacherPresentPageCount") == len(EXPECTED_PAGES), "teacher-present page count mismatch")
    _require(scope.get("heldOutAccessed") is False, "held-out access is forbidden")
    _require(scope.get("trainingAuthorized") is False, "training is not authorized")

    independence = package.get("independenceBoundary") or {}
    _require(independence.get("reviewBasis") == "source_page_only", "review basis must be source-only")
    _require(independence.get("modelOutputShown") is False, "model output must remain hidden")
    _require(independence.get("restoredOutputShown") is False, "restored output must remain hidden")
    _require(independence.get("detectorOutputUsedAsGroundTruth") is False, "detector output cannot be ground truth")

    coordinates = package.get("coordinateContract") or {}
    _require(coordinates.get("renderProfile") == EXPECTED_RENDER_PROFILE, "render profile mismatch")
    _require(coordinates.get("origin") == "top_left", "coordinate origin mismatch")
    _require(coordinates.get("units") == "integer_source_page_pixels", "coordinate units mismatch")
    _require(coordinates.get("boxOrder") == ["xMin", "yMin", "xMaxExclusive", "yMaxExclusive"], "box order mismatch")

    clef = package.get("clefAnnotationContract") or {}
    _require(clef.get("geometry") == "axis_aligned_boxes", "clef geometry mismatch")
    _require(clef.get("includeEveryVisibleClef") is True, "all visible clefs must be requested")
    _require(clef.get("modelSuggestionsAllowed") is False, "clef model suggestions are forbidden")
    _require(clef.get("emptyArrayMeansTeacherConfirmedAbsent") is True, "clef empty-array semantics missing")

    staff = package.get("staffLineAnnotationContract") or {}
    _require(staff.get("maskFormat") == "single_channel_png", "staff mask format mismatch")
    _require(staff.get("maskValues") == {"background": 0, "staffLine": 255}, "staff mask values mismatch")
    _require(staff.get("systemTopologyRequired") is True, "staff system topology must be required")
    _require(staff.get("individualLineOrder") == "top_to_bottom", "staff line ordering mismatch")
    _require(staff.get("modelSuggestionsAllowed") is False, "staff model suggestions are forbidden")

    _validate_sources(package.get("sourceAssets"))
    pages = package.get("pages")
    _require(isinstance(pages, list) and len(pages) == len(EXPECTED_PAGES), "exactly 18 review pages required")
    for page, (page_id, source_id, page_number) in zip(pages, EXPECTED_PAGES):
        _require(isinstance(page, Mapping), "review page must be an object")
        _require(page.get("pageId") == page_id, f"review page order/identity mismatch: {page_id}")
        _require(page.get("sourceId") == source_id, f"review source mismatch: {page_id}")
        _require(page.get("sourcePageNumber") == page_number, f"review page number mismatch: {page_id}")
        _require(page.get("teacherExpectedState") == {"clef": "present", "staff_line": "present"}, f"teacher state mismatch: {page_id}")
        _require(page.get("reviewImagePath") == f"source-pages/{page_id}.png", f"review image path mismatch: {page_id}")
        annotations = page.get("humanAnnotations")
        _require(isinstance(annotations, Mapping), f"human annotation object required: {page_id}")
        _require(set(annotations) == set(HUMAN_FIELDS), f"human annotation fields mismatch: {page_id}")
        for field in HUMAN_FIELDS:
            _require(annotations.get(field) is None, f"work package unexpectedly contains human evidence: {page_id}.{field}")

    boundary = package.get("claimBoundary") or {}
    for key in FORBIDDEN_CLAIMS:
        _require(boundary.get(key) is False, f"claim must remain false: {key}")
    _require(boundary.get("newColabRunRequiredNow") is False, "package preparation cannot request Colab")
    return {
        "status": "pass",
        "state": EXPECTED_STATE,
        "sourceAssetCount": len(EXPECTED_SOURCES),
        "reviewPageCount": len(EXPECTED_PAGES),
        "humanAnnotationFieldCount": len(EXPECTED_PAGES) * len(HUMAN_FIELDS),
        "humanAnnotationsPopulated": 0,
        "newColabRunRequiredNow": False,
    }


def validate_spatial_review_work_package_file(path: Path) -> dict[str, Any]:
    try:
        package = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Stage11V2cSemanticPreservationError("spatial work package is not valid JSON") from exc
    _require(isinstance(package, Mapping), "spatial work package must be an object")
    return validate_spatial_review_work_package(package)
