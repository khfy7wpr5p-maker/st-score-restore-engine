from __future__ import annotations

import numpy as np

from st_score_restore import stage11_v2d_restored_topology_successor_v1_5_2 as detector


def _system(
    index: int,
    center: float,
    *,
    spacing: float = 6.0,
    x1: int = 80,
    x2: int = 560,
    provenance: str = "source-only:v1.2-parent-anchored-horizontal-template",
):
    ys = [center + offset * spacing for offset in (-2, -1, 0, 1, 2)]
    lines = tuple(
        detector.StaffLineDetection(i, float(y), (x1, x2), ((x1, int(round(y)), x2, int(round(y))),))
        for i, y in enumerate(ys, start=1)
    )
    return detector.StaffSystemDetection(
        index,
        (x1, int(ys[0] - 2), x2, int(ys[-1] + 3)),
        spacing,
        0.9,
        lines,
        provenance,
        detector.PARENT_DETECTOR_VERSION,
    )


def _candidate(center: float, *, spacing: float = 6.0, x1: int = 80, x2: int = 560, score: float = 0.9):
    ys = tuple(float(center + offset * spacing) for offset in (-2, -1, 0, 1, 2))
    return detector.pixel_parent._PeriodicCandidate(
        ys=ys,
        spacing=float(spacing),
        x1=x1,
        x2=x2,
        score=float(score),
        median_support_fraction=0.4,
    )


def _center(item) -> float:
    return float(np.mean([line.center_y for line in item.lines]))


def test_replaces_weak_geometry_with_duplicate_pixel_periodic_evidence() -> None:
    current = _system(1, 100.0)
    candidate = _candidate(100.5)
    result, diagnostics = detector._pixel_backed_replacement(
        [current],
        [candidate],
        image_height=320,
        config=detector.RestoredTopologyConfig(),
    )
    assert len(result) == 1
    assert diagnostics["systemCountPreserved"] is True
    assert diagnostics["addedSystemCount"] == 0
    assert diagnostics["removedSystemCount"] == 0
    assert diagnostics["replacementCount"] == 1
    assert abs(_center(result[0]) - 100.5) < 1e-9
    assert result[0].provenance == "restored-only:v1.5.2-pixel-backed-replacement"


def test_does_not_replace_source_topology_anchor() -> None:
    current = _system(
        1,
        100.0,
        provenance="source-only:v1.2-parent-preserved:source-only:v1-compatibility+v1.1-local-spacing-topology",
    )
    result, diagnostics = detector._pixel_backed_replacement(
        [current],
        [_candidate(100.5)],
        image_height=320,
        config=detector.RestoredTopologyConfig(),
    )
    assert len(result) == 1
    assert diagnostics["replacementCount"] == 0
    assert result[0].provenance == current.provenance
    assert abs(_center(result[0]) - 100.0) < 1e-9


def test_never_adds_system_when_parent_is_empty() -> None:
    result, diagnostics = detector._pixel_backed_replacement(
        [],
        [_candidate(100.0), _candidate(180.0)],
        image_height=320,
        config=detector.RestoredTopologyConfig(),
    )
    assert result == []
    assert diagnostics["parentSystemCount"] == 0
    assert diagnostics["periodicCandidateCount"] == 2
    assert diagnostics["replacementCount"] == 0
    assert diagnostics["finalSystemCount"] == 0
    assert diagnostics["systemCountPreserved"] is True


def test_does_not_replace_already_pixel_periodic_detection() -> None:
    current = _system(
        1,
        100.0,
        provenance="restored-only:v1.5-horizontal-periodicity-five-line",
    )
    result, diagnostics = detector._pixel_backed_replacement(
        [current],
        [_candidate(100.5)],
        image_height=320,
        config=detector.RestoredTopologyConfig(),
    )
    assert diagnostics["replacementCount"] == 0
    assert result[0].provenance == current.provenance


def test_one_to_one_matching_and_count_invariance() -> None:
    parent = [_system(1, 100.0), _system(2, 180.0)]
    candidates = [_candidate(100.5), _candidate(180.5)]
    result, diagnostics = detector._pixel_backed_replacement(
        parent,
        candidates,
        image_height=320,
        config=detector.RestoredTopologyConfig(),
    )
    assert len(result) == len(parent)
    assert diagnostics["replacementCount"] == 2
    assert diagnostics["systemCountPreserved"] is True
    assert [_center(item) for item in result] == [100.5, 180.5]


def test_full_detector_is_deterministic_count_safe_and_teacher_blind() -> None:
    image = np.full((320, 640), 255, dtype=np.uint8)
    first, first_diag = detector.detect_staff_systems_with_diagnostics(image)
    second, second_diag = detector.detect_staff_systems_with_diagnostics(image)
    assert [item.as_dict() for item in first] == [item.as_dict() for item in second]
    assert first_diag == second_diag
    assert first_diag["pixelBackedReplacement"]["systemCountPreserved"] is True
    assert first_diag["pixelBackedReplacement"]["addedSystemCount"] == 0
    assert first_diag["pixelBackedReplacement"]["removedSystemCount"] == 0
    assert first_diag["teacherCoordinatesUsed"] is False
    assert first_diag["teacherMasksUsed"] is False
    assert first_diag["heldOutAccessed"] is False
    assert first_diag["qualificationDataAccessed"] is False
    assert first_diag["pageIdentityUsed"] is False
    assert first_diag["pageSpecificRulesUsed"] is False
    assert first_diag["familySpecificRulesUsed"] is False
