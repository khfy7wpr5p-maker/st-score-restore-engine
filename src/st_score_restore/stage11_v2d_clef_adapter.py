"""Development-only P4.1 adapter for Oemer clef/key semantic components.

Oemer exposes clefs and key-signature glyphs in one mask.  This adapter keeps
the two outputs separate, assigns only the supported treble/bass subtype, and
expands connected-component bounds to the complete clef object used by the
teacher-box contract.  It is deliberately deterministic and does not train on
or consume teacher boxes at inference time.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

import cv2
import numpy as np


ADAPTER_ID = "oemer-clefs-keys-source-geometry.p4_2.v1"
TAB_ADAPTER_ID = "source-six-line-tab-marker.p4_2.v1"

# Ratios are relative to the original source image so a cached Oemer component
# can be re-resolved without running inference again.
TREBLE_MIN_HEIGHT_RATIO = 0.023
TREBLE_MIN_WIDTH_RATIO = 0.012
BASS_MIN_HEIGHT_RATIO = 0.014
BASS_MIN_WIDTH_RATIO = 0.009
BASS_MIN_ASPECT_RATIO = 0.48
MAX_CLEF_LEFT_RATIO = 0.25

TREBLE_WIDTH_SCALE = 1.45
TREBLE_HEIGHT_SCALE = 1.10
TREBLE_MIN_OUTPUT_HEIGHT_RATIO = 0.032
BASS_WIDTH_SCALE = 1.50
BASS_HEIGHT_SCALE = 1.90

# A key signature follows its clef on the same staff.  Suppress only the close
# right-hand neighbour; a farther clef can belong to a parallel/indented system.
FOLLOW_ON_MIN_X_GAP_RATIO = 0.005
FOLLOW_ON_MAX_X_GAP_RATIO = 0.075
FOLLOW_ON_MAX_Y_GAP_HEIGHT_RATIO = 0.50
PARALLEL_BASS_MIN_X_GAP_RATIO = 0.070
PARALLEL_BASS_MIN_ASPECT_RATIO = 0.60

TAB_HORIZONTAL_KERNEL_RATIO = 0.08
TAB_MARKER_KERNEL_RATIO = 0.06
TAB_MAX_SPACING_HEIGHT_RATIO = 0.025
TAB_MIN_LINE_COVERAGE = 0.075
TAB_STRONG_LINE_COVERAGE = 0.25
TAB_MIN_MEAN_LINE_COVERAGE = 0.43


def adapter_parameters() -> dict[str, float | str]:
    return {
        "adapterId": ADAPTER_ID,
        "trebleMinHeightRatio": TREBLE_MIN_HEIGHT_RATIO,
        "trebleMinWidthRatio": TREBLE_MIN_WIDTH_RATIO,
        "bassMinHeightRatio": BASS_MIN_HEIGHT_RATIO,
        "bassMinWidthRatio": BASS_MIN_WIDTH_RATIO,
        "bassMinAspectRatio": BASS_MIN_ASPECT_RATIO,
        "maxClefLeftRatio": MAX_CLEF_LEFT_RATIO,
        "trebleWidthScale": TREBLE_WIDTH_SCALE,
        "trebleHeightScale": TREBLE_HEIGHT_SCALE,
        "trebleMinOutputHeightRatio": TREBLE_MIN_OUTPUT_HEIGHT_RATIO,
        "bassWidthScale": BASS_WIDTH_SCALE,
        "bassHeightScale": BASS_HEIGHT_SCALE,
        "followOnMinXGapRatio": FOLLOW_ON_MIN_X_GAP_RATIO,
        "followOnMaxXGapRatio": FOLLOW_ON_MAX_X_GAP_RATIO,
        "followOnMaxYGapHeightRatio": FOLLOW_ON_MAX_Y_GAP_HEIGHT_RATIO,
        "parallelBassMinXGapRatio": PARALLEL_BASS_MIN_X_GAP_RATIO,
        "parallelBassMinAspectRatio": PARALLEL_BASS_MIN_ASPECT_RATIO,
    }


def tab_adapter_parameters() -> dict[str, float | str]:
    return {
        "tabAdapterId": TAB_ADAPTER_ID,
        "horizontalKernelRatio": TAB_HORIZONTAL_KERNEL_RATIO,
        "markerKernelRatio": TAB_MARKER_KERNEL_RATIO,
        "maxSpacingHeightRatio": TAB_MAX_SPACING_HEIGHT_RATIO,
        "minimumLineCoverage": TAB_MIN_LINE_COVERAGE,
        "strongLineCoverage": TAB_STRONG_LINE_COVERAGE,
        "minimumMeanLineCoverage": TAB_MIN_MEAN_LINE_COVERAGE,
    }


def _clip_box(
    box: Sequence[float], *, source_width: int, source_height: int
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = box
    return (
        max(0.0, min(float(source_width), float(x1))),
        max(0.0, min(float(source_height), float(y1))),
        max(0.0, min(float(source_width), float(x2))),
        max(0.0, min(float(source_height), float(y2))),
    )


def _six_line_candidates(line_mask: np.ndarray) -> list[dict[str, Any]]:
    height, width = line_mask.shape
    coverage = (line_mask > 0).mean(axis=1)
    widened = cv2.dilate(coverage.astype(np.float32)[:, None], np.ones((3, 1), np.uint8))[:, 0]
    candidates: list[dict[str, Any]] = []
    maximum_spacing = max(4, int(height * TAB_MAX_SPACING_HEIGHT_RATIO))
    offsets = np.arange(6)
    for spacing in range(3, maximum_spacing + 1):
        for start in range(0, height - 5 * spacing):
            values = widened[start + offsets * spacing]
            if (
                float(values.min()) < TAB_MIN_LINE_COVERAGE
                or int(np.count_nonzero(values >= TAB_STRONG_LINE_COVERAGE)) < 4
                or float(values.mean()) < TAB_MIN_MEAN_LINE_COVERAGE
            ):
                continue
            candidates.append(
                {
                    "score": float(values.mean() + 0.1 * values.min()),
                    "start": start,
                    "spacing": spacing,
                }
            )

    selected: list[dict[str, Any]] = []
    for candidate in sorted(candidates, key=lambda item: item["score"], reverse=True):
        top = int(candidate["start"]) - 2
        bottom = int(candidate["start"]) + 5 * int(candidate["spacing"]) + 3
        if any(
            not (
                bottom < int(prior["start"]) - 2
                or top > int(prior["start"]) + 5 * int(prior["spacing"]) + 3
            )
            for prior in selected
        ):
            continue
        selected.append(candidate)
    selected.sort(key=lambda item: item["start"])

    for candidate in selected:
        rows: list[int] = []
        line_starts: list[int] = []
        for index in range(6):
            nominal = int(candidate["start"]) + index * int(candidate["spacing"])
            nearby = range(max(0, nominal - 1), min(height, nominal + 2))
            row = max(nearby, key=lambda value: coverage[value])
            rows.append(row)
            xs = np.flatnonzero(line_mask[row] > 0)
            if xs.size:
                line_starts.append(int(xs.min()))
        candidate["rows"] = rows
        candidate["lineStart"] = min(line_starts) if line_starts else width
    return selected


def detect_tab_clef_markers(source_image: np.ndarray) -> dict[str, Any]:
    """Detect an explicit TAB marker attached to a high-confidence six-line system.

    Both common source layouts are supported: vertically stacked T/A/B glyphs
    inside the left edge of the system, and a horizontal TAB label immediately
    outside it.  Six line-like rows without the marker are an abstention.
    """
    if not isinstance(source_image, np.ndarray) or source_image.ndim not in (2, 3) or source_image.size == 0:
        raise ValueError("non-empty grayscale or BGR source image required")
    gray = source_image if source_image.ndim == 2 else cv2.cvtColor(source_image, cv2.COLOR_BGR2GRAY)
    gray = gray.astype(np.uint8, copy=False)
    height, width = gray.shape
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    line_kernel = np.ones((1, max(15, int(width * TAB_HORIZONTAL_KERNEL_RATIO))), np.uint8)
    line_mask = cv2.morphologyEx(ink, cv2.MORPH_OPEN, line_kernel)
    marker_kernel = np.ones((1, max(15, int(width * TAB_MARKER_KERNEL_RATIO))), np.uint8)
    marker_mask = cv2.subtract(ink, cv2.morphologyEx(ink, cv2.MORPH_OPEN, marker_kernel))
    _, _, stats, _ = cv2.connectedComponentsWithStats((marker_mask > 0).astype(np.uint8), 8)
    components = [tuple(int(value) for value in item) for item in stats[1:] if int(item[4]) >= 2]

    detections: list[dict[str, Any]] = []
    abstentions: list[dict[str, Any]] = []
    for system in _six_line_candidates(line_mask):
        spacing = int(system["spacing"])
        rows = [int(value) for value in system["rows"]]
        top, bottom = rows[0], rows[-1]
        center_y = (top + bottom) / 2.0
        line_start = int(system["lineStart"])

        embedded = []
        for component in components:
            x, y, component_width, component_height, _ = component
            component_center_x = x + component_width / 2.0
            component_center_y = y + component_height / 2.0
            if (
                line_start <= component_center_x <= line_start + 2 * spacing
                and top - 0.5 * spacing <= component_center_y <= bottom + 0.5 * spacing
                and component_width >= max(2.0, 0.15 * spacing)
                and not (component_width < 0.25 * spacing and component_height > 1.5 * spacing)
            ):
                embedded.append(component)
        if len(embedded) >= 3:
            x1 = min(item[0] for item in embedded)
            y1 = min(item[1] for item in embedded)
            x2 = max(item[0] + item[2] for item in embedded)
            y2 = max(item[1] + item[3] for item in embedded)
            vertical_bands = {
                min(2, max(0, int(((item[1] + item[3] / 2.0) - top) / max(1, bottom - top) * 3)))
                for item in embedded
            }
            if len(vertical_bands) >= 3 and y2 - y1 >= 2.5 * spacing and x2 - x1 <= 1.5 * spacing:
                center_x = (x1 + x2) / 2.0
                marker_center_y = (y1 + y2) / 2.0
                marker_width = max(2.0 * spacing, (x2 - x1) * 1.65)
                marker_height = max(5.6 * spacing, (y2 - y1) * 1.35)
                detections.append(
                    {
                        "bbox": _clip_box(
                            (
                                center_x - marker_width / 2.0,
                                marker_center_y - marker_height / 2.0,
                                center_x + marker_width / 2.0,
                                marker_center_y + marker_height / 2.0,
                            ),
                            source_width=width,
                            source_height=height,
                        ),
                        "clefType": "tab",
                        "layout": "embedded_vertical",
                        "lineRows": rows,
                        "lineSpacing": spacing,
                    }
                )
                continue

        external = []
        for component in components:
            x, y, component_width, component_height, _ = component
            component_center_x = x + component_width / 2.0
            component_center_y = y + component_height / 2.0
            if (
                max(0.0, line_start - 7 * spacing) <= component_center_x <= line_start - 0.2 * spacing
                and top - 0.5 * spacing <= component_center_y <= bottom + 0.5 * spacing
                and 0.25 * spacing <= component_height <= 1.8 * spacing
                and component_width <= 2 * spacing
            ):
                external.append(component)
        groups: list[tuple[float, int, int, int, int]] = []
        for seed in external:
            seed_y = seed[1] + seed[3] / 2.0
            group = [item for item in external if abs(item[1] + item[3] / 2.0 - seed_y) <= 0.55 * spacing]
            x1 = min((item[0] for item in group), default=0)
            y1 = min((item[1] for item in group), default=0)
            x2 = max((item[0] + item[2] for item in group), default=0)
            y2 = max((item[1] + item[3] for item in group), default=0)
            if len(group) >= 3 and 1.2 * spacing <= x2 - x1 <= 3.0 * spacing:
                groups.append((abs((y1 + y2) / 2.0 - center_y), x1, y1, x2, y2))
        if groups:
            _, x1, y1, x2, y2 = min(groups)
            center_x = (x1 + x2) / 2.0
            marker_center_y = (y1 + y2) / 2.0
            marker_width = max(4.0 * spacing, (x2 - x1) * 1.8)
            marker_height = max(2.7 * spacing, (y2 - y1) * 3.0)
            detections.append(
                {
                    "bbox": _clip_box(
                        (
                            center_x - marker_width / 2.0,
                            marker_center_y - marker_height / 2.0,
                            center_x + marker_width / 2.0,
                            marker_center_y + marker_height / 2.0,
                        ),
                        source_width=width,
                        source_height=height,
                    ),
                    "clefType": "tab",
                    "layout": "external_horizontal",
                    "lineRows": rows,
                    "lineSpacing": spacing,
                }
            )
        else:
            abstentions.append(
                {
                    "reason": "six_line_system_without_explicit_tab_marker",
                    "lineRows": rows,
                    "lineSpacing": spacing,
                }
            )
    return {
        "adapterId": TAB_ADAPTER_ID,
        "detections": detections,
        "clefBoxes": [item["bbox"] for item in detections],
        "clefTypes": ["tab"] * len(detections),
        "abstentions": abstentions,
    }


def _validated_box(value: Sequence[float]) -> tuple[float, float, float, float]:
    if len(value) != 4:
        raise ValueError("clef candidate box must contain x1,y1,x2,y2")
    x1, y1, x2, y2 = (float(item) for item in value)
    if not all(math.isfinite(item) for item in (x1, y1, x2, y2)) or x2 <= x1 or y2 <= y1:
        raise ValueError("clef candidate box must be finite with positive area")
    return x1, y1, x2, y2


def _expanded_box(
    box: tuple[float, float, float, float],
    *,
    width_scale: float,
    height_scale: float,
    source_width: float,
    source_height: float,
    minimum_height: float = 0.0,
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = box
    center_x = (x1 + x2) / 2.0
    center_y = (y1 + y2) / 2.0
    width = (x2 - x1) * width_scale
    height = max((y2 - y1) * height_scale, minimum_height)
    return (
        max(0.0, center_x - width / 2.0),
        max(0.0, center_y - height / 2.0),
        min(source_width, center_x + width / 2.0),
        min(source_height, center_y + height / 2.0),
    )


def resolve_oemer_clef_candidates(
    candidate_boxes: Sequence[Sequence[float]],
    *,
    source_width: int | float,
    source_height: int | float,
) -> dict[str, Any]:
    """Resolve combined Oemer clef/key components in source-image coordinates."""
    width = float(source_width)
    height = float(source_height)
    if not math.isfinite(width) or not math.isfinite(height) or width <= 0.0 or height <= 0.0:
        raise ValueError("positive finite source geometry required")

    boxes = [_validated_box(value) for value in candidate_boxes]
    provisional: list[dict[str, Any]] = []
    for index, box in enumerate(boxes):
        x1, y1, x2, y2 = box
        box_width = x2 - x1
        box_height = y2 - y1
        width_ratio = box_width / width
        height_ratio = box_height / height
        aspect_ratio = box_width / box_height
        left_ratio = x1 / width

        if height_ratio >= TREBLE_MIN_HEIGHT_RATIO and width_ratio >= TREBLE_MIN_WIDTH_RATIO:
            clef_type = "treble"
            resolved_box = _expanded_box(
                box,
                width_scale=TREBLE_WIDTH_SCALE,
                height_scale=TREBLE_HEIGHT_SCALE,
                source_width=width,
                source_height=height,
                minimum_height=TREBLE_MIN_OUTPUT_HEIGHT_RATIO * height,
            )
        elif (
            height_ratio >= BASS_MIN_HEIGHT_RATIO
            and width_ratio >= BASS_MIN_WIDTH_RATIO
            and aspect_ratio >= BASS_MIN_ASPECT_RATIO
            and left_ratio <= MAX_CLEF_LEFT_RATIO
        ):
            clef_type = "bass"
            resolved_box = _expanded_box(
                box,
                width_scale=BASS_WIDTH_SCALE,
                height_scale=BASS_HEIGHT_SCALE,
                source_width=width,
                source_height=height,
            )
        else:
            continue
        provisional.append(
            {
                "sourceCandidateIndex": index,
                "sourceBox": box,
                "bbox": resolved_box,
                "clefType": clef_type,
            }
        )

    accepted: list[dict[str, Any]] = []
    for candidate in sorted(provisional, key=lambda item: (item["bbox"][0], item["sourceCandidateIndex"])):
        x1, y1, x2, y2 = candidate["bbox"]
        center_x = (x1 + x2) / 2.0
        center_y = (y1 + y2) / 2.0
        candidate_height = y2 - y1
        is_follow_on = False
        for prior in accepted:
            px1, py1, px2, py2 = prior["bbox"]
            x_gap_ratio = (center_x - (px1 + px2) / 2.0) / width
            y_gap = abs(center_y - (py1 + py2) / 2.0)
            comparable_height = max(candidate_height, py2 - py1)
            if (
                FOLLOW_ON_MIN_X_GAP_RATIO <= x_gap_ratio <= FOLLOW_ON_MAX_X_GAP_RATIO
                and y_gap <= FOLLOW_ON_MAX_Y_GAP_HEIGHT_RATIO * comparable_height
            ):
                source_x1, source_y1, source_x2, source_y2 = candidate["sourceBox"]
                source_aspect_ratio = (source_x2 - source_x1) / (source_y2 - source_y1)
                if (
                    candidate["clefType"] == prior["clefType"] == "bass"
                    and x_gap_ratio >= PARALLEL_BASS_MIN_X_GAP_RATIO
                    and source_aspect_ratio >= PARALLEL_BASS_MIN_ASPECT_RATIO
                ):
                    continue
                is_follow_on = True
                break
        if not is_follow_on:
            accepted.append(candidate)

    accepted.sort(key=lambda item: item["sourceCandidateIndex"])
    accepted_indexes = {int(item["sourceCandidateIndex"]) for item in accepted}
    key_indexes = [index for index in range(len(boxes)) if index not in accepted_indexes]
    return {
        "adapterId": ADAPTER_ID,
        "clefBoxes": [item["bbox"] for item in accepted],
        "clefTypes": [str(item["clefType"]) for item in accepted],
        "detections": [
            {
                "bbox": list(item["bbox"]),
                "clefType": str(item["clefType"]),
                "sourceCandidateIndex": int(item["sourceCandidateIndex"]),
            }
            for item in accepted
        ],
        "sourceCandidateIndexes": [int(item["sourceCandidateIndex"]) for item in accepted],
        "keyCandidateBoxes": [boxes[index] for index in key_indexes],
        "keyCandidateIndexes": key_indexes,
    }
