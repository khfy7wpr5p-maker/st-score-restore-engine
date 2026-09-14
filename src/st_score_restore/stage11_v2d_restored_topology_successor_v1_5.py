"""Stage 11 V2d restored-output topology successor v1.5.

Development-only successor for restored grayscale pages. Frozen v1.4 remains
immutable. This module calls v1.4 as a parent and adds a deterministic
restored-pixel periodicity recovery channel that is intentionally independent
of teacher coordinates, page identity, source family, held-out data, and
training state.

The recovery channel:
* extracts long horizontal line likelihood with a bounded morphology kernel;
* groups locally regular five-line periodic patterns;
* rejects six-line continuations (TAB-like controls);
* removes implausible large-spacing parent systems on restored pages;
* preserves plausible v1.4 parent systems and adds only non-duplicate recovery.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Sequence

import cv2
import numpy as np

from . import stage11_v2d_staff_line_multisystem_source_detector_v1_4 as parent

DETECTOR_VERSION = "stage11-v2d-restored-topology-successor.v1.5"
PARENT_DETECTOR_VERSION = parent.DETECTOR_VERSION
StaffLineDetection = parent.StaffLineDetection
StaffSystemDetection = parent.StaffSystemDetection


class RestoredTopologySuccessorV15Error(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RestoredTopologySuccessorV15Error(message)


@dataclass(frozen=True)
class RestoredTopologyConfig:
    horizontal_kernel_fraction: float = 0.06
    min_horizontal_support_fraction: float = 0.15
    min_candidate_width_fraction: float = 0.35
    min_staff_spacing_px: float = 3.0
    max_staff_spacing_px: float = 18.0
    regularity_tolerance_fraction: float = 0.38
    six_line_tolerance_fraction: float = 0.35
    x_overlap_min: float = 0.35
    peak_window_size: int = 7
    parent_min_spacing_px: float = 3.0
    parent_max_spacing_px: float = 18.0
    duplicate_center_tolerance_factor: float = 1.30
    duplicate_line_mean_error_factor: float = 0.75

    def validate(self) -> None:
        _require(0.02 <= self.horizontal_kernel_fraction <= 0.20, "invalid horizontal kernel fraction")
        _require(0.05 <= self.min_horizontal_support_fraction <= 0.80, "invalid support fraction")
        _require(0.20 <= self.min_candidate_width_fraction <= 0.95, "invalid width fraction")
        _require(1.0 <= self.min_staff_spacing_px < self.max_staff_spacing_px <= 64.0, "invalid staff spacing bounds")
        _require(0.10 <= self.regularity_tolerance_fraction <= 0.75, "invalid regularity tolerance")
        _require(0.10 <= self.six_line_tolerance_fraction <= 0.75, "invalid six-line tolerance")
        _require(0.10 <= self.x_overlap_min <= 0.95, "invalid x overlap minimum")
        _require(5 <= self.peak_window_size <= 9, "invalid peak window size")
        _require(1.0 <= self.parent_min_spacing_px < self.parent_max_spacing_px <= 64.0, "invalid parent spacing bounds")
        _require(0.25 <= self.duplicate_center_tolerance_factor <= 3.0, "invalid duplicate center tolerance")
        _require(0.10 <= self.duplicate_line_mean_error_factor <= 2.0, "invalid duplicate line error tolerance")


@dataclass(frozen=True)
class _RowEvidence:
    y: float
    support: float
    x1: int
    x2: int


@dataclass(frozen=True)
class _PeriodicCandidate:
    ys: tuple[float, float, float, float, float]
    spacing: float
    x1: int
    x2: int
    score: float
    median_support_fraction: float


def _as_grayscale(image: np.ndarray) -> np.ndarray:
    _require(isinstance(image, np.ndarray), "image must be numpy array")
    if image.ndim == 2:
        gray = image
    elif image.ndim == 3 and image.shape[2] in (3, 4):
        code = cv2.COLOR_BGR2GRAY if image.shape[2] == 3 else cv2.COLOR_BGRA2GRAY
        gray = cv2.cvtColor(image, code)
    else:
        raise RestoredTopologySuccessorV15Error("unsupported image shape")
    _require(gray.size > 0, "image must be non-empty")
    return gray.astype(np.uint8, copy=False)


def _x_overlap_fraction(a: _RowEvidence, b: _RowEvidence) -> float:
    inter = max(0, min(a.x2, b.x2) - max(a.x1, b.x1))
    denom = max(1, min(a.x2 - a.x1, b.x2 - b.x1))
    return inter / float(denom)


def _row_evidence(gray: np.ndarray, cfg: RestoredTopologyConfig) -> tuple[list[_RowEvidence], dict[str, Any]]:
    height, width = gray.shape
    _threshold, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel_length = max(9, int(round(width * cfg.horizontal_kernel_fraction)))
    if kernel_length % 2 == 0:
        kernel_length += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))
    opened = cv2.morphologyEx(ink, cv2.MORPH_OPEN, kernel)
    support = np.count_nonzero(opened, axis=1).astype(np.float64)
    minimum = float(width) * cfg.min_horizontal_support_fraction
    mask = support >= minimum

    rows: list[_RowEvidence] = []
    y = 0
    while y < height:
        if not mask[y]:
            y += 1
            continue
        end = y + 1
        while end < height and mask[end]:
            end += 1
        peak = y + int(np.argmax(support[y:end]))
        band = opened[max(0, peak - 1):min(height, peak + 2)] > 0
        xs = np.where(np.any(band, axis=0))[0]
        if xs.size:
            rows.append(_RowEvidence(float(peak), float(support[peak]), int(xs[0]), int(xs[-1]) + 1))
        y = end

    return rows, {
        "horizontalKernelLength": kernel_length,
        "minimumRowSupportPixels": minimum,
        "rowEvidenceCount": len(rows),
    }


def _candidate_score(selected: Sequence[_RowEvidence], spacing: float, page_width: int) -> tuple[float, float]:
    ys = np.asarray([row.y for row in selected], dtype=np.float64)
    differences = np.diff(ys)
    regularity = 1.0 - min(1.0, float(np.mean(np.abs(differences - spacing))) / max(1.0, spacing))
    median_support_fraction = float(np.median([row.support for row in selected])) / float(page_width)
    score = 0.70 * regularity + 0.30 * min(1.0, median_support_fraction / 0.60)
    return score, median_support_fraction


def _has_sixth_line(
    rows: Sequence[_RowEvidence],
    selected_indices: set[int],
    ys: np.ndarray,
    spacing: float,
    x1: int,
    x2: int,
    cfg: RestoredTopologyConfig,
) -> bool:
    tolerance = max(1.5, spacing * cfg.six_line_tolerance_fraction)
    for index, row in enumerate(rows):
        if index in selected_indices:
            continue
        near = (
            abs(row.y - (ys[0] - spacing)) <= tolerance
            or abs(row.y - (ys[-1] + spacing)) <= tolerance
        )
        if not near:
            continue
        intersection = max(0, min(x2, row.x2) - max(x1, row.x1))
        if intersection >= cfg.x_overlap_min * max(1, x2 - x1):
            return True
    return False


def _periodic_candidates(gray: np.ndarray, cfg: RestoredTopologyConfig) -> tuple[list[_PeriodicCandidate], dict[str, Any]]:
    rows, row_diagnostics = _row_evidence(gray, cfg)
    _height, width = gray.shape
    candidates: list[_PeriodicCandidate] = []

    for start in range(len(rows)):
        stop = min(len(rows), start + cfg.peak_window_size)
        indices = list(range(start, stop))
        if len(indices) < 5:
            continue
        # Deterministic combinations of exactly five rows from a bounded local window.
        from itertools import combinations
        for combo in combinations(indices, 5):
            if combo[0] != start:
                continue
            selected = [rows[index] for index in combo]
            ys = np.asarray([row.y for row in selected], dtype=np.float64)
            differences = np.diff(ys)
            spacing = float(np.median(differences))
            if not (cfg.min_staff_spacing_px <= spacing <= cfg.max_staff_spacing_px):
                continue
            tolerance = max(1.5, spacing * cfg.regularity_tolerance_fraction)
            if float(np.max(np.abs(differences - spacing))) > tolerance:
                continue
            if min(_x_overlap_fraction(selected[0], row) for row in selected[1:]) < cfg.x_overlap_min:
                continue
            x1 = int(np.median([row.x1 for row in selected]))
            x2 = int(np.median([row.x2 for row in selected]))
            if x2 - x1 < width * cfg.min_candidate_width_fraction:
                continue
            if _has_sixth_line(rows, set(combo), ys, spacing, x1, x2, cfg):
                continue
            score, median_support_fraction = _candidate_score(selected, spacing, width)
            candidates.append(_PeriodicCandidate(tuple(float(y) for y in ys), spacing, x1, x2, score, median_support_fraction))

    candidates.sort(key=lambda item: (-item.score, item.ys[0], item.x1, item.spacing))
    kept: list[_PeriodicCandidate] = []
    for candidate in candidates:
        center = float(np.mean(candidate.ys))
        duplicate = False
        for existing in kept:
            existing_center = float(np.mean(existing.ys))
            if abs(center - existing_center) < max(candidate.spacing, existing.spacing) * 1.20:
                duplicate = True
                break
        if not duplicate:
            kept.append(candidate)
    kept.sort(key=lambda item: (item.ys[0], item.x1, item.spacing))

    diagnostics = dict(row_diagnostics)
    diagnostics.update({
        "rawPeriodicCandidateCount": len(candidates),
        "acceptedPeriodicCandidateCount": len(kept),
    })
    return kept, diagnostics


def _candidate_to_detection(candidate: _PeriodicCandidate, image_height: int) -> StaffSystemDetection:
    lines = tuple(
        StaffLineDetection(
            index,
            float(y),
            (candidate.x1, candidate.x2),
            ((candidate.x1, int(round(y)), candidate.x2, int(round(y))),),
        )
        for index, y in enumerate(candidate.ys, start=1)
    )
    y1 = max(0, int(math.floor(candidate.ys[0] - max(2.0, candidate.spacing * 0.40))))
    y2 = min(image_height, int(math.ceil(candidate.ys[-1] + max(2.0, candidate.spacing * 0.40))) + 1)
    confidence = max(0.50, min(0.99, 0.50 + 0.49 * candidate.score))
    return StaffSystemDetection(
        0,
        (candidate.x1, y1, candidate.x2, y2),
        float(candidate.spacing),
        float(confidence),
        lines,
        "restored-only:v1.5-horizontal-periodicity-five-line",
        DETECTOR_VERSION,
    )


def _plausible_parent(item: StaffSystemDetection, cfg: RestoredTopologyConfig) -> bool:
    if len(item.lines) != 5:
        return False
    spacing = float(item.staff_spacing)
    if not (cfg.parent_min_spacing_px <= spacing <= cfg.parent_max_spacing_px):
        return False
    ys = [float(line.center_y) for line in item.lines]
    return all(a < b for a, b in zip(ys, ys[1:]))


def _detections_duplicate(a: StaffSystemDetection, b: StaffSystemDetection, cfg: RestoredTopologyConfig) -> bool:
    if len(a.lines) != 5 or len(b.lines) != 5:
        return False
    a_ys = np.asarray([line.center_y for line in a.lines], dtype=np.float64)
    b_ys = np.asarray([line.center_y for line in b.lines], dtype=np.float64)
    scale = max(float(a.staff_spacing), float(b.staff_spacing), 1.0)
    center_close = abs(float(np.mean(a_ys)) - float(np.mean(b_ys))) < scale * cfg.duplicate_center_tolerance_factor
    line_close = float(np.mean(np.abs(a_ys - b_ys))) < scale * cfg.duplicate_line_mean_error_factor
    return center_close and line_close


def _reindexed(item: StaffSystemDetection, index: int) -> StaffSystemDetection:
    lines = tuple(
        StaffLineDetection(i, float(line.center_y), line.x_extent, line.segments)
        for i, line in enumerate(item.lines, start=1)
    )
    return StaffSystemDetection(
        index,
        item.bbox,
        float(item.staff_spacing),
        float(item.confidence),
        lines,
        item.provenance,
        DETECTOR_VERSION,
    )


def detect_staff_systems_with_diagnostics(
    image: np.ndarray,
    *,
    config: RestoredTopologyConfig | None = None,
) -> tuple[list[StaffSystemDetection], dict[str, Any]]:
    cfg = config or RestoredTopologyConfig()
    cfg.validate()
    gray = _as_grayscale(image)
    height, _width = gray.shape

    parent_detections, parent_diagnostics = parent.detect_staff_systems_with_diagnostics(gray)
    plausible_parent = [item for item in parent_detections if _plausible_parent(item, cfg)]
    periodic, periodic_diagnostics = _periodic_candidates(gray, cfg)
    recovery = [_candidate_to_detection(item, height) for item in periodic]

    added: list[StaffSystemDetection] = []
    for candidate in recovery:
        if any(_detections_duplicate(candidate, item, cfg) for item in plausible_parent):
            continue
        if any(_detections_duplicate(candidate, item, cfg) for item in added):
            continue
        added.append(candidate)

    merged = list(plausible_parent) + added
    merged.sort(key=lambda item: (item.lines[0].center_y, item.bbox[0], item.staff_spacing, item.provenance))
    reindexed = [_reindexed(item, index) for index, item in enumerate(merged, start=1)]

    diagnostics = {
        "developmentOnly": True,
        "restoredOutputInput": True,
        "teacherCoordinatesUsed": False,
        "heldOutAccessed": False,
        "trainingUsed": False,
        "pageIdentityUsed": False,
        "pageSpecificRulesUsed": False,
        "familySpecificRulesUsed": False,
        "parentDetectorVersion": PARENT_DETECTOR_VERSION,
        "parentSystemCount": len(parent_detections),
        "plausibleParentSystemCount": len(plausible_parent),
        "rejectedImplausibleParentSystemCount": len(parent_detections) - len(plausible_parent),
        "periodicityRecovery": periodic_diagnostics,
        "addedRecoverySystemCount": len(added),
        "finalSystemCount": len(reindexed),
        "config": asdict(cfg),
        "parentDiagnostics": parent_diagnostics,
    }
    return reindexed, diagnostics


def detect_staff_systems(image: np.ndarray, *, config: RestoredTopologyConfig | None = None) -> list[StaffSystemDetection]:
    return detect_staff_systems_with_diagnostics(image, config=config)[0]


__all__ = [
    "DETECTOR_VERSION",
    "PARENT_DETECTOR_VERSION",
    "RestoredTopologyConfig",
    "RestoredTopologySuccessorV15Error",
    "StaffLineDetection",
    "StaffSystemDetection",
    "detect_staff_systems",
    "detect_staff_systems_with_diagnostics",
]
