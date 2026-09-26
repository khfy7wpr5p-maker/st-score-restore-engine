"""Private source-only morphology/Hough fusion for Stage 11 V2d staff-line v1.2."""
from __future__ import annotations
import numpy as np
from . import stage11_v2d_staff_line_multisystem_source_detector_v1_1 as parent
from ._stage11_v2d_staff_line_multisystem_source_detector_v1_2_template import (DetectorConfig, _RecoveryCandidate, _source_anchors, _x_overlap, _candidate_duplicate, _duplicate_of_parent, _template_candidates)
StaffSystemDetection = parent.StaffSystemDetection

def _morph_candidates(gray: np.ndarray, parent_detections: list[StaffSystemDetection], cfg: DetectorConfig) -> list[_RecoveryCandidate]:
    parent_cfg = parent.DetectorConfig()
    ink, support, _kernel_lengths = parent._multi_scale_support(gray, parent_cfg)
    rows = parent._morph_rows(support, parent_cfg)
    anchor, width_anchor, _band_x1, _band_x2 = _source_anchors(parent_detections)
    min_spacing = max(2.5, anchor * cfg.recovery_spacing_low_factor)
    max_spacing = min(parent_cfg.max_spacing_px, anchor * cfg.recovery_spacing_high_factor)
    candidates: list[_RecoveryCandidate] = []
    for first_index, first in enumerate(rows):
        if first.x2 - first.x1 < width_anchor * 0.5:
            continue
        for second_index in range(first_index + 1, len(rows)):
            second = rows[second_index]
            spacing_guess = second.y - first.y
            if spacing_guess < min_spacing:
                continue
            if spacing_guess > max_spacing:
                break
            if _x_overlap(first.x1, first.x2, second.x1, second.x2) < 0.25:
                continue
            tolerance = max(1.5, spacing_guess * 0.32)
            selected = [first, second]
            used = {first_index, second_index}
            for line_index in range(2, 5):
                target = first.y + spacing_guess * line_index
                options = []
                for row_index, row in enumerate(rows):
                    if row_index in used or abs(row.y - target) > tolerance:
                        continue
                    if _x_overlap(first.x1, first.x2, row.x1, row.x2) < 0.2:
                        continue
                    options.append((abs(row.y - target), -row.supported_width, row_index, row))
                if not options:
                    selected = []
                    break
                _distance, _negative_support, row_index, row = min(options)
                selected.append(row)
                used.add(row_index)
            if len(selected) != 5:
                continue
            selected.sort(key=lambda row: row.y)
            differences = np.diff(np.asarray([row.y for row in selected], dtype=np.float64))
            spacing = float(np.median(differences))
            if float(np.max(np.abs(differences - spacing))) > max(1.5, spacing * 0.32):
                continue
            spans = [row.x2 - row.x1 for row in selected]
            if float(np.median(spans)) < width_anchor * cfg.recovery_width_factor:
                continue
            x1 = int(np.median([row.x1 for row in selected]))
            x2 = int(np.median([row.x2 for row in selected]))
            if x2 - x1 < width_anchor * cfg.recovery_width_factor:
                continue
            six_line = False
            for target in (selected[0].y - spacing, selected[-1].y + spacing):
                for row in rows:
                    if row in selected or abs(row.y - target) > max(1.5, spacing * 0.38):
                        continue
                    if _x_overlap(x1, x2, row.x1, row.x2) >= 0.4 and row.x2 - row.x1 >= width_anchor * 0.5:
                        six_line = True
                        break
                if six_line:
                    break
            if six_line:
                continue
            vertical_runs = parent._vertical_run_count(ink, y_values=[row.y for row in selected], spacing=spacing, x1=x1, x2=x2)
            if vertical_runs < cfg.recovery_min_vertical_runs:
                continue
            common_strips = sum((all((row.strip_mask[strip_index] for row in selected)) for strip_index in range(parent_cfg.local_spacing_strip_count)))
            if common_strips < 1:
                continue
            regularity = 1.0 - min(1.0, float(np.mean(np.abs(differences - spacing))) / max(1.0, spacing))
            support_score = min(1.0, float(np.mean([row.supported_width for row in selected])) / max(1.0, width_anchor))
            score = 0.65 * regularity + 0.25 * support_score + 0.1 * (common_strips / parent_cfg.local_spacing_strip_count)
            candidates.append(_RecoveryCandidate(score=score, ys=tuple((float(row.y) for row in selected)), spacing=spacing, x1=x1, x2=x2, provenance='source-only:v1.2-parent-anchored-morph-ridge'))
    return candidates

