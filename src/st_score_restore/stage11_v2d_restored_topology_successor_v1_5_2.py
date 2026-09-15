"""Stage 11 V2d restored-output topology successor v1.5.2.

Development-only minor successor to v1.5.1. Frozen v1.4, v1.5, and v1.5.1
remain immutable. This revision does not add or remove staff systems. It only
allows a bounded geometry replacement when an existing weak/generic hypothesis
is already geometrically duplicate with a five-line periodic candidate observed
directly in the restored pixels by the existing v1.5 recovery channel.

The replacement step is deliberately conservative:
* system count is invariant;
* it uses only restored pixels and the parent detector output on this page;
* it reuses v1.5 periodic-candidate and duplicate gates without loosening them;
* it does not replace already pixel-periodic or source-topology detections;
* it never reads teacher coordinates, masks, page identity, source family, or
  holdout/qualification data;
* no page/family-specific rule or edge extrapolation is used.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Sequence

import numpy as np

from . import stage11_v2d_restored_topology_successor_v1_5 as pixel_parent
from . import stage11_v2d_restored_topology_successor_v1_5_1 as parent

DETECTOR_VERSION = "stage11-v2d-restored-topology-successor.v1.5.2"
PARENT_DETECTOR_VERSION = parent.DETECTOR_VERSION
PIXEL_EVIDENCE_DETECTOR_VERSION = pixel_parent.DETECTOR_VERSION
StaffLineDetection = parent.StaffLineDetection
StaffSystemDetection = parent.StaffSystemDetection
RestoredTopologyConfig = parent.RestoredTopologyConfig
CadenceRecoveryConfig = parent.CadenceRecoveryConfig


class RestoredTopologySuccessorV152Error(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RestoredTopologySuccessorV152Error(message)


def _center(item: StaffSystemDetection) -> float:
    _require(len(item.lines) == 5, "replacement input must contain five-line systems")
    return float(np.mean([float(line.center_y) for line in item.lines]))


def _line_error(a: StaffSystemDetection, b: StaffSystemDetection) -> float:
    _require(len(a.lines) == 5 and len(b.lines) == 5, "replacement comparison requires five lines")
    a_ys = np.asarray([float(line.center_y) for line in a.lines], dtype=np.float64)
    b_ys = np.asarray([float(line.center_y) for line in b.lines], dtype=np.float64)
    return float(np.mean(np.abs(a_ys - b_ys)))


def _x_overlap_fraction(a: StaffSystemDetection, b: StaffSystemDetection) -> float:
    ax1, _ay1, ax2, _ay2 = a.bbox
    bx1, _by1, bx2, _by2 = b.bbox
    intersection = max(0, min(int(ax2), int(bx2)) - max(int(ax1), int(bx1)))
    denominator = max(1, min(int(ax2) - int(ax1), int(bx2) - int(bx1)))
    return intersection / float(denominator)


def _eligible_for_pixel_replacement(item: StaffSystemDetection) -> bool:
    """Return True only for generic weaker hypotheses, never page/family rules."""
    provenance = str(item.provenance)
    return (
        "parent-anchored-horizontal-template" in provenance
        or "skew-tolerant-horizontal-segment" in provenance
        or "parent-anchored-skew-segment" in provenance
        or "v1.5.1-interior-cadence-recovery" in provenance
    )


def _as_replacement(
    original: StaffSystemDetection,
    evidence: StaffSystemDetection,
) -> StaffSystemDetection:
    lines = tuple(
        StaffLineDetection(
            index,
            float(line.center_y),
            line.x_extent,
            line.segments,
        )
        for index, line in enumerate(evidence.lines, start=1)
    )
    return StaffSystemDetection(
        int(original.system_index),
        evidence.bbox,
        float(evidence.staff_spacing),
        float(original.confidence),
        lines,
        "restored-only:v1.5.2-pixel-backed-replacement",
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


def _pixel_backed_replacement(
    detections: Sequence[StaffSystemDetection],
    periodic_candidates: Sequence[pixel_parent._PeriodicCandidate],
    *,
    image_height: int,
    config: RestoredTopologyConfig,
) -> tuple[list[StaffSystemDetection], dict[str, Any]]:
    """Replace geometry one-for-one; never add, remove, or reorder by identity."""
    config.validate()
    ordered = sorted(detections, key=lambda item: (_center(item), item.bbox[0], item.provenance))
    evidence = [pixel_parent._candidate_to_detection(candidate, image_height) for candidate in periodic_candidates]

    pair_rows: list[tuple[float, float, float, int, int]] = []
    for detection_index, current in enumerate(ordered):
        if not _eligible_for_pixel_replacement(current):
            continue
        for candidate_index, candidate in enumerate(evidence):
            if _x_overlap_fraction(current, candidate) < config.x_overlap_min:
                continue
            if not pixel_parent._detections_duplicate(current, candidate, config):
                continue
            error = _line_error(current, candidate)
            if error <= 0.0:
                continue
            scale = max(float(current.staff_spacing), float(candidate.staff_spacing), 1.0)
            center_delta = abs(_center(current) - _center(candidate)) / scale
            normalized_error = error / scale
            candidate_score = float(periodic_candidates[candidate_index].score)
            # Deterministic preference: least geometry change first, then nearest
            # center, then strongest already-accepted restored-pixel evidence.
            pair_rows.append((normalized_error, center_delta, -candidate_score, detection_index, candidate_index))

    pair_rows.sort()
    replacements: dict[int, int] = {}
    used_candidates: set[int] = set()
    for _error, _center_delta, _negative_score, detection_index, candidate_index in pair_rows:
        if detection_index in replacements or candidate_index in used_candidates:
            continue
        replacements[detection_index] = candidate_index
        used_candidates.add(candidate_index)

    result: list[StaffSystemDetection] = []
    replacement_rows: list[dict[str, Any]] = []
    for detection_index, current in enumerate(ordered):
        candidate_index = replacements.get(detection_index)
        if candidate_index is None:
            result.append(current)
            continue
        candidate = evidence[candidate_index]
        replacement = _as_replacement(current, candidate)
        replacement_rows.append({
            "systemIndexBeforeReindex": int(current.system_index),
            "oldProvenance": str(current.provenance),
            "oldCenterY": _center(current),
            "newCenterY": _center(replacement),
            "oldStaffSpacing": float(current.staff_spacing),
            "newStaffSpacing": float(replacement.staff_spacing),
            "meanLineDeltaPx": _line_error(current, replacement),
            "pixelCandidateScore": float(periodic_candidates[candidate_index].score),
        })
        result.append(replacement)

    result.sort(key=lambda item: (_center(item), item.bbox[0], item.staff_spacing, item.provenance))
    reindexed = [_reindexed(item, index) for index, item in enumerate(result, start=1)]
    _require(len(reindexed) == len(ordered), "v1.5.2 replacement must preserve system count")
    return reindexed, {
        "parentSystemCount": len(ordered),
        "periodicCandidateCount": len(periodic_candidates),
        "eligibleParentSystemCount": sum(1 for item in ordered if _eligible_for_pixel_replacement(item)),
        "replacementCount": len(replacement_rows),
        "finalSystemCount": len(reindexed),
        "systemCountPreserved": len(reindexed) == len(ordered),
        "addedSystemCount": 0,
        "removedSystemCount": 0,
        "replacements": replacement_rows,
    }


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
        parent_config=p_cfg,
        cadence_config=c_cfg,
    )
    gray = pixel_parent._as_grayscale(image)
    height, _width = gray.shape
    periodic_candidates, periodic_diagnostics = pixel_parent._periodic_candidates(gray, p_cfg)
    detections, replacement_diagnostics = _pixel_backed_replacement(
        parent_detections,
        periodic_candidates,
        image_height=int(height),
        config=p_cfg,
    )

    diagnostics = {
        "developmentOnly": True,
        "restoredOutputInput": True,
        "teacherCoordinatesUsed": False,
        "teacherMasksUsed": False,
        "heldOutAccessed": False,
        "qualificationDataAccessed": False,
        "trainingUsed": False,
        "pageIdentityUsed": False,
        "pageSpecificRulesUsed": False,
        "familySpecificRulesUsed": False,
        "edgeExtrapolationUsed": False,
        "parentDetectorVersion": PARENT_DETECTOR_VERSION,
        "pixelEvidenceDetectorVersion": PIXEL_EVIDENCE_DETECTOR_VERSION,
        "parentSystemCount": len(parent_detections),
        "pixelBackedReplacement": replacement_diagnostics,
        "finalSystemCount": len(detections),
        "parentConfig": asdict(p_cfg),
        "cadenceConfig": asdict(c_cfg),
        "periodicityEvidenceDiagnostics": periodic_diagnostics,
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
    "PIXEL_EVIDENCE_DETECTOR_VERSION",
    "CadenceRecoveryConfig",
    "RestoredTopologyConfig",
    "RestoredTopologySuccessorV152Error",
    "StaffLineDetection",
    "StaffSystemDetection",
    "detect_staff_systems",
    "detect_staff_systems_with_diagnostics",
]
