"""Deterministic, non-generative Stage 2 image quality analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Mapping

import cv2
import numpy as np

from .input_inspection import inspect_bytes

SCHEMA_VERSION = "1.0.0"
ANALYZER_VERSION = "0.1.0"
CALIBRATION_STATE = "uncalibrated_engineering_defaults"

FINDING_TYPES = (
    "orientation",
    "skew",
    "perspective",
    "crop",
    "blur",
    "glare",
    "shadow",
    "uneven_lighting",
    "noise",
    "compression",
    "low_resolution",
    "staff_visibility",
    "tab_visibility",
)


class QualityAnalysisError(ValueError):
    """Stable fail-closed rejection for unsupported quality-analysis inputs."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "rejected",
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


@dataclass(frozen=True)
class QualityAnalysisConfig:
    """Explicit deterministic engineering defaults; not held-out calibrated."""

    max_decode_pixels: int = 80_000_000
    max_working_dimension: int = 2400
    skew_max_degrees: float = 15.0
    skew_possible_degrees: float = 0.20
    skew_probable_degrees: float = 1.00
    blur_possible_laplacian_variance: float = 120.0
    blur_probable_laplacian_variance: float = 60.0
    glare_possible_score: float = 0.08
    glare_probable_score: float = 0.22
    shadow_possible_strength: float = 0.10
    shadow_probable_strength: float = 0.20
    uneven_lighting_possible_cv: float = 0.07
    uneven_lighting_probable_cv: float = 0.14
    noise_possible_p90: float = 0.020
    noise_probable_p90: float = 0.050
    compression_possible_score: float = 0.12
    compression_probable_score: float = 0.30
    low_resolution_min_dimension: int = 1200
    low_dpi: float = 150.0
    crop_edge_margin_fraction: float = 0.008
    visibility_min_line_coverage: float = 0.35

    def __post_init__(self) -> None:
        integer_fields = {
            "max_decode_pixels": (1, 200_000_000),
            "max_working_dimension": (256, 8000),
            "low_resolution_min_dimension": (256, 10000),
        }
        for name, (minimum, maximum) in integer_fields.items():
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                self._invalid(name)
            if not minimum <= value <= maximum:
                self._invalid(name)

        bounded_unit_fields = (
            "glare_possible_score",
            "glare_probable_score",
            "shadow_possible_strength",
            "shadow_probable_strength",
            "uneven_lighting_possible_cv",
            "uneven_lighting_probable_cv",
            "noise_possible_p90",
            "noise_probable_p90",
            "compression_possible_score",
            "compression_probable_score",
            "crop_edge_margin_fraction",
            "visibility_min_line_coverage",
        )
        for name in bounded_unit_fields:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                self._invalid(name)
            if not math.isfinite(float(value)) or not 0 <= float(value) <= 1:
                self._invalid(name)

        positive_fields = (
            "skew_max_degrees",
            "skew_possible_degrees",
            "skew_probable_degrees",
            "blur_possible_laplacian_variance",
            "blur_probable_laplacian_variance",
            "low_dpi",
        )
        for name in positive_fields:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                self._invalid(name)
            if not math.isfinite(float(value)) or float(value) <= 0:
                self._invalid(name)

        if not 0 < self.skew_probable_degrees <= self.skew_max_degrees:
            self._invalid("skew_probable_degrees")
        if self.skew_possible_degrees > self.skew_probable_degrees:
            self._invalid("skew degree thresholds")
        if self.blur_probable_laplacian_variance > self.blur_possible_laplacian_variance:
            self._invalid("blur thresholds")
        for possible_name, probable_name in (
            ("glare_possible_score", "glare_probable_score"),
            ("shadow_possible_strength", "shadow_probable_strength"),
            ("uneven_lighting_possible_cv", "uneven_lighting_probable_cv"),
            ("noise_possible_p90", "noise_probable_p90"),
            ("compression_possible_score", "compression_probable_score"),
        ):
            if getattr(self, possible_name) > getattr(self, probable_name):
                self._invalid(f"{possible_name}/{probable_name}")

    @staticmethod
    def _invalid(name: str) -> None:
        raise QualityAnalysisError(
            "invalid_configuration",
            f"Invalid quality-analysis configuration field: {name}.",
        )

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any] | None,
    ) -> "QualityAnalysisConfig":
        if value is None:
            return cls()
        if not isinstance(value, Mapping):
            raise QualityAnalysisError(
                "invalid_configuration",
                "Quality analysis configuration must be an object.",
            )
        known = set(cls.__dataclass_fields__)
        unknown = sorted(str(key) for key in value if key not in known)
        if unknown:
            raise QualityAnalysisError(
                "invalid_configuration",
                "Unknown quality analysis configuration fields.",
                details={"fields": unknown},
            )
        return cls(**dict(value))

    def digest(self) -> str:
        raw = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def analyze_quality_bytes(
    data: bytes,
    *,
    source_name: str | None = None,
    config: QualityAnalysisConfig | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Measure one immutable PNG/JPEG source; never modifies source bytes."""

    if not isinstance(data, bytes) or not data:
        raise QualityAnalysisError(
            "invalid_source",
            "A non-empty immutable byte sequence is required.",
        )

    resolved = (
        config
        if isinstance(config, QualityAnalysisConfig)
        else QualityAnalysisConfig.from_mapping(config)
    )
    inspected = inspect_bytes(data, source_name=source_name)
    artifact = inspected["artifact"]
    inspection = inspected["analysis"]
    kind = inspection["inputKind"]
    source_digest = artifact["digest"]["value"]

    if kind == "pdf":
        classification = inspection["document"]["classification"]
        if classification == "digital":
            return _vector_pdf_report(
                artifact=artifact,
                inspection=inspection,
                config=resolved,
                source_digest=source_digest,
                data=data,
            )
        raise QualityAnalysisError(
            "pdf_renderer_not_available",
            "Raster quality analysis for scanned/hybrid PDFs requires the approved Stage 3 renderer boundary.",
            details={"classification": classification},
        )
    if kind not in {"png", "jpeg"}:
        raise QualityAnalysisError(
            "unsupported_media_type",
            "Stage 2 quality analysis supports accepted PNG and JPEG raster inputs.",
            details={"inputKind": kind},
        )

    image_metadata = inspection.get("imageMetadata") or {}
    encoded_width = image_metadata.get("encodedWidthPixels")
    encoded_height = image_metadata.get("encodedHeightPixels")
    if encoded_width and encoded_height:
        declared_pixels = int(encoded_width) * int(encoded_height)
        if declared_pixels > resolved.max_decode_pixels:
            raise QualityAnalysisError(
                "decoded_image_too_large",
                "Declared image dimensions exceed the quality-analysis pixel limit.",
                details={
                    "declaredPixels": declared_pixels,
                    "maxDecodePixels": resolved.max_decode_pixels,
                },
            )

    flags = cv2.IMREAD_UNCHANGED | getattr(cv2, "IMREAD_IGNORE_ORIENTATION", 0)
    image = cv2.imdecode(np.frombuffer(data, np.uint8), flags)
    if image is None:
        raise QualityAnalysisError(
            "image_decode_failed",
            "OpenCV could not decode the accepted raster image.",
        )
    decoded_pixels = int(image.shape[0]) * int(image.shape[1])
    if decoded_pixels > resolved.max_decode_pixels:
        raise QualityAnalysisError(
            "decoded_image_too_large",
            "Decoded image exceeds the quality-analysis pixel limit.",
            details={
                "decodedPixels": decoded_pixels,
                "maxDecodePixels": resolved.max_decode_pixels,
            },
        )

    gray = _to_gray(image)
    exif_value = (
        ((inspection.get("imageMetadata") or {}).get("exifOrientation") or {}).get(
            "exifValue"
        )
    )
    gray = _apply_exif_orientation(gray, exif_value)
    display_height, display_width = gray.shape
    working, scale = _working_image(gray, resolved.max_working_dimension)

    skew = _skew_metrics(working, resolved)
    page = _page_geometry_metrics(working, resolved)
    blur = _blur_metrics(working)
    tiles = _tile_statistics(working)
    glare = _glare_metrics(working, tiles)
    shadow = _shadow_metrics(tiles)
    uneven = _uneven_lighting_metrics(working, tiles)
    noise = _noise_metrics(working)
    compression = _compression_metrics(working, kind, data)
    visibility = _visibility_metrics(working, resolved)
    dpi = image_metadata.get("dpiEstimate")
    resolution = _resolution_metrics(display_width, display_height, dpi, resolved)

    metrics = {
        "orientation": {
            "exifValue": exif_value,
            "displayWidthPixels": display_width,
            "displayHeightPixels": display_height,
            "workingWidthPixels": int(working.shape[1]),
            "workingHeightPixels": int(working.shape[0]),
            "workingScale": round(float(scale), 8),
        },
        "skew": skew,
        "perspective": page["perspective"],
        "crop": page["crop"],
        "blur": blur,
        "glare": glare,
        "shadow": shadow,
        "unevenLighting": uneven,
        "noise": noise,
        "compression": compression,
        "resolution": resolution,
        "visibility": visibility,
    }

    findings = [
        _orientation_finding(exif_value),
        _skew_finding(skew, resolved),
        _perspective_finding(page["perspective"]),
        _crop_finding(page["crop"], resolved),
        _blur_finding(blur, resolved),
        _higher_is_worse_finding(
            "glare",
            glare["score"],
            resolved.glare_possible_score,
            resolved.glare_probable_score,
            evidence=glare,
        ),
        _higher_is_worse_finding(
            "shadow",
            shadow["strength"],
            resolved.shadow_possible_strength,
            resolved.shadow_probable_strength,
            evidence=shadow,
        ),
        _higher_is_worse_finding(
            "uneven_lighting",
            uneven["coefficientOfVariation"],
            resolved.uneven_lighting_possible_cv,
            resolved.uneven_lighting_probable_cv,
            evidence=uneven,
        ),
        _higher_is_worse_finding(
            "noise",
            noise["residualP90"],
            resolved.noise_possible_p90,
            resolved.noise_probable_p90,
            evidence=noise,
        ),
        _compression_finding(compression, resolved),
        _resolution_finding(resolution),
        _visibility_finding("staff_visibility", visibility["staffLikeGroupCount"]),
        _visibility_finding("tab_visibility", visibility["tabLikeGroupCount"]),
    ]

    config_dict = asdict(resolved)
    report = {
        "schemaVersion": SCHEMA_VERSION,
        "analyzerVersion": ANALYZER_VERSION,
        "status": "analyzed",
        "sourceArtifactId": artifact["artifactId"],
        "sourceDigest": {"algorithm": "sha256", "value": source_digest},
        "sourceReturnedUnmodified": hashlib.sha256(data).hexdigest() == source_digest,
        "configuration": config_dict,
        "configurationDigest": {
            "algorithm": "sha256",
            "value": resolved.digest(),
        },
        "calibration": {
            "state": CALIBRATION_STATE,
            "heldOutThresholdTuningUsed": False,
            "thresholdPurpose": "engineering_detection_defaults_only",
        },
        "input": {
            "kind": kind,
            "mediaType": artifact["detectedMediaType"],
            "pageType": "single_page_raster",
            "captureType": "raster_image_unknown_origin",
            "displayWidthPixels": display_width,
            "displayHeightPixels": display_height,
            "dpiEstimate": dpi,
        },
        "metrics": metrics,
        "findings": findings,
        "assertions": {
            "sourceBytesModified": False,
            "generativeOperationsUsed": False,
            "symbolCompletionUsed": False,
            "omrPerformed": False,
            "musicalCorrectnessAssessed": False,
            "restorationEffectivenessAssessed": False,
            "trainingPermissionInferred": False,
            "calibrationPermissionInferred": False,
        },
        "limitations": [
            "Stage 2 findings use uncalibrated engineering defaults; Stage 4 owns real-data threshold calibration.",
            "Staff/TAB visibility indicators are geometric evidence only and do not establish notation identity or OMR correctness.",
            "Capture origin is not inferred beyond deterministically known raster metadata.",
            "Scanned/hybrid PDF pixel analysis remains blocked until the approved Stage 3 renderer boundary.",
        ],
    }
    report["reportDigest"] = {
        "algorithm": "sha256",
        "value": _report_digest(report),
    }
    return report


def _report_digest(report: Mapping[str, Any]) -> str:
    payload = dict(report)
    payload.pop("reportDigest", None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _vector_pdf_report(
    *,
    artifact: Mapping[str, Any],
    inspection: Mapping[str, Any],
    config: QualityAnalysisConfig,
    source_digest: str,
    data: bytes,
) -> dict[str, Any]:
    findings = []
    for kind in FINDING_TYPES:
        findings.append(
            {
                "type": kind,
                "status": "not_applicable" if kind not in {"orientation"} else "not_assessed",
                "confidence": "none",
                "evidence": {"reason": "vector_pdf_preserved_without_rasterization"},
            }
        )
    report = {
        "schemaVersion": SCHEMA_VERSION,
        "analyzerVersion": ANALYZER_VERSION,
        "status": "not_applicable_vector_pdf",
        "sourceArtifactId": artifact["artifactId"],
        "sourceDigest": {"algorithm": "sha256", "value": source_digest},
        "sourceReturnedUnmodified": hashlib.sha256(data).hexdigest() == source_digest,
        "configuration": asdict(config),
        "configurationDigest": {"algorithm": "sha256", "value": config.digest()},
        "calibration": {
            "state": CALIBRATION_STATE,
            "heldOutThresholdTuningUsed": False,
            "thresholdPurpose": "engineering_detection_defaults_only",
        },
        "input": {
            "kind": "pdf",
            "mediaType": artifact["detectedMediaType"],
            "pageType": "vector_pdf",
            "captureType": "not_applicable",
            "documentClassification": inspection["document"]["classification"],
        },
        "metrics": {},
        "findings": findings,
        "assertions": {
            "sourceBytesModified": False,
            "generativeOperationsUsed": False,
            "symbolCompletionUsed": False,
            "omrPerformed": False,
            "musicalCorrectnessAssessed": False,
            "restorationEffectivenessAssessed": False,
            "trainingPermissionInferred": False,
            "calibrationPermissionInferred": False,
        },
        "limitations": [
            "Digital PDF content remains vector and is not rasterized for Stage 2 image-quality analysis."
        ],
    }
    report["reportDigest"] = {"algorithm": "sha256", "value": _report_digest(report)}
    return report


def _to_gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image.astype(np.uint8, copy=False)
    if image.ndim != 3:
        raise QualityAnalysisError(
            "unsupported_image_shape",
            "Unsupported image dimensions.",
        )
    if image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if image.shape[2] == 4:
        bgr = image[:, :, :3].astype(np.float32)
        alpha = image[:, :, 3:].astype(np.float32) / 255.0
        composited = (bgr * alpha + 255.0 * (1.0 - alpha)).astype(np.uint8)
        return cv2.cvtColor(composited, cv2.COLOR_BGR2GRAY)
    raise QualityAnalysisError(
        "unsupported_image_shape",
        "Unsupported channel count.",
    )


def _apply_exif_orientation(gray: np.ndarray, exif_value: int | None) -> np.ndarray:
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
    return transform(gray) if transform is not None else gray


def _working_image(gray: np.ndarray, max_dimension: int) -> tuple[np.ndarray, float]:
    height, width = gray.shape
    largest = max(height, width)
    if largest <= max_dimension:
        return gray, 1.0
    scale = max_dimension / largest
    resized = cv2.resize(
        gray,
        (max(1, round(width * scale)), max(1, round(height * scale))),
        interpolation=cv2.INTER_AREA,
    )
    return resized, float(scale)


def _skew_metrics(
    gray: np.ndarray,
    config: QualityAnalysisConfig,
) -> dict[str, Any]:
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 1800,
        50,
        minLineLength=max(30, int(gray.shape[1] * 0.20)),
        maxLineGap=20,
    )
    if lines is None:
        return {"angleDegrees": 0.0, "confidence": 0.0, "lineCount": 0}
    values: list[tuple[float, float]] = []
    for x1, y1, x2, y2 in lines[:, 0]:
        length = math.hypot(x2 - x1, y2 - y1)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        while angle <= -90:
            angle += 180
        while angle > 90:
            angle -= 180
        if length and abs(angle) <= config.skew_max_degrees:
            values.append((angle, length))
    if not values:
        return {"angleDegrees": 0.0, "confidence": 0.0, "lineCount": 0}
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
    return {
        "angleDegrees": round(float(median), 6),
        "confidence": round(float(confidence), 6),
        "lineCount": len(values),
    }


def _order_points(points: np.ndarray) -> np.ndarray:
    ordered = np.zeros((4, 2), np.float32)
    sums = points.sum(1)
    differences = np.diff(points, axis=1).ravel()
    ordered[0] = points[np.argmin(sums)]
    ordered[2] = points[np.argmax(sums)]
    ordered[1] = points[np.argmin(differences)]
    ordered[3] = points[np.argmax(differences)]
    return ordered


def _page_geometry_metrics(
    gray: np.ndarray,
    config: QualityAnalysisConfig,
) -> dict[str, Any]:
    height, width = gray.shape
    scale = min(1.0, 1600.0 / max(height, width))
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
    best = None
    best_area = 0.0
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue
        candidate = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        area = cv2.contourArea(contour)
        if len(candidate) == 4 and cv2.isContourConvex(candidate) and area > best_area:
            best = candidate.reshape(4, 2).astype(np.float32)
            best_area = float(area)
    if best is None:
        return {
            "perspective": {
                "detected": False,
                "confidence": 0.0,
                "areaRatio": 0.0,
                "edgeScaleAsymmetry": None,
                "quad": None,
            },
            "crop": {
                "assessed": False,
                "minimumMarginFraction": None,
                "margins": None,
            },
        }

    quad = _order_points(best / scale)
    area_ratio = best_area / float(small.shape[0] * small.shape[1])
    tl, tr, br, bl = quad
    top = float(np.linalg.norm(tr - tl))
    bottom = float(np.linalg.norm(br - bl))
    left = float(np.linalg.norm(bl - tl))
    right = float(np.linalg.norm(br - tr))
    width_asymmetry = abs(top - bottom) / max(top, bottom, 1.0)
    height_asymmetry = abs(left - right) / max(left, right, 1.0)
    asymmetry = max(width_asymmetry, height_asymmetry)
    rectangularity = max(0.0, 1.0 - asymmetry)
    confidence = min(1.0, max(0.0, 0.55 + 0.30 * min(1.0, area_ratio / 0.55) + 0.15 * rectangularity))

    xs = quad[:, 0]
    ys = quad[:, 1]
    margins = {
        "left": max(0.0, float(xs.min()) / max(width - 1, 1)),
        "right": max(0.0, float(width - 1 - xs.max()) / max(width - 1, 1)),
        "top": max(0.0, float(ys.min()) / max(height - 1, 1)),
        "bottom": max(0.0, float(height - 1 - ys.max()) / max(height - 1, 1)),
    }
    min_margin = min(margins.values())
    return {
        "perspective": {
            "detected": True,
            "confidence": round(float(confidence), 6),
            "areaRatio": round(float(area_ratio), 6),
            "edgeScaleAsymmetry": round(float(asymmetry), 6),
            "quad": [[round(float(x), 3), round(float(y), 3)] for x, y in quad],
        },
        "crop": {
            "assessed": True,
            "minimumMarginFraction": round(float(min_margin), 6),
            "margins": {key: round(float(value), 6) for key, value in margins.items()},
        },
    }


def _blur_metrics(gray: np.ndarray) -> dict[str, Any]:
    variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return {"laplacianVariance": round(variance, 6)}


def _tile_statistics(gray: np.ndarray, grid: int = 8) -> dict[str, list[float]]:
    height, width = gray.shape
    means: list[float] = []
    clipped: list[float] = []
    for row in range(grid):
        y0 = row * height // grid
        y1 = (row + 1) * height // grid
        for column in range(grid):
            x0 = column * width // grid
            x1 = (column + 1) * width // grid
            tile = gray[y0:y1, x0:x1]
            if not tile.size:
                continue
            means.append(float(np.mean(tile)))
            clipped.append(float(np.mean(tile >= 250)))
    return {"means": means, "clipped": clipped}


def _glare_metrics(
    gray: np.ndarray,
    tiles: Mapping[str, list[float]],
) -> dict[str, Any]:
    clipped = np.asarray(tiles["clipped"], dtype=np.float64)
    global_clipped = float(np.mean(gray >= 250))
    if clipped.size == 0:
        concentration = 0.0
        hot_fraction = 0.0
    else:
        concentration = max(0.0, float(np.max(clipped)) - float(np.median(clipped)))
        hot_fraction = float(np.mean(clipped >= 0.20))
    p995 = float(np.percentile(gray, 99.5))
    p005 = float(np.percentile(gray, 0.5))
    dynamic = max(0.0, min(1.0, (p995 - p005) / 180.0))
    score = min(1.0, concentration * 0.75 + hot_fraction * 0.15 + global_clipped * 0.10)
    score *= dynamic
    return {
        "score": round(float(score), 6),
        "globalClippedFraction": round(global_clipped, 6),
        "spatialConcentration": round(concentration, 6),
        "hotTileFraction": round(hot_fraction, 6),
        "dynamicRangeFactor": round(dynamic, 6),
    }


def _shadow_metrics(tiles: Mapping[str, list[float]]) -> dict[str, Any]:
    values = np.asarray(tiles["means"], dtype=np.float64)
    if values.size == 0:
        return {"strength": 0.0, "darkTileFraction": 0.0}
    median = float(np.median(values))
    baseline = max(median, 1.0)
    dark_threshold = median * 0.72
    strength = max(0.0, median - float(np.percentile(values, 10))) / baseline
    dark_fraction = float(np.mean(values <= dark_threshold))
    return {
        "strength": round(float(min(1.0, strength)), 6),
        "darkTileFraction": round(dark_fraction, 6),
        "tileMedian": round(median, 6),
    }


def _uneven_lighting_metrics(
    gray: np.ndarray,
    tiles: Mapping[str, list[float]],
) -> dict[str, Any]:
    values = np.asarray(tiles["means"], dtype=np.float64)
    if values.size == 0:
        return {
            "coefficientOfVariation": 0.0,
            "backgroundRange": 0.0,
        }
    mean = max(float(np.mean(values)), 1.0)
    cv = float(np.std(values) / mean)
    background_range = float(np.percentile(values, 90) - np.percentile(values, 10)) / 255.0
    return {
        "coefficientOfVariation": round(cv, 6),
        "backgroundRange": round(background_range, 6),
    }


def _noise_metrics(gray: np.ndarray) -> dict[str, Any]:
    filtered = cv2.medianBlur(gray, 3)
    residual = cv2.absdiff(gray, filtered).astype(np.float32) / 255.0
    edges = cv2.Canny(gray, 50, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
    sample = residual[edges == 0]
    if sample.size < max(64, gray.size // 100):
        sample = residual.reshape(-1)
    return {
        "residualMedian": round(float(np.median(sample)), 6),
        "residualP90": round(float(np.percentile(sample, 90)), 6),
        "sampleFraction": round(float(sample.size / gray.size), 6),
    }


def _jpeg_quantization_metrics(data: bytes) -> dict[str, Any]:
    values: list[int] = []
    offset = 2
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if marker == 0xDA:
            break
        if offset + 2 > len(data):
            break
        length = int.from_bytes(data[offset : offset + 2], "big")
        if length < 2 or offset + length > len(data):
            break
        payload = data[offset + 2 : offset + length]
        if marker == 0xDB:
            index = 0
            while index < len(payload):
                spec = payload[index]
                index += 1
                precision = spec >> 4
                count = 128 if precision else 64
                raw = payload[index : index + count]
                if len(raw) != count:
                    break
                index += count
                if precision:
                    values.extend(
                        int.from_bytes(raw[position : position + 2], "big")
                        for position in range(0, count, 2)
                    )
                else:
                    values.extend(int(value) for value in raw)
        offset += length
    if not values:
        return {
            "tableValueCount": 0,
            "meanQuantization": None,
            "maxQuantization": None,
            "quantizationSeverity": None,
        }
    mean_quantization = float(np.mean(np.asarray(values, dtype=np.float64)))
    max_quantization = int(max(values))
    severity = min(1.0, mean_quantization / 200.0)
    return {
        "tableValueCount": len(values),
        "meanQuantization": round(mean_quantization, 6),
        "maxQuantization": max_quantization,
        "quantizationSeverity": round(float(severity), 6),
    }


def _compression_metrics(
    gray: np.ndarray,
    kind: str,
    data: bytes,
) -> dict[str, Any]:
    if kind != "jpeg" or min(gray.shape) < 24:
        return {
            "applicable": False,
            "score": None,
            "blockiness": None,
            "boundaryDifference": None,
            "interiorDifference": None,
            "quantization": None,
        }
    vertical = np.abs(np.diff(gray.astype(np.float32), axis=1))
    horizontal = np.abs(np.diff(gray.astype(np.float32), axis=0))
    v_boundary_idx = np.arange(7, vertical.shape[1], 8)
    h_boundary_idx = np.arange(7, horizontal.shape[0], 8)
    v_boundary = (
        vertical[:, v_boundary_idx].reshape(-1)
        if v_boundary_idx.size
        else np.array([], dtype=np.float32)
    )
    h_boundary = (
        horizontal[h_boundary_idx, :].reshape(-1)
        if h_boundary_idx.size
        else np.array([], dtype=np.float32)
    )
    boundary = np.concatenate([v_boundary, h_boundary])

    v_mask = np.ones(vertical.shape[1], dtype=bool)
    h_mask = np.ones(horizontal.shape[0], dtype=bool)
    v_mask[v_boundary_idx] = False
    h_mask[h_boundary_idx] = False
    interior = np.concatenate(
        [
            vertical[:, v_mask].reshape(-1),
            horizontal[h_mask, :].reshape(-1),
        ]
    )
    boundary_mean = float(np.mean(boundary)) if boundary.size else 0.0
    interior_mean = float(np.mean(interior)) if interior.size else 0.0
    blockiness = max(0.0, boundary_mean - interior_mean) / 255.0
    quantization = _jpeg_quantization_metrics(data)
    quantization_severity = quantization["quantizationSeverity"]
    score = max(
        min(1.0, blockiness * 4.0),
        float(quantization_severity) if quantization_severity is not None else 0.0,
    )
    return {
        "applicable": True,
        "score": round(float(score), 6),
        "blockiness": round(float(blockiness), 6),
        "boundaryDifference": round(boundary_mean / 255.0, 6),
        "interiorDifference": round(interior_mean / 255.0, 6),
        "quantization": quantization,
    }


def _resolution_metrics(
    width: int,
    height: int,
    dpi: Mapping[str, Any] | None,
    config: QualityAnalysisConfig,
) -> dict[str, Any]:
    min_dimension = min(width, height)
    dpi_min = None
    if dpi and isinstance(dpi, Mapping):
        x = dpi.get("x")
        y = dpi.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            dpi_min = min(float(x), float(y))
    low_pixels = min_dimension < config.low_resolution_min_dimension
    low_dpi = dpi_min is not None and dpi_min < config.low_dpi
    return {
        "minimumDimensionPixels": int(min_dimension),
        "dpiMinimum": round(dpi_min, 3) if dpi_min is not None else None,
        "lowPixelDimension": bool(low_pixels),
        "lowDpi": bool(low_dpi),
    }


def _visibility_metrics(
    gray: np.ndarray,
    config: QualityAnalysisConfig,
) -> dict[str, Any]:
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )
    kernel_width = max(15, gray.shape[1] // 8)
    horizontal = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        np.ones((1, kernel_width), np.uint8),
    )
    row_coverage = np.mean(horizontal > 0, axis=1)
    candidate_rows = np.flatnonzero(row_coverage >= config.visibility_min_line_coverage)
    centers: list[int] = []
    if candidate_rows.size:
        start = previous = int(candidate_rows[0])
        for value in candidate_rows[1:]:
            value = int(value)
            if value > previous + 1:
                centers.append(round((start + previous) / 2))
                start = value
            previous = value
        centers.append(round((start + previous) / 2))

    tab_groups, used = _count_regular_groups(centers, 6)
    remaining = [value for index, value in enumerate(centers) if index not in used]
    staff_groups, _ = _count_regular_groups(remaining, 5)
    mean_coverage = (
        float(np.mean(row_coverage[candidate_rows])) if candidate_rows.size else 0.0
    )
    return {
        "horizontalLineRowCount": len(centers),
        "horizontalLineRows": centers[:128],
        "meanCandidateLineCoverage": round(mean_coverage, 6),
        "staffLikeGroupCount": staff_groups,
        "tabLikeGroupCount": tab_groups,
        "evidenceOnly": True,
    }


def _count_regular_groups(
    centers: list[int],
    size: int,
) -> tuple[int, set[int]]:
    count = 0
    used: set[int] = set()
    if len(centers) < size:
        return count, used
    index = 0
    while index <= len(centers) - size:
        sequence = centers[index : index + size]
        gaps = np.diff(np.asarray(sequence, dtype=np.float64))
        median = float(np.median(gaps)) if gaps.size else 0.0
        tolerance = max(1.5, median * 0.30)
        if (
            2.0 <= median <= 80.0
            and np.all(gaps > 0)
            and float(np.max(np.abs(gaps - median))) <= tolerance
        ):
            count += 1
            used.update(range(index, index + size))
            index += size
        else:
            index += 1
    return count, used


def _orientation_finding(exif_value: int | None) -> dict[str, Any]:
    if exif_value in {None, 1}:
        return {
            "type": "orientation",
            "status": "unlikely",
            "confidence": "medium" if exif_value == 1 else "low",
            "evidence": {"exifOrientation": exif_value},
        }
    return {
        "type": "orientation",
        "status": "observed",
        "confidence": "high",
        "evidence": {"exifOrientation": exif_value, "displayTransformAppliedForAnalysis": True},
    }


def _skew_finding(
    metric: Mapping[str, Any],
    config: QualityAnalysisConfig,
) -> dict[str, Any]:
    angle = abs(float(metric["angleDegrees"]))
    confidence = float(metric["confidence"])
    if metric["lineCount"] == 0 or confidence < 0.20:
        return {
            "type": "skew",
            "status": "not_assessed",
            "confidence": "none",
            "evidence": dict(metric),
        }
    if angle >= config.skew_probable_degrees:
        status = "probable"
    elif angle >= config.skew_possible_degrees:
        status = "possible"
    else:
        status = "unlikely"
    return {
        "type": "skew",
        "status": status,
        "confidence": "high" if confidence >= 0.70 else "medium",
        "evidence": dict(metric),
    }


def _perspective_finding(metric: Mapping[str, Any]) -> dict[str, Any]:
    if not metric["detected"] or metric["edgeScaleAsymmetry"] is None:
        return {
            "type": "perspective",
            "status": "not_assessed",
            "confidence": "none",
            "evidence": dict(metric),
        }
    asymmetry = float(metric["edgeScaleAsymmetry"])
    status = "probable" if asymmetry >= 0.08 else "possible" if asymmetry >= 0.03 else "unlikely"
    confidence = float(metric["confidence"])
    return {
        "type": "perspective",
        "status": status,
        "confidence": "high" if confidence >= 0.85 else "medium" if confidence >= 0.60 else "low",
        "evidence": {
            "edgeScaleAsymmetry": metric["edgeScaleAsymmetry"],
            "areaRatio": metric["areaRatio"],
            "quadConfidence": metric["confidence"],
        },
    }


def _crop_finding(
    metric: Mapping[str, Any],
    config: QualityAnalysisConfig,
) -> dict[str, Any]:
    if not metric["assessed"] or metric["minimumMarginFraction"] is None:
        return {
            "type": "crop",
            "status": "not_assessed",
            "confidence": "none",
            "evidence": dict(metric),
        }
    margin = float(metric["minimumMarginFraction"])
    status = "possible" if margin <= config.crop_edge_margin_fraction else "unlikely"
    return {
        "type": "crop",
        "status": status,
        "confidence": "medium",
        "evidence": dict(metric),
    }


def _blur_finding(
    metric: Mapping[str, Any],
    config: QualityAnalysisConfig,
) -> dict[str, Any]:
    variance = float(metric["laplacianVariance"])
    if variance <= config.blur_probable_laplacian_variance:
        status = "probable"
    elif variance <= config.blur_possible_laplacian_variance:
        status = "possible"
    else:
        status = "unlikely"
    return {
        "type": "blur",
        "status": status,
        "confidence": "medium",
        "evidence": dict(metric),
    }


def _higher_is_worse_finding(
    kind: str,
    value: float,
    possible: float,
    probable: float,
    *,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    if value >= probable:
        status = "probable"
    elif value >= possible:
        status = "possible"
    else:
        status = "unlikely"
    return {
        "type": kind,
        "status": status,
        "confidence": "medium",
        "evidence": dict(evidence),
    }


def _compression_finding(
    metric: Mapping[str, Any],
    config: QualityAnalysisConfig,
) -> dict[str, Any]:
    if not metric["applicable"] or metric["score"] is None:
        return {
            "type": "compression",
            "status": "not_applicable",
            "confidence": "none",
            "evidence": dict(metric),
        }
    return _higher_is_worse_finding(
        "compression",
        float(metric["score"]),
        config.compression_possible_score,
        config.compression_probable_score,
        evidence=metric,
    )


def _resolution_finding(metric: Mapping[str, Any]) -> dict[str, Any]:
    if metric["lowPixelDimension"] and metric["lowDpi"]:
        status, confidence = "probable", "high"
    elif metric["lowPixelDimension"] or metric["lowDpi"]:
        status, confidence = "probable", "medium"
    elif metric["dpiMinimum"] is not None:
        status, confidence = "unlikely", "medium"
    else:
        status, confidence = "unlikely", "low"
    return {
        "type": "low_resolution",
        "status": status,
        "confidence": confidence,
        "evidence": dict(metric),
    }


def _visibility_finding(kind: str, group_count: int) -> dict[str, Any]:
    if group_count:
        return {
            "type": kind,
            "status": "observed",
            "confidence": "medium",
            "evidence": {
                "regularHorizontalGroupCount": int(group_count),
                "geometricEvidenceOnly": True,
            },
        }
    return {
        "type": kind,
        "status": "not_assessed",
        "confidence": "none",
        "evidence": {
            "regularHorizontalGroupCount": 0,
            "geometricEvidenceOnly": True,
        },
    }


__all__ = [
    "ANALYZER_VERSION",
    "CALIBRATION_STATE",
    "FINDING_TYPES",
    "SCHEMA_VERSION",
    "QualityAnalysisConfig",
    "QualityAnalysisError",
    "analyze_quality_bytes",
]
