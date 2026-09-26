"""Stage 11 V2d v1.1 source-only multi-system staff-line detector.

Development-only. This detector uses source pixels only. It does not load teacher
coordinates, restored outputs, held-out data, training state, page identities, or
page-specific rules. The frozen v1 detector/evidence remains immutable.

v1.1 keeps a compatibility implementation of the v1 source detector, then applies
source-derived spacing/topology guards and a deterministic skew-tolerant horizontal
segment supplement. Development results from this module cannot qualify staff_line or
authorize Stage 11/12 or production transitions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

import cv2
import numpy as np

DETECTOR_VERSION = "stage11-v2d-staff-multisystem-source.v1.1"
RAW_ARTIFACT_SCHEMA_VERSION = "stage11.v2d.staff-line-multisystem-source-raw.v1.1"
PARENT_DETECTOR_VERSION = "stage11-v2d-staff-multisystem-source.v1"


class StaffLineMultiSystemDetectorV11Error(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StaffLineMultiSystemDetectorV11Error(message)


@dataclass(frozen=True)
class DetectorConfig:
    multi_scale_horizontal_kernel_fractions: tuple[float, ...] = (0.018, 0.028, 0.040)
    max_horizontal_kernel_px: int = 96
    min_segment_width_fraction: float = 0.18
    local_spacing_strip_count: int = 5
    local_spacing_min_support_strips: int = 2
    local_spacing_consensus_tolerance_fraction: float = 0.22
    spacing_tolerance_fraction: float = 0.20
    staff_height_expected_spacing_multiples: float = 4.0
    staff_height_tolerance_fraction: float = 0.22
    row_merge_tolerance_px: float = 2.0
    six_line_rejection_tolerance_fraction: float = 0.20
    min_spacing_px: float = 3.0
    max_spacing_px: float = 72.0

    def validate(self) -> None:
        _require(len(self.multi_scale_horizontal_kernel_fractions) >= 2, "at least two scales required")
        _require(all(0.005 <= x <= 0.20 for x in self.multi_scale_horizontal_kernel_fractions), "invalid scale")
        _require(15 <= self.max_horizontal_kernel_px <= 511, "invalid kernel cap")
        _require(0.05 <= self.min_segment_width_fraction <= 0.50, "invalid aggregate support fraction")
        _require(3 <= self.local_spacing_strip_count <= 9, "invalid strip count")
        _require(1 <= self.local_spacing_min_support_strips <= self.local_spacing_strip_count, "invalid strip support")
        _require(0.05 <= self.local_spacing_consensus_tolerance_fraction <= 0.40, "invalid local spacing tolerance")
        _require(0.05 <= self.spacing_tolerance_fraction <= 0.40, "invalid spacing tolerance")
        _require(3.0 <= self.staff_height_expected_spacing_multiples <= 5.0, "invalid staff height multiple")
        _require(0.05 <= self.staff_height_tolerance_fraction <= 0.40, "invalid staff height tolerance")
        _require(0.5 <= self.row_merge_tolerance_px <= 8.0, "invalid row merge tolerance")
        _require(0.05 <= self.six_line_rejection_tolerance_fraction <= 0.50, "invalid six-line tolerance")
        _require(1.0 <= self.min_spacing_px < self.max_spacing_px, "invalid spacing bounds")


@dataclass(frozen=True)
class StaffLineDetection:
    line_index: int
    center_y: float
    x_extent: tuple[int, int]
    segments: tuple[tuple[int, int, int, int], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "lineIndex": self.line_index,
            "centerY": self.center_y,
            "xExtent": list(self.x_extent),
            "segments": [list(item) for item in self.segments],
        }


@dataclass(frozen=True)
class StaffSystemDetection:
    system_index: int
    bbox: tuple[int, int, int, int]
    staff_spacing: float
    confidence: float
    lines: tuple[StaffLineDetection, ...]
    provenance: str
    detector_version: str = DETECTOR_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "systemIndex": self.system_index,
            "bbox": list(self.bbox),
            "staffSpacing": self.staff_spacing,
            "confidence": self.confidence,
            "lineCount": 5,
            "lines": [line.as_dict() for line in self.lines],
            "provenance": self.provenance,
            "detectorVersion": self.detector_version,
        }


@dataclass(frozen=True)
class _LegacySegment:
    x1: int
    x2: int
    y: float
    height: int
    width: int
    pixel_count: int


@dataclass(frozen=True)
class _LegacyRow:
    row_id: int
    y: float
    segments: tuple[_LegacySegment, ...]
    x1: int
    x2: int
    supported_width: int


@dataclass(frozen=True)
class _MorphRow:
    y: float
    x1: int
    x2: int
    supported_width: int
    strip_mask: tuple[bool, ...]


@dataclass(frozen=True)
class _SkewRow:
    row_id: int
    y: float
    span: int
    supported_width: int
    strip_mask: tuple[bool, ...]
    intervals: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class _SpacingMode:
    spacing: float
    observations: int
    support_strips: int


_V1_MIN_SPACING = 3.0
_V1_MAX_SPACING = 72.0
_V1_SPACING_TOL = 0.20
_V1_MIN_SEGMENT_WIDTH_FRAC = 0.055
_V1_MIN_COMMON_EXTENT_FRAC = 0.045
_V1_HORIZONTAL_KERNEL_FRAC = 0.035
_V1_MAX_HORIZONTAL_KERNEL = 151
_V1_ROW_MERGE_TOL = 2.5
_V1_SIX_TOL = 0.22


def _as_grayscale(image: np.ndarray) -> np.ndarray:
    _require(isinstance(image, np.ndarray), "image must be a numpy array")
    _require(image.size > 0, "image must be non-empty")
    if image.ndim == 2:
        gray = image
    elif image.ndim == 3 and image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif image.ndim == 3 and image.shape[2] == 4:
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    else:
        raise StaffLineMultiSystemDetectorV11Error("image must be grayscale, BGR, or BGRA")
    if gray.dtype != np.uint8:
        if np.issubdtype(gray.dtype, np.floating):
            _require(bool(np.isfinite(gray).all()), "image contains non-finite pixels")
        gray = np.clip(gray, 0, 255).astype(np.uint8)
    _require(gray.shape[0] >= 16 and gray.shape[1] >= 32, "image too small for staff detection")
    return gray


def _union_width(intervals: Iterable[tuple[int, int]]) -> int:
    ordered = sorted((int(a), int(b)) for a, b in intervals if b > a)
    if not ordered:
        return 0
    total = 0
    start, end = ordered[0]
    for left, right in ordered[1:]:
        if left <= end:
            end = max(end, right)
        else:
            total += end - start
            start, end = left, right
    return total + end - start


def _legacy_horizontal_support(gray: np.ndarray) -> np.ndarray:
    _h, width = gray.shape
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, ink = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    kernel_len = int(round(width * _V1_HORIZONTAL_KERNEL_FRAC))
    kernel_len = max(15, min(_V1_MAX_HORIZONTAL_KERNEL, kernel_len))
    if kernel_len % 2 == 0:
        kernel_len += 1
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    support = cv2.morphologyEx(ink, cv2.MORPH_OPEN, horizontal_kernel)
    close_len = max(3, kernel_len // 5)
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (close_len, 1))
    return cv2.morphologyEx(support, cv2.MORPH_CLOSE, close_kernel)


def _legacy_segments(support: np.ndarray) -> list[_LegacySegment]:
    _height, width = support.shape
    minimum_width = max(12, int(round(width * _V1_MIN_SEGMENT_WIDTH_FRAC)))
    count, _labels, stats, centroids = cv2.connectedComponentsWithStats(support, 8)
    segments: list[_LegacySegment] = []
    for component in range(1, count):
        x, _y, w, h, area = (int(v) for v in stats[component])
        if w < minimum_width:
            continue
        if h > max(10, int(round(_V1_MAX_SPACING * 0.35))):
            continue
        center_y = float(centroids[component][1])
        if not math.isfinite(center_y):
            continue
        segments.append(_LegacySegment(x, x + w, center_y, h, w, area))
    segments.sort(key=lambda item: (item.y, item.x1, item.x2))
    return segments


def _legacy_rows(segments: list[_LegacySegment]) -> list[_LegacyRow]:
    if not segments:
        return []
    clusters: list[list[_LegacySegment]] = []
    for segment in segments:
        if not clusters:
            clusters.append([segment])
            continue
        current_y = float(np.average(
            [item.y for item in clusters[-1]],
            weights=[max(1, item.pixel_count) for item in clusters[-1]],
        ))
        if abs(segment.y - current_y) <= _V1_ROW_MERGE_TOL:
            clusters[-1].append(segment)
        else:
            clusters.append([segment])
    rows: list[_LegacyRow] = []
    for row_id, cluster in enumerate(clusters):
        weighted_y = float(np.average(
            [item.y for item in cluster],
            weights=[max(1, item.pixel_count) for item in cluster],
        ))
        x1 = min(item.x1 for item in cluster)
        x2 = max(item.x2 for item in cluster)
        rows.append(_LegacyRow(
            row_id=row_id,
            y=weighted_y,
            segments=tuple(cluster),
            x1=x1,
            x2=x2,
            supported_width=_union_width((item.x1, item.x2) for item in cluster),
        ))
    return rows


def _legacy_x_overlap(a: _LegacyRow, b: _LegacyRow) -> int:
    return max(0, min(a.x2, b.x2) - max(a.x1, b.x1))


def _legacy_nearest(rows: list[_LegacyRow], target_y: float, tolerance: float, used: set[int]) -> _LegacyRow | None:
    candidates = [row for row in rows if row.row_id not in used and abs(row.y - target_y) <= tolerance]
    if not candidates:
        return None
    return min(candidates, key=lambda row: (abs(row.y - target_y), -row.supported_width, row.row_id))


def _legacy_looks_six(rows: list[_LegacyRow], selected: list[_LegacyRow], spacing: float) -> bool:
    tolerance = max(1.5, spacing * _V1_SIX_TOL)
    first, last = selected[0], selected[-1]
    selected_span = max(1, min(row.x2 for row in selected) - max(row.x1 for row in selected))
    for target in (first.y - spacing, last.y + spacing):
        for row in rows:
            if row in selected or abs(row.y - target) > tolerance:
                continue
            overlap = min(_legacy_x_overlap(row, item) for item in selected)
            if overlap >= max(8, int(selected_span * 0.45)):
                return True
    return False


def _legacy_hypotheses(rows: list[_LegacyRow], width: int) -> list[tuple[float, list[_LegacyRow], float]]:
    hypotheses: list[tuple[float, list[_LegacyRow], float]] = []
    minimum_common = max(16, int(round(width * _V1_MIN_COMMON_EXTENT_FRAC)))
    for first_index, first in enumerate(rows):
        for second in rows[first_index + 1:]:
            spacing = second.y - first.y
            if spacing < _V1_MIN_SPACING:
                continue
            if spacing > _V1_MAX_SPACING:
                break
            tolerance = max(1.5, spacing * _V1_SPACING_TOL)
            selected = [first, second]
            used = {first.row_id, second.row_id}
            for line_index in range(2, 5):
                row = _legacy_nearest(rows, first.y + spacing * line_index, tolerance, used)
                if row is None:
                    selected = []
                    break
                selected.append(row)
                used.add(row.row_id)
            if len(selected) != 5:
                continue
            selected.sort(key=lambda item: item.y)
            spacings = np.diff(np.asarray([row.y for row in selected], dtype=np.float64))
            median_spacing = float(np.median(spacings))
            if not (_V1_MIN_SPACING <= median_spacing <= _V1_MAX_SPACING):
                continue
            if float(np.max(np.abs(spacings - median_spacing))) > max(1.5, median_spacing * _V1_SPACING_TOL):
                continue
            common_x1 = max(row.x1 for row in selected)
            common_x2 = min(row.x2 for row in selected)
            common_width = max(0, common_x2 - common_x1)
            if common_width < minimum_common:
                continue
            if _legacy_looks_six(rows, selected, median_spacing):
                continue
            regularity = 1.0 - min(
                1.0,
                float(np.mean(np.abs(spacings - median_spacing))) / max(median_spacing, 1.0),
            )
            support_fraction = min(
                1.0,
                float(np.mean([row.supported_width / max(width, 1) for row in selected])) / 0.60,
            )
            common_fraction = min(1.0, common_width / max(width * 0.35, 1.0))
            score = 0.45 * regularity + 0.35 * support_fraction + 0.20 * common_fraction
            hypotheses.append((score, selected, median_spacing))
    hypotheses.sort(key=lambda item: (-item[0], item[1][0].y, item[1][0].x1))
    return hypotheses


def _legacy_dedup(hypotheses: list[tuple[float, list[_LegacyRow], float]]) -> list[tuple[float, list[_LegacyRow], float]]:
    kept: list[tuple[float, list[_LegacyRow], float]] = []
    used_row_sets: list[set[int]] = []
    for hypothesis in hypotheses:
        row_set = {row.row_id for row in hypothesis[1]}
        if any(len(row_set & existing) >= 3 for existing in used_row_sets):
            continue
        kept.append(hypothesis)
        used_row_sets.append(row_set)
    kept.sort(key=lambda item: (item[1][0].y, item[1][0].x1))
    return kept


def _legacy_detect(gray: np.ndarray) -> list[StaffSystemDetection]:
    height, width = gray.shape
    support = _legacy_horizontal_support(gray)
    rows = _legacy_rows(_legacy_segments(support))
    hypotheses = _legacy_dedup(_legacy_hypotheses(rows, width))
    detections: list[StaffSystemDetection] = []
    for system_index, (score, selected, spacing) in enumerate(hypotheses, start=1):
        lines: list[StaffLineDetection] = []
        for line_index, row in enumerate(selected, start=1):
            raw_segments = tuple(
                (segment.x1, int(round(row.y)), segment.x2, int(round(row.y)))
                for segment in row.segments
            )
            lines.append(StaffLineDetection(line_index, float(row.y), (row.x1, row.x2), raw_segments))
        x1 = min(line.x_extent[0] for line in lines)
        x2 = max(line.x_extent[1] for line in lines)
        y1 = max(0, int(math.floor(lines[0].center_y - max(2.0, spacing * 0.35))))
        y2 = min(height, int(math.ceil(lines[-1].center_y + max(2.0, spacing * 0.35))) + 1)
        confidence = max(0.50, min(0.99, 0.50 + 0.49 * float(score)))
        detections.append(StaffSystemDetection(
            system_index,
            (int(x1), int(y1), int(x2), int(y2)),
            float(spacing),
            confidence,
            tuple(lines),
            "source-only:v1-compatibility-path",
        ))
    return detections


def _binarize(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, ink = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    return ink


def _multi_scale_support(gray: np.ndarray, cfg: DetectorConfig) -> tuple[np.ndarray, np.ndarray, list[int]]:
    _height, width = gray.shape
    ink = _binarize(gray)
    outputs: list[np.ndarray] = []
    kernel_lengths: list[int] = []
    for fraction in cfg.multi_scale_horizontal_kernel_fractions:
        kernel_len = max(9, min(cfg.max_horizontal_kernel_px, int(round(width * fraction))))
        if kernel_len % 2 == 0:
            kernel_len += 1
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
        support = cv2.morphologyEx(ink, cv2.MORPH_OPEN, kernel)
        close_len = max(3, kernel_len // 7)
        close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (close_len, 1))
        outputs.append(cv2.morphologyEx(support, cv2.MORPH_CLOSE, close_kernel))
        kernel_lengths.append(kernel_len)
    return ink, np.maximum.reduce(outputs), kernel_lengths


def _morph_rows(support: np.ndarray, cfg: DetectorConfig) -> list[_MorphRow]:
    height, width = support.shape
    row_pixels = np.count_nonzero(support, axis=1).astype(np.float64)
    floor = max(8.0, width * 0.010)
    maxima: list[int] = []
    for y in range(height):
        if row_pixels[y] < floor:
            continue
        lo, hi = max(0, y - 1), min(height, y + 2)
        if row_pixels[y] < float(np.max(row_pixels[lo:hi])):
            continue
        if y > 0 and row_pixels[y] == row_pixels[y - 1]:
            continue
        maxima.append(y)
    bands: list[tuple[int, int]] = []
    for y in maxima:
        threshold = max(floor, 0.65 * row_pixels[y])
        top, bottom = y, y + 1
        while top > 0 and row_pixels[top - 1] >= threshold:
            top -= 1
        while bottom < height and row_pixels[bottom] >= threshold:
            bottom += 1
        if bands and top <= bands[-1][1] and bottom >= bands[-1][0]:
            bands[-1] = (min(bands[-1][0], top), max(bands[-1][1], bottom))
        else:
            bands.append((top, bottom))
    bounds = np.linspace(0, width, cfg.local_spacing_strip_count + 1, dtype=int)
    rows: list[_MorphRow] = []
    for top, bottom in bands:
        weights = np.maximum(row_pixels[top:bottom], 1.0)
        center_y = float(np.average(np.arange(top, bottom, dtype=np.float64), weights=weights))
        xmask = np.any(support[top:bottom] > 0, axis=0)
        xs = np.flatnonzero(xmask)
        if len(xs) == 0:
            continue
        idx = np.flatnonzero(xmask)
        cuts = np.where(np.diff(idx) > 1)[0]
        starts = np.r_[0, cuts + 1]
        ends = np.r_[cuts, len(idx) - 1]
        intervals = [(int(idx[a]), int(idx[b]) + 1) for a, b in zip(starts, ends)]
        aggregate = _union_width(intervals)
        if aggregate < int(round(width * cfg.min_segment_width_fraction)):
            continue
        strip_mask: list[bool] = []
        for left, right in zip(bounds[:-1], bounds[1:]):
            support_fraction = float(np.count_nonzero(xmask[left:right])) / max(1, right - left)
            strip_mask.append(support_fraction >= _V1_MIN_SEGMENT_WIDTH_FRAC)
        rows.append(_MorphRow(center_y, int(xs[0]), int(xs[-1]) + 1, aggregate, tuple(strip_mask)))
    rows.sort(key=lambda row: row.y)
    return rows


def _spacing_modes(rows: list[_MorphRow], cfg: DetectorConfig) -> list[_SpacingMode]:
    bins: dict[float, dict[str, Any]] = {}
    for strip_index in range(cfg.local_spacing_strip_count):
        strip_rows = [row for row in rows if row.strip_mask[strip_index]]
        for first, second in zip(strip_rows, strip_rows[1:]):
            gap = second.y - first.y
            if not (cfg.min_spacing_px <= gap <= cfg.max_spacing_px):
                continue
            quantized = round(gap * 2.0) / 2.0
            record = bins.setdefault(quantized, {"observations": 0, "strips": set()})
            record["observations"] += 1
            record["strips"].add(strip_index)
    modes = [
        _SpacingMode(spacing, int(record["observations"]), len(record["strips"]))
        for spacing, record in bins.items()
        if len(record["strips"]) >= cfg.local_spacing_min_support_strips
    ]
    modes.sort(key=lambda item: (-item.observations, -item.support_strips, item.spacing))
    if not modes:
        return []
    peak = modes[0].observations
    minimum_observations = max(
        cfg.local_spacing_min_support_strips,
        int(math.ceil(peak / cfg.local_spacing_strip_count)),
    )
    return [item for item in modes if item.observations >= minimum_observations]


def _spacing_supported(spacing: float, modes: list[_SpacingMode], cfg: DetectorConfig) -> bool:
    if not modes:
        return False
    return any(
        abs(spacing - mode.spacing)
        <= max(1.0, mode.spacing * cfg.local_spacing_consensus_tolerance_fraction)
        for mode in modes
    )


def _vertical_run_count(ink: np.ndarray, *, y_values: Iterable[float], spacing: float, x1: int, x2: int) -> int:
    height, width = ink.shape
    ys = [float(y) for y in y_values]
    if not ys:
        return 0
    kernel_height = max(3, int(round(spacing * 1.8)))
    vertical = cv2.morphologyEx(
        ink,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_height)),
    )
    top = max(0, int(math.floor(min(ys) - spacing)))
    bottom = min(height, int(math.ceil(max(ys) + spacing)) + 1)
    left = max(0, int(x1))
    right = min(width, int(x2) + 1)
    if bottom <= top or right <= left:
        return 0
    columns = np.any(vertical[top:bottom, left:right] > 0, axis=0)
    indices = np.flatnonzero(columns)
    if len(indices) == 0:
        return 0
    return 1 + int(np.sum(np.diff(indices) > 1))


def _legacy_source_supported(detection: StaffSystemDetection, modes: list[_SpacingMode], ink: np.ndarray, cfg: DetectorConfig) -> tuple[bool, str, int]:
    if not modes:
        return True, "fallback:no-source-spacing-mode", 0
    if not _spacing_supported(detection.staff_spacing, modes, cfg):
        return False, "unsupported-local-spacing", 0
    run_count = _vertical_run_count(
        ink,
        y_values=[line.center_y for line in detection.lines],
        spacing=detection.staff_spacing,
        x1=min(line.x_extent[0] for line in detection.lines),
        x2=max(line.x_extent[1] for line in detection.lines),
    )
    if run_count < 3:
        return False, "insufficient-vertical-topology", run_count
    return True, "source-supported", run_count


def _merge_intervals(intervals: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    ordered = sorted((int(a), int(b)) for a, b in intervals if b > a)
    if not ordered:
        return ()
    merged: list[tuple[int, int]] = [ordered[0]]
    for left, right in ordered[1:]:
        if left <= merged[-1][1] + 3:
            merged[-1] = (merged[-1][0], max(merged[-1][1], right))
        else:
            merged.append((left, right))
    return tuple(merged)


def _skew_rows(ink: np.ndarray, cfg: DetectorConfig) -> tuple[list[_SkewRow], int]:
    _height, width = ink.shape
    close_len = max(3, min(21, int(round(width * min(cfg.multi_scale_horizontal_kernel_fractions) * (2.0 / 3.0)))))
    work = cv2.morphologyEx(
        ink,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (close_len, 1)),
    )
    lines = cv2.HoughLinesP(
        work,
        1,
        np.pi / 720.0,
        threshold=max(20, int(round(width * 0.025))),
        minLineLength=max(30, int(round(width * 0.10))),
        maxLineGap=max(10, int(round(width * 0.03))),
    )
    if lines is None:
        return [], 0
    segments: list[tuple[float, float, float, float]] = []
    for raw in lines[:, 0, :]:
        x1, y1, x2, y2 = (float(value) for value in raw)
        if x1 > x2:
            x1, y1, x2, y2 = x2, y2, x1, y1
        dx, dy = x2 - x1, y2 - y1
        if dx <= 0:
            continue
        if abs(dy) / dx > 0.035:
            continue
        length = math.hypot(dx, dy)
        if length < width * 0.10:
            continue
        center_y = y1 + dy * ((width / 2.0 - x1) / dx)
        segments.append((center_y, x1, x2, length))
    segments.sort(key=lambda item: (item[0], item[1], item[2]))
    clusters: list[list[tuple[float, float, float, float]]] = []
    for segment in segments:
        if clusters:
            current_y = float(np.average(
                [item[0] for item in clusters[-1]],
                weights=[item[3] for item in clusters[-1]],
            ))
            if abs(segment[0] - current_y) <= max(1.0, cfg.row_merge_tolerance_px + 0.2):
                clusters[-1].append(segment)
                continue
        clusters.append([segment])
    bounds = np.linspace(0, width, cfg.local_spacing_strip_count + 1, dtype=int)
    rows: list[_SkewRow] = []
    for cluster in clusters:
        center_y = float(np.average(
            [item[0] for item in cluster],
            weights=[item[3] for item in cluster],
        ))
        intervals = _merge_intervals((int(item[1]), int(item[2])) for item in cluster)
        if not intervals:
            continue
        span = max(right for _left, right in intervals) - min(left for left, _right in intervals)
        supported_width = _union_width(intervals)
        if span < int(round(width * cfg.min_segment_width_fraction)):
            continue
        strip_mask: list[bool] = []
        for left, right in zip(bounds[:-1], bounds[1:]):
            overlap = sum(max(0, min(b, right) - max(a, left)) for a, b in intervals)
            strip_mask.append(overlap >= max(8, int(round((right - left) * _V1_MIN_SEGMENT_WIDTH_FRAC))))
        rows.append(_SkewRow(
            row_id=len(rows),
            y=center_y,
            span=span,
            supported_width=supported_width,
            strip_mask=tuple(strip_mask),
            intervals=intervals,
        ))
    rows.sort(key=lambda row: row.y)
    return [
        _SkewRow(i, row.y, row.span, row.supported_width, row.strip_mask, row.intervals)
        for i, row in enumerate(rows)
    ], len(segments)


def _skew_nearest(rows: list[_SkewRow], target: float, tolerance: float, used: set[int]) -> _SkewRow | None:
    candidates = [row for row in rows if row.row_id not in used and abs(row.y - target) <= tolerance]
    if not candidates:
        return None
    return min(candidates, key=lambda row: (abs(row.y - target), -row.supported_width, row.row_id))


def _common_strip_indices(rows: list[_SkewRow], cfg: DetectorConfig) -> tuple[int, ...]:
    return tuple(
        index
        for index in range(cfg.local_spacing_strip_count)
        if all(row.strip_mask[index] for row in rows)
    )


def _skew_six_line(all_rows: list[_SkewRow], selected: list[_SkewRow], spacing: float, cfg: DetectorConfig) -> bool:
    tolerance = max(1.5, spacing * cfg.six_line_rejection_tolerance_fraction)
    for target in (selected[0].y - spacing, selected[-1].y + spacing):
        for row in all_rows:
            if row in selected or abs(row.y - target) > tolerance:
                continue
            if len(_common_strip_indices(selected + [row], cfg)) >= cfg.local_spacing_min_support_strips:
                return True
    return False


def _skew_hypotheses(rows: list[_SkewRow], width: int, modes: list[_SpacingMode], cfg: DetectorConfig) -> tuple[list[tuple[float, list[_SkewRow], float]], dict[str, int]]:
    rejected = {"missing": 0, "spacing": 0, "height": 0, "commonStrips": 0, "localSpacing": 0, "sixLine": 0}
    hypotheses: list[tuple[float, list[_SkewRow], float]] = []
    if not modes:
        return hypotheses, rejected
    for first_index, first in enumerate(rows):
        for second in rows[first_index + 1:]:
            spacing = second.y - first.y
            if spacing < cfg.min_spacing_px:
                continue
            if spacing > cfg.max_spacing_px:
                break
            tolerance = max(1.5, spacing * cfg.spacing_tolerance_fraction)
            selected = [first, second]
            used = {first.row_id, second.row_id}
            for line_index in range(2, 5):
                row = _skew_nearest(rows, first.y + spacing * line_index, tolerance, used)
                if row is None:
                    selected = []
                    rejected["missing"] += 1
                    break
                selected.append(row)
                used.add(row.row_id)
            if len(selected) != 5:
                continue
            selected.sort(key=lambda row: row.y)
            differences = np.diff(np.asarray([row.y for row in selected], dtype=np.float64))
            median_spacing = float(np.median(differences))
            if float(np.max(np.abs(differences - median_spacing))) > max(
                1.5,
                median_spacing * cfg.spacing_tolerance_fraction,
            ):
                rejected["spacing"] += 1
                continue
            staff_height = selected[-1].y - selected[0].y
            expected_height = cfg.staff_height_expected_spacing_multiples * median_spacing
            if abs(staff_height - expected_height) > max(
                1.5,
                expected_height * cfg.staff_height_tolerance_fraction,
            ):
                rejected["height"] += 1
                continue
            common_strips = _common_strip_indices(selected, cfg)
            if len(common_strips) < cfg.local_spacing_min_support_strips:
                rejected["commonStrips"] += 1
                continue
            if not _spacing_supported(median_spacing, modes, cfg):
                rejected["localSpacing"] += 1
                continue
            if _skew_six_line(rows, selected, median_spacing, cfg):
                rejected["sixLine"] += 1
                continue
            regularity = 1.0 - min(
                1.0,
                float(np.mean(np.abs(differences - median_spacing))) / max(1.0, median_spacing),
            )
            support = min(1.0, float(np.mean([row.supported_width / max(1, width) for row in selected])) / 0.60)
            strip_score = len(common_strips) / cfg.local_spacing_strip_count
            score = 0.50 * regularity + 0.30 * support + 0.20 * strip_score
            hypotheses.append((score, selected, median_spacing))
    hypotheses.sort(key=lambda item: (-item[0], item[1][0].y, item[1][0].row_id))
    kept: list[tuple[float, list[_SkewRow], float]] = []
    for hypothesis in hypotheses:
        ys = np.asarray([row.y for row in hypothesis[1]], dtype=np.float64)
        duplicate = False
        for existing in kept:
            other = np.asarray([row.y for row in existing[1]], dtype=np.float64)
            tolerance = max(1.5, min(hypothesis[2], existing[2]) * 0.30)
            matches = int(np.sum(np.min(np.abs(ys[:, None] - other[None, :]), axis=1) <= tolerance))
            if matches >= 3:
                duplicate = True
                break
        if not duplicate:
            kept.append(hypothesis)
    kept.sort(key=lambda item: item[1][0].y)
    return kept, rejected


def _duplicate_of_system(hypothesis: tuple[float, list[_SkewRow], float], systems: list[StaffSystemDetection]) -> bool:
    _score, rows, spacing = hypothesis
    ys = np.asarray([row.y for row in rows], dtype=np.float64)
    hx1 = min(left for row in rows for left, _right in row.intervals)
    hx2 = max(right for row in rows for _left, right in row.intervals)
    for system in systems:
        system_ys = np.asarray([line.center_y for line in system.lines], dtype=np.float64)
        tolerance = max(1.5, min(spacing, system.staff_spacing) * 0.35)
        matches = int(np.sum(np.min(np.abs(ys[:, None] - system_ys[None, :]), axis=1) <= tolerance))
        sx1 = min(line.x_extent[0] for line in system.lines)
        sx2 = max(line.x_extent[1] for line in system.lines)
        overlap = max(0, min(hx2, sx2) - max(hx1, sx1))
        denominator = max(1, min(hx2 - hx1, sx2 - sx1))
        if matches >= 3 and overlap / denominator >= 0.25:
            return True
    return False


def _supplement_detection(hypothesis: tuple[float, list[_SkewRow], float], *, system_index: int, image_height: int) -> StaffSystemDetection:
    score, rows, spacing = hypothesis
    lines: list[StaffLineDetection] = []
    for line_index, row in enumerate(rows, start=1):
        x1 = min(left for left, _right in row.intervals)
        x2 = max(right for _left, right in row.intervals)
        segments = tuple((left, int(round(row.y)), right, int(round(row.y))) for left, right in row.intervals)
        lines.append(StaffLineDetection(line_index, float(row.y), (x1, x2), segments))
    x1 = min(line.x_extent[0] for line in lines)
    x2 = max(line.x_extent[1] for line in lines)
    y1 = max(0, int(math.floor(lines[0].center_y - max(2.0, spacing * 0.35))))
    y2 = min(image_height, int(math.ceil(lines[-1].center_y + max(2.0, spacing * 0.35))) + 1)
    confidence = max(0.50, min(0.97, 0.50 + 0.47 * float(score)))
    return StaffSystemDetection(
        system_index,
        (int(x1), int(y1), int(x2), int(y2)),
        float(spacing),
        confidence,
        tuple(lines),
        "source-only:v1.1-skew-tolerant-horizontal-segment",
    )


def detect_staff_systems_with_diagnostics(image: np.ndarray, *, config: DetectorConfig | None = None) -> tuple[list[StaffSystemDetection], dict[str, Any]]:
    cfg = config or DetectorConfig()
    cfg.validate()
    gray = _as_grayscale(image)
    height, width = gray.shape
    ink, support, kernel_lengths = _multi_scale_support(gray, cfg)
    morphology_rows = _morph_rows(support, cfg)
    modes = _spacing_modes(morphology_rows, cfg)

    legacy = _legacy_detect(gray)
    retained: list[StaffSystemDetection] = []
    legacy_rejections: dict[str, int] = {}
    for detection in legacy:
        keep, reason, _run_count = _legacy_source_supported(detection, modes, ink, cfg)
        if keep:
            retained.append(StaffSystemDetection(
                system_index=0,
                bbox=detection.bbox,
                staff_spacing=detection.staff_spacing,
                confidence=detection.confidence,
                lines=detection.lines,
                provenance="source-only:v1-compatibility+v1.1-local-spacing-topology",
            ))
        else:
            legacy_rejections[reason] = legacy_rejections.get(reason, 0) + 1

    skew_rows, skew_segment_count = _skew_rows(ink, cfg)
    skew_hypotheses, skew_rejections = _skew_hypotheses(skew_rows, width, modes, cfg)
    source_topology_rejections = 0
    accepted_supplements: list[tuple[float, list[_SkewRow], float]] = []
    duplicate_supplements = 0
    for hypothesis in skew_hypotheses:
        _score, rows, spacing = hypothesis
        x1 = min(left for row in rows for left, _right in row.intervals)
        x2 = max(right for row in rows for _left, right in row.intervals)
        run_count = _vertical_run_count(
            ink,
            y_values=[row.y for row in rows],
            spacing=spacing,
            x1=x1,
            x2=x2,
        )
        if run_count < 3:
            source_topology_rejections += 1
            continue
        if _duplicate_of_system(hypothesis, retained):
            duplicate_supplements += 1
            continue
        accepted_supplements.append(hypothesis)

    detections = list(retained)
    detections.extend(_supplement_detection(hypothesis, system_index=0, image_height=height) for hypothesis in accepted_supplements)
    detections.sort(key=lambda item: (item.lines[0].center_y, item.bbox[0], item.staff_spacing))
    detections = [
        StaffSystemDetection(
            system_index=index,
            bbox=item.bbox,
            staff_spacing=item.staff_spacing,
            confidence=item.confidence,
            lines=tuple(
                StaffLineDetection(i, line.center_y, line.x_extent, line.segments)
                for i, line in enumerate(item.lines, start=1)
            ),
            provenance=item.provenance,
        )
        for index, item in enumerate(detections, start=1)
    ]
    diagnostics = {
        "sourceOnly": True,
        "teacherCoordinatesUsed": False,
        "restoredOutputsUsed": False,
        "pageIdentityUsed": False,
        "kernelLengths": kernel_lengths,
        "morphologyRowCount": len(morphology_rows),
        "localSpacingModes": [asdict(mode) for mode in modes],
        "legacyCandidateCount": len(legacy),
        "legacyRetainedCount": len(retained),
        "legacyRejected": legacy_rejections,
        "skewSourceSegmentCount": skew_segment_count,
        "skewRowCount": len(skew_rows),
        "skewPostDedupHypothesisCount": len(skew_hypotheses),
        "skewRejected": skew_rejections,
        "sourceTopologyRejected": source_topology_rejections,
        "supplementDuplicateCount": duplicate_supplements,
        "supplementAcceptedCount": len(accepted_supplements),
        "finalSystemCount": len(detections),
    }
    return detections, diagnostics


def detect_staff_systems(image: np.ndarray, *, config: DetectorConfig | None = None) -> list[StaffSystemDetection]:
    detections, _diagnostics = detect_staff_systems_with_diagnostics(image, config=config)
    return detections


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def freeze_source_folder(source_dir: Path, output_path: Path, *, config: DetectorConfig | None = None, expected_source_sha256: Mapping[str, str] | None = None) -> dict[str, Any]:
    cfg = config or DetectorConfig()
    cfg.validate()
    source_dir = Path(source_dir)
    output_path = Path(output_path)
    paths = sorted(source_dir.glob("*.png"), key=lambda path: path.name)
    _require(bool(paths), "source folder has no PNG pages")
    pages: list[dict[str, Any]] = []
    identity_matches = 0
    for path in paths:
        source_sha = sha256_file(path)
        if expected_source_sha256 is not None:
            _require(path.name in expected_source_sha256, f"unregistered source page: {path.name}")
            _require(source_sha == expected_source_sha256[path.name], f"source SHA-256 mismatch: {path.name}")
            identity_matches += 1
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        _require(image is not None, f"unreadable source page: {path.name}")
        detections, diagnostics = detect_staff_systems_with_diagnostics(image, config=cfg)
        height, width = image.shape
        pages.append({
            "pageId": path.stem,
            "sourceFileName": path.name,
            "sourceSha256": source_sha,
            "width": int(width),
            "height": int(height),
            "systemCount": len(detections),
            "systems": [item.as_dict() for item in detections],
            "abstentionReason": None if detections else "NO_SOURCE_SUPPORTED_STANDARD_FIVE_LINE_STAFF_SYSTEM",
            "diagnostics": diagnostics,
        })
    if expected_source_sha256 is not None:
        _require(len(paths) == len(expected_source_sha256), "source page count differs from frozen identity manifest")
    source_path = Path(__file__)
    payload: dict[str, Any] = {
        "schemaVersion": RAW_ARTIFACT_SCHEMA_VERSION,
        "detectorVersion": DETECTOR_VERSION,
        "parentDetectorVersion": PARENT_DETECTOR_VERSION,
        "parentV1DetectorImmutable": True,
        "developmentOnly": True,
        "qualificationEvidence": False,
        "sourceOnly": True,
        "teacherArtifactLoadedDuringInference": False,
        "teacherCoordinatesUsedDuringInference": False,
        "restoredOutputsLoadedDuringInference": False,
        "heldOutAccessed": False,
        "trainingOrFineTuningPerformed": False,
        "pageSpecificRulesUsed": False,
        "detectorSourceSha256": sha256_file(source_path),
        "config": asdict(cfg),
        "sourceIdentityExpectedCount": len(expected_source_sha256) if expected_source_sha256 is not None else None,
        "sourceIdentityMatchedCount": identity_matches if expected_source_sha256 is not None else None,
        "pageCount": len(pages),
        "pages": pages,
        "claimBoundary": {
            "detectorQualified": False,
            "semanticPreservationEstablished": False,
            "overallStage11PassAuthorized": False,
            "productionReady": False,
            "productionPromotionAuthorized": False,
            "stage12EntryAuthorized": False,
        },
    }
    canonical = _canonical_bytes(payload)
    artifact_sha = hashlib.sha256(canonical).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(canonical)
    Path(str(output_path) + ".sha256").write_text(artifact_sha + "\n", encoding="utf-8")
    return {"artifactSha256": artifact_sha, "artifact": payload}


__all__ = [
    "DETECTOR_VERSION",
    "RAW_ARTIFACT_SCHEMA_VERSION",
    "DetectorConfig",
    "StaffLineDetection",
    "StaffSystemDetection",
    "StaffLineMultiSystemDetectorV11Error",
    "detect_staff_systems",
    "detect_staff_systems_with_diagnostics",
    "freeze_source_folder",
    "sha256_file",
]
