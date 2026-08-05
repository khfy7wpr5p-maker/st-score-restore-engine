"""Deterministic orientation, deskew, perspective, and crop operations."""

from __future__ import annotations

import hashlib
import math
from typing import Any

import cv2
import numpy as np

from .restoration_types import RestorationConfig, RestorationError


def pixel_digest(image: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(image).tobytes()).hexdigest()


def operation_record(
    name: str,
    enabled: bool,
    applied: bool,
    parameters: dict[str, Any],
    evidence: dict[str, Any],
    warnings: list[str],
    before: np.ndarray,
    after: np.ndarray,
) -> dict[str, Any]:
    return {
        "name": name,
        "enabled": enabled,
        "applied": applied,
        "parameters": parameters,
        "evidence": evidence,
        "warnings": warnings,
        "inputPixelDigest": pixel_digest(before),
        "outputPixelDigest": pixel_digest(after),
    }


def to_gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image.astype(np.uint8, copy=False)
    if image.ndim != 3:
        raise RestorationError("unsupported_image_shape", "Unsupported image dimensions.")
    if image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if image.shape[2] == 4:
        bgr = image[:, :, :3].astype(np.float32)
        alpha = image[:, :, 3:].astype(np.float32) / 255
        composited = (bgr * alpha + 255 * (1 - alpha)).astype(np.uint8)
        return cv2.cvtColor(composited, cv2.COLOR_BGR2GRAY)
    raise RestorationError("unsupported_image_shape", "Unsupported channel count.")


def apply_orientation(
    gray: np.ndarray,
    exif_value: int | None,
    enabled: bool,
) -> tuple[np.ndarray, dict[str, Any]]:
    before = gray
    applied = False
    warnings: list[str] = []
    if enabled and exif_value not in {None, 1}:
        mapping = {
            2: lambda x: cv2.flip(x, 1),
            3: lambda x: cv2.rotate(x, cv2.ROTATE_180),
            4: lambda x: cv2.flip(x, 0),
            5: lambda x: cv2.transpose(x),
            6: lambda x: cv2.rotate(x, cv2.ROTATE_90_CLOCKWISE),
            7: lambda x: cv2.flip(cv2.transpose(x), -1),
            8: lambda x: cv2.rotate(x, cv2.ROTATE_90_COUNTERCLOCKWISE),
        }
        transform = mapping.get(exif_value)
        if transform is not None:
            gray = transform(gray)
            applied = True
        else:
            warnings.append("unsupported_exif_orientation")
    elif not enabled and exif_value not in {None, 1}:
        warnings.append("source_orientation_ignored")
    return gray, operation_record(
        "orientation",
        enabled,
        applied,
        {"exifValue": exif_value},
        {},
        warnings,
        before,
        gray,
    )


def make_protected_mask(
    gray: np.ndarray,
    supplied: np.ndarray | None,
    config: RestorationConfig,
) -> np.ndarray:
    if supplied is not None:
        mask = np.asarray(supplied)
        if mask.shape != gray.shape:
            raise RestorationError(
                "invalid_protected_mask",
                "Protected mask dimensions must match the oriented image.",
            )
        result = mask.astype(bool)
    else:
        otsu, _ = cv2.threshold(
            cv2.GaussianBlur(gray, (3, 3), 0),
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )
        threshold = int(min(config.protected_dark_threshold, max(80, otsu)))
        result = gray <= threshold
    if config.protected_dilation:
        kernel = np.ones((3, 3), np.uint8)
        result = cv2.dilate(
            result.astype(np.uint8),
            kernel,
            iterations=config.protected_dilation,
        ).astype(bool)
    return result


def _estimate_angle(
    gray: np.ndarray,
    config: RestorationConfig,
) -> tuple[float, float, int]:
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 1800,
        50,
        minLineLength=max(30, int(gray.shape[1] * 0.2)),
        maxLineGap=20,
    )
    if lines is None:
        return 0.0, 0.0, 0
    values: list[tuple[float, float]] = []
    for x1, y1, x2, y2 in lines[:, 0]:
        length = math.hypot(x2 - x1, y2 - y1)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        while angle <= -90:
            angle += 180
        while angle > 90:
            angle -= 180
        if length and abs(angle) <= config.max_deskew_degrees:
            values.append((angle, length))
    if not values:
        return 0.0, 0.0, 0
    values.sort()
    total = sum(weight for _, weight in values)
    running = 0.0
    median = 0.0
    for median, weight in values:
        running += weight
        if running >= total / 2:
            break
    confidence = sum(
        weight for angle, weight in values if abs(angle - median) <= 0.75
    ) / total
    return float(median), float(confidence), len(values)


