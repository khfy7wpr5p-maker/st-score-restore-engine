"""Stage 11 V2d restored-output topology successor v1.5.1.

Development-only minor successor to v1.5. Frozen v1.4 and the first v1.5
prototype remain immutable. This module adds one bounded geometry-only recovery
step after v1.5: when already-detected staff systems establish a strong regular
vertical cadence, missing *interior* cadence slots may be recovered.

The cadence step is deliberately conservative:
* it uses only detections produced from restored pixels on the current page;
* it never reads teacher coordinates, page identity, source family, or holdout data;
* it never extrapolates above the first or below the last detected cadence slot;
* it requires multiple directly observed cadence gaps and low phase residual;
* it preserves every parent detection and adds only missing interior slots.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Sequence

import numpy as np

from . import stage11_v2d_restored_topology_successor_v1_5 as parent

DETECTOR_VERSION = "stage11-v2d-restored-topology-successor.v1.5.1"
PARENT_DETECTOR_VERSION = parent.DETECTOR_VERSION
StaffLineDetection = parent.StaffLineDetection
StaffSystemDetection = parent.StaffSystemDetection
RestoredTopologyConfig = parent.RestoredTopologyConfig


class RestoredTopologySuccessorV151Error(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RestoredTopologySuccessorV151Error(message)


@dataclass(frozen=True)
class CadenceRecoveryConfig:
    min_system_count: int = 4
    min_gap_px: float = 35.0
    max_gap_px: float = 180.0
    max_gap_multiple: int = 4
    gap_tolerance_fraction: float = 0.12
    min_direct_gap_count: int = 3
    min_explained_gap_fraction: float = 0.80
    max_phase_residual_fraction: float = 0.04
    duplicate_center_fraction: float = 0.30

    def validate(self) -> None:
        _require(4 <= self.min_system_count <= 64, "invalid cadence minimum system count")
        _require(10.0 <= self.min_gap_px < self.max_gap_px <= 512.0, "invalid cadence gap bounds")
        _require(2 <= self.max_gap_multiple <= 8, "invalid cadence maximum multiple")
        _require(0.02 <= self.gap_tolerance_fraction <= 0.30, "invalid cadence gap tolerance")
        _require(2 <= self.min_direct_gap_count <= 32, "invalid direct cadence gap count")
        _require(0.50 <= self.min_explained_gap_fraction <= 1.0, "invalid explained cadence fraction")
        _require(0.005 <= self.max_phase_residual_fraction <= 0.20, "invalid cadence phase residual")
        _require(0.10 <= self.duplicate_center_fraction <= 0.49, "invalid cadence duplicate-center fraction")


@dataclass(frozen=True)
class _CadenceModel:
    gap: float
    phase: float
    slot_indices: tuple[int, ...]
    explained_gap_fraction: float
    direct_gap_count: int
    phase_residual_fraction: float


def _center(item: StaffSystemDetection) -> float:
    _require(len(item.lines) == 5, "cadence input must contain five-line systems")
    return float(np.mean([float(line.center_y) for line in item.lines]))


def _estimate_cadence(
    detections: Sequence[StaffSystemDetection],
    config: CadenceRecoveryConfig,
) -> _CadenceModel | None:
    config.validate()
    ordered = sorted(detections, key=lambda item: (_center(item), item.bbox[0]))
    if len(ordered) < config.min_system_count:
        return None

    centers = np.asarray([_center(item) for item in ordered], dtype=np.float64)
    adjacent = np.diff(centers)
    usable = adjacent[adjacent >= config.min_gap_px]
    if usable.size < config.min_direct_gap_count:
        return None

    candidates = [
        float(gap)
        for gap in usable
        if config.min_gap_px <= float(gap) <= config.max_gap_px
    ]
    if not candidates:
        return None

    best: tuple[tuple[int, int, float, float], float, list[float], int, int] | None = None
    for gap in candidates:
        residuals: list[float] = []
        direct = 0
        explained = 0
        for observed in usable:
            multiple = max(1, int(round(float(observed) / gap)))
            if multiple > config.max_gap_multiple:
                residual = math.inf
            else:
                residual = abs(float(observed) - multiple * gap)
            residuals.append(residual)
            if residual <= config.gap_tolerance_fraction * gap:
                explained += 1
                if multiple == 1:
                    direct += 1
        clipped = [min(value, 0.5 * gap) for value in residuals]
        median_residual = float(np.median(clipped)) if clipped else math.inf
        # Prefer a candidate that explains the most observed adjacent gaps,
        # then the most directly observed one-gap intervals, then lower residual.
        score = (explained, direct, -median_residual, -gap)
        if best is None or score > best[0]:
            best = (score, gap, residuals, direct, explained)

    assert best is not None
    _score, gap, _residuals, direct, explained = best
    explained_fraction = explained / float(len(usable))
    if direct < config.min_direct_gap_count:
        return None
    if explained_fraction < config.min_explained_gap_fraction:
        return None

    anchor = float(centers[0])
    slots = np.rint((centers - anchor) / gap).astype(np.int64)
    offsets = centers - slots.astype(np.float64) * gap
    phase = float(np.median(offsets))
    residual = np.abs(centers - (phase + slots.astype(np.float64) * gap))
    phase_residual_fraction = float(np.median(residual)) / gap
    if phase_residual_fraction > config.max_phase_residual_fraction:
        return None

    return _CadenceModel(
        gap=gap,
        phase=phase,
        slot_indices=tuple(int(value) for value in slots),
        explained_gap_fraction=explained_fraction,
        direct_gap_count=direct,
        phase_residual_fraction=phase_residual_fraction,
    )


def _cadence_detection(
    center: float,
    spacing: float,
    x1: int,
    x2: int,
    image_height: int,
) -> StaffSystemDetection:
    ys = tuple(center + offset * spacing for offset in (-2, -1, 0, 1, 2))
    lines = tuple(
        StaffLineDetection(
            index,
            float(y),
            (x1, x2),
            ((x1, int(round(y)), x2, int(round(y))),),
        )
        for index, y in enumerate(ys, start=1)
    )
    y1 = max(0, int(math.floor(ys[0] - max(2.0, spacing * 0.40))))
    y2 = min(image_height, int(math.ceil(ys[-1] + max(2.0, spacing * 0.40))) + 1)
    return StaffSystemDetection(
        0,
        (x1, y1, x2, y2),
        float(spacing),
        0.80,
        lines,
        "restored-only:v1.5.1-interior-cadence-recovery",
        DETECTOR_VERSION,
    )


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


def _interior_cadence_recovery(
    detections: Sequence[StaffSystemDetection],
    *,
    image_height: int,
    image_width: int,
    config: CadenceRecoveryConfig,
) -> tuple[list[StaffSystemDetection], dict[str, Any]]:
    config.validate()
    ordered = sorted(detections, key=lambda item: (_center(item), item.bbox[0]))
    model = _estimate_cadence(ordered, config)
    if model is None:
        return list(ordered), {
            "cadenceAccepted": False,
            "parentSystemCount": len(ordered),
            "addedInteriorSystemCount": 0,
            "finalSystemCount": len(ordered),
        }

    centers = np.asarray([_center(item) for item in ordered], dtype=np.float64)
    slots = np.asarray(model.slot_indices, dtype=np.int64)
    low_slot = int(np.min(slots))
    high_slot = int(np.max(slots))
    spacing = float(np.median([float(item.staff_spacing) for item in ordered]))
    _require(math.isfinite(spacing) and spacing > 0.0, "invalid cadence staff spacing")

    lefts = [int(item.bbox[0]) for item in ordered]
    rights = [int(item.bbox[2]) for item in ordered]
    x1 = max(0, min(image_width - 1, int(round(float(np.median(lefts))))))
    x2 = max(x1 + 1, min(image_width, int(round(float(np.median(rights))))))

    additions: list[StaffSystemDetection] = []
    added_slots: list[int] = []
    for slot in range(low_slot, high_slot + 1):
        center = model.phase + slot * model.gap
        if float(np.min(np.abs(centers - center))) < config.duplicate_center_fraction * model.gap:
            continue
        candidate = _cadence_detection(center, spacing, x1, x2, image_height)
        additions.append(candidate)
        added_slots.append(slot)

    merged = list(ordered) + additions
    merged.sort(key=lambda item: (_center(item), item.bbox[0], item.staff_spacing, item.provenance))
    reindexed = [_reindexed(item, index) for index, item in enumerate(merged, start=1)]
    diagnostics = {
        "cadenceAccepted": True,
        "parentSystemCount": len(ordered),
        "gapPx": model.gap,
        "phasePx": model.phase,
        "explainedGapFraction": model.explained_gap_fraction,
        "directGapCount": model.direct_gap_count,
        "phaseResidualFraction": model.phase_residual_fraction,
        "lowObservedSlot": low_slot,
        "highObservedSlot": high_slot,
        "edgeExtrapolationPerformed": False,
        "addedInteriorSlots": added_slots,
        "addedInteriorSystemCount": len(additions),
        "cadenceStaffSpacingPx": spacing,
        "finalSystemCount": len(reindexed),
    }
    return reindexed, diagnostics


def detect_staff_systems_with_diagnostics(
    image: np.ndarray,
    *,
    parent_config: RestoredTopologyConfig | None = None,
    cadence_config: CadenceRecoveryConfig | None = None,
) -> tuple[list[StaffSystemDetection], dict[str, Any]]:
    p_cfg = parent_config or RestoredTopologyConfig()
    p_cfg.validate()
    c_cfg = cadence_config or CadenceRecoveryConfig()
    c_cfg.validate()

    parent_detections, parent_diagnostics = parent.detect_staff_systems_with_diagnostics(
        image,
        config=p_cfg,
    )
    gray = parent._as_grayscale(image)
    height, width = gray.shape
    detections, cadence_diagnostics = _interior_cadence_recovery(
        parent_detections,
        image_height=int(height),
        image_width=int(width),
        config=c_cfg,
    )
    diagnostics = {
        "developmentOnly": True,
        "restoredOutputInput": True,
        "teacherCoordinatesUsed": False,
        "heldOutAccessed": False,
        "trainingUsed": False,
        "pageIdentityUsed": False,
        "pageSpecificRulesUsed": False,
        "familySpecificRulesUsed": False,
        "edgeExtrapolationUsed": False,
        "parentDetectorVersion": PARENT_DETECTOR_VERSION,
        "parentSystemCount": len(parent_detections),
        "cadenceRecovery": cadence_diagnostics,
        "finalSystemCount": len(detections),
        "parentConfig": asdict(p_cfg),
        "cadenceConfig": asdict(c_cfg),
        "parentDiagnostics": parent_diagnostics,
    }
    return detections, diagnostics


def detect_staff_systems(
    image: np.ndarray,
    *,
    parent_config: RestoredTopologyConfig | None = None,
    cadence_config: CadenceRecoveryConfig | None = None,
) -> list[StaffSystemDetection]:
    return detect_staff_systems_with_diagnostics(
        image,
        parent_config=parent_config,
        cadence_config=cadence_config,
    )[0]


__all__ = [
    "DETECTOR_VERSION",
    "PARENT_DETECTOR_VERSION",
    "CadenceRecoveryConfig",
    "RestoredTopologyConfig",
    "RestoredTopologySuccessorV151Error",
    "StaffLineDetection",
    "StaffSystemDetection",
    "detect_staff_systems",
    "detect_staff_systems_with_diagnostics",
]
