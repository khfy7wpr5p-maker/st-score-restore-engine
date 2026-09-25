"""P4.14 development-only deterministic C-clef precision selection.

This module consumes source-only proposal records produced by the existing
P4.12/P4.13 development chain. It does not read teacher truth, page identity,
source-family identity, restored images, or qualification holdouts at
inference time.

The policy deliberately separates source-semantic scoring, threshold-based
abstention, and staff-aware overlap suppression that preserves spatially
distinct clefs.

This is development code only. It does not qualify a detector or authorize
Stage 11 closure, production, or Stage 12.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .stage11_v2d_c_clef_p4_13_semantic_group_localizer import (
    semantic_confidence_score,
)


OUTPUT_KEYS = (
    "proposalIndex",
    "bbox",
    "staffIndex",
    "staffSpacing",
    "anchor",
    "anchorRank",
    "xOffsetStaffSpaces",
    "componentGroupIndex",
    "features",
)


def _bbox_iou(a: Sequence[float], b: Sequence[float]) -> float:
    ax1, ay1, ax2, ay2 = map(float, a)
    bx1, by1, bx2, by2 = map(float, b)
    if ax2 <= ax1 or ay2 <= ay1 or bx2 <= bx1 or by2 <= by1:
        raise ValueError("bbox must have positive area")
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0.0:
        return 0.0
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union


def candidate_score(record: Mapping[str, Any]) -> float:
    """Return deterministic source-only P4.13 semantic score.

    Only approved proposal geometry and the source-derived feature dictionary
    are consulted. Extra fields such as teacher labels or match annotations do
    not affect the result.
    """
    features = record.get("features")
    if not isinstance(features, Mapping):
        raise ValueError("record.features mapping required")
    proposal = {
        "xOffsetStaffSpaces": float(record.get("xOffsetStaffSpaces", 0.0)),
        "anchorRank": int(record.get("anchorRank", 1)),
    }
    score, _parts = semantic_confidence_score(dict(features), proposal)
    return float(score)


def _sanitized_output(record: Mapping[str, Any], score: float) -> Dict[str, Any]:
    missing = [key for key in OUTPUT_KEYS if key not in record]
    if missing:
        raise ValueError("record missing required keys: " + ", ".join(missing))
    out = {key: record[key] for key in OUTPUT_KEYS}
    out["precisionScore"] = float(score)
    return out


def select_precision_candidates(
    records: Iterable[Mapping[str, Any]],
    *,
    minimum_score: float = 0.60,
    duplicate_iou: float = 0.50,
) -> List[Dict[str, Any]]:
    """Select deterministic high-confidence candidates.

    Candidates below the minimum score abstain. Within the same staff, a lower
    ranked candidate is suppressed only when its box materially overlaps an
    already selected box. Spatially distinct clefs on the same staff remain
    eligible, preserving mid-staff clef changes.
    """
    minimum_score = float(minimum_score)
    duplicate_iou = float(duplicate_iou)
    if not 0.0 <= minimum_score <= 1.0:
        raise ValueError("minimum_score must be in [0,1]")
    if not 0.0 < duplicate_iou <= 1.0:
        raise ValueError("duplicate_iou must be in (0,1]")

    scored: List[tuple[float, Mapping[str, Any]]] = []
    for record in records:
        score = candidate_score(record)
        if score >= minimum_score:
            scored.append((score, record))

    scored.sort(
        key=lambda item: (
            -item[0],
            int(item[1]["staffIndex"]),
            int(item[1].get("anchorRank", 1)),
            abs(float(item[1].get("xOffsetStaffSpaces", 0.0))),
            int(item[1]["proposalIndex"]),
        )
    )

    selected: List[Dict[str, Any]] = []
    for score, record in scored:
        staff_index = int(record["staffIndex"])
        box = record["bbox"]
        duplicate = any(
            int(prior["staffIndex"]) == staff_index
            and _bbox_iou(prior["bbox"], box) >= duplicate_iou
            for prior in selected
        )
        if duplicate:
            continue
        selected.append(_sanitized_output(record, score))

    selected.sort(
        key=lambda item: (
            int(item["staffIndex"]),
            float(item["bbox"][0]),
            float(item["bbox"][1]),
            int(item["proposalIndex"]),
        )
    )
    return selected
