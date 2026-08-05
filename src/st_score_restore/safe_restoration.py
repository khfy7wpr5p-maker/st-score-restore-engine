"""Deterministic, non-generative OpenCV restoration candidate engine."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
from pathlib import Path, PureWindowsPath
from typing import Any, Mapping

import cv2
import numpy as np

from .input_inspection import inspect_bytes
from .restoration_encoding import encode_candidate, output_format_from_suffix
from .restoration_geometry import (
    apply_crop,
    apply_orientation,
    apply_perspective,
    deskew,
    detect_page_quad,
    make_protected_mask,
    to_gray,
)
from .restoration_photometric import (
    adjust_contrast,
    binarize,
    conservative_denoise,
    normalize_illumination,
)
from .restoration_types import (
    ENGINE_VERSION,
    SCHEMA_VERSION,
    RestorationCandidate,
    RestorationConfig,
    RestorationError,
)


def restore_bytes(
    data: bytes,
    *,
    source_name: str | None = None,
    config: RestorationConfig | Mapping[str, Any] | None = None,
    output_format: str = "png",
    protected_mask: np.ndarray | None = None,
    candidate_name: str | None = None,
) -> RestorationCandidate:
    """Create a deterministic candidate while preserving the immutable source."""

    if not isinstance(data, bytes) or not data:
        raise RestorationError(
            "invalid_source",
            "A non-empty immutable byte sequence is required.",
        )
    resolved_config = (
        config
        if isinstance(config, RestorationConfig)
        else RestorationConfig.from_mapping(config)
    )
    if output_format not in {"png", "jpeg", "pdf"}:
        raise RestorationError(
            "unsupported_output_format",
            "Output must be png, jpeg, or pdf.",
        )

    inspected = inspect_bytes(data, source_name=source_name)
    source = inspected["artifact"]
    analysis = inspected["analysis"]
    if analysis["inputKind"] == "pdf":
        classification = analysis["document"]["classification"]
        if classification == "digital":
            raise RestorationError(
                "digital_pdf_must_remain_vector",
                "A digital PDF must remain vector.",
                details={"recommendedAction": "preserve_vector_pdf"},
            )
        raise RestorationError(
            "pdf_renderer_not_available",
            "PDF restoration requires an approved renderer.",
            details={"classification": classification},
        )

    image_metadata = analysis.get("imageMetadata") or {}
    encoded_width = image_metadata.get("encodedWidthPixels")
    encoded_height = image_metadata.get("encodedHeightPixels")
    if encoded_width and encoded_height:
        declared_pixels = int(encoded_width) * int(encoded_height)
        if declared_pixels > resolved_config.max_decode_pixels:
            raise RestorationError(
                "decoded_image_too_large",
                "The declared image dimensions exceed the configured pixel limit.",
                details={
                    "declaredPixels": declared_pixels,
                    "maxDecodePixels": resolved_config.max_decode_pixels,
                },
            )

    flags = cv2.IMREAD_UNCHANGED | getattr(cv2, "IMREAD_IGNORE_ORIENTATION", 0)
    image = cv2.imdecode(np.frombuffer(data, np.uint8), flags)
    if image is None:
        raise RestorationError(
            "image_decode_failed",
            "OpenCV could not decode the accepted image.",
        )
    decoded_pixels = int(image.shape[0]) * int(image.shape[1])
    if decoded_pixels > resolved_config.max_decode_pixels:
        raise RestorationError(
            "decoded_image_too_large",
            "The decoded image exceeds the configured pixel limit.",
            details={
                "decodedPixels": decoded_pixels,
                "maxDecodePixels": resolved_config.max_decode_pixels,
            },
        )

    gray = to_gray(image)
    operations: list[dict[str, Any]] = []
    review_reasons: list[str] = []
    exif_value = (
        ((analysis.get("imageMetadata") or {}).get("exifOrientation") or {}).get(
            "exifValue"
        )
    )
    gray, operation = apply_orientation(
        gray,
        exif_value,
        resolved_config.orientation_enabled,
    )
    operations.append(operation)

    protected = make_protected_mask(gray, protected_mask, resolved_config)
    initial_fraction = np.count_nonzero(protected) / protected.size
    if initial_fraction > resolved_config.max_protected_fraction:
        review_reasons.append("protected_region_fraction_high")
    aligned = gray.copy()

    gray, protected, aligned, operation, new_reasons = deskew(
        gray,
        protected,
        aligned,
        resolved_config,
    )
    operations.append(operation)
    review_reasons.extend(new_reasons)

    quad, geometry_evidence = detect_page_quad(gray, resolved_config)
    gray, protected, aligned, operation, new_reasons = apply_perspective(
        gray,
        protected,
        aligned,
        quad,
        geometry_evidence,
        resolved_config,
    )
    operations.append(operation)
    review_reasons.extend(new_reasons)
    perspective_applied = operation["applied"]

    gray, protected, aligned, operation, new_reasons = apply_crop(
        gray,
        protected,
        aligned,
        quad,
        geometry_evidence,
        resolved_config,
        perspective_applied,
    )
    operations.append(operation)
    review_reasons.extend(new_reasons)

    gray, operation = normalize_illumination(
        gray,
        aligned,
        protected,
        resolved_config,
    )
    operations.append(operation)
    gray, operation = conservative_denoise(
        gray,
        aligned,
        protected,
        resolved_config,
    )
    operations.append(operation)
    gray, operation = adjust_contrast(
        gray,
        aligned,
        protected,
        resolved_config,
    )
    operations.append(operation)
    gray, operation, new_reasons = binarize(
        gray,
        aligned,
        protected,
        resolved_config,
    )
    operations.append(operation)
    review_reasons.extend(new_reasons)

    protected_pixels_made_lighter = int(
        np.count_nonzero((gray > aligned) & protected)
    )
    if protected_pixels_made_lighter:
        raise RestorationError(
            "protected_pixel_invariant_failed",
            "Protected notation pixels became lighter.",
            details={"count": protected_pixels_made_lighter},
        )

    output_bytes, media_type = encode_candidate(
        gray,
        output_format,
        resolved_config,
    )
    output_digest = hashlib.sha256(output_bytes).hexdigest()
    source_digest = source["digest"]["value"]
    review_reasons = sorted(set(review_reasons))
    protected_count = int(np.count_nonzero(protected))
    protected_fraction = protected_count / protected.size

    resolved_candidate_name = _candidate_name(
        candidate_name,
        source.get("sourceName"),
        output_format,
    )
    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "engineVersion": ENGINE_VERSION,
        "engine": "opencv_safe_baseline",
        "status": "review_required" if review_reasons else "candidate_ready",
        "sourceArtifactId": source["artifactId"],
        "sourceDigest": {"algorithm": "sha256", "value": source_digest},
        "sourceReturnedUnmodified": hashlib.sha256(data).hexdigest() == source_digest,
        "configuration": asdict(resolved_config),
        "configurationDigest": {
            "algorithm": "sha256",
            "value": resolved_config.digest(),
        },
        "candidate": {
            "artifactId": f"sha256:{output_digest}",
            "candidateName": resolved_candidate_name,
            "role": "restoration_candidate",
            "immutable": True,
            "derivedFrom": source["artifactId"],
            "mediaType": media_type,
            "byteSize": len(output_bytes),
            "digest": {"algorithm": "sha256", "value": output_digest},
            "widthPixels": gray.shape[1],
            "heightPixels": gray.shape[0],
            "teacherApproved": False,
        },
        "safety": {
            "generativeOperationsUsed": False,
            "symbolCompletionUsed": False,
            "protectedPixelCount": protected_count,
            "protectedPixelFraction": round(float(protected_fraction), 8),
            "protectedPixelsMadeLighter": protected_pixels_made_lighter,
            "reviewRequiredReasons": review_reasons,
        },
        "operations": operations,
    }
    return RestorationCandidate(data, output_bytes, manifest)


def restore_path(
    source_path: str | Path,
    output_path: str | Path,
    *,
    config: RestorationConfig | Mapping[str, Any] | None = None,
    protected_mask: np.ndarray | None = None,
) -> dict[str, Any]:
    """Restore a regular file to a new path without following symlinks or overwriting."""

    source = Path(source_path)
    output = Path(output_path)
    if source.is_symlink():
        raise RestorationError(
            "symlink_input_not_allowed",
            "Symbolic-link inputs are rejected to preserve a stable source boundary.",
        )
    try:
        before = source.stat()
    except OSError as error:
        raise RestorationError(
            "source_read_failed",
            "The source could not be read.",
            details={"osError": str(error)},
        ) from error
    if not source.is_file():
        raise RestorationError(
            "input_not_regular_file",
            "The source must be a regular file.",
        )
    if source.resolve() == output.resolve():
        raise RestorationError(
            "source_overwrite_forbidden",
            "The output path must differ from the source.",
        )
    if output.exists():
        raise RestorationError(
            "derived_output_exists",
            "The derived output already exists.",
        )
    try:
        raw = source.read_bytes()
        after = source.stat()
    except OSError as error:
        raise RestorationError(
            "source_read_failed",
            "The source could not be read.",
            details={"osError": str(error)},
        ) from error
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if before_identity != after_identity:
        raise RestorationError(
            "source_changed_during_read",
            "The source changed while it was being read.",
        )

    candidate = restore_bytes(
        raw,
        source_name=source.name,
        config=config,
        output_format=output_format_from_suffix(output.suffix),
        protected_mask=protected_mask,
        candidate_name=output.name,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("xb") as handle:
            handle.write(candidate.output_bytes)
    except FileExistsError as error:
        raise RestorationError(
            "derived_output_exists",
            "The derived output already exists.",
        ) from error
    except OSError as error:
        try:
            output.unlink(missing_ok=True)
        except OSError:
            pass
        raise RestorationError(
            "derived_output_write_failed",
            "The derived output could not be written.",
            details={"osError": str(error)},
        ) from error
    return candidate.manifest


def _candidate_name(
    requested: str | None,
    source_name: str | None,
    output_format: str,
) -> str:
    suffix = {"png": ".png", "jpeg": ".jpg", "pdf": ".pdf"}[output_format]
    if requested:
        normalized = requested.replace("\\", "/")
        name = PureWindowsPath(normalized).name
        if name not in {"", ".", ".."}:
            return name
    source = source_name or "source"
    stem = Path(source).stem or "source"
    return f"{stem}.restored{suffix}"


__all__ = [
    "ENGINE_VERSION",
    "SCHEMA_VERSION",
    "RestorationCandidate",
    "RestorationConfig",
    "RestorationError",
    "restore_bytes",
    "restore_path",
]