def _rotate(
    image: np.ndarray,
    angle: float,
    interpolation: int,
    border: int,
) -> np.ndarray:
    height, width = image.shape[:2]
    center = (width / 2, height / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1)
    cosine = abs(matrix[0, 0])
    sine = abs(matrix[0, 1])
    new_width = math.ceil(height * sine + width * cosine)
    new_height = math.ceil(height * cosine + width * sine)
    matrix[0, 2] += new_width / 2 - center[0]
    matrix[1, 2] += new_height / 2 - center[1]
    return cv2.warpAffine(
        image,
        matrix,
        (new_width, new_height),
        flags=interpolation,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border,
    )


def deskew(
    gray: np.ndarray,
    protected: np.ndarray,
    aligned: np.ndarray,
    config: RestorationConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any], list[str]]:
    before = gray
    angle, confidence, line_count = _estimate_angle(gray, config)
    applied = False
    warnings: list[str] = []
    reviews: list[str] = []
    if config.deskew_enabled and abs(angle) >= config.min_deskew_degrees:
        if confidence >= config.deskew_min_confidence:
            correction = -angle
            gray = _rotate(gray, correction, cv2.INTER_LINEAR, 255)
            aligned = _rotate(aligned, correction, cv2.INTER_NEAREST, 255)
            protected = _rotate(
                protected.astype(np.uint8) * 255,
                correction,
                cv2.INTER_NEAREST,
                0,
            ) > 0
            applied = True
        else:
            warnings.append("deskew_confidence_below_threshold")
            reviews.append("ambiguous_deskew")
    operation = operation_record(
        "deskew",
        config.deskew_enabled,
        applied,
        {
            "minDegrees": config.min_deskew_degrees,
            "maxDegrees": config.max_deskew_degrees,
            "minConfidence": config.deskew_min_confidence,
        },
        {
            "estimatedAngleDegrees": round(angle, 6),
            "confidence": round(confidence, 6),
            "lineCount": line_count,
        },
        warnings,
        before,
        gray,
    )
    return gray, protected, aligned, operation, reviews


def _order_points(points: np.ndarray) -> np.ndarray:
    ordered = np.zeros((4, 2), np.float32)
    sums = points.sum(1)
    differences = np.diff(points, axis=1).ravel()
    ordered[0] = points[np.argmin(sums)]
    ordered[2] = points[np.argmax(sums)]
    ordered[1] = points[np.argmin(differences)]
    ordered[3] = points[np.argmax(differences)]
    return ordered


def detect_page_quad(
    gray: np.ndarray,
    config: RestorationConfig,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    height, width = gray.shape
    scale = min(1.0, 1600 / max(height, width))
    small = (
        cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        if scale < 1
        else gray
    )
    blurred = cv2.GaussianBlur(small, (5, 5), 0)
    edges = cv2.Canny(blurred, 40, 120)
    edges = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        np.ones((5, 5), np.uint8),
        iterations=2,
    )
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    best: np.ndarray | None = None
    best_area = 0.0
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        candidate = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        candidate_area = cv2.contourArea(contour)
        if (
            len(candidate) == 4
            and cv2.isContourConvex(candidate)
            and candidate_area > best_area
        ):
            best = candidate.reshape(4, 2).astype(np.float32)
            best_area = candidate_area
    if best is None:
        return None, {
            "confidence": 0.0,
            "areaRatio": 0.0,
            "reason": "no_quadrilateral",
            "validArea": False,
        }
    ratio = best_area / (small.shape[0] * small.shape[1])
    confidence = max(
        0.0,
        min(1.0, 0.7 + 0.3 * min(1.0, ratio / config.min_page_area_ratio)),
    )
    return _order_points(best / scale), {
        "confidence": round(confidence, 6),
        "areaRatio": round(ratio, 6),
        "validArea": config.min_page_area_ratio <= ratio <= config.max_page_area_ratio,
        "reason": "detected",
    }


