from __future__ import annotations

import cv2
import numpy as np

from st_score_restore.stage11_v2d_c_clef_p4_10_localizer_v3_2_candidate_ceiling import (
    source_spacing_hint_v32,
)


def test_source_spacing_hint_v32_recovers_scale_from_horizontal_staff_lines():
    image = np.full((800, 1200), 255, dtype=np.uint8)
    for staff_top in (120, 350, 580):
        for line_index in range(5):
            y = staff_top + line_index * 16
            cv2.line(image, (100, y), (1100, y), 0, 2)

    hint, diagnostics = source_spacing_hint_v32(image)

    assert hint == 16.0
    assert diagnostics["status"] == "SOURCE_PROJECTION_HINT"
    assert diagnostics["modeCount"] >= 8


def test_source_spacing_hint_v32_abstains_without_supported_horizontal_runs():
    image = np.full((600, 800), 255, dtype=np.uint8)

    hint, diagnostics = source_spacing_hint_v32(image)

    assert hint is None
    assert diagnostics["status"] == "INSUFFICIENT_HORIZONTAL_RUNS"
