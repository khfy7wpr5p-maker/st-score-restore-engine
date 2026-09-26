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


CANDIDATE_GENERATOR_ID = "stage11-general-clef-candidate-generator.hybrid-oemer-staff-relative-c-review.v2"

_C_CLEF_REVIEW_MIN_TOPOLOGY_SUPPORT = 0.60
_C_CLEF_REVIEW_MIN_PRESENCE_CONFIDENCE = 0.79
_C_CLEF_REVIEW_MIN_X_OFFSET_SPACES = 0.50
_C_CLEF_REVIEW_MAX_X_OFFSET_SPACES = 2.00
_C_CLEF_REVIEW_MIN_Y_OFFSET_SPACES = 1.50
_C_CLEF_REVIEW_MAX_Y_OFFSET_SPACES = 2.50
_C_CLEF_REVIEW_TYPED_SUPPRESSION_IOU = 0.20
_C_CLEF_REVIEW_PROVENANCE = "source-only:c-clef-review:five-line-c1-compact"
_C_CLEF_REVIEW_REASON = "POSSIBLE_C_CLEF"

_OEMER_TARGET_PIXEL_MIDPOINT = 3_675_000.0
_TREBLE_MIN_HEIGHT_SPACES = 5.10
_TREBLE_MIN_WIDTH_SPACES = 1.40
_TREBLE_MIN_ASPECT = 1.40
_TREBLE_MAX_ASPECT = 3.60
_TREBLE_WIDTH_SCALE = 1.225
_TREBLE_HEIGHT_SCALE = 1.125
_BASS_MIN_HEIGHT_SPACES = 2.70
_BASS_MAX_HEIGHT_SPACES = 3.70
_BASS_MIN_WIDTH_SPACES = 1.25
_BASS_MAX_ASPECT = 2.20
_BASS_MIN_START_OFFSET_SPACES = -2.0
_BASS_MAX_START_OFFSET_SPACES = 15.0
_BASS_WIDTH_SCALE = 1.95
_BASS_HEIGHT_SCALE = 1.50

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
                line_starts: list[float] = []
                line_ends: list[float] = []
                for row in rows:
                    yy = min(height - 1, max(0, int(round(row))))
                    band = line_mask[max(0, yy - 1) : min(height, yy + 2), :]
                    xs = np.flatnonzero(np.any(band > 0, axis=0))
                    if xs.size:
                        line_starts.append(float(xs.min()))
                        line_ends.append(float(xs.max() + 1))
                staff_x1 = float(np.median(line_starts)) if line_starts else 0.0
                staff_x2 = float(np.median(line_ends)) if line_ends else float(width)
                pool.append(
                    {
                        "line_count": line_count,
                        "line_rows": [float(value) for value in rows],
                        "staff_spacing": spacing,
                        "staff_center_y": float(np.mean(rows)),
                        "support": support,
                        "x1": staff_x1,
                        "x2": staff_x2,
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


def oemer_prediction_shape_for_source(
    *,
    source_width: int,
    source_height: int,
) -> tuple[int, int]:
    """Reproduce Oemer's deterministic 3M-4.35M pixel resize contract."""
    if source_width <= 0 or source_height <= 0:
        raise ValueError("positive source geometry required")
    pixels = int(source_width) * int(source_height)
    if 3_000_000 <= pixels <= 4_350_000:
        return int(source_width), int(source_height)
    ratio = math.sqrt(_OEMER_TARGET_PIXEL_MIDPOINT / float(pixels))
    return (
        int(round(ratio * source_width)),
        int(round(ratio * source_height)),
    )


def normalize_oemer_candidate_box(
    bbox: Sequence[float],
    *,
    source_width: int,
    source_height: int,
    prediction_shape: Sequence[int],
) -> list[float]:
    """Map an Oemer prediction-space bbox back to original source pixels."""
    if len(bbox) != 4 or len(prediction_shape) != 2:
        raise ValueError("bbox and prediction_shape geometry mismatch")
    prediction_width = int(prediction_shape[0])
    prediction_height = int(prediction_shape[1])
    if prediction_width <= 0 or prediction_height <= 0:
        raise ValueError("positive Oemer prediction geometry required")
    values = [float(value) for value in bbox]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("finite Oemer bbox required")
    x1, y1, x2, y2 = values
    if (
        x1 < 0.0
        or y1 < 0.0
        or x2 <= x1
        or y2 <= y1
        or x2 > prediction_width
        or y2 > prediction_height
    ):
        raise ValueError("Oemer bbox must remain inside prediction geometry")
    return [
        x1 * float(source_width) / prediction_width,
        y1 * float(source_height) / prediction_height,
        x2 * float(source_width) / prediction_width,
        y2 * float(source_height) / prediction_height,
    ]


def _normalized_external_staff_systems(
    staff_systems: Sequence[dict[str, Any]] | None,
    fallback_topologies: Sequence[dict[str, Any]],
    *,
    source_width: int,
) -> list[dict[str, Any]]:
    if staff_systems is None:
        return [
            {
                "staff_index": int(item["topology_index"]),
                "line_rows": [float(value) for value in item["line_rows"]],
                "staff_spacing": float(item["staff_spacing"]),
                "staff_center_y": float(item["staff_center_y"]),
                "x1": float(item.get("x1", 0.0)),
                "x2": float(item.get("x2", source_width)),
            }
            for item in fallback_topologies
            if int(item["line_count"]) == 5
        ]

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(staff_systems):
        rows_raw = item.get("line_rows", item.get("lineRows"))
        if not isinstance(rows_raw, Sequence) or len(rows_raw) != 5:
            continue
        rows = [float(value) for value in rows_raw]
        if not all(math.isfinite(value) for value in rows):
            continue
        if not all(a < b for a, b in zip(rows, rows[1:])):
            continue
        spacing = float(np.median(np.diff(np.asarray(rows, dtype=float))))
        if not math.isfinite(spacing) or spacing <= 0.0:
            continue
        normalized.append(
            {
                "staff_index": int(item.get("staff_index", item.get("staffIndex", index))),
                "line_rows": rows,
                "staff_spacing": spacing,
                "staff_center_y": float(np.mean(rows)),
                "x1": float(item.get("x1", 0.0)),
                "x2": float(item.get("x2", source_width)),
            }
        )
    return normalized


def _expand_source_box(
    bbox: Sequence[float],
    *,
    width_scale: float,
    height_scale: float,
    source_width: int,
    source_height: int,
) -> list[float]:
    x1, y1, x2, y2 = [float(value) for value in bbox]
    center_x = (x1 + x2) / 2.0
    center_y = (y1 + y2) / 2.0
    width = (x2 - x1) * width_scale
    height = (y2 - y1) * height_scale
    return [
        max(0.0, center_x - width / 2.0),
        max(0.0, center_y - height / 2.0),
        min(float(source_width), center_x + width / 2.0),
        min(float(source_height), center_y + height / 2.0),
    ]


def _typed_oemer_candidates(
    boxes: Sequence[Sequence[float]],
    *,
    source_width: int,
    source_height: int,
    prediction_shape: Sequence[int] | None,
    staff_systems: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not boxes or not staff_systems:
        return []
    page_spacing = float(
        np.median(
            np.asarray(
                [float(item["staff_spacing"]) for item in staff_systems],
                dtype=float,
            )
        )
    )
    if not math.isfinite(page_spacing) or page_spacing <= 0.0:
        return []

    typed: list[dict[str, Any]] = []
    for raw_box in boxes:
        try:
            box = (
                normalize_oemer_candidate_box(
                    raw_box,
                    source_width=source_width,
                    source_height=source_height,
                    prediction_shape=prediction_shape,
                )
                if prediction_shape is not None
                else [float(value) for value in raw_box]
            )
        except (TypeError, ValueError):
            continue
        if len(box) != 4:
            continue
        x1, y1, x2, y2 = box
        if (
            x1 < 0.0
            or y1 < 0.0
            or x2 <= x1
            or y2 <= y1
            or x2 > source_width
            or y2 > source_height
        ):
            continue
        center_x = (x1 + x2) / 2.0
        center_y = (y1 + y2) / 2.0
        staff = min(
            staff_systems,
            key=lambda item: (
                abs(center_y - float(item["staff_center_y"])),
                int(item["staff_index"]),
            ),
        )
        local_spacing = float(staff["staff_spacing"])
        if (
            abs(center_y - float(staff["staff_center_y"]))
            > _COMPONENT_STAFF_RADIUS_SPACES * local_spacing
        ):
            continue

        width_spaces = (x2 - x1) / page_spacing
        height_spaces = (y2 - y1) / page_spacing
        aspect = (y2 - y1) / max(x2 - x1, 1e-9)
        start_offset_spaces = (
            center_x - float(staff.get("x1", 0.0))
        ) / page_spacing

        if (
            height_spaces >= _TREBLE_MIN_HEIGHT_SPACES
            and width_spaces >= _TREBLE_MIN_WIDTH_SPACES
            and _TREBLE_MIN_ASPECT <= aspect <= _TREBLE_MAX_ASPECT
        ):
            clef_type = "treble"
            refined = _expand_source_box(
                box,
                width_scale=_TREBLE_WIDTH_SCALE,
                height_scale=_TREBLE_HEIGHT_SCALE,
                source_width=source_width,
                source_height=source_height,
            )
            presence_confidence = 0.95
            type_confidence = 0.92
        elif (
            _BASS_MIN_HEIGHT_SPACES <= height_spaces <= _BASS_MAX_HEIGHT_SPACES
            and width_spaces >= _BASS_MIN_WIDTH_SPACES
            and aspect <= _BASS_MAX_ASPECT
            and _BASS_MIN_START_OFFSET_SPACES
            <= start_offset_spaces
            <= _BASS_MAX_START_OFFSET_SPACES
        ):
            clef_type = "bass"
            refined = _expand_source_box(
                box,
                width_scale=_BASS_WIDTH_SCALE,
                height_scale=_BASS_HEIGHT_SCALE,
                source_width=source_width,
                source_height=source_height,
            )
            presence_confidence = 0.94
            type_confidence = 0.90
        else:
            continue

        typed.append(
            {
                "bbox": refined,
                "clef_presence_confidence": presence_confidence,
                "clef_type_or_unknown": clef_type,
                "clef_type_confidence": type_confidence,
                "candidate_provenance": f"source-only:oemer-staff-relative:{clef_type}",
            }
        )

    typed.sort(
        key=lambda item: (
            float(item["bbox"][1]),
            float(item["bbox"][0]),
            str(item["clef_type_or_unknown"]),
        )
    )
    return typed


def _bbox_iou(a: Sequence[float], b: Sequence[float]) -> float:
    ax1, ay1, ax2, ay2 = (float(value) for value in a)
    bx1, by1, bx2, by2 = (float(value) for value in b)
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    intersection = iw * ih
    if intersection <= 0.0:
        return 0.0
    union = (
        (ax2 - ax1) * (ay2 - ay1)
        + (bx2 - bx1) * (by2 - by1)
        - intersection
    )
    return intersection / union if union > 0.0 else 0.0


def _c_clef_review_candidates(
    gray: np.ndarray,
    five_line_topologies: Sequence[dict[str, Any]],
    typed_standard: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return fail-closed source-only C-clef review candidates.

    This path intentionally does not emit a C-clef subtype. It uses only
    five-line topology support, staff-relative location and source connected
    components. Candidates that materially overlap an already typed treble/bass
    candidate are suppressed before the semantic successor sees them.
    """
    if not five_line_topologies:
        return []

    presence = _component_presence_candidates(gray, five_line_topologies)
    eligible_by_topology: dict[int, list[tuple[tuple[float, ...], dict[str, Any]]]] = {}

    for item in presence:
        if item.get("candidate_provenance") != "source-only:staff-relative-cc:5-line:compact":
            continue
        confidence = float(item["clef_presence_confidence"])
        if confidence < _C_CLEF_REVIEW_MIN_PRESENCE_CONFIDENCE:
            continue

        box = item["bbox"]
        center_x = (float(box[0]) + float(box[2])) / 2.0
        center_y = (float(box[1]) + float(box[3])) / 2.0
        topology = _nearest_topology(center_y, five_line_topologies)
        if topology is None:
            continue
        if float(topology["support"]) < _C_CLEF_REVIEW_MIN_TOPOLOGY_SUPPORT:
            continue

        spacing = float(topology["staff_spacing"])
        x_offset_spaces = (center_x - float(topology.get("x1", 0.0))) / spacing
        y_offset_spaces = (center_y - float(topology["staff_center_y"])) / spacing
        if not (
            _C_CLEF_REVIEW_MIN_X_OFFSET_SPACES
            <= x_offset_spaces
            <= _C_CLEF_REVIEW_MAX_X_OFFSET_SPACES
        ):
            continue
        if not (
            _C_CLEF_REVIEW_MIN_Y_OFFSET_SPACES
            <= y_offset_spaces
            <= _C_CLEF_REVIEW_MAX_Y_OFFSET_SPACES
        ):
            continue
        if any(
            _bbox_iou(box, typed["bbox"]) >= _C_CLEF_REVIEW_TYPED_SUPPRESSION_IOU
            for typed in typed_standard
        ):
            continue

        candidate = {
            "bbox": [float(value) for value in box],
            "clef_presence_confidence": confidence,
            "clef_type_or_unknown": "unknown",
            "clef_type_confidence": 0.0,
            "candidate_provenance": _C_CLEF_REVIEW_PROVENANCE,
            "review_required_reason": _C_CLEF_REVIEW_REASON,
        }
        rank = (
            abs(y_offset_spaces - 2.0),
            abs(x_offset_spaces - 1.25),
            -confidence,
            float(box[0]),
            float(box[1]),
            float(box[2]),
            float(box[3]),
        )
        eligible_by_topology.setdefault(int(topology["topology_index"]), []).append(
            (rank, candidate)
        )

    selected: list[dict[str, Any]] = []
    for topology_index in sorted(eligible_by_topology):
        ranked = sorted(eligible_by_topology[topology_index], key=lambda item: item[0])
        selected.append(ranked[0][1])
    return selected


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


def generate_general_clef_candidates(
    source_image: np.ndarray,
    *,
    oemer_candidate_boxes: Sequence[Sequence[float]] = (),
    oemer_prediction_shape: Sequence[int] | None = None,
    staff_systems: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate deterministic source-only general-clef candidates.

    When Oemer proposals are supplied, the generator normalizes them back to
    source pixels and applies the frozen development-only staff-relative
    treble/bass geometry sieve. Without Oemer proposals, the earlier
    source-image connected-component presence fallback remains available.
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

    normalized_staff_systems = _normalized_external_staff_systems(
        staff_systems,
        five_line,
        source_width=gray.shape[1],
    )
    typed_standard = _typed_oemer_candidates(
        list(oemer_candidate_boxes),
        source_width=gray.shape[1],
        source_height=gray.shape[0],
        prediction_shape=oemer_prediction_shape,
        staff_systems=normalized_staff_systems,
    )
    c_clef_review = (
        _c_clef_review_candidates(gray, five_line, typed_standard)
        if oemer_candidate_boxes
        else []
    )
    candidates = (
        [*typed_standard, *c_clef_review]
        if oemer_candidate_boxes
        else _component_presence_candidates(gray, topologies)
    )
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
            "typed_standard_candidate_count": sum(
                1
                for item in candidates
                if item["clef_type_or_unknown"] in {"treble", "bass"}
            ),
            "c_clef_review_candidate_count": sum(
                1
                for item in candidates
                if item.get("review_required_reason") == _C_CLEF_REVIEW_REASON
            ),
            "oemer_candidate_count": len(oemer_candidate_boxes),
            "oemer_prediction_shape": (
                list(oemer_prediction_shape)
                if oemer_prediction_shape is not None
                else None
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
    "normalize_oemer_candidate_box",
    "oemer_prediction_shape_for_source",
]
