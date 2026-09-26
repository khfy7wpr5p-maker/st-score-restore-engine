"""Development-only Stage 11 general-clef successor semantic validator.

Implements the first deterministic Hybrid-C slice approved for ST Score Restore:
source-coordinate safety, staff-topology validation, explicit abstention,
conflict-aware duplicate handling, inference-metadata independence, and
fail-closed coexistence with the frozen P4.14 C-clef path.

This module does not train a classifier, access qualification holdout data, or
claim upstream candidate generation is qualified. Upstream source-only evidence
must already supply presence/subtype confidence; this module validates and
normalizes it into the stable successor evidence schema.
"""
from __future__ import annotations

import math
from statistics import median
from typing import Any, Iterable, Mapping, Sequence


SUCCESSOR_ID = "stage11-general-clef-successor.hybrid-c.v1"
SUPPORTED_TYPES = frozenset({"treble", "bass", "tab", "soprano", "unknown"})
STANDARD_STAFF_TYPES = frozenset({"treble", "bass", "soprano"})
DUPLICATE_IOU_THRESHOLD = 0.70
P414_COLLISION_IOU_THRESHOLD = 0.50
STAFF_BAND_MARGIN_SPACES = 2.0
STAFF_HORIZONTAL_MARGIN_SPACES = 2.0


def _finite_float(value: Any) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("finite numeric value required")
    return result


def _source_geometry(*, source_width: int | float, source_height: int | float) -> tuple[float, float]:
    width = _finite_float(source_width)
    height = _finite_float(source_height)
    if width <= 0.0 or height <= 0.0:
        raise ValueError("positive finite source geometry required")
    return width, height


def _bbox(value: Sequence[float], *, width: float, height: float) -> tuple[float, float, float, float]:
    if len(value) != 4:
        raise ValueError("bbox must contain x1,y1,x2,y2")
    x1, y1, x2, y2 = (_finite_float(item) for item in value)
    if x2 <= x1 or y2 <= y1:
        raise ValueError("bbox must have positive area")
    if x1 < 0.0 or y1 < 0.0 or x2 > width or y2 > height:
        raise ValueError("bbox must remain inside original source-image bounds")
    return x1, y1, x2, y2


def _iou(a: Sequence[float], b: Sequence[float]) -> float:
    ax1, ay1, ax2, ay2 = map(float, a)
    bx1, by1, bx2, by2 = map(float, b)
    iw = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    ih = max(0.0, min(ay2, by2) - max(ay1, by1))
    if iw <= 0.0 or ih <= 0.0:
        return 0.0
    intersection = iw * ih
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - intersection
    return intersection / union if union > 0.0 else 0.0


