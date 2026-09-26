"""Development-only source-only high-recall general-clef candidate generator.

This module implements the candidate-generation seam of ADR 0025. It proposes
staff-relative clef localizations without teacher truth, filenames, page IDs,
source-family IDs, held-out evidence, or learned weights.

Standard five-line and six-line proposals are intentionally presence-first:
subtype is left as unknown until later semantic validation. TAB becomes a
typed proposal only when the existing source-only TAB marker detector reports
positive marker evidence; six-line topology by itself never forces TAB.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

import cv2
import numpy as np

from .stage11_v2d_clef_adapter import detect_tab_clef_markers


CANDIDATE_GENERATOR_ID = "stage11-general-clef-candidate-generator.staff-relative-cc.v1"

_TOPOLOGY_KERNEL_WIDTH_RATIOS = (0.015, 0.025, 0.04, 0.06)
_TOPOLOGY_ROW_COVERAGE_FLOORS = (0.04, 0.07, 0.10, 0.15, 0.22)
_TOPOLOGY_GAP_DEVIATION_RATIO = 0.28
_TOPOLOGY_GAP_DEVIATION_MIN_PX = 2.5
_TOPOLOGY_DEDUP_CENTER_SPACES = 1.15
_TOPOLOGY_DEDUP_SPACING_RATIO = 0.32
_COMPONENT_STAFF_RADIUS_SPACES = 4.5
_COMPONENT_MAX_WIDTH_SPACES = 10.0
_COMPONENT_MAX_HEIGHT_SPACES = 14.0
_COMPONENT_MIN_AREA_PX = 5
_CANDIDATE_OFFSETS_SPACES = ((0.0, 0.0), (-0.6, 0.0), (0.6, 0.0), (0.0, -0.3), (0.0, 0.3))
_STANDARD_SHAPES_SPACES = (
    ("tall", 3.7, 8.0),
    ("compact", 3.8, 4.8),
)
_SIX_LINE_SHAPES_SPACES = (
    ("tab_vertical_presence", 2.5, 6.2),
    ("tab_horizontal_presence", 5.0, 3.0),
)
_GRID_SPACES = 0.55
_MAX_CANDIDATES_PER_TOPOLOGY_AND_SHAPE = 192


def _require_source_image(source_image: np.ndarray) -> np.ndarray:
    if not isinstance(source_image, np.ndarray) or source_image.size == 0:
        raise ValueError("non-empty source image required")
    if source_image.ndim == 2:
        gray = source_image
    elif source_image.ndim == 3 and source_image.shape[2] in (3, 4):
        conversion = cv2.COLOR_BGRA2GRAY if source_image.shape[2] == 4 else cv2.COLOR_BGR2GRAY
        gray = cv2.cvtColor(source_image, conversion)
    else:
        raise ValueError("source image must be grayscale, BGR, or BGRA")
    if gray.dtype != np.uint8:
        if not np.issubdtype(gray.dtype, np.number):
            raise ValueError("source image must contain numeric pixels")
        gray = np.clip(gray, 0, 255).astype(np.uint8)
    return gray


def _grouped_runs(indices: np.ndarray) -> list[tuple[int, int]]:
    if indices.size == 0:
        return []
    result: list[tuple[int, int]] = []
    start = previous = int(indices[0])
    for raw in indices[1:]:
        value = int(raw)
        if value > previous + 1:
            result.append((start, previous))
            start = value
        previous = value
    result.append((start, previous))
    return result


def _candidate_line_centers(coverage: np.ndarray, floor: float) -> np.ndarray:
    runs = _grouped_runs(np.flatnonzero(coverage >= floor))
    return np.asarray([(start + end) / 2.0 for start, end in runs], dtype=float)


def _line_topology_proposals(gray: np.ndarray, line_count: int) -> list[dict[str, Any]]:
    if line_count not in (5, 6):
        raise ValueError("line_count must be five or six")

    height, width = gray.shape
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    pool: list[dict[str, Any]] = []

    for kernel_ratio in _TOPOLOGY_KERNEL_WIDTH_RATIOS:
        kernel_width = max(12, int(round(width * kernel_ratio)))
        line_mask = cv2.morphologyEx(
            ink,
            cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 1)),
        )
        coverage = (line_mask > 0).mean(axis=1)
        for floor in _TOPOLOGY_ROW_COVERAGE_FLOORS:
            centers = _candidate_line_centers(coverage, floor)
            for index in range(max(0, len(centers) - line_count + 1)):
                rows = centers[index : index + line_count]
                gaps = np.diff(rows)
                spacing = float(np.median(gaps))
                minimum_spacing = max(3.0, height * 0.004)
                maximum_spacing = min(55.0, height * 0.055)
                if not minimum_spacing <= spacing <= maximum_spacing:
                    continue
                tolerance = max(
                    _TOPOLOGY_GAP_DEVIATION_MIN_PX,
                    _TOPOLOGY_GAP_DEVIATION_RATIO * spacing,
                )
                if float(np.max(np.abs(gaps - spacing))) > tolerance:
                    continue
                support = float(
                    np.mean(
                        [
                            coverage[min(height - 1, max(0, int(round(row))))]
                            for row in rows
                        ]
                    )
                )
                pool.append(
                    {
                        "line_count": line_count,
                        "line_rows": [float(value) for value in rows],
                        "staff_spacing": spacing,
                        "staff_center_y": float(np.mean(rows)),
                        "support": support,
                    }
                )

    pool.sort(
        key=lambda item: (
            -float(item["support"]),
            float(item["staff_center_y"]),
            float(item["staff_spacing"]),
        )
    )
    selected: list[dict[str, Any]] = []
    for candidate in pool:
        center = float(candidate["staff_center_y"])
        spacing = float(candidate["staff_spacing"])
        duplicate = False
        for prior in selected:
            prior_spacing = float(prior["staff_spacing"])
            if (
                abs(center - float(prior["staff_center_y"]))
                <= _TOPOLOGY_DEDUP_CENTER_SPACES * max(spacing, prior_spacing)
                and abs(spacing - prior_spacing)
                <= _TOPOLOGY_DEDUP_SPACING_RATIO * max(spacing, prior_spacing)
            ):
                duplicate = True
                break
        if not duplicate:
            selected.append(candidate)

    selected.sort(
        key=lambda item: (
            float(item["staff_center_y"]),
            float(item["staff_spacing"]),
            -float(item["support"]),
        )
    )
    for index, item in enumerate(selected):
        item["topology_index"] = index
    return selected


def _symbol_mask(gray: np.ndarray) -> np.ndarray:
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel_width = max(15, int(round(gray.shape[1] * 0.025)))
    horizontal = cv2.morphologyEx(
        ink,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 1)),
    )
    removal = cv2.dilate(horizontal, np.ones((2, 1), np.uint8))
    symbols = ink.copy()
    symbols[removal > 0] = 0
    return cv2.morphologyEx(
        symbols,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (2, 4)),
    )


def _bbox(
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    source_width: int,
    source_height: int,
) -> list[float] | None:
    x1 = center_x - width / 2.0
    y1 = center_y - height / 2.0
    x2 = x1 + width
    y2 = y1 + height
    if x1 < 0.0 or y1 < 0.0 or x2 > source_width or y2 > source_height:
        return None
    if not all(math.isfinite(value) for value in (x1, y1, x2, y2)):
        return None
    return [float(x1), float(y1), float(x2), float(y2)]


def _nearest_topology(
    center_y: float,
    proposals: Sequence[dict[str, Any]],
) -> dict[str, Any] | None:
    eligible = [
        item
        for item in proposals
        if abs(center_y - float(item["staff_center_y"]))
        <= _COMPONENT_STAFF_RADIUS_SPACES * float(item["staff_spacing"])
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda item: (
            abs(center_y - float(item["staff_center_y"]))
            / max(float(item["staff_spacing"]), 1e-9),
            int(item["topology_index"]),
        ),
    )


def _presence_confidence(
    topology_support: float,
    component_area: int,
    spacing: float,
) -> float:
    support_term = min(1.0, max(0.0, topology_support / 0.30))
    area_spaces = component_area / max(spacing * spacing, 1e-9)
    component_term = min(1.0, max(0.0, area_spaces / 2.5))
    return float(min(0.79, 0.34 + 0.26 * support_term + 0.19 * component_term))


def _grid_key(
    *,
    topology_index: int,
    shape_name: str,
    bbox: Sequence[float],
    spacing: float,
) -> tuple[int, str, int, int]:
    center_x = (float(bbox[0]) + float(bbox[2])) / 2.0
    center_y = (float(bbox[1]) + float(bbox[3])) / 2.0
    cell = max(1.0, _GRID_SPACES * spacing)
    return (
        topology_index,
        shape_name,
        int(round(center_x / cell)),
        int(round(center_y / cell)),
    )


def _component_presence_candidates(
    gray: np.ndarray,
    topologies: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    symbols = _symbol_mask(gray)
    count, _labels, stats, centroids = cv2.connectedComponentsWithStats(
        (symbols > 0).astype(np.uint8),
        connectivity=8,
    )
    source_height, source_width = gray.shape

    best_by_grid: dict[tuple[int, str, int, int], dict[str, Any]] = {}
    for component_id in range(1, count):
        x, y, component_width, component_height, area = (
            int(value) for value in stats[component_id]
        )
        if area < _COMPONENT_MIN_AREA_PX:
            continue
        center_x, center_y = (
            float(centroids[component_id][0]),
            float(centroids[component_id][1]),
        )
        topology = _nearest_topology(center_y, topologies)
        if topology is None:
            continue
        spacing = float(topology["staff_spacing"])
        if (
            component_width > _COMPONENT_MAX_WIDTH_SPACES * spacing
            or component_height > _COMPONENT_MAX_HEIGHT_SPACES * spacing
        ):
            continue
        if (
            component_height < 0.25 * spacing
            and component_width < 0.25 * spacing
        ):
            continue

        shapes = (
            _STANDARD_SHAPES_SPACES
            if int(topology["line_count"]) == 5
            else _SIX_LINE_SHAPES_SPACES
        )
        confidence = _presence_confidence(
            float(topology["support"]),
            area,
            spacing,
        )
        for shape_name, width_spaces, height_spaces in shapes:
            width_px = width_spaces * spacing
            height_px = height_spaces * spacing
            for offset_x_spaces, offset_y_spaces in _CANDIDATE_OFFSETS_SPACES:
                candidate_box = _bbox(
                    center_x + offset_x_spaces * spacing,
                    center_y + offset_y_spaces * spacing,
                    width_px,
                    height_px,
                    source_width,
                    source_height,
                )
                if candidate_box is None:
                    continue
                provenance = (
                    "source-only:staff-relative-cc:"
                    f"{int(topology['line_count'])}-line:{shape_name}"
                )
                item = {
                    "bbox": candidate_box,
                    "clef_presence_confidence": confidence,
                    "clef_type_or_unknown": "unknown",
                    "clef_type_confidence": 0.0,
                    "candidate_provenance": provenance,
                    "_topology_index": int(topology["topology_index"]),
                    "_shape_name": shape_name,
                    "_spacing": spacing,
                    "_component_area": area,
                    "_component_id": component_id,
                }
                key = _grid_key(
                    topology_index=int(topology["topology_index"]),
                    shape_name=shape_name,
                    bbox=candidate_box,
                    spacing=spacing,
                )
                previous = best_by_grid.get(key)
                if previous is None or (
                    float(item["clef_presence_confidence"]),
                    int(item["_component_area"]),
                    -component_id,
                ) > (
                    float(previous["clef_presence_confidence"]),
                    int(previous["_component_area"]),
                    -int(previous["_component_id"]),
                ):
                    best_by_grid[key] = item

    grouped: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for item in best_by_grid.values():
        key = (int(item["_topology_index"]), str(item["_shape_name"]))
        grouped.setdefault(key, []).append(item)

    bounded: list[dict[str, Any]] = []
    for key in sorted(grouped):
        items = sorted(
            grouped[key],
            key=lambda item: (
                -float(item["clef_presence_confidence"]),
                -int(item["_component_area"]),
                float(item["bbox"][0]),
                float(item["bbox"][1]),
            ),
        )
        bounded.extend(items[:_MAX_CANDIDATES_PER_TOPOLOGY_AND_SHAPE])

    for item in bounded:
        for internal in (
            "_topology_index",
            "_shape_name",
            "_spacing",
            "_component_area",
            "_component_id",
        ):
            item.pop(internal, None)
    return bounded


def _typed_tab_candidates(gray: np.ndarray) -> list[dict[str, Any]]:
    result = detect_tab_clef_markers(gray)
    detections = result.get("detections") or []
    typed: list[dict[str, Any]] = []
    for detection in detections:
        box = detection.get("bbox")
        if not isinstance(box, Sequence) or len(box) != 4:
            continue
        typed.append(
            {
                "bbox": [float(value) for value in box],
                "clef_presence_confidence": 0.90,
                "clef_type_or_unknown": "tab",
                "clef_type_confidence": 0.90,
                "candidate_provenance": (
                    "source-only:explicit-tab-marker:"
                    + str(detection.get("layout", "unknown-layout"))
                ),
            }
        )
    return typed


def generate_general_clef_candidates(source_image: np.ndarray) -> dict[str, Any]:
    """Generate deterministic source-only high-recall clef localizations.

    The function intentionally exposes only the source image as an inference
    input. Standard clef subtype evidence is deferred to the semantic stage.
    """
    gray = _require_source_image(source_image)
    five_line = _line_topology_proposals(gray, 5)
    six_line = _line_topology_proposals(gray, 6)
    topologies = [*five_line, *six_line]
    topologies.sort(
        key=lambda item: (
            float(item["staff_center_y"]),
            int(item["line_count"]),
            float(item["staff_spacing"]),
        )
    )
    for index, item in enumerate(topologies):
        item["topology_index"] = index

    candidates = _component_presence_candidates(gray, topologies)
    candidates.extend(_typed_tab_candidates(gray))
    candidates.sort(
        key=lambda item: (
            float(item["bbox"][1]),
            float(item["bbox"][0]),
            str(item["clef_type_or_unknown"]),
            str(item["candidate_provenance"]),
        )
    )

    return {
        "candidate_generator_id": CANDIDATE_GENERATOR_ID,
        "candidates": candidates,
        "diagnostics": {
            "source_only": True,
            "teacher_metadata_used": False,
            "heldout_accessed": False,
            "training_or_fine_tuning_performed": False,
            "page_identity_used": False,
            "filename_used": False,
            "source_family_used": False,
            "five_line_topology_count": len(five_line),
            "six_line_topology_count": len(six_line),
            "presence_candidate_count": sum(
                1
                for item in candidates
                if item["clef_type_or_unknown"] == "unknown"
            ),
            "typed_tab_candidate_count": sum(
                1
                for item in candidates
                if item["clef_type_or_unknown"] == "tab"
            ),
        },
    }


__all__ = [
    "CANDIDATE_GENERATOR_ID",
    "generate_general_clef_candidates",
]
