from __future__ import annotations

import numpy as np

from st_score_restore import stage11_v2d_restored_topology_successor_v1_5_3 as detector


def _system(index: int, center: float, *, provenance: str, spacing: float = 6.0):
    x1, x2 = 80, 560
    ys = [center + offset * spacing for offset in (-2, -1, 0, 1, 2)]
    lines = tuple(
        detector.StaffLineDetection(i, float(y), (x1, x2), ((x1, int(round(y)), x2, int(round(y))),))
        for i, y in enumerate(ys, start=1)
    )
    return detector.StaffSystemDetection(
        index, (x1, int(ys[0] - 2), x2, int(ys[-1] + 3)), spacing, 0.9,
        lines, provenance, detector.PARENT_DETECTOR_VERSION,
    )


def _candidate(center: float, *, spacing: float = 6.0):
    ys = tuple(float(center + offset * spacing) for offset in (-2, -1, 0, 1, 2))
    return detector.pixel_parent._PeriodicCandidate(
        ys=ys, spacing=spacing, x1=80, x2=560, score=0.9, median_support_fraction=0.4,
    )


def _center(item) -> float:
    return float(np.mean([line.center_y for line in item.lines]))


def test_replaces_skew_tolerant_geometry() -> None:
    current = _system(1, 100.0, provenance="source-only:v1.2-parent-preserved:source-only:v1.1-skew-tolerant-horizontal-segment")
    result, diagnostics = detector._pixel_backed_replacement(
        [current], [_candidate(100.5)], image_height=320, config=detector.RestoredTopologyConfig()
    )
    assert diagnostics["replacementCount"] == 1
    assert diagnostics["systemCountPreserved"] is True
    assert diagnostics["horizontalTemplateReplacementAllowed"] is False
    assert abs(_center(result[0]) - 100.5) < 1e-9


def test_does_not_replace_horizontal_template_geometry() -> None:
    current = _system(1, 100.0, provenance="source-only:v1.2-parent-anchored-horizontal-template")
    result, diagnostics = detector._pixel_backed_replacement(
        [current], [_candidate(100.5)], image_height=320, config=detector.RestoredTopologyConfig()
    )
    assert diagnostics["replacementCount"] == 0
    assert result[0].provenance == current.provenance
    assert abs(_center(result[0]) - 100.0) < 1e-9


def test_never_adds_or_removes_systems() -> None:
    result, diagnostics = detector._pixel_backed_replacement(
        [], [_candidate(100.0)], image_height=320, config=detector.RestoredTopologyConfig()
    )
    assert result == []
    assert diagnostics["addedSystemCount"] == 0
    assert diagnostics["removedSystemCount"] == 0
    assert diagnostics["systemCountPreserved"] is True


def test_full_detector_is_deterministic_and_teacher_blind() -> None:
    image = np.full((320, 640), 255, dtype=np.uint8)
    first, first_diag = detector.detect_staff_systems_with_diagnostics(image)
    second, second_diag = detector.detect_staff_systems_with_diagnostics(image)
    assert [item.as_dict() for item in first] == [item.as_dict() for item in second]
    assert first_diag == second_diag
    assert first_diag["pixelBackedReplacement"]["systemCountPreserved"] is True
    assert first_diag["teacherCoordinatesUsed"] is False
    assert first_diag["teacherMasksUsed"] is False
    assert first_diag["heldOutAccessed"] is False
    assert first_diag["qualificationDataAccessed"] is False
    assert first_diag["pageIdentityUsed"] is False
    assert first_diag["pageSpecificRulesUsed"] is False
    assert first_diag["familySpecificRulesUsed"] is False
