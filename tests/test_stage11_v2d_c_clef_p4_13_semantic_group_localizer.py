from __future__ import annotations

import cv2
import numpy as np

from st_score_restore.stage11_v2d_c_clef_p4_13_semantic_group_localizer import (
    _bbox_gap,
    refine_bbox_to_source_ink,
    semantic_confidence_score,
)


def _features(**overrides):
    values = {
        "inkDensity": 0.32,
        "cleanInkDensity": 0.24,
        "leftMidDensity": 0.24,
        "leftBottomDensity": 0.22,
        "leftVerticalRunP90": 0.30,
        "leftVerticalRunMax": 0.55,
        "anchorInkBalance": 0.85,
    }
    values.update(overrides)
    return values


def _proposal(**overrides):
    values = {
        "bbox": [58.0, 66.0, 104.0, 136.0],
        "staffSpacing": 10.0,
        "staffIndex": 0,
        "anchor": "C3",
        "anchorRank": 1,
        "xOffsetStaffSpaces": 0.0,
        "componentGroupIndex": 3,
        "componentGroupXCenter": 76.0,
        "componentGroupYCenter": 101.0,
    }
    values.update(overrides)
    return values


def test_semantic_confidence_is_bounded_and_prefers_stronger_source_structure():
    strong, strong_parts = semantic_confidence_score(_features(), _proposal())
    weak, weak_parts = semantic_confidence_score(
        _features(
            cleanInkDensity=0.08,
            leftMidDensity=0.04,
            leftBottomDensity=0.01,
            leftVerticalRunP90=0.09,
            leftVerticalRunMax=0.12,
            anchorInkBalance=0.10,
        ),
        _proposal(xOffsetStaffSpaces=1.25, anchorRank=2),
    )

    assert 0.0 <= weak <= 1.0
    assert 0.0 <= strong <= 1.0
    assert strong > weak
    assert set(strong_parts) == set(weak_parts)
    assert "anchorInkBalance" in strong_parts


def test_semantic_confidence_does_not_require_teacher_label_or_coordinates():
    score, parts = semantic_confidence_score(_features(), _proposal())

    assert score > 0.0
    assert parts["xOffsetAlignment"] == 1.0


def test_bbox_gap_is_zero_for_overlap_and_positive_for_separation():
    assert _bbox_gap([0, 0, 10, 10], [5, 5, 12, 12]) == 0.0
    assert _bbox_gap([0, 0, 10, 10], [13, 14, 20, 22]) == 5.0


def test_refine_bbox_uses_non_staff_source_ink_near_component_group_center():
    image = np.full((220, 320), 255, dtype=np.uint8)
    for y in (80, 90, 100, 110, 120):
        cv2.line(image, (20, y), (300, y), 0, 1)

    # C-clef-like source ink. The representative proposal is intentionally
    # wider than this source support so refinement has useful work to do.
    cv2.rectangle(image, (67, 72), (73, 130), 0, -1)
    cv2.ellipse(image, (85, 90), (11, 12), 0, 0, 360, 0, 3)
    cv2.ellipse(image, (85, 113), (11, 12), 0, 0, 360, 0, 3)

    proposal = _proposal()
    staff = {
        "staffLines": [80.0, 90.0, 100.0, 110.0, 120.0],
        "staffSpacing": 10.0,
    }

    refined = refine_bbox_to_source_ink(image, proposal, staff)

    assert refined["supportFound"] is True
    assert refined["selectedComponentCount"] >= 1
    assert refined["supportPixelArea"] > 0
    x1, y1, x2, y2 = refined["bbox"]
    assert x1 >= 0.0 and y1 >= 0.0
    assert x2 <= image.shape[1] and y2 <= image.shape[0]
    assert x2 > x1 and y2 > y1


def test_refine_bbox_falls_back_without_nearby_non_staff_support():
    image = np.full((220, 320), 255, dtype=np.uint8)
    proposal = _proposal()
    staff = {
        "staffLines": [80.0, 90.0, 100.0, 110.0, 120.0],
        "staffSpacing": 10.0,
    }

    refined = refine_bbox_to_source_ink(image, proposal, staff)

    assert refined["supportFound"] is False
    assert refined["bbox"] == proposal["bbox"]
    assert refined["selectedComponentCount"] == 0