def _normalize_staff_systems(
    staff_systems: Iterable[Mapping[str, Any]],
    *,
    width: float,
    height: float,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen_indexes: set[int] = set()
    for raw in staff_systems:
        staff_index = int(raw["staff_index"])
        if staff_index in seen_indexes:
            raise ValueError("staff_index values must be unique")
        seen_indexes.add(staff_index)

        rows = [_finite_float(value) for value in raw["line_rows"]]
        if len(rows) not in (5, 6) or rows != sorted(rows) or len(set(rows)) != len(rows):
            raise ValueError("staff line_rows must contain five or six strictly increasing rows")
        if rows[0] < 0.0 or rows[-1] > height:
            raise ValueError("staff line_rows must remain inside source-image bounds")

        gaps = [rows[index + 1] - rows[index] for index in range(len(rows) - 1)]
        spacing = float(median(gaps))
        if spacing <= 0.0:
            raise ValueError("staff spacing must be positive")

        x1 = _finite_float(raw.get("x1", 0.0))
        x2 = _finite_float(raw.get("x2", width))
        if x1 < 0.0 or x2 > width or x2 <= x1:
            raise ValueError("staff horizontal extent must remain inside source-image bounds")

        normalized.append(
            {
                "staff_index": staff_index,
                "line_rows": rows,
                "line_count": len(rows),
                "staff_spacing": spacing,
                "x1": x1,
                "x2": x2,
            }
        )
    normalized.sort(key=lambda item: item["staff_index"])
    return normalized


def _staff_overlap_score(box: Sequence[float], staff: Mapping[str, Any]) -> float:
    x1, y1, x2, y2 = map(float, box)
    spacing = float(staff["staff_spacing"])
    line_rows = staff["line_rows"]
    band_top = float(line_rows[0]) - STAFF_BAND_MARGIN_SPACES * spacing
    band_bottom = float(line_rows[-1]) + STAFF_BAND_MARGIN_SPACES * spacing
    band_left = float(staff["x1"]) - STAFF_HORIZONTAL_MARGIN_SPACES * spacing
    band_right = float(staff["x2"]) + STAFF_HORIZONTAL_MARGIN_SPACES * spacing

    overlap_w = max(0.0, min(x2, band_right) - max(x1, band_left))
    overlap_h = max(0.0, min(y2, band_bottom) - max(y1, band_top))
    if overlap_w <= 0.0 or overlap_h <= 0.0:
        return 0.0

    candidate_area = max((x2 - x1) * (y2 - y1), 1e-9)
    overlap_area = overlap_w * overlap_h
    center_y = (y1 + y2) / 2.0
    staff_center_y = (float(line_rows[0]) + float(line_rows[-1])) / 2.0
    center_penalty = abs(center_y - staff_center_y) / max(spacing, 1e-9)
    return overlap_area / candidate_area + 1.0 / (1.0 + center_penalty)


def _associate_staff(box: Sequence[float], staffs: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    scored = [(_staff_overlap_score(box, staff), int(staff["staff_index"]), staff) for staff in staffs]
    scored = [item for item in scored if item[0] > 0.0]
    if not scored:
        return None
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][2]


def _confidence(value: Any) -> float:
    result = _finite_float(value)
    if not 0.0 <= result <= 1.0:
        raise ValueError("confidence must be in [0,1]")
    return result


def _abstention(index: int, reason: str, bbox: Sequence[float] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"source_candidate_index": index, "reason": reason}
    if bbox is not None:
        result["bbox"] = [float(value) for value in bbox]
    return result


def _candidate_record(
    raw: Mapping[str, Any],
    *,
    index: int,
    width: float,
    height: float,
    staffs: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    try:
        box = _bbox(raw["bbox"], width=width, height=height)
    except (KeyError, TypeError, ValueError):
        return None, _abstention(index, "INVALID_GEOMETRY")

    staff = _associate_staff(box, staffs)
    if staff is None:
        return None, _abstention(index, "TOPOLOGY_MISMATCH", box)

    try:
        presence = _confidence(raw["clef_presence_confidence"])
        type_confidence = _confidence(raw.get("clef_type_confidence", 0.0))
    except (KeyError, TypeError, ValueError):
        return None, _abstention(index, "INSUFFICIENT_CLEF_EVIDENCE", box)

    raw_type = str(raw.get("clef_type_or_unknown", "unknown")).lower()
    reason: str | None = None
    if raw_type not in SUPPORTED_TYPES:
        clef_type = "unknown"
        status = "REVIEW_REQUIRED"
        reason = "MULTI_CLASS_AMBIGUOUS"
    else:
        clef_type = raw_type
        status = "ACCEPT_PRESENCE_ONLY" if clef_type == "unknown" else "ACCEPT_TYPED"

    line_count = int(staff["line_count"])
    if clef_type == "tab" and line_count != 6:
        return None, _abstention(index, "TOPOLOGY_MISMATCH", box)
    if clef_type in STANDARD_STAFF_TYPES and line_count != 5:
        return None, _abstention(index, "TOPOLOGY_MISMATCH", box)

    return (
        {
            "bbox": [float(value) for value in box],
            "staff_index": int(staff["staff_index"]),
            "clef_presence_confidence": presence,
            "clef_type_or_unknown": clef_type,
            "clef_type_confidence": type_confidence if clef_type != "unknown" else 0.0,
            "status": status,
            "abstain_reason": reason,
            "candidate_provenance": str(raw.get("candidate_provenance", "unspecified")),
            "_source_candidate_index": index,
        },
        None,
    )


def _merge_ambiguous(a: Mapping[str, Any], b: Mapping[str, Any]) -> dict[str, Any]:
    ranked = sorted(
        (dict(a), dict(b)),
        key=lambda item: (
            -float(item["clef_presence_confidence"]),
            -float(item["clef_type_confidence"]),
            int(item["_source_candidate_index"]),
        ),
    )
    geometry_source = ranked[0]
    provenances = sorted({str(a["candidate_provenance"]), str(b["candidate_provenance"])})
    return {
        "bbox": list(geometry_source["bbox"]),
        "staff_index": int(geometry_source["staff_index"]),
        "clef_presence_confidence": max(
            float(a["clef_presence_confidence"]),
            float(b["clef_presence_confidence"]),
        ),
        "clef_type_or_unknown": "unknown",
        "clef_type_confidence": 0.0,
        "status": "REVIEW_REQUIRED",
        "abstain_reason": "MULTI_CLASS_AMBIGUOUS",
        "candidate_provenance": "conflict:" + "|".join(provenances),
        "_source_candidate_index": min(
            int(a["_source_candidate_index"]),
            int(b["_source_candidate_index"]),
        ),
    }


def _deduplicate(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ranked = sorted(
        (dict(record) for record in records),
        key=lambda item: (
            -float(item["clef_presence_confidence"]),
            -float(item["clef_type_confidence"]),
            int(item["_source_candidate_index"]),
        ),
    )
    kept: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    for record in ranked:
        overlap_index = next(
            (
                index
                for index, prior in enumerate(kept)
                if int(prior["staff_index"]) == int(record["staff_index"])
                and _iou(prior["bbox"], record["bbox"]) >= DUPLICATE_IOU_THRESHOLD
            ),
            None,
        )
        if overlap_index is None:
            kept.append(record)
            continue

        prior = kept[overlap_index]
        if str(prior["clef_type_or_unknown"]) != str(record["clef_type_or_unknown"]):
            kept[overlap_index] = _merge_ambiguous(prior, record)
            continue

        suppressed.append(
            {
                "source_candidate_index": int(record["_source_candidate_index"]),
                "kept_source_candidate_index": int(prior["_source_candidate_index"]),
                "reason": "DUPLICATE_CANDIDATE",
            }
        )
    return kept, suppressed


def _p414_collision(
    record: Mapping[str, Any],
    p414_detections: Sequence[Mapping[str, Any]],
    *,
    width: float,
    height: float,
) -> dict[str, Any]:
    collisions: list[tuple[float, int, Mapping[str, Any], tuple[float, float, float, float]]] = []
    for index, raw in enumerate(p414_detections):
        try:
            box = _bbox(raw["bbox"], width=width, height=height)
        except (KeyError, TypeError, ValueError):
            continue
        p414_staff_index = raw.get("staff_index", raw.get("staffIndex"))
        if p414_staff_index is not None and int(p414_staff_index) != int(record["staff_index"]):
            continue
        overlap = _iou(record["bbox"], box)
        if overlap >= P414_COLLISION_IOU_THRESHOLD:
            collisions.append((overlap, index, raw, box))

    if not collisions:
        return dict(record)

    collisions.sort(key=lambda item: (-item[0], item[1]))
    _, _, raw, box = collisions[0]
    presence = raw.get(
        "clef_presence_confidence",
        raw.get("presenceConfidence", record["clef_presence_confidence"]),
    )
    try:
        p414_presence = _confidence(presence)
    except (TypeError, ValueError):
        p414_presence = float(record["clef_presence_confidence"])

    resolved = dict(record)
    resolved.update(
        {
            "bbox": [float(value) for value in box],
            "clef_presence_confidence": max(float(record["clef_presence_confidence"]), p414_presence),
            "clef_type_or_unknown": "unknown",
            "clef_type_confidence": 0.0,
            "status": "REVIEW_REQUIRED",
            "abstain_reason": "P4_14_COLLISION",
        }
    )
    return resolved


def resolve_general_clef_successor(
    candidates: Iterable[Mapping[str, Any]],
    staff_systems: Iterable[Mapping[str, Any]],
    *,
    source_width: int | float,
    source_height: int | float,
    p414_detections: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Validate source-only general-clef evidence against staff topology.

    Extra teacher/page/file/source-family metadata on candidates is ignored by
    construction. Output ordering is deterministic and every detection follows
    the stable evidence schema approved for the general-clef successor.
    """
    width, height = _source_geometry(source_width=source_width, source_height=source_height)
    staffs = _normalize_staff_systems(staff_systems, width=width, height=height)
    p414 = list(p414_detections)

    records: list[dict[str, Any]] = []
    abstentions: list[dict[str, Any]] = []
    for index, raw in enumerate(candidates):
        record, abstention = _candidate_record(
            raw,
            index=index,
            width=width,
            height=height,
            staffs=staffs,
        )
        if record is not None:
            records.append(record)
        if abstention is not None:
            abstentions.append(abstention)

    deduplicated, suppressed = _deduplicate(records)
    resolved = [
        _p414_collision(record, p414, width=width, height=height)
        for record in deduplicated
    ]
    resolved.sort(
        key=lambda item: (
            int(item["staff_index"]),
            float(item["bbox"][0]),
            float(item["bbox"][1]),
            int(item["_source_candidate_index"]),
        )
    )
    abstentions.sort(key=lambda item: int(item["source_candidate_index"]))
    suppressed.sort(key=lambda item: int(item["source_candidate_index"]))

    for record in resolved:
        record.pop("_source_candidate_index", None)

    return {
        "candidate_id": SUCCESSOR_ID,
        "detections": resolved,
        "abstentions": abstentions,
        "suppressed_duplicates": suppressed,
    }
