"""Deterministic reviewer evidence crops and bundle generation."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping

import cv2
import numpy as np

SCHEMA_VERSION = "1.0.0"
GENERATOR_VERSION = "0.4.0"


class ReviewEvidenceError(ValueError):
    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "evidence_failed",
            "automaticApproval": False,
            "error": {"code": self.code, "message": self.message, "details": self.details},
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
    """Create byte-stable reviewer evidence without claiming semantic meaning."""

    if not isinstance(source_bytes, bytes) or not source_bytes:
        raise ReviewEvidenceError("invalid_source", "Non-empty source bytes are required.")
    if not isinstance(candidate_bytes, bytes) or not candidate_bytes:
        raise ReviewEvidenceError("invalid_candidate", "Non-empty candidate bytes are required.")
    if not isinstance(safety_report, Mapping):
        raise ReviewEvidenceError("invalid_safety_report", "A safety report object is required.")
    if safety_report.get("status") != "completed" or safety_report.get("automaticApproval") is not False:
        raise ReviewEvidenceError("invalid_safety_report", "Evidence requires a completed non-approving safety report.")
    if not isinstance(page_number, int) or page_number < 1:
        raise ReviewEvidenceError("invalid_page_number", "page_number must be a positive integer.")
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        raise ReviewEvidenceError("invalid_attempt_id", "attempt_id is required.")
    if not 0 <= int(crop_padding_pixels) <= 512:
        raise ReviewEvidenceError("invalid_evidence_configuration", "crop padding is outside the supported range.")
    if not 0 <= int(max_regions) <= 256:
        raise ReviewEvidenceError("invalid_evidence_configuration", "max_regions is outside the supported range.")
    if not 1 <= int(max_crop_pixels) <= 40_000_000:
        raise ReviewEvidenceError("invalid_evidence_configuration", "max_crop_pixels is outside the supported range.")

    source_digest = hashlib.sha256(source_bytes).hexdigest()
    candidate_digest = hashlib.sha256(candidate_bytes).hexdigest()
    _require_artifact_id(source_artifact_id, source_digest, "source")
    _require_artifact_id(candidate_artifact_id, candidate_digest, "candidate")
    report_source_id = ((safety_report.get("source") or {}).get("artifactId"))
    report_candidate_id = ((safety_report.get("candidate") or {}).get("artifactId"))
    if report_source_id != source_artifact_id or report_candidate_id != candidate_artifact_id:
        raise ReviewEvidenceError(
            "evidence_parent_mismatch",
            "Safety report parents do not match the supplied source and candidate.",
        )

    source = _decode_grayscale(source_bytes, "source")
    candidate = _decode_grayscale(candidate_bytes, "candidate")
    source_h, source_w = source.shape
    declared_source = safety_report.get("source") or {}
    declared_candidate = safety_report.get("candidate") or {}
    if int(declared_source.get("widthPixels", -1)) != source_w or int(declared_source.get("heightPixels", -1)) != source_h:
        raise ReviewEvidenceError("evidence_dimension_mismatch", "Safety report source dimensions do not match decoded bytes.")
    if int(declared_candidate.get("widthPixels", -1)) != int(candidate.shape[1]) or int(declared_candidate.get("heightPixels", -1)) != int(candidate.shape[0]):
        raise ReviewEvidenceError("evidence_dimension_mismatch", "Safety report candidate dimensions do not match decoded bytes.")

    registration = safety_report.get("registration") or {}
    aligned_candidate, transform = _align_candidate(candidate, source.shape, registration)
    findings = safety_report.get("findings")
    if not isinstance(findings, list):
        raise ReviewEvidenceError("invalid_safety_report", "Safety report findings must be an array.")

    regional_count = sum(1 for item in findings if isinstance(item, Mapping) and item.get("region") is not None)
    if regional_count > max_regions:
        raise ReviewEvidenceError(
            "too_many_evidence_regions",
            "Safety report contains more regional findings than the evidence limit.",
            details={"regionalFindings": regional_count, "maxRegions": max_regions},
        )

    artifacts: list[EvidenceArtifact] = []
    bundle_findings: list[dict[str, Any]] = []
    for index, raw in enumerate(findings):
        if not isinstance(raw, Mapping):
            raise ReviewEvidenceError("invalid_safety_report", "Every safety finding must be an object.")
        region = raw.get("region")
        entry: dict[str, Any] = {
            "findingIndex": index,
            "code": str(raw.get("code", "")),
            "severity": str(raw.get("severity", "")),
            "semanticCertainty": "not_claimed",
            "sourceRegion": None,
            "normalizedRegion": None,
            "cropBounds": None,
            "sourceCropArtifactId": None,
            "candidateCropArtifactId": None,
        }
        if region is not None:
            pixel_region = _validated_region(region, source_w, source_h)
            crop_bounds = _padded_bounds(pixel_region, source_w, source_h, int(crop_padding_pixels))
            if crop_bounds[2] * crop_bounds[3] > max_crop_pixels:
                crop_bounds = _padded_bounds(pixel_region, source_w, source_h, 0)
            if crop_bounds[2] * crop_bounds[3] > max_crop_pixels:
                raise ReviewEvidenceError(
                    "evidence_crop_too_large",
                    "A safety finding region exceeds the configured crop pixel limit.",
                    details={"findingIndex": index, "cropPixels": crop_bounds[2] * crop_bounds[3]},
                )
            x, y, width, height = crop_bounds
            source_crop = source[y : y + height, x : x + width]
            candidate_crop = aligned_candidate[y : y + height, x : x + width]
            source_png = _encode_png(source_crop)
            candidate_png = _encode_png(candidate_crop)
            source_crop_id = _artifact_id(source_png)
            candidate_crop_id = _artifact_id(candidate_png)
            artifacts.extend(
                (
                    EvidenceArtifact(source_crop_id, "review_source_crop", f"page-{page_number}.finding-{index}.source.png", "image/png", source_png, index),
                    EvidenceArtifact(candidate_crop_id, "review_candidate_crop", f"page-{page_number}.finding-{index}.candidate.png", "image/png", candidate_png, index),
                )
            )
            entry.update(
                {
                    "sourceRegion": pixel_region,
                    "normalizedRegion": _normalized_region(pixel_region, source_w, source_h),
                    "cropBounds": {"x": x, "y": y, "width": width, "height": height},
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
            "safetyReportId": safety_report.get("reportId"),
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
            "colorInterpretation": "grayscale_no_profile",
            "interpolation": {"resize": "area", "registration": "linear"},
            "sourcePixelDigest": hashlib.sha256(source.tobytes(order="C")).hexdigest(),
            "alignedCandidatePixelDigest": hashlib.sha256(aligned_candidate.tobytes(order="C")).hexdigest(),
        },
        "navigation": {
            "findingCount": len(findings),
            "regionalFindingCount": regional_count,
            "pagination": "finding_index",
            "zoom": {"minimum": 0.25, "maximum": 8.0, "step": 0.25, "fitModes": ["fit_width", "fit_region", "actual_pixels"]},
            "keyboardOrder": ["previous_finding", "next_finding", "source_view", "candidate_view", "approve", "reject", "reprocess"],
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


def _align_candidate(candidate: np.ndarray, source_shape: tuple[int, int], registration: Mapping[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    source_h, source_w = source_shape
    resized = candidate.shape != source_shape
    report_resized = registration.get("resizedToSource") is True
    if resized != report_resized:
        raise ReviewEvidenceError("invalid_registration_provenance", "Decoded dimensions disagree with resizedToSource provenance.")
    if resized:
        candidate = cv2.resize(candidate, (source_w, source_h), interpolation=cv2.INTER_AREA)
    method = registration.get("method")
    dx = _finite_number(registration.get("translationX"), "translationX")
    dy = _finite_number(registration.get("translationY"), "translationY")
    reliable = registration.get("reliable") is True
    if method != "phase_correlation_translation":
        raise ReviewEvidenceError("unsupported_registration_provenance", "Unsupported safety-report registration method.")
    applied = reliable and (abs(dx) > 0.05 or abs(dy) > 0.05)
    if applied:
        matrix = np.array([[1.0, 0.0, -dx], [0.0, 1.0, -dy]], dtype=np.float32)
        candidate = cv2.warpAffine(candidate, matrix, (source_w, source_h), flags=cv2.INTER_LINEAR, borderValue=255)
    return candidate, {
        "method": method,
        "resizedToSource": resized,
        "reportResizedToSource": report_resized,
        "translationX": dx,
        "translationY": dy,
        "reliable": reliable,
        "translationApplied": applied,
        "candidateToSourceMatrix": [[1.0, 0.0, round(-dx if applied else 0.0, 6)], [0.0, 1.0, round(-dy if applied else 0.0, 6)]],
    }


def _validated_region(value: Any, width: int, height: int) -> dict[str, int]:
    if not isinstance(value, Mapping):
        raise ReviewEvidenceError("invalid_evidence_region", "Safety finding region must be an object.")
    try:
        x = int(value["x"])
        y = int(value["y"])
        region_width = int(value["width"])
        region_height = int(value["height"])
    except (KeyError, TypeError, ValueError) as error:
        raise ReviewEvidenceError("invalid_evidence_region", "Safety finding region coordinates are invalid.") from error
    if x < 0 or y < 0 or region_width < 1 or region_height < 1 or x >= width or y >= height:
        raise ReviewEvidenceError("invalid_evidence_region", "Safety finding region is outside the source page.")
    clipped_width = min(region_width, width - x)
    clipped_height = min(region_height, height - y)
    return {"x": x, "y": y, "width": clipped_width, "height": clipped_height}


def _padded_bounds(region: Mapping[str, int], width: int, height: int, padding: int) -> tuple[int, int, int, int]:
    x0 = max(0, int(region["x"]) - padding)
    y0 = max(0, int(region["y"]) - padding)
    x1 = min(width, int(region["x"]) + int(region["width"]) + padding)
    y1 = min(height, int(region["y"]) + int(region["height"]) + padding)
    return x0, y0, x1 - x0, y1 - y0


def _normalized_region(region: Mapping[str, int], width: int, height: int) -> dict[str, float]:
    return {
        "x": round(int(region["x"]) / width, 8),
        "y": round(int(region["y"]) / height, 8),
        "width": round(int(region["width"]) / width, 8),
        "height": round(int(region["height"]) / height, 8),
    }


def _decode_grayscale(data: bytes, role: str) -> np.ndarray:
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None or image.ndim != 2 or image.size == 0:
        raise ReviewEvidenceError(f"{role}_decode_failed", f"The {role} could not be decoded for review evidence.")
    return image


def _encode_png(image: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    if not ok:
        raise ReviewEvidenceError("evidence_encode_failed", "A review evidence crop could not be encoded.")
    return bytes(encoded)


def _require_artifact_id(artifact_id: str, digest: str, role: str) -> None:
    if artifact_id != f"sha256:{digest}":
        raise ReviewEvidenceError("evidence_parent_mismatch", f"The {role} artifact ID does not match supplied bytes.")


def _finite_number(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ReviewEvidenceError("invalid_registration_provenance", f"{field} must be a finite number.")
    return round(float(value), 6)


def _artifact_id(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")