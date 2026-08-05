"""Conservative photometric operations that preserve protected notation pixels."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from .restoration_geometry import operation_record
from .restoration_types import RestorationConfig


def _protect(
    candidate: np.ndarray,
    aligned: np.ndarray,
    mask: np.ndarray,
) -> np.ndarray:
    output = candidate.copy()
    output[mask] = np.minimum(output[mask], aligned[mask])
    return output


def normalize_illumination(
    gray: np.ndarray,
    aligned: np.ndarray,
    mask: np.ndarray,
    config: RestorationConfig,
) -> tuple[np.ndarray, dict[str, Any]]:
    before = gray
    applied = False
    protected_fraction = np.count_nonzero(mask) / mask.size
    if config.illumination_enabled and protected_fraction <= config.max_protected_fraction:
        size = max(15, round(min(gray.shape) * config.illumination_kernel_fraction))
        size += 1 - size % 2
        background = cv2.GaussianBlur(gray, (size, size), 0)
        normalized = cv2.divide(gray, np.maximum(background, 1), scale=245)
        candidate = cv2.addWeighted(
            gray,
            1 - config.illumination_strength,
            normalized,
            config.illumination_strength,
            0,
        )
        gray = _protect(candidate, aligned, mask)
        applied = True
    return gray, operation_record(
        "illumination_normalization",
        config.illumination_enabled,
        applied,
        {
            "kernelFraction": config.illumination_kernel_fraction,
            "strength": config.illumination_strength,
        },
        {"protectedFraction": round(protected_fraction, 6)},
        [],
        before,
        gray,
    )


def conservative_denoise(
    gray: np.ndarray,
    aligned: np.ndarray,
    mask: np.ndarray,
    config: RestorationConfig,
) -> tuple[np.ndarray, dict[str, Any]]:
    before = gray
    applied = False
    if config.denoise_enabled and config.denoise_kernel > 1:
        filtered = cv2.medianBlur(gray, config.denoise_kernel)
        output = gray.copy()
        output[~mask] = filtered[~mask]
        gray = _protect(output, aligned, mask)
        applied = True
    return gray, operation_record(
        "conservative_denoise",
        config.denoise_enabled,
        applied,
        {"kernel": config.denoise_kernel},
        {},
        [],
        before,
        gray,
    )


def adjust_contrast(
    gray: np.ndarray,
    aligned: np.ndarray,
    mask: np.ndarray,
    config: RestorationConfig,
) -> tuple[np.ndarray, dict[str, Any]]:
    before = gray
    applied = False
    if config.contrast_enabled:
        clahe = cv2.createCLAHE(
            config.clahe_clip_limit,
            (config.clahe_grid_size, config.clahe_grid_size),
        )
        gray = _protect(clahe.apply(gray), aligned, mask)
        applied = True
    return gray, operation_record(
        "clahe_contrast",
        config.contrast_enabled,
        applied,
        {
            "clipLimit": config.clahe_clip_limit,
            "gridSize": config.clahe_grid_size,
        },
        {},
        [],
        before,
        gray,
    )


def binarize(
    gray: np.ndarray,
    aligned: np.ndarray,
    mask: np.ndarray,
    config: RestorationConfig,
) -> tuple[np.ndarray, dict[str, Any], list[str]]:
    before = gray
    applied = False
    reviews: list[str] = []
    if config.binarization_profile == "otsu":
        _, gray = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )
        applied = True
    elif config.binarization_profile == "adaptive":
        gray = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            15,
        )
        applied = True
    if applied:
        gray[mask] = 0
        reviews.append("binarized_candidate_requires_review")
    operation = operation_record(
        "binarization",
        config.binarization_profile != "none",
        applied,
        {"profile": config.binarization_profile},
        {},
        [],
        before,
        gray,
    )
    return gray, operation, reviews
