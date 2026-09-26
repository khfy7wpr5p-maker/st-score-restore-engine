"""Private source-only template recovery primitives for Stage 11 V2d staff-line v1.2."""
from __future__ import annotations
from dataclasses import dataclass
import cv2
import numpy as np
from . import stage11_v2d_staff_line_multisystem_source_detector_v1_1 as parent
StaffSystemDetection = parent.StaffSystemDetection

class RecoveryConfigError(ValueError):
    pass

def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RecoveryConfigError(message)

@dataclass(frozen=True)
class DetectorConfig:
    template_spacing_low_factor: float = 0.78
    template_spacing_high_factor: float = 1.22
    template_spacing_steps: int = 7
    template_peak_floor: float = 0.06
    template_median_support_floor: float = 0.1
    template_min_line_support_floor: float = 0.045
    template_six_line_relative_support: float = 0.7
    recovery_min_vertical_runs: int = 2
    recovery_spacing_low_factor: float = 0.68
    recovery_spacing_high_factor: float = 1.38
    recovery_width_factor: float = 0.58
    hough_width_factor: float = 0.65
    recovery_match_tolerance_fraction: float = 0.45
    recovery_overlap_fraction: float = 0.2
    horizontal_open_fractions: tuple[float, ...] = (0.008, 0.012, 0.018, 0.028)

    def validate(self) -> None:
        _require(0.5 <= self.template_spacing_low_factor < 1.0, 'invalid template low spacing factor')
        _require(1.0 < self.template_spacing_high_factor <= 1.6, 'invalid template high spacing factor')
        _require(3 <= self.template_spacing_steps <= 15, 'invalid template spacing steps')
        _require(0.01 <= self.template_peak_floor <= 0.3, 'invalid template peak floor')
        _require(0.02 <= self.template_median_support_floor <= 0.5, 'invalid template support floor')
        _require(0.01 <= self.template_min_line_support_floor <= 0.3, 'invalid template line floor')
        _require(0.4 <= self.template_six_line_relative_support <= 0.95, 'invalid six-line support ratio')
        _require(1 <= self.recovery_min_vertical_runs <= 10, 'invalid vertical topology floor')
        _require(0.5 <= self.recovery_spacing_low_factor < 1.0, 'invalid recovery low spacing factor')
        _require(1.0 < self.recovery_spacing_high_factor <= 1.7, 'invalid recovery high spacing factor')
        _require(0.4 <= self.recovery_width_factor <= 0.9, 'invalid recovery width factor')
        _require(self.recovery_width_factor <= self.hough_width_factor <= 0.95, 'invalid hough width factor')
        _require(0.2 <= self.recovery_match_tolerance_fraction <= 0.6, 'invalid match tolerance')
        _require(0.1 <= self.recovery_overlap_fraction <= 0.6, 'invalid overlap floor')
        _require(len(self.horizontal_open_fractions) >= 2, 'multiple horizontal support scales required')
        _require(all((0.004 <= x <= 0.08 for x in self.horizontal_open_fractions)), 'invalid horizontal support scale')

@dataclass(frozen=True)
class _RecoveryCandidate:
    score: float
    ys: tuple[float, float, float, float, float]
    spacing: float
    x1: int
    x2: int
    provenance: str

def _source_anchors(parent_detections: list[StaffSystemDetection]) -> tuple[float, float, int, int]:
    spacings = np.asarray([item.staff_spacing for item in parent_detections], dtype=np.float64)
    spacing = float(np.median(spacings))
    compact = spacings[(spacings >= max(2.5, spacing * 0.55)) & (spacings <= spacing * 1.5)]
    if compact.size:
        spacing = float(np.median(compact))
    widths = np.asarray([item.bbox[2] - item.bbox[0] for item in parent_detections], dtype=np.float64)
    width = float(np.median(widths))
    x1 = int(np.median([item.bbox[0] for item in parent_detections]))
    x2 = int(np.median([item.bbox[2] for item in parent_detections]))
    return (spacing, width, x1, x2)

def _x_overlap(a1: int, a2: int, b1: int, b2: int) -> float:
    overlap = max(0, min(a2, b2) - max(a1, b1))
    return overlap / max(1, min(a2 - a1, b2 - b1))

def _candidate_duplicate(a: _RecoveryCandidate, b: _RecoveryCandidate, cfg: DetectorConfig) -> bool:
    ys_a = np.asarray(a.ys, dtype=np.float64)
    ys_b = np.asarray(b.ys, dtype=np.float64)
    tolerance = max(1.5, min(a.spacing, b.spacing) * cfg.recovery_match_tolerance_fraction)
    matches = int(np.sum(np.min(np.abs(ys_a[:, None] - ys_b[None, :]), axis=1) <= tolerance))
    return matches >= 3 and _x_overlap(a.x1, a.x2, b.x1, b.x2) >= cfg.recovery_overlap_fraction

