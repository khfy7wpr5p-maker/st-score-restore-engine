from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable


def _first(obj: dict[str, Any], names: Iterable[str], default: Any = None) -> Any:
    for name in names:
        if name in obj:
            return obj[name]
    return default


def _line_y(line: dict[str, Any]) -> float | None:
    value = _first(line, ("centerY", "center_y", "y", "row"))
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _systems_from_node(node: Any) -> list[dict[str, Any]]:
    if not isinstance(node, dict):
        return []
    for key in ("systems", "staffSystems", "staff_systems"):
        value = node.get(key)
        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
            return value
    return []


def _page_id(node: dict[str, Any]) -> str | None:
    value = _first(node, ("pageId", "teacherPageId", "page_id", "id", "stem"))
    return value if isinstance(value, str) else None


def _find_page(root: Any, target: str) -> dict[str, Any] | None:
    stack = [root]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if _page_id(node) == target and _systems_from_node(node):
                return node
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return None


def _system_geometry(system: dict[str, Any]) -> tuple[float, float] | None:
    lines = _first(system, ("lines", "staffLines", "staff_lines"), [])
    if not isinstance(lines, list):
        return None
    ys = [_line_y(line) for line in lines if isinstance(line, dict)]
    ys = [y for y in ys if y is not None]
    if len(ys) != 5:
        return None
    ys.sort()
    diffs = [b - a for a, b in zip(ys, ys[1:])]
    spacing = float(sorted(diffs)[len(diffs) // 2]) if diffs else 0.0
    if spacing <= 0.0:
        return None
    return sum(ys) / 5.0, spacing


def _raw_geometry(system: dict[str, Any]) -> tuple[float, float] | None:
    lines = system.get("lines", [])
    if not isinstance(lines, list):
        return None
    ys = [_line_y(line) for line in lines if isinstance(line, dict)]
    ys = [y for y in ys if y is not None]
    if len(ys) != 5:
        return None
    ys.sort()
    spacing_value = _first(system, ("staffSpacing", "staff_spacing"))
    spacing = float(spacing_value) if isinstance(spacing_value, (int, float)) else float(sorted([b-a for a,b in zip(ys,ys[1:])])[2])
    return sum(ys) / 5.0, spacing


def _nearest_residuals(predicted: list[tuple[float, float]], teacher: list[tuple[float, float]]) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for center, spacing in predicted:
        if not teacher:
            break
        nearest_center, nearest_spacing = min(teacher, key=lambda item: abs(item[0] - center))
        scale = max(1.0, nearest_spacing)
        rows.append({
            "predictedCenter": round(center, 4),
            "nearestTeacherCenter": round(nearest_center, 4),
            "centerResidualPx": round(abs(center-nearest_center), 4),
            "centerResidualInTeacherSpacing": round(abs(center-nearest_center)/scale, 4),
            "predictedSpacing": round(spacing, 4),
            "teacherSpacing": round(nearest_spacing, 4),
            "spacingResidualFraction": round(abs(spacing-nearest_spacing)/scale, 4),
        })
    return rows


def _taxonomy(teacher_count: int, predicted_count: int, matched_count: int, residuals: list[dict[str, float]]) -> str:
    fn = teacher_count - matched_count
    fp = predicted_count - matched_count
    large_alignment = sum(1 for row in residuals if row["centerResidualInTeacherSpacing"] > 0.5)
    if predicted_count >= teacher_count - 1 and matched_count < 0.5 * teacher_count:
        return "COUNT_PRESENT_BUT_ALIGNMENT_OR_PATTERN_SELECTION_FAILS"
    if predicted_count < teacher_count and fp > 0 and fn >= 3:
        return "HYBRID_UNDERCOUNT_AND_ALIGNMENT_OR_PATTERN_SELECTION_FAILURE"
    if predicted_count < teacher_count and fp == 0:
        return "PREDOMINANTLY_MISSING_SYSTEM_SLOTS"
    if large_alignment > max(1, len(residuals) // 3):
        return "PREDOMINANTLY_VERTICAL_ALIGNMENT_MISMATCH"
    if fn or fp:
        return "MIXED_MINOR_TOPOLOGY_MISMATCH"
    return "EXACT"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--score", required=True)
    parser.add_argument("--teacher", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    raw = json.loads(Path(args.raw).read_text())
    score = json.loads(Path(args.score).read_text())["scoring"]
    teacher = json.loads(Path(args.teacher).read_text())

    raw_by = {page["pageId"]: page for page in raw["pages"]}
    score_by = {page["teacherPageId"]: page for page in score["pages"]}

    page_rows = []
    mechanism_counts: dict[str, int] = {}
    for pid in sorted(score_by):
        scored = score_by[pid]
        raw_page = raw_by.get(pid, {"systems": [], "diagnostics": {}})
        teacher_page = _find_page(teacher, pid)
        teacher_geometry = [] if teacher_page is None else [g for g in (_system_geometry(s) for s in _systems_from_node(teacher_page)) if g]
        predicted_geometry = [g for g in (_raw_geometry(s) for s in raw_page.get("systems", [])) if g]
        residuals = _nearest_residuals(predicted_geometry, teacher_geometry)

        t = int(scored["teacherSystemCount"])
        p = int(scored["predictedSystemCount"])
        m = int(scored["matchedSystemCount"])
        mechanism = _taxonomy(t, p, m, residuals)
        mechanism_counts[mechanism] = mechanism_counts.get(mechanism, 0) + 1

        centers = [g[0] for g in predicted_geometry]
        gaps = [b-a for a,b in zip(centers, centers[1:])]
        page_rows.append({
            "pageId": pid,
            "teacherSystemCount": t,
            "predictedSystemCount": p,
            "matchedSystemCount": m,
            "falseNegativeCount": t-m,
            "falsePositiveCount": p-m,
            "failureMechanism": mechanism,
            "teacherGeometryParsed": len(teacher_geometry),
            "predictedCenters": [round(x,4) for x in centers],
            "predictedCenterGaps": [round(x,4) for x in gaps],
            "nearestTeacherResiduals": residuals,
            "provenances": [s.get("provenance") for s in raw_page.get("systems", [])],
            "cadenceRecovery": raw_page.get("diagnostics", {}).get("cadenceRecovery", {}),
        })

    hard = [row for row in page_rows if row["falseNegativeCount"] or row["falsePositiveCount"]]
    payload = {
        "schemaVersion": "stage11.v2d.restored-topology-v1_5_1-failure-taxonomy.v1",
        "developmentOnly": True,
        "qualificationEvidence": False,
        "teacherLoadedOnlyAfterInference": True,
        "teacherCoordinatesUsedDuringInference": False,
        "heldOutAccessed": False,
        "pageIdentityUsedDuringInference": False,
        "pageSpecificRulesUsedDuringInference": False,
        "familySpecificRulesUsedDuringInference": False,
        "mechanismCounts": mechanism_counts,
        "aggregate": {
            "teacherSystemCount": score["teacherSystemCount"],
            "predictedSystemCount": score["predictedSystemCount"],
            "matchedSystemCount": score["matchedSystemCount"],
            "teacherSystemRecallAtHalfSpacing": score["teacherSystemRecallAtHalfSpacing"],
            "predictedSystemPrecisionAtHalfSpacing": score["predictedSystemPrecisionAtHalfSpacing"],
            "presentPageCoverage": score["presentPageCoverage"]["rate"],
            "absentPageSpecificity": score["absentPageSpecificity"]["rate"],
        },
        "hardPages": hard,
        "claimBoundary": {
            "successorQualified": False,
            "overallStage11Pass": False,
            "productionPromotionAuthorized": False,
            "stage12EntryAuthorized": False,
            "pr211MergeAuthorized": False,
        },
    }
    Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True)+"\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
