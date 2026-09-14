from __future__ import annotations

import numpy as np
import pytest

from st_score_restore import stage11_v2d_restored_topology_successor_v1_5_1 as detector


def _system(index: int, center: float, *, spacing: float = 6.0, x1: int = 80, x2: int = 560):
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
        "synthetic-parent",
        detector.PARENT_DETECTOR_VERSION,
    )


def test_cadence_recovers_only_missing_interior_slot() -> None:
    # Observed cadence is 80 px. Slot 3 (center=340) is missing, while three
    # direct 80 px gaps establish the cadence strongly enough for recovery.
    parent = [
        _system(1, 100),
        _system(2, 180),
        _system(3, 260),
        _system(4, 420),
        _system(5, 500),
    ]
    recovered, diagnostics = detector._interior_cadence_recovery(
        parent,
        image_height=640,
        image_width=640,
        config=detector.CadenceRecoveryConfig(),
    )
    centers = [round(float(np.mean([line.center_y for line in item.lines])), 6) for item in recovered]
    assert diagnostics["cadenceAccepted"] is True
    assert diagnostics["edgeExtrapolationPerformed"] is False
    assert diagnostics["addedInteriorSystemCount"] == 1
    assert any(abs(center - 340.0) < 1e-6 for center in centers)
    assert len(recovered) == 6


def test_cadence_does_not_invent_edges_when_sequence_is_complete() -> None:
    parent = [_system(i + 1, center) for i, center in enumerate([100, 250, 400, 550])]
    recovered, diagnostics = detector._interior_cadence_recovery(
        parent,
        image_height=700,
        image_width=640,
        config=detector.CadenceRecoveryConfig(),
    )
    assert diagnostics["cadenceAccepted"] is True
    assert diagnostics["addedInteriorSystemCount"] == 0
    assert diagnostics["edgeExtrapolationPerformed"] is False
    assert len(recovered) == len(parent)


def test_cadence_abstains_when_too_few_systems() -> None:
    parent = [_system(i + 1, center) for i, center in enumerate([100, 180, 260])]
    recovered, diagnostics = detector._interior_cadence_recovery(
        parent,
        image_height=400,
        image_width=640,
        config=detector.CadenceRecoveryConfig(),
    )
    assert diagnostics["cadenceAccepted"] is False
    assert diagnostics["addedInteriorSystemCount"] == 0
    assert len(recovered) == len(parent)


def test_full_detector_is_deterministic_and_teacher_blind() -> None:
    image = np.full((320, 640), 255, dtype=np.uint8)
    first, first_diag = detector.detect_staff_systems_with_diagnostics(image)
    second, second_diag = detector.detect_staff_systems_with_diagnostics(image)
    assert [item.as_dict() for item in first] == [item.as_dict() for item in second]
    assert first_diag == second_diag
    assert first_diag["teacherCoordinatesUsed"] is False
    assert first_diag["heldOutAccessed"] is False
    assert first_diag["pageIdentityUsed"] is False
    assert first_diag["pageSpecificRulesUsed"] is False
    assert first_diag["familySpecificRulesUsed"] is False
    assert first_diag["edgeExtrapolationUsed"] is False


def test_config_rejects_invalid_cadence_bounds() -> None:
    with pytest.raises(detector.RestoredTopologySuccessorV151Error):
        detector.CadenceRecoveryConfig(min_gap_px=200.0, max_gap_px=100.0).validate()
