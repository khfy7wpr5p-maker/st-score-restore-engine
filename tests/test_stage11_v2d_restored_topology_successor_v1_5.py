from __future__ import annotations

import cv2
import numpy as np
import pytest

from st_score_restore import stage11_v2d_restored_topology_successor_v1_5 as detector


def _canvas(height: int = 320, width: int = 640) -> np.ndarray:
    return np.full((height, width), 255, dtype=np.uint8)


def _draw_lines(image: np.ndarray, ys: list[int], *, x1: int = 72, x2: int = 568) -> None:
    for y in ys:
        cv2.line(image, (x1, y), (x2, y), 0, 1, cv2.LINE_8)


def test_periodicity_recovers_standard_five_line_staff() -> None:
    image = _canvas()
    expected = [80, 86, 92, 98, 104]
    _draw_lines(image, expected)
    candidates, diagnostics = detector._periodic_candidates(image, detector.RestoredTopologyConfig())
    assert diagnostics["rowEvidenceCount"] >= 5
    assert any(max(abs(a - b) for a, b in zip(candidate.ys, expected)) <= 1.0 for candidate in candidates)


def test_periodicity_rejects_six_line_tab_like_control() -> None:
    image = _canvas()
    _draw_lines(image, [120, 126, 132, 138, 144, 150])
    candidates, _diagnostics = detector._periodic_candidates(image, detector.RestoredTopologyConfig())
    assert candidates == []


def test_periodicity_rejects_irregular_horizontal_graphics() -> None:
    image = _canvas()
    _draw_lines(image, [50, 67, 91, 128, 181])
    candidates, _diagnostics = detector._periodic_candidates(image, detector.RestoredTopologyConfig())
    assert candidates == []


def test_full_detector_is_deterministic_and_teacher_blind() -> None:
    image = _canvas()
    _draw_lines(image, [80, 86, 92, 98, 104])
    first, first_diag = detector.detect_staff_systems_with_diagnostics(image)
    second, second_diag = detector.detect_staff_systems_with_diagnostics(image)
    assert [item.as_dict() for item in first] == [item.as_dict() for item in second]
    assert first_diag == second_diag
    assert first_diag["teacherCoordinatesUsed"] is False
    assert first_diag["heldOutAccessed"] is False
    assert first_diag["pageIdentityUsed"] is False
    assert first_diag["pageSpecificRulesUsed"] is False
    assert first_diag["familySpecificRulesUsed"] is False


def test_config_rejects_invalid_spacing_bounds() -> None:
    with pytest.raises(detector.RestoredTopologySuccessorV15Error):
        detector.RestoredTopologyConfig(min_staff_spacing_px=20.0, max_staff_spacing_px=10.0).validate()