def _hough_candidates(gray: np.ndarray, parent_detections: list[StaffSystemDetection], cfg: DetectorConfig) -> list[_RecoveryCandidate]:
    parent_cfg = parent.DetectorConfig()
    ink = parent._binarize(gray)
    rows, _segment_count = parent._skew_rows(ink, parent_cfg)
    anchor, width_anchor, _band_x1, _band_x2 = _source_anchors(parent_detections)
    min_spacing = max(2.5, anchor * 0.72)
    max_spacing = min(parent_cfg.max_spacing_px, anchor * 1.32)
    candidates: list[_RecoveryCandidate] = []
    for first_index, first in enumerate(rows):
        first_x1 = min((left for left, _right in first.intervals))
        first_x2 = max((right for _left, right in first.intervals))
        if first_x2 - first_x1 < width_anchor * 0.58:
            continue
        for second in rows[first_index + 1:]:
            spacing_guess = second.y - first.y
            if spacing_guess < min_spacing:
                continue
            if spacing_guess > max_spacing:
                break
            second_x1 = min((left for left, _right in second.intervals))
            second_x2 = max((right for _left, right in second.intervals))
            if _x_overlap(first_x1, first_x2, second_x1, second_x2) < 0.3:
                continue
            tolerance = max(1.6, spacing_guess * 0.28)
            selected = [first, second]
            used = {first.row_id, second.row_id}
            for line_index in range(2, 5):
                target = first.y + spacing_guess * line_index
                options = []
                for row in rows:
                    if row.row_id in used or abs(row.y - target) > tolerance:
                        continue
                    row_x1 = min((left for left, _right in row.intervals))
                    row_x2 = max((right for _left, right in row.intervals))
                    if _x_overlap(first_x1, first_x2, row_x1, row_x2) < 0.3:
                        continue
                    options.append((abs(row.y - target), -row.supported_width, row.row_id, row))
                if not options:
                    selected = []
                    break
                _distance, _negative_support, row_id, row = min(options)
                selected.append(row)
                used.add(row_id)
            if len(selected) != 5:
                continue
            selected.sort(key=lambda row: row.y)
            differences = np.diff(np.asarray([row.y for row in selected], dtype=np.float64))
            spacing = float(np.median(differences))
            if float(np.max(np.abs(differences - spacing))) > max(1.6, spacing * 0.28):
                continue
            spans = [max((right for _left, right in row.intervals)) - min((left for left, _right in row.intervals)) for row in selected]
            if float(np.median(spans)) < width_anchor * cfg.hough_width_factor:
                continue
            x1 = int(np.median([min((left for left, _right in row.intervals)) for row in selected]))
            x2 = int(np.median([max((right for _left, right in row.intervals)) for row in selected]))
            if x2 - x1 < width_anchor * cfg.hough_width_factor:
                continue
            six_line = False
            for target in (selected[0].y - spacing, selected[-1].y + spacing):
                for row in rows:
                    if row in selected or abs(row.y - target) > max(1.6, spacing * 0.35):
                        continue
                    row_x1 = min((left for left, _right in row.intervals))
                    row_x2 = max((right for _left, right in row.intervals))
                    if _x_overlap(x1, x2, row_x1, row_x2) >= 0.45 and row_x2 - row_x1 >= width_anchor * 0.55:
                        six_line = True
                        break
                if six_line:
                    break
            if six_line:
                continue
            vertical_runs = parent._vertical_run_count(ink, y_values=[row.y for row in selected], spacing=spacing, x1=x1, x2=x2)
            if vertical_runs < cfg.recovery_min_vertical_runs:
                continue
            regularity = 1.0 - min(1.0, float(np.mean(np.abs(differences - spacing))) / max(1.0, spacing))
            support_score = min(1.0, float(np.mean([row.supported_width for row in selected])) / max(1.0, width_anchor))
            score = 0.65 * regularity + 0.35 * support_score
            candidates.append(_RecoveryCandidate(score=score, ys=tuple((float(row.y) for row in selected)), spacing=spacing, x1=x1, x2=x2, provenance='source-only:v1.2-parent-anchored-skew-segment'))
    return candidates

def _recovery_candidates(gray: np.ndarray, parent_detections: list[StaffSystemDetection], cfg: DetectorConfig) -> tuple[list[_RecoveryCandidate], dict[str, Any]]:
    if not parent_detections:
        return ([], {'recoveryDisabledWithoutSourceSupportedParent': True, 'templateCandidateCount': 0, 'morphCandidateCount': 0, 'houghCandidateCount': 0, 'acceptedRecoveryCount': 0})
    channels = [_template_candidates(gray, parent_detections, cfg), _morph_candidates(gray, parent_detections, cfg), _hough_candidates(gray, parent_detections, cfg)]
    candidates = [item for channel in channels for item in channel]
    candidates.sort(key=lambda item: (-item.score, item.ys[0], item.x1, item.provenance))
    kept: list[_RecoveryCandidate] = []
    rejected_parent_duplicate = 0
    rejected_recovery_duplicate = 0
    for candidate in candidates:
        if _duplicate_of_parent(candidate, parent_detections, cfg):
            rejected_parent_duplicate += 1
            continue
        if any((_candidate_duplicate(candidate, existing, cfg) for existing in kept)):
            rejected_recovery_duplicate += 1
            continue
        kept.append(candidate)
    kept.sort(key=lambda item: (item.ys[0], item.x1, item.spacing, item.provenance))
    return (kept, {'recoveryDisabledWithoutSourceSupportedParent': False, 'templateCandidateCount': len(channels[0]), 'morphCandidateCount': len(channels[1]), 'houghCandidateCount': len(channels[2]), 'rejectedParentDuplicateCount': rejected_parent_duplicate, 'rejectedRecoveryDuplicateCount': rejected_recovery_duplicate, 'acceptedRecoveryCount': len(kept)})
