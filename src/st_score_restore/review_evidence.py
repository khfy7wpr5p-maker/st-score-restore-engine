"""Deterministic reviewer evidence crops and bundle generation."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any, Mapping

import cv2
import numpy as np

SCHEMA_VERSION = "1.0.0"
GENERATOR_VERSION = "0.5.0"
DEFAULT_MAX_INPUT_BYTES = 50_000_000
DEFAULT_MAX_DECODE_PIXELS = 80_000_000
_ARTIFACT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


class ReviewEvidenceError(ValueError):
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
            "status": "evidence_failed",
            "automaticApproval": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


@dataclass(frozen=True)
class EvidenceArtifact:
    artifact_id: str
    role: str
    name: str
    media_type: str
    data: bytes
    finding_index: int | None


@dataclass(frozen=True)
class ReviewEvidenceResult:
    bundle: dict[str, Any]
    bundle_bytes: bytes
    artifacts: tuple[EvidenceArtifact, ...]


def generate_review_evidence(
    source_bytes: bytes,
    candidate_bytes: bytes,
    safety_report: Mapping[str, Any],
    *,
    source_artifact_id: str,
    candidate_artifact_id: str,
    safety_report_artifact_id: str,
    page_number: int,
    attempt_id: str,
    crop_padding_pixels: int = 24,
    max_regions: int = 64,
    max_crop_pixels: int = 4_000_000,
) -> ReviewEvidenceResult:
    """Create byte-stable evidence without claiming semantic recognition."""

    _validate_configuration(
        crop_padding_pixels=crop_padding_pixels,
        max_regions=max_regions,
        max_crop_pixels=max_crop_pixels,
    )
    _validate_parent_bytes(source_bytes, source_artifact_id, "source")
    _validate_parent_bytes(candidate_bytes, candidate_artifact_id, "candidate")
    if not _ARTIFACT_ID.fullmatch(str(safety_report_artifact_id)):
        raise ReviewEvidenceError(
            "invalid_safety_report_artifact_id",
            "The safety report artifact ID is invalid.",
        )
    if not isinstance(safety_report, Mapping):
        raise ReviewEvidenceError(
            "invalid_safety_report",
            "A safety report object is required.",
        )
    if (
        safety_report.get("status") != "completed"
        or safety_report.get("automaticApproval") is not False
    ):
        raise ReviewEvidenceError(
            "invalid_safety_report",
            "Evidence requires a completed non-approving safety report.",
        )
    safety_report_id = safety_report.get("reportId")
    if not isinstance(safety_report_id, str) or not re.fullmatch(
        r"safety-report:[0-9a-f]{64}", safety_report_id
    ):
        raise ReviewEvidenceError(
            "invalid_safety_report",
            "The safety report identifier is invalid.",
        )
    if not isinstance(page_number, int) or page_number < 1:
        raise ReviewEvidenceError(
            "invalid_page_number",
            "page_number must be a positive integer.",
        )
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        raise ReviewEvidenceError(
            "invalid_attempt_id",
            "attempt_id is required.",
        )

    report_source = safety_report.get("source") or {}
    report_candidate = safety_report.get("candidate") or {}
    if (
        report_source.get("artifactId") != source_artifact_id
        or report_candidate.get("artifactId") != candidate_artifact_id
    ):
        raise ReviewEvidenceError(
            "evidence_parent_mismatch",
            "Safety report parents do not match the supplied source and candidate.",
        )

    source = _decode_grayscale(source_bytes, "source")
    candidate = _decode_grayscale(candidate_bytes, "candidate")
    source_h, source_w = source.shape
    _require_declared_dimensions(report_source, source, "source")
    _require_declared_dimensions(report_candidate, candidate, "candidate")

    aligned_candidate, transform = _align_candidate(
        candidate,
        source.shape,
        safety_report.get("registration") or {},
    )
    findings = safety_report.get("findings")
    if not isinstance(findings, list):
        raise ReviewEvidenceError(
            "invalid_safety_report",
            "Safety report findings must be an array.",
        )
    regional_count = sum(
        1
        for item in findings
        if isinstance(item, Mapping) and item.get("region") is not None
    )
    if regional_count > max_regions:
        raise ReviewEvidenceError(
            "too_many_evidence_regions",
            "Safety report contains more regional findings than the evidence limit.",
            details={
                "regionalFindings": regional_count,
                "maxRegions": max_regions,
            },
        )

    artifacts: list[EvidenceArtifact] = []
    bundle_findings: list[dict[str, Any]] = []
    for index, raw_finding in enumerate(findings):
        if not isinstance(raw_finding, Mapping):
            raise ReviewEvidenceError(
                "invalid_safety_report",
                "Every safety finding must be an object.",
            )
        code = raw_finding.get("code")
        severity = raw_finding.get("severity")
        if not isinstance(code, str) or not code:
            raise ReviewEvidenceError(
                "invalid_safety_report",
                "Every safety finding must have a non-empty code.",
            )
        if severity not in {"low", "medium", "high", "critical"}:
            raise ReviewEvidenceError(
                "invalid_safety_report",
                "Every safety finding must have a supported severity.",
            )
        entry: dict[str, Any] = {
            "findingIndex": index,
            "code": code,
            "severity": severity,
            "semanticCertainty": "not_claimed",
            "sourceRegion": None,
            "normalizedRegion": None,
            "cropBounds": None,
            "sourceCropArtifactId": None,
            "candidateCropArtifactId": None,
        }
        region = raw_finding.get("region")
        if region is not None:
            pixel_region = _validated_region(region, source_w, source_h)
            crop_bounds = _bounded_crop(
                pixel_region,
                source_w,
                source_h,
                int(crop_padding_pixels),
                int(max_crop_pixels),
                index,
            )
            x, y, width, height = crop_bounds
            source_png = _encode_png(source[y : y + height, x : x + width])
            candidate_png = _encode_png(
                aligned_candidate[y : y + height, x : x + width]
            )
            source_crop_id = _artifact_id(source_png)
            candidate_crop_id = _artifact_id(candidate_png)
            artifacts.extend(
                (
                    EvidenceArtifact(
                        source_crop_id,
                        "review_source_crop",
                        f"page-{page_number}.finding-{index}.source.png",
                        "image/png",
                        source_png,
                        index,
                    ),
                    EvidenceArtifact(
                        candidate_crop_id,
                        "review_candidate_crop",
                        f"page-{page_number}.finding-{index}.candidate.png",
                        "image/png",
                        candidate_png,
                        index,
                    ),
                )
            )
            entry.update(
                {
                    "sourceRegion": pixel_region,
                    "normalizedRegion": _normalized_region(
                        pixel_region, source_w, source_h
                    ),
                    "cropBounds": {
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height,
                    },
                    "sourceCropArtifactId": source_crop_id,
                    "candidateCropArtifactId": candidate_crop_id,
                }
            )
        bundle_findings.append(entry)

    artifact_manifest = [
        {
            "artifactId": item.artifact_id,
            "role": item.role,
            "name": item.name,
            "mediaType": item.media_type,
            "byteSize": len(item.data),
            "findingIndex": item.finding_index,
        }
        for item in artifacts
    ]
    bundle = {
        "schemaVersion": SCHEMA_VERSION,
        "generatorVersion": GENERATOR_VERSION,
        "status": "completed",
        "automaticApproval": False,
        "semanticRecognitionClaimed": False,
        "pageNumber": page_number,
        "attemptId": attempt_id,
        "parents": {
            "sourceArtifactId": source_artifact_id,
            "candidateArtifactId": candidate_artifact_id,
            "safetyReportArtifactId": safety_report_artifact_id,
            "safetyReportId": safety_report_id,
        },
        "coordinateSpace": {
            "name": "source_pixels",
            "widthPixels": source_w,
            "heightPixels": source_h,
            "origin": "top_left",
            "normalizedRange": [0.0, 1.0],
        },
        "configuration": {
            "cropPaddingPixels": int(crop_padding_pixels),
            "maxRegions": int(max_regions),
            "maxCropPixels": int(max_crop_pixels),
        },
        "candidateTransform": transform,
        "displayIntegrity": {
            "cropEncoding": "png_grayscale_8bit",
            "interpolation": {
                "resize": "area",
                "registration": "linear",
            },
            "sourcePixelDigest": hashlib.sha256(
                source.tobytes(order="C")
            ).hexdigest(),
            "alignedCandidatePixelDigest": hashlib.sha256(
                aligned_candidate.tobytes(order="C")
            ).hexdigest(),
            "rendering": "grayscale_luminance_evidence",
            "inputColorProfiles": "not_inspected",
            "colorManagementValidated": False,
        },
        "navigation": {
            "findingCount": len(findings),
            "regionalFindingCount": regional_count,
            "pagination": "finding_index",
            "zoom": {
                "minimum": 0.25,
                "maximum": 8.0,
                "step": 0.25,
                "fitModes": ["fit_width", "fit_region", "actual_pixels"],
            },
            "keyboardOrder": [
                "previous_finding",
                "next_finding",
                "source_view",
                "candidate_view",
                "approve",
                "reject",
                "reprocess",
            ],
            "screenReaderLabelsRequired": True,
        },
        "findings": bundle_findings,
        "artifacts": artifact_manifest,
        "reviewBinding": {
            "requiredEvidenceBundleArtifactId": True,
            "trainingConsentImplied": False,
        },
    }
    bundle_bytes = _canonical_json_bytes(bundle)
    return ReviewEvidenceResult(bundle, bundle_bytes, tuple(artifacts))


def _validate_configuration(
    *,
    crop_padding_pixels: int,
    max_regions: int,
    max_crop_pixels: int,
) -> None:
    if not 0 <= int(crop_padding_pixels) <= 512:
        raise ReviewEvidenceError(
            "invalid_evidence_configuration",
            "crop padding is outside the supported range.",
        )
    if not 0 <= int(max_regions) <= 256:
        raise ReviewEvidenceError(
            "invalid_evidence_configuration",
            "max_regions is outside the supported range.",
        )
    if not 1 <= int(max_crop_pixels) <= 40_000_000:
        raise ReviewEvidenceError(
            "invalid_evidence_configuration",
            "max_crop_pixels is outside the supported range.",
        )


def _validate_parent_bytes(data: bytes, artifact_id: str, role: str) -> None:
    if not isinstance(data, bytes) or not data:
        raise ReviewEvidenceError(
            f"invalid_{role}",
            f"Non-empty {role} bytes are required.",
        )
    if len(data) > DEFAULT_MAX_INPUT_BYTES:
        raise ReviewEvidenceError(
            f"{role}_input_too_large",
            f"The {role} exceeds the review-evidence byte limit.",
            details={
                "byteSize": len(data),
                "maxInputBytes": DEFAULT_MAX_INPUT_BYTES,
            },
        )
    digest = hashlib.sha256(data).hexdigest()
    if artifact_id != f"sha256:{digest}":
        raise ReviewEvidenceError(
            "evidence_parent_mismatch",
            f"The {role} artifact ID does not match supplied bytes.",
        )


def _decode_grayscale(data: bytes, role: str) -> np.ndarray:
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None or image.ndim != 2 or image.size == 0:
        raise ReviewEvidenceError(
            f"{role}_decode_failed",
            f"The {role} could not be decoded for review evidence.",
        )
    pixels = int(image.shape[0]) * int(image.shape[1])
    if pixels > DEFAULT_MAX_DECODE_PIXELS:
        raise ReviewEvidenceError(
            f"{role}_decoded_image_too_large",
            f"The decoded {role} exceeds the review-evidence pixel limit.",
            details={
                "decodedPixels": pixels,
                "maxDecodePixels": DEFAULT_MAX_DECODE_PIXELS,
            },
        )
    return image


def _require_declared_dimensions(
    declared: Mapping[str, Any],
    image: np.ndarray,
    role: str,
) -> None:
    try:
        width = int(declared.get("widthPixels", -1))
        height = int(declared.get("heightPixels", -1))
    except (TypeError, ValueError) as error:
        raise ReviewEvidenceError(
            "evidence_dimension_mismatch",
            f"Safety report {role} dimensions are invalid.",
        ) from error
    if width != int(image.shape[1]) or height != int(image.shape[0]):
        raise ReviewEvidenceError(
            "evidence_dimension_mismatch",
            f"Safety report {role} dimensions do not match decoded bytes.",
        )


def _align_candidate(
    candidate: np.ndarray,
    source_shape: tuple[int, int],
    registration: Mapping[str, Any],
) -> tuple[np.ndarray, dict[str, Any]]:
    source_h, source_w = source_shape
    resized = candidate.shape != source_shape
    report_resized = registration.get("resizedToSource") is True
    if resized != report_resized:
        raise ReviewEvidenceError(
            "invalid_registration_provenance",
            "Decoded dimensions disagree with resizedToSource provenance.",
        )
    if resized:
        candidate = cv2.resize(
            candidate,
            (source_w, source_h),
            interpolation=cv2.INTER_AREA,
        )
    method = registration.get("method")
    dx = _finite_number(registration.get("translationX"), "translationX")
    dy = _finite_number(registration.get("translationY"), "translationY")
    reliable = registration.get("reliable") is True
    if method != "phase_correlation_translation":
        raise ReviewEvidenceError(
            "unsupported_registration_provenance",
            "Unsupported safety-report registration method.",
        )
    applied = reliable and (abs(dx) > 0.05 or abs(dy) > 0.05)
    if applied:
        matrix = np.array(
            [[1.0, 0.0, -dx], [0.0, 1.0, -dy]],
            dtype=np.float32,
        )
        candidate = cv2.warpAffine(
            candidate,
            matrix,
            (source_w, source_h),
            flags=cv2.INTER_LINEAR,
            borderValue=255,
        )
    return candidate, {
        "method": method,
        "resizedToSource": resized,
        "reportResizedToSource": report_resized,
        "translationX": dx,
        "translationY": dy,
        "reliable": reliable,
        "translationApplied": applied,
        "candidateToSourceMatrix": [
            [1.0, 0.0, round(-dx if applied else 0.0, 6)],
            [0.0, 1.0, round(-dy if applied else 0.0, 6)],
        ],
    }


def _validated_region(value: Any, width: int, height: int) -> dict[str, int]:
    if not isinstance(value, Mapping):
        raise ReviewEvidenceError(
            "invalid_evidence_region",
            "Safety finding region must be an object.",
        )
    try:
        x = int(value["x"])
        y = int(value["y"])
        region_width = int(value["width"])
        region_height = int(value["height"])
    except (KeyError, TypeError, ValueError) as error:
        raise ReviewEvidenceError(
            "invalid_evidence_region",
            "Safety finding region coordinates are invalid.",
        ) from error
    if (
        x < 0
        or y < 0
        or region_width < 1
        or region_height < 1
        or x >= width
        or y >= height
    ):
        raise ReviewEvidenceError(
            "invalid_evidence_region",
            "Safety finding region is outside the source page.",
        )
    return {
        "x": x,
        "y": y,
        "width": min(region_width, width - x),
        "height": min(region_height, height - y),
    }


def _bounded_crop(
    region: Mapping[str, int],
    width: int,
    height: int,
    padding: int,
    max_crop_pixels: int,
    finding_index: int,
) -> tuple[int, int, int, int]:
    bounds = _padded_bounds(region, width, height, padding)
    if bounds[2] * bounds[3] > max_crop_pixels:
        bounds = _padded_bounds(region, width, height, 0)
    if bounds[2] * bounds[3] > max_crop_pixels:
        raise ReviewEvidenceError(
            "evidence_crop_too_large",
            "A safety finding region exceeds the configured crop pixel limit.",
            details={
                "findingIndex": finding_index,
                "cropPixels": bounds[2] * bounds[3],
            },
        )
    return bounds


def _padded_bounds(
    region: Mapping[str, int],
    width: int,
    height: int,
    padding: int,
) -> tuple[int, int, int, int]:
    x0 = max(0, int(region["x"]) - padding)
    y0 = max(0, int(region["y"]) - padding)
    x1 = min(width, int(region["x"]) + int(region["width"]) + padding)
    y1 = min(height, int(region["y"]) + int(region["height"]) + padding)
    return x0, y0, x1 - x0, y1 - y0


def _normalized_region(
    region: Mapping[str, int],
    width: int,
    height: int,
) -> dict[str, float]:
    return {
        "x": round(int(region["x"]) / width, 8),
        "y": round(int(region["y"]) / height, 8),
        "width": round(int(region["width"]) / width, 8),
        "height": round(int(region["height"]) / height, 8),
    }


def _encode_png(image: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(
        ".png",
        image,
        [cv2.IMWRITE_PNG_COMPRESSION, 9],
    )
    if not ok:
        raise ReviewEvidenceError(
            "evidence_encode_failed",
            "A review evidence crop could not be encoded.",
        )
    return bytes(encoded)


def _finite_number(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ReviewEvidenceError(
            "invalid_registration_provenance",
            f"{field} must be a finite number.",
        )
    return round(float(value), 6)


def _artifact_id(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
