from __future__ import annotations

import cv2
import numpy as np

from st_score_restore.stage11_v2d_c_clef_p4_11_glyph_proposal_generator import (
    generate_page_proposals,
    greedy_match,
    reconstruct_staffs_from_frozen_candidates,
)


def _frozen_staff_candidates(spacing: float = 10.0, y0: float = 100.0):
    anchor_line = {"C1": 4, "C3": 2, "C4": 1}
    candidates = []
    for anchor, line_index in anchor_line.items():
        y_center = y0 + line_index * spacing
        for offset in (-1.0, 0.0, 1.25):
            candidates.append(
                {
                    "staffIndex": 0,
                    "staffSpacing": spacing,
                    "staffSource": "p45",
                    "anchor": anchor,
                    "sizeTag": "base",
                    "xOffsetStaffSpaces": offset,
                    "bbox": [50.0, y_center - 25.0, 82.0, y_center + 25.0],
                }
            )
    return candidates


def test_reconstruct_staffs_from_frozen_candidates_recovers_five_lines():
    staffs = reconstruct_staffs_from_frozen_candidates(
        {"candidates": _frozen_staff_candidates()}
    )

    assert len(staffs) == 1
    assert staffs[0]["staffIndex"] == 0
    assert staffs[0]["staffSpacing"] == 10.0
    assert staffs[0]["staffLines"] == [100.0, 110.0, 120.0, 130.0, 140.0]
    assert staffs[0]["staffSource"] == "p45"


def test_generate_page_proposals_uses_source_component_centres_and_two_anchor_cap():
    image = np.full((300, 600), 255, dtype=np.uint8)
    for y in (100, 110, 120, 130, 140):
        cv2.line(image, (20, y), (580, y), 0, 1)
    # Glyph-like source ink in the left proposal region.
    cv2.rectangle(image, (80, 92), (96, 148), 0, -1)

    staffs = reconstruct_staffs_from_frozen_candidates(
        {"candidates": _frozen_staff_candidates()}
    )
    proposals, diagnostics = generate_page_proposals(image, staffs)

    assert diagnostics["staffCount"] == 1
    assert diagnostics["componentGroupCount"] == 1
    assert len(proposals) > 0
    assert len({item["anchor"] for item in proposals}) <= 2
    assert all(item["proposalSource"] == "source_component_center_nominal_geometry" for item in proposals)
    assert all(item["componentGroupXCenter"] < 0.45 * image.shape[1] for item in proposals)


def test_generate_page_proposals_ignores_right_side_component_groups():
    image = np.full((300, 600), 255, dtype=np.uint8)
    for y in (100, 110, 120, 130, 140):
        cv2.line(image, (20, y), (580, y), 0, 1)
    # This source component is beyond the frozen 45% proposal region.
    cv2.rectangle(image, (500, 92), (516, 148), 0, -1)

    staffs = reconstruct_staffs_from_frozen_candidates(
        {"candidates": _frozen_staff_candidates()}
    )
    proposals, diagnostics = generate_page_proposals(image, staffs)

    assert diagnostics["componentGroupCount"] == 0
    assert proposals == []


def test_greedy_match_never_treats_geometric_anchor_as_teacher_subtype():
    candidates = [
        {
            "bbox": [10.0, 20.0, 40.0, 70.0],
            "anchor": "C3",
        }
    ]
    teacher_boxes = [
        {
            "x": 10,
            "y": 20,
            "w": 30,
            "h": 50,
            "label": "C1",
        }
    ]

    matches = greedy_match(candidates, teacher_boxes)

    assert len(matches) == 1
    assert matches[0][2] == 1.0