def _duplicate_of_parent(candidate: _RecoveryCandidate, detections: list[StaffSystemDetection], cfg: DetectorConfig) -> bool:
    ys = np.asarray(candidate.ys, dtype=np.float64)
    for item in detections:
        other = np.asarray([line.center_y for line in item.lines], dtype=np.float64)
        tolerance = max(1.5, min(candidate.spacing, item.staff_spacing) * cfg.recovery_match_tolerance_fraction)
        matches = int(np.sum(np.min(np.abs(ys[:, None] - other[None, :]), axis=1) <= tolerance))
        if matches >= 3 and _x_overlap(candidate.x1, candidate.x2, item.bbox[0], item.bbox[2]) >= cfg.recovery_overlap_fraction:
            return True
    return False

def _horizontal_support(ink: np.ndarray, fractions: tuple[float, ...]) -> np.ndarray:
    _height, width = ink.shape
    close_len = max(3, int(round(width * 0.005)))
    work = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (close_len, 1)))
    outputs: list[np.ndarray] = []
    for fraction in fractions:
        kernel_len = max(7, int(round(width * fraction)))
        if kernel_len % 2 == 0:
            kernel_len += 1
        outputs.append(cv2.morphologyEx(work, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))))
    return np.maximum.reduce(outputs)

def _template_candidates(gray: np.ndarray, parent_detections: list[StaffSystemDetection], cfg: DetectorConfig) -> list[_RecoveryCandidate]:
    height, width = gray.shape
    anchor, width_anchor, band_x1, band_x2 = _source_anchors(parent_detections)
    if band_x2 - band_x1 < width_anchor * 0.8:
        centers = [(item.bbox[0] + item.bbox[2]) / 2.0 for item in parent_detections]
        center = int(np.median(centers))
        band_x1 = max(0, int(round(center - width_anchor / 2.0)))
        band_x2 = min(width, int(round(center + width_anchor / 2.0)))
    ink = parent._binarize(gray)
    support = _horizontal_support(ink, cfg.horizontal_open_fractions)
    band = support[:, band_x1:band_x2]
    row_fraction = np.count_nonzero(band, axis=1).astype(np.float64) / max(1, band_x2 - band_x1)
    smooth = np.convolve(row_fraction, np.asarray([0.2, 0.6, 0.2], dtype=np.float64), mode='same')
    threshold = max(cfg.template_peak_floor, float(np.percentile(smooth, 70)) * 0.55)
    peaks = [y for y in range(1, height - 1) if smooth[y] >= threshold and smooth[y] >= smooth[y - 1] and (smooth[y] >= smooth[y + 1])]
    kept_peaks: list[int] = []
    for y in sorted(peaks, key=lambda value: (-smooth[value], value)):
        if any((abs(y - existing) <= 1 for existing in kept_peaks)):
            continue
        kept_peaks.append(y)
    peaks = sorted(kept_peaks)
    candidates: list[_RecoveryCandidate] = []
    for y0 in peaks:
        for spacing_guess in np.linspace(anchor * cfg.template_spacing_low_factor, anchor * cfg.template_spacing_high_factor, cfg.template_spacing_steps):
            tolerance = max(1.4, spacing_guess * 0.32)
            selected = [y0]
            used = {y0}
            for line_index in range(1, 5):
                target = y0 + line_index * spacing_guess
                options = [y for y in peaks if y not in used and abs(y - target) <= tolerance]
                if not options:
                    selected = []
                    break
                chosen = max(options, key=lambda y: (smooth[y], -abs(y - target)))
                selected.append(chosen)
                used.add(chosen)
            if len(selected) != 5:
                continue
            selected.sort()
            differences = np.diff(np.asarray(selected, dtype=np.float64))
            spacing = float(np.median(differences))
            if float(np.max(np.abs(differences - spacing))) > max(1.5, spacing * 0.33):
                continue
            values = [float(smooth[y]) for y in selected]
            if float(np.median(values)) < max(cfg.template_median_support_floor, threshold * 1.25):
                continue
            if min(values) < max(cfg.template_min_line_support_floor, threshold * 0.65):
                continue
            six_line = False
            for target in (selected[0] - spacing, selected[-1] + spacing):
                low = max(0, int(round(target - max(1.5, spacing * 0.35))))
                high = min(height, int(round(target + max(1.5, spacing * 0.35))) + 1)
                if low < high and float(np.max(smooth[low:high])) >= float(np.median(values)) * cfg.template_six_line_relative_support:
                    six_line = True
                    break
            if six_line:
                continue
            vertical_runs = parent._vertical_run_count(ink, y_values=selected, spacing=spacing, x1=band_x1, x2=band_x2)
            if vertical_runs < cfg.recovery_min_vertical_runs:
                continue
            regularity = 1.0 - min(1.0, float(np.mean(np.abs(differences - spacing))) / max(1.0, spacing))
            support_score = min(1.0, float(np.mean(values)) / 0.45)
            score = 0.55 * regularity + 0.45 * support_score
            candidates.append(_RecoveryCandidate(score=score, ys=tuple((float(y) for y in selected)), spacing=spacing, x1=band_x1, x2=band_x2, provenance='source-only:v1.2-parent-anchored-horizontal-template'))
    return candidates