def _warp(
    image: np.ndarray,
    quad: np.ndarray,
    interpolation: int,
    border: int,
) -> np.ndarray:
    top_left, top_right, bottom_right, bottom_left = quad
    width = round(
        max(
            np.linalg.norm(bottom_right - bottom_left),
            np.linalg.norm(top_right - top_left),
        )
    )
    height = round(
        max(
            np.linalg.norm(top_right - bottom_right),
            np.linalg.norm(top_left - bottom_left),
        )
    )
    if width < 32 or height < 32:
        raise RestorationError("unsafe_geometry", "Perspective target is too small.")
    target = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        np.float32,
    )
    matrix = cv2.getPerspectiveTransform(quad, target)
    return cv2.warpPerspective(
        image,
        matrix,
        (width, height),
        flags=interpolation,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border,
    )


def apply_perspective(
    gray: np.ndarray,
    protected: np.ndarray,
    aligned: np.ndarray,
    quad: np.ndarray | None,
    evidence: dict[str, Any],
    config: RestorationConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any], list[str]]:
    before = gray
    applied = False
    warnings: list[str] = []
    reviews: list[str] = []
    if config.perspective_enabled:
        if (
            quad is not None
            and evidence["validArea"]
            and evidence["confidence"] >= config.perspective_min_confidence
        ):
            gray = _warp(gray, quad, cv2.INTER_LINEAR, 255)
            aligned = _warp(aligned, quad, cv2.INTER_NEAREST, 255)
            protected = _warp(
                protected.astype(np.uint8) * 255,
                quad,
                cv2.INTER_NEAREST,
                0,
            ) > 0
            applied = True
        else:
            warnings.append("perspective_not_applied_due_to_ambiguity")
            reviews.append("ambiguous_perspective")
    elif quad is not None and evidence["validArea"]:
        reviews.append("perspective_proposal_requires_opt_in")
    operation = operation_record(
        "perspective",
        config.perspective_enabled,
        applied,
        {"minConfidence": config.perspective_min_confidence},
        evidence,
        warnings,
        before,
        gray,
    )
    return gray, protected, aligned, operation, reviews


def apply_crop(
    gray: np.ndarray,
    protected: np.ndarray,
    aligned: np.ndarray,
    quad: np.ndarray | None,
    evidence: dict[str, Any],
    config: RestorationConfig,
    perspective_applied: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any], list[str]]:
    before = gray
    applied = False
    warnings: list[str] = []
    reviews: list[str] = []
    operation_evidence = dict(evidence)
    if perspective_applied:
        warnings.append("crop_satisfied_by_perspective_rectification")
        operation_evidence["coveredByPerspective"] = True
    elif config.crop_enabled:
        if (
            quad is not None
            and evidence["validArea"]
            and evidence["confidence"] >= config.perspective_min_confidence
        ):
            x, y, width, height = cv2.boundingRect(quad.astype(np.int32))
            padding = max(2, int(min(gray.shape) * 0.005))
            x = max(0, x - padding)
            y = max(0, y - padding)
            x2 = min(gray.shape[1], x + width + 2 * padding)
            y2 = min(gray.shape[0], y + height + 2 * padding)
            if x2 - x >= 32 and y2 - y >= 32:
                gray = gray[y:y2, x:x2]
                aligned = aligned[y:y2, x:x2]
                protected = protected[y:y2, x:x2]
                applied = True
            else:
                warnings.append("crop_too_small")
                reviews.append("ambiguous_crop")
        else:
            warnings.append("crop_not_applied_due_to_ambiguity")
            reviews.append("ambiguous_crop")
    elif quad is not None and evidence["validArea"]:
        reviews.append("crop_proposal_requires_opt_in")
    operation = operation_record(
        "crop",
        config.crop_enabled,
        applied,
        {"safePaddingFraction": 0.005},
        operation_evidence,
        warnings,
        before,
        gray,
    )
    return gray, protected, aligned, operation, reviews
