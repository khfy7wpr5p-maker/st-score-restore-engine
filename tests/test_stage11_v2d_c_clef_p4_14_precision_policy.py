from __future__ import annotations

from copy import deepcopy

from st_score_restore.stage11_v2d_c_clef_p4_14_precision_policy import (
    candidate_score,
    select_precision_candidates,
)


def _record(*, proposal_index: int, staff_index: int = 0, x1: float = 10.0, x2: float = 30.0, **feature_overrides):
    features = {
        "inkDensity": 0.34,
        "cleanInkDensity": 0.27,
        "leftMidDensity": 0.24,
        "leftBottomDensity": 0.22,
        "leftVerticalRunP90": 0.34,
        "leftVerticalRunMax": 0.58,
        "anchorInkBalance": 0.86,
    }
    features.update(feature_overrides)
    return {
        "proposalIndex": proposal_index,
        "bbox": [x1, 20.0, x2, 90.0],
        "staffIndex": staff_index,
        "staffSpacing": 10.0,
        "anchor": "C3",
        "anchorRank": 1,
        "xOffsetStaffSpaces": 0.05,
        "componentGroupIndex": proposal_index,
        "features": features,
    }


def test_candidate_score_prefers_strong_source_structure_and_is_bounded():
    strong = _record(proposal_index=1)
    weak = _record(
        proposal_index=2,
        cleanInkDensity=0.07,
        leftMidDensity=0.03,
        leftBottomDensity=0.02,
        leftVerticalRunP90=0.05,
        leftVerticalRunMax=0.08,
        anchorInkBalance=0.10,
    )
    weak["xOffsetStaffSpaces"] = 1.4
    weak["anchorRank"] = 2

    strong_score = candidate_score(strong)
    weak_score = candidate_score(weak)

    assert 0.0 <= weak_score <= 1.0
    assert 0.0 <= strong_score <= 1.0
    assert strong_score > weak_score


def test_teacher_metadata_cannot_change_inference_score_or_selection():
    base = _record(proposal_index=1)
    contaminated = deepcopy(base)
    contaminated["teacherLabel"] = "C1"
    contaminated["teacherBox"] = [1, 2, 3, 4]
    contaminated["isTeacherMatch"] = True

    assert candidate_score(base) == candidate_score(contaminated)
    assert select_precision_candidates([base]) == select_precision_candidates([contaminated])


def test_overlapping_duplicate_is_suppressed_but_mid_staff_clef_change_is_preserved():
    first = _record(proposal_index=1, x1=10.0, x2=30.0)
    duplicate = _record(proposal_index=2, x1=11.0, x2=31.0, anchorInkBalance=0.60)
    later_change = _record(proposal_index=3, x1=90.0, x2=112.0)

    selected = select_precision_candidates([duplicate, later_change, first], minimum_score=0.45)

    assert [item["proposalIndex"] for item in selected] == [1, 3]


def test_selection_is_deterministic_under_input_order():
    records = [
        _record(proposal_index=3, staff_index=1, x1=80.0, x2=100.0),
        _record(proposal_index=1, staff_index=0, x1=10.0, x2=30.0),
        _record(proposal_index=2, staff_index=0, x1=11.0, x2=31.0, anchorInkBalance=0.60),
    ]

    forward = select_precision_candidates(records, minimum_score=0.45)
    reverse = select_precision_candidates(list(reversed(records)), minimum_score=0.45)

    assert forward == reverse


def test_low_confidence_candidate_abstains():
    weak = _record(
        proposal_index=9,
        cleanInkDensity=0.04,
        leftMidDensity=0.01,
        leftBottomDensity=0.01,
        leftVerticalRunP90=0.02,
        leftVerticalRunMax=0.04,
        anchorInkBalance=0.03,
    )
    weak["xOffsetStaffSpaces"] = 1.8
    weak["anchorRank"] = 3

    assert select_precision_candidates([weak], minimum_score=0.45) == []
