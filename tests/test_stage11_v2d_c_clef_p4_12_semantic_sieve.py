from __future__ import annotations

import cv2
import numpy as np

from st_score_restore.stage11_v2d_c_clef_p4_12_semantic_sieve import (
    longest_vertical_runs,
    semantic_features,
    sieve_keep,
)


def test_longest_vertical_runs_detects_contiguous_left_stem():
    mask = np.zeros((20, 8), dtype=np.uint8)
    mask[3:18, 1] = 1
    mask[8:12, 5] = 1

    runs = longest_vertical_runs(mask)

    assert runs.shape == (8,)
    assert runs[1] == 15 / 20
    assert runs[5] == 4 / 20


def test_semantic_features_measure_source_pixels_and_left_structure():
    image = np.full((220, 320), 255, dtype=np.uint8)
    # Five staff lines.
    for y in (80, 90, 100, 110, 120):
        cv2.line(image, (20, y), (300, y), 0, 1)
    # C-clef-like left vertical ink and two right lobes.
    cv2.rectangle(image, (66, 70), (73, 132), 0, -1)
    cv2.ellipse(image, (86, 90), (12, 13), 0, 0, 360, 0, 3)
    cv2.ellipse(image, (86, 114), (12, 13), 0, 0, 360, 0, 3)

    proposal = {
        "bbox": [62.0, 68.0, 102.0, 132.0],
        "staffSpacing": 10.0,
        "anchor": "C3",
        "componentGroupXCenter": 82.0,
        "componentFragmentCount": 2,
    }
    staff = {
        "staffLines": [80.0, 90.0, 100.0, 110.0, 120.0],
        "staffSpacing": 10.0,
    }

    features = semantic_features(image, proposal, staff)

    assert features["inkDensity"] > 0.05
    assert features["leftVerticalRunP90"] > 0.05
    assert 0.0 <= features["anchorInkBalance"] <= 1.0
    assert features["componentGroupXFraction"] == 82.0 / 320.0
    assert features["componentFragmentCount"] == 2


def test_sieve_is_source_feature_only_and_requires_all_three_broad_conditions():
    passing = {
        "componentGroupXFraction": 0.20,
        "inkDensity": 0.30,
        "leftVerticalRunP90": 0.15,
    }
    assert sieve_keep(passing) is True

    too_far_right = dict(passing, componentGroupXFraction=0.41)
    too_little_ink = dict(passing, inkDensity=0.21)
    weak_left_structure = dict(passing, leftVerticalRunP90=0.07)

    assert sieve_keep(too_far_right) is False
    assert sieve_keep(too_little_ink) is False
    assert sieve_keep(weak_left_structure) is False


def test_sieve_does_not_require_teacher_subtype_or_semantic_anchor_equality():
    # The geometric anchor is intentionally absent: the sieve consumes only
    # source-derived features and never equates anchor with teacher subtype.
    features = {
        "componentGroupXFraction": 0.30,
        "inkDensity": 0.25,
        "leftVerticalRunP90": 0.10,
    }

    assert sieve_keep(features) is True
