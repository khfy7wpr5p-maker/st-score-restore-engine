"""Read-only, deterministic input inspection for PDF, JPEG, and PNG files."""

from __future__ import annotations

import hashlib
import os
import re
import struct
import zlib
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
INSPECTOR_VERSION = "0.1.0"
DEFAULT_MAX_BYTES = 50_000_000

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PDF_HEADER_RE = re.compile(rb"%PDF-(\d\.\d)")
_PDF_PAGE_RE = re.compile(rb"/Type\s*/Page(?!s)\b")
_PDF_MEDIA_BOX_RE = re.compile(
    rb"/MediaBox\s*\[\s*([-+]?\d+(?:\.\d+)?)\s+([-+]?\d+(?:\.\d+)?)\s+"
    rb"([-+]?\d+(?:\.\d+)?)\s+([-+]?\d+(?:\.\d+)?)\s*\]"
)
_SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
}
_QUALITY_TYPES = (
    "perspective",
    "crop",
    "glare",
    "shadow",
    "blur",
    "noise",
    "compression",
    "low_resolution",
)


class InputInspectionError(ValueError):
    """A safe, actionable rejection with a stable machine-readable code."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

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


def inspect_path(
    path: str | Path,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> dict[str, Any]:
    """Inspect a regular file without writing to or replacing it."""

    source_path = Path(path)
    if source_path.is_symlink():
        raise InputInspectionError(
            "symlink_input_not_allowed",
            "Symbolic-link inputs are rejected to preserve a stable source boundary.",
        )

    try:
        before = source_path.stat()
    except OSError as error:
        raise InputInspectionError(
            "input_unreadable",
            "The input file could not be read.",
            details={"osError": str(error)},
        ) from error

    if not source_path.is_file():
        raise InputInspectionError(
            "input_not_regular_file",
            "The input must be a regular file.",
        )
    if before.st_size > max_bytes:
        raise InputInspectionError(
            "oversized_input",
            "The input exceeds the configured byte limit.",
            details={"byteSize": before.st_size, "maxBytes": max_bytes},
        )

    try:
        data = source_path.read_bytes()
        after = source_path.stat()
    except OSError as error:
        raise InputInspectionError(
            "input_unreadable",
            "The input file could not be read.",
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
        raise InputInspectionError(
            "source_changed_during_read",
            "The source changed while it was being inspected.",
        )

    return inspect_bytes(data, source_name=source_path.name, max_bytes=max_bytes)


def inspect_bytes(
    data: bytes,
    *,
    source_name: str | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> dict[str, Any]:
    """Inspect immutable bytes and return deterministic artifact and analysis manifests."""

    if not isinstance(data, bytes):
        raise InputInspectionError(
            "invalid_input_type",
            "The inspector accepts bytes only.",
        )
    if not data:
        raise InputInspectionError("empty_input", "The input is empty.")
    if len(data) > max_bytes:
        raise InputInspectionError(
            "oversized_input",
            "The input exceeds the configured byte limit.",
            details={"byteSize": len(data), "maxBytes": max_bytes},
        )

    digest = hashlib.sha256(data).hexdigest()
    detected_kind = _detect_kind(data)
    if detected_kind is None:
        raise InputInspectionError(
            "unsupported_media_type",
            "Only PDF, JPEG, and PNG inputs are supported.",
            details={
                "byteSize": len(data),
                "sha256": digest,
                "signatureHex": data[:12].hex(),
            },
        )

    safe_source_name = os.path.basename(source_name) if source_name else None
    supplied_extension = _safe_extension(safe_source_name)
    expected_kind = _SUPPORTED_EXTENSIONS.get(supplied_extension)
    extension_matches = (
        None if supplied_extension is None else expected_kind == detected_kind
    )

    if detected_kind == "pdf":
        parsed = _parse_pdf(data)
        media_type = "application/pdf"
    elif detected_kind == "png":
        parsed = _parse_png(data)
        media_type = "image/png"
    else:
        parsed = _parse_jpeg(data)
        media_type = "image/jpeg"

    warnings = list(parsed.pop("warnings"))
    if supplied_extension is not None and not extension_matches:
        warnings.append(
            _warning(
                "extension_content_mismatch",
                "warning",
                "The supplied filename extension does not match the detected content.",
                evidence=[
                    f"extension={supplied_extension}",
                    f"detectedKind={detected_kind}",
                ],
            )
        )

    artifact_id = f"sha256:{digest}"
    inspection_id = "inspection:" + hashlib.sha256(
        f"{INSPECTOR_VERSION}:{digest}".encode("ascii")
    ).hexdigest()

    artifact = {
        "schemaVersion": SCHEMA_VERSION,
        "artifactId": artifact_id,
        "role": "source",
        "immutable": True,
        "sourceName": safe_source_name,
        "byteSize": len(data),
        "digest": {"algorithm": "sha256", "value": digest},
        "detectedMediaType": media_type,
        "detectedKind": detected_kind,
        "derivedFrom": None,
    }

    analysis = {
        "schemaVersion": SCHEMA_VERSION,
        "inspectionId": inspection_id,
        "artifactId": artifact_id,
        "inspectorVersion": INSPECTOR_VERSION,
        "status": "accepted",
        "restorationPerformed": False,
        "inputKind": detected_kind,
        "suppliedExtension": supplied_extension,
        "extensionMatchesContent": extension_matches,
        "document": parsed["document"],
        "pages": parsed["pages"],
        "imageMetadata": parsed["imageMetadata"],
        "qualityFindings": parsed["qualityFindings"],
        "warnings": warnings,
        "recommendedAction": parsed["recommendedAction"],
    }
    return {"artifact": artifact, "analysis": analysis}


def _detect_kind(data: bytes) -> str | None:
    if data.startswith(_PNG_SIGNATURE):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if _PDF_HEADER_RE.match(data[:16]):
        return "pdf"
    return None


def _safe_extension(source_name: str | None) -> str | None:
    if source_name is None:
        return None
    suffix = Path(os.path.basename(source_name)).suffix.lower()
    return suffix or None


def _parse_pdf(data: bytes) -> dict[str, Any]:
    header = _PDF_HEADER_RE.match(data[:16])
    if header is None:
        raise InputInspectionError("malformed_pdf", "The PDF header is invalid.")
    if b"%%EOF" not in data[-4096:]:
        raise InputInspectionError(
            "malformed_pdf",
            "The PDF end-of-file marker is missing.",
        )
    if re.search(rb"/Encrypt\b", data):
        raise InputInspectionError(
            "encrypted_pdf",
            "Encrypted PDFs are not inspected in this milestone.",
        )

    page_count = len(_PDF_PAGE_RE.findall(data)) or None
    media_boxes = []
    for match in _PDF_MEDIA_BOX_RE.finditer(data):
        x0, y0, x1, y1 = (float(value) for value in match.groups())
        width = abs(x1 - x0)
        height = abs(y1 - y0)
        if width > 0 and height > 0:
            media_boxes.append((width, height))

    has_text_operators = bool(
        re.search(rb"\bBT\b[\s\S]{0,200000}?\bET\b", data)
        or re.search(rb"\bTj\b|\bTJ\b", data)
        or re.search(rb"/Font\b", data)
    )
    has_image_xobjects = bool(re.search(rb"/Subtype\s*/Image\b", data))
    has_object_streams = bool(re.search(rb"/Type\s*/ObjStm\b", data))

    if has_text_operators and has_image_xobjects:
        classification = "hybrid"
        confidence = "medium"
    elif has_text_operators:
        classification = "digital"
        confidence = "medium"
    elif has_image_xobjects:
        classification = "scanned"
        confidence = "medium"
    else:
        classification = "unknown"
        confidence = "low"

    warnings: list[dict[str, Any]] = []
    if page_count is None:
        warnings.append(
            _warning(
                "pdf_page_count_uncertain",
                "review_required",
                "No uncompressed page markers were found; page count is unknown.",
                evidence=["pageObjectMarkers=0"],
            )
        )
    if classification == "unknown":
        warnings.append(
            _warning(
                "pdf_classification_uncertain",
                "review_required",
                "The PDF could not be safely classified as digital, scanned, or hybrid.",
                evidence=[
                    f"hasTextEvidence={str(has_text_operators).lower()}",
                    f"hasImageEvidence={str(has_image_xobjects).lower()}",
                    f"hasObjectStreams={str(has_object_streams).lower()}",
                ],
            )
        )
    if has_object_streams:
        warnings.append(
            _warning(
                "pdf_object_streams_present",
                "info",
                "Compressed object streams may hide structural evidence from the baseline inspector.",
                evidence=["/Type /ObjStm"],
            )
        )

    pages: list[dict[str, Any]] = []
    if page_count is not None:
        for index in range(page_count):
            box = media_boxes[index] if index < len(media_boxes) else (
                media_boxes[0] if media_boxes else None
            )
            pages.append(
                {
                    "pageIndex": index,
                    "width": box[0] if box else None,
                    "height": box[1] if box else None,
                    "unit": "points",
                    "orientation": _page_orientation(box),
                    "dpiEstimate": None,
                }
            )

    if classification == "digital":
        recommended_action = "preserve_vector_pdf"
    elif classification in {"scanned", "hybrid"}:
        recommended_action = "review_before_raster_processing"
    else:
        recommended_action = "manual_review_required"

    return {
        "document": {
            "pdfVersion": header.group(1).decode("ascii"),
            "pageCount": page_count,
            "pageCountMethod": (
                "uncompressed_page_object_markers" if page_count is not None else "unknown"
            ),
            "classification": classification,
            "classificationConfidence": confidence,
            "encrypted": False,
            "structuralEvidence": {
                "hasTextOperatorsOrFonts": has_text_operators,
                "hasImageXObjects": has_image_xobjects,
                "hasObjectStreams": has_object_streams,
                "mediaBoxCount": len(media_boxes),
            },
        },
        "pages": pages,
        "imageMetadata": None,
        "qualityFindings": _baseline_quality_findings(
            page_count=page_count,
            image_width=None,
            image_height=None,
            dpi=None,
            is_pdf=True,
        ),
        "warnings": warnings,
        "recommendedAction": recommended_action,
    }


def _parse_png(data: bytes) -> dict[str, Any]:
    if not data.startswith(_PNG_SIGNATURE):
        raise InputInspectionError("malformed_png", "The PNG signature is invalid.")

    offset = len(_PNG_SIGNATURE)
    ihdr: bytes | None = None
    physical: tuple[int, int, int] | None = None
    exif_orientation: int | None = None
    saw_iend = False

    while offset < len(data):
        if len(data) - offset < 12:
            raise InputInspectionError("malformed_png", "A PNG chunk is truncated.")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_end = offset + 12 + length
        if chunk_end > len(data):
            raise InputInspectionError(
                "malformed_png",
                "A PNG chunk length exceeds the available bytes.",
            )
        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : chunk_end])[0]
        actual_crc = zlib.crc32(chunk_type)
        actual_crc = zlib.crc32(payload, actual_crc) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise InputInspectionError(
                "malformed_png",
                "A PNG chunk CRC is invalid.",
                details={"chunkType": chunk_type.decode("latin-1")},
            )

        if chunk_type == b"IHDR":
            if ihdr is not None or length != 13:
                raise InputInspectionError("malformed_png", "The PNG IHDR chunk is invalid.")
            ihdr = payload
        elif chunk_type == b"pHYs" and length == 9:
            physical = (
                struct.unpack(">I", payload[0:4])[0],
                struct.unpack(">I", payload[4:8])[0],
                payload[8],
            )
        elif chunk_type == b"eXIf":
            exif_orientation = _parse_tiff_orientation(payload)
        elif chunk_type == b"IEND":
            if length != 0:
                raise InputInspectionError("malformed_png", "The PNG IEND chunk is invalid.")
            saw_iend = True
            offset = chunk_end
            break
        offset = chunk_end

    if ihdr is None or not saw_iend:
        raise InputInspectionError(
            "malformed_png",
            "The PNG is missing required IHDR or IEND chunks.",
        )
    if offset != len(data):
        raise InputInspectionError(
            "malformed_png",
            "Unexpected trailing bytes follow the PNG IEND chunk.",
        )

    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", ihdr
    )
    if width <= 0 or height <= 0:
        raise InputInspectionError("malformed_png", "PNG dimensions must be positive.")
    if compression != 0 or filtering != 0 or interlace not in {0, 1}:
        raise InputInspectionError(
            "malformed_png",
            "The PNG uses unsupported structural parameters.",
        )

    dpi = _png_dpi(physical)
    orientation = _orientation_details(exif_orientation)
    display_width, display_height = _display_dimensions(width, height, orientation)

    return {
        "document": {
            "pdfVersion": None,
            "pageCount": 1,
            "pageCountMethod": "single_image",
            "classification": "not_applicable",
            "classificationConfidence": "not_applicable",
            "encrypted": False,
            "structuralEvidence": {
                "pngBitDepth": bit_depth,
                "pngColorType": color_type,
                "pngInterlaceMethod": interlace,
            },
        },
        "pages": [
            {
                "pageIndex": 0,
                "width": display_width,
                "height": display_height,
                "unit": "pixels",
                "orientation": _image_orientation_label(display_width, display_height),
                "dpiEstimate": dpi,
            }
        ],
        "imageMetadata": {
            "encodedWidthPixels": width,
            "encodedHeightPixels": height,
            "displayWidthPixels": display_width,
            "displayHeightPixels": display_height,
            "exifOrientation": orientation,
            "dpiEstimate": dpi,
            "encoding": {
                "format": "png",
                "bitDepth": bit_depth,
                "colorType": color_type,
                "interlaced": interlace == 1,
            },
        },
        "qualityFindings": _baseline_quality_findings(
            page_count=1,
            image_width=display_width,
            image_height=display_height,
            dpi=dpi,
            is_pdf=False,
        ),
        "warnings": _image_warnings(
            "png", width, height, display_width, display_height, dpi, orientation
        ),
        "recommendedAction": "review_quality_before_restoration",
    }


def _parse_jpeg(data: bytes) -> dict[str, Any]:
    if not data.startswith(b"\xff\xd8"):
        raise InputInspectionError("malformed_jpeg", "The JPEG SOI marker is missing.")
    if b"\xff\xd9" not in data[2:]:
        raise InputInspectionError("malformed_jpeg", "The JPEG EOI marker is missing.")

    offset = 2
    width: int | None = None
    height: int | None = None
    precision: int | None = None
    components: int | None = None
    dpi: dict[str, Any] | None = None
    exif_orientation: int | None = None
    saw_sos = False

    while offset < len(data):
        if data[offset] != 0xFF:
            if saw_sos:
                break
            raise InputInspectionError(
                "malformed_jpeg",
                "Unexpected bytes occur outside a JPEG segment.",
            )
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1

        if marker == 0xD9:
            break
        if marker == 0xDA:
            saw_sos = True
            if offset + 2 > len(data):
                raise InputInspectionError("malformed_jpeg", "The JPEG SOS is truncated.")
            segment_length = struct.unpack(">H", data[offset : offset + 2])[0]
            if segment_length < 2 or offset + segment_length > len(data):
                raise InputInspectionError("malformed_jpeg", "The JPEG SOS is invalid.")
            offset += segment_length
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            raise InputInspectionError("malformed_jpeg", "A JPEG segment is truncated.")
        segment_length = struct.unpack(">H", data[offset : offset + 2])[0]
        if segment_length < 2 or offset + segment_length > len(data):
            raise InputInspectionError("malformed_jpeg", "A JPEG segment length is invalid.")
        payload = data[offset + 2 : offset + segment_length]

        if marker == 0xE0 and payload.startswith(b"JFIF\x00") and len(payload) >= 12:
            unit = payload[7]
            x_density = struct.unpack(">H", payload[8:10])[0]
            y_density = struct.unpack(">H", payload[10:12])[0]
            if unit == 1 and x_density and y_density:
                dpi = _dpi_object(float(x_density), float(y_density), "jfif")
            elif unit == 2 and x_density and y_density:
                dpi = _dpi_object(x_density * 2.54, y_density * 2.54, "jfif")
        elif marker == 0xE1 and payload.startswith(b"Exif\x00\x00"):
            exif_orientation = _parse_tiff_orientation(payload[6:])
        elif marker in {
            0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
            0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
        }:
            if len(payload) < 6:
                raise InputInspectionError("malformed_jpeg", "The JPEG SOF is truncated.")
            precision = payload[0]
            height = struct.unpack(">H", payload[1:3])[0]
            width = struct.unpack(">H", payload[3:5])[0]
            components = payload[5]

        offset += segment_length

    if width is None or height is None or width <= 0 or height <= 0:
        raise InputInspectionError(
            "malformed_jpeg",
            "No valid JPEG frame dimensions were found.",
        )

    orientation = _orientation_details(exif_orientation)
    display_width, display_height = _display_dimensions(width, height, orientation)

    return {
        "document": {
            "pdfVersion": None,
            "pageCount": 1,
            "pageCountMethod": "single_image",
            "classification": "not_applicable",
            "classificationConfidence": "not_applicable",
            "encrypted": False,
            "structuralEvidence": {
                "jpegPrecision": precision,
                "jpegComponents": components,
                "hasStartOfScan": saw_sos,
            },
        },
        "pages": [
            {
                "pageIndex": 0,
                "width": display_width,
                "height": display_height,
                "unit": "pixels",
                "orientation": _image_orientation_label(display_width, display_height),
                "dpiEstimate": dpi,
            }
        ],
        "imageMetadata": {
            "encodedWidthPixels": width,
            "encodedHeightPixels": height,
            "displayWidthPixels": display_width,
            "displayHeightPixels": display_height,
            "exifOrientation": orientation,
            "dpiEstimate": dpi,
            "encoding": {
                "format": "jpeg",
                "samplePrecision": precision,
                "components": components,
                "compressed": True,
            },
        },
        "qualityFindings": _baseline_quality_findings(
            page_count=1,
            image_width=display_width,
            image_height=display_height,
            dpi=dpi,
            is_pdf=False,
        ),
        "warnings": _image_warnings(
            "jpeg", width, height, display_width, display_height, dpi, orientation
        ),
        "recommendedAction": "review_quality_before_restoration",
    }


def _parse_tiff_orientation(tiff: bytes) -> int | None:
    if len(tiff) < 8:
        return None
    if tiff[:2] == b"II":
        byte_order = "<"
    elif tiff[:2] == b"MM":
        byte_order = ">"
    else:
        return None
    try:
        if struct.unpack(byte_order + "H", tiff[2:4])[0] != 42:
            return None
        ifd_offset = struct.unpack(byte_order + "I", tiff[4:8])[0]
        if ifd_offset + 2 > len(tiff):
            return None
        count = struct.unpack(byte_order + "H", tiff[ifd_offset : ifd_offset + 2])[0]
        entries_start = ifd_offset + 2
        for index in range(count):
            start = entries_start + index * 12
            end = start + 12
            if end > len(tiff):
                return None
            tag, field_type, value_count = struct.unpack(
                byte_order + "HHI", tiff[start : start + 8]
            )
            if tag == 0x0112 and field_type == 3 and value_count == 1:
                value = struct.unpack(
                    byte_order + "H", tiff[start + 8 : start + 10]
                )[0]
                return value if 1 <= value <= 8 else None
    except (struct.error, OverflowError):
        return None
    return None


def _png_dpi(physical: tuple[int, int, int] | None) -> dict[str, Any] | None:
    if physical is None:
        return None
    x_ppm, y_ppm, unit = physical
    if unit != 1 or x_ppm <= 0 or y_ppm <= 0:
        return None
    return _dpi_object(x_ppm * 0.0254, y_ppm * 0.0254, "png_pHYs")


def _dpi_object(x: float, y: float, source: str) -> dict[str, Any]:
    return {
        "x": round(x, 3),
        "y": round(y, 3),
        "unit": "dpi",
        "source": source,
    }


def _orientation_details(value: int | None) -> dict[str, Any]:
    mapping = {
        1: (0, False, False),
        2: (0, True, False),
        3: (180, False, False),
        4: (180, True, False),
        5: (90, True, True),
        6: (90, False, True),
        7: (270, True, True),
        8: (270, False, True),
    }
    rotation, mirrored, swaps_dimensions = mapping.get(value or 1, (0, False, False))
    return {
        "exifValue": value,
        "rotationDegrees": rotation,
        "mirrored": mirrored,
        "swapsDimensions": swaps_dimensions,
        "appliedToSource": False,
    }


def _display_dimensions(
    width: int,
    height: int,
    orientation: dict[str, Any],
) -> tuple[int, int]:
    if orientation["swapsDimensions"]:
        return height, width
    return width, height


def _page_orientation(box: tuple[float, float] | None) -> str | None:
    if box is None:
        return None
    return "landscape" if box[0] > box[1] else "portrait"


def _image_orientation_label(width: int, height: int) -> str:
    if width == height:
        return "square"
    return "landscape" if width > height else "portrait"


def _image_warnings(
    kind: str,
    encoded_width: int,
    encoded_height: int,
    display_width: int,
    display_height: int,
    dpi: dict[str, Any] | None,
    orientation: dict[str, Any],
) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    if orientation["exifValue"] not in {None, 1}:
        warnings.append(
            _warning(
                "display_orientation_from_metadata",
                "info",
                "Display dimensions account for EXIF orientation; source bytes were not changed.",
                page_index=0,
                evidence=[
                    f"exifOrientation={orientation['exifValue']}",
                    f"encoded={encoded_width}x{encoded_height}",
                    f"display={display_width}x{display_height}",
                ],
            )
        )
    warnings.append(
        _warning(
            "pixel_quality_analysis_limited",
            "info",
            "The standard-library baseline does not decode pixels; glare, shadow, blur, noise, and perspective remain unassessed.",
            page_index=0,
            evidence=[f"format={kind}", f"dpiKnown={str(dpi is not None).lower()}"],
        )
    )
    return warnings


def _baseline_quality_findings(
    *,
    page_count: int | None,
    image_width: int | None,
    image_height: int | None,
    dpi: dict[str, Any] | None,
    is_pdf: bool,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    page_index = 0 if (page_count or image_width) else None

    for quality_type in _QUALITY_TYPES:
        status = "not_assessed"
        confidence = "none"
        evidence = ["pixel_decoder_not_available"]
        if is_pdf and quality_type in {"low_resolution", "compression"}:
            status = "not_applicable"
            evidence = ["document_level_pdf_inspection"]
        elif quality_type == "crop" and image_width and image_height:
            ratio = image_width / image_height
            if ratio < 0.45 or ratio > 2.2:
                status = "probable"
                confidence = "low"
                evidence = [f"displayAspectRatio={ratio:.4f}", "extreme_aspect_ratio"]
            else:
                evidence = [f"displayAspectRatio={ratio:.4f}", "page_boundary_not_detected"]
        elif quality_type == "low_resolution" and image_width and image_height:
            low_pixels = min(image_width, image_height) < 1200
            low_dpi = bool(dpi and min(dpi["x"], dpi["y"]) < 150)
            if low_pixels or low_dpi:
                status = "probable"
                confidence = "medium"
            else:
                status = "unlikely"
                confidence = "low"
            evidence = [
                f"displayDimensions={image_width}x{image_height}",
                f"dpi={dpi if dpi is not None else 'unknown'}",
            ]
        findings.append(
            {
                "type": quality_type,
                "status": status,
                "confidence": confidence,
                "pageIndex": page_index,
                "region": None,
                "evidence": evidence,
            }
        )
    return findings


def _warning(
    code: str,
    severity: str,
    message: str,
    *,
    page_index: int | None = None,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "pageIndex": page_index,
        "region": None,
        "evidence": evidence or [],
    }
