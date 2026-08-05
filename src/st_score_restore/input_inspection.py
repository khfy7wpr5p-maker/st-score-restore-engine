"""Read-only, deterministic input inspection for PDF, JPEG, and PNG files."""

from __future__ import annotations

import errno
import hashlib
import os
import re
import stat
import struct
import zlib
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
INSPECTOR_VERSION = "0.1.0"
DEFAULT_MAX_BYTES = 50_000_000

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PDF_HEADER = re.compile(rb"%PDF-(\d\.\d)")
PDF_PAGES = re.compile(rb"/Type\s*/Page(?!s)\b")
PDF_BOXES = re.compile(
    rb"/MediaBox\s*\[\s*([-+]?\d+(?:\.\d+)?)\s+([-+]?\d+(?:\.\d+)?)\s+"
    rb"([-+]?\d+(?:\.\d+)?)\s+([-+]?\d+(?:\.\d+)?)\s*\]"
)
EXTENSIONS = {".pdf": "pdf", ".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg"}
QUALITY_TYPES = (
    "perspective", "crop", "glare", "shadow",
    "blur", "noise", "compression", "low_resolution",
)


class InputInspectionError(ValueError):
    """Safe rejection with a stable machine-readable code."""

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
    """Inspect one regular file without changing it."""

    source = Path(path)
    if source.is_symlink():
        _reject("symlink_input_not_allowed", "Symbolic-link inputs are rejected.")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(source, flags)
    except OSError as error:
        if error.errno == errno.ELOOP:
            _reject("symlink_input_not_allowed", "Symbolic-link inputs are rejected.")
        raise InputInspectionError(
            "input_unreadable",
            "The input file could not be read.",
            details={"osError": str(error)},
        ) from error

    try:
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode):
                _reject("input_not_regular_file", "The input must be a regular file.")
            if before.st_size > max_bytes:
                _reject(
                    "oversized_input",
                    "The input exceeds the configured byte limit.",
                    byteSize=before.st_size,
                    maxBytes=max_bytes,
                )
            data = handle.read(max_bytes + 1)
            after = os.fstat(handle.fileno())
    except InputInspectionError:
        raise
    except OSError as error:
        raise InputInspectionError(
            "input_unreadable",
            "The input file could not be read.",
            details={"osError": str(error)},
        ) from error

    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after:
        _reject("source_changed_during_read", "The source changed during inspection.")
    if len(data) > max_bytes:
        _reject(
            "oversized_input",
            "The input exceeds the configured byte limit.",
            byteSizeAtLeast=len(data),
            maxBytes=max_bytes,
        )
    return inspect_bytes(data, source_name=source.name, max_bytes=max_bytes)


def inspect_bytes(
    data: bytes,
    *,
    source_name: str | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> dict[str, Any]:
    """Return deterministic artifact and analysis manifests for immutable bytes."""

    if not isinstance(data, bytes):
        _reject("invalid_input_type", "The inspector accepts bytes only.")
    if not data:
        _reject("empty_input", "The input is empty.")
    if len(data) > max_bytes:
        _reject(
            "oversized_input",
            "The input exceeds the configured byte limit.",
            byteSize=len(data),
            maxBytes=max_bytes,
        )

    digest = hashlib.sha256(data).hexdigest()
    kind = _detect_kind(data)
    if kind is None:
        _reject(
            "unsupported_media_type",
            "Only PDF, JPEG, and PNG inputs are supported.",
            byteSize=len(data),
            sha256=digest,
            signatureHex=data[:12].hex(),
        )

    safe_name = re.split(r"[\\/]", source_name)[-1] if source_name else None
    extension = Path(safe_name).suffix.lower() or None if safe_name else None
    extension_matches = None if extension is None else EXTENSIONS.get(extension) == kind

    if kind == "pdf":
        parsed, media_type = _parse_pdf(data), "application/pdf"
    elif kind == "png":
        parsed, media_type = _parse_png(data), "image/png"
    else:
        parsed, media_type = _parse_jpeg(data), "image/jpeg"

    warnings = parsed.pop("warnings")
    if extension is not None and not extension_matches:
        warnings.append(
            _warning(
                "extension_content_mismatch",
                "warning",
                "The filename extension does not match the detected content.",
                evidence=[f"extension={extension}", f"detectedKind={kind}"],
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
        "sourceName": safe_name,
        "byteSize": len(data),
        "digest": {"algorithm": "sha256", "value": digest},
        "detectedMediaType": media_type,
        "detectedKind": kind,
        "derivedFrom": None,
    }
    analysis = {
        "schemaVersion": SCHEMA_VERSION,
        "inspectionId": inspection_id,
        "artifactId": artifact_id,
        "inspectorVersion": INSPECTOR_VERSION,
        "status": "accepted",
        "restorationPerformed": False,
        "inputKind": kind,
        "suppliedExtension": extension,
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
    if data.startswith(PNG_SIGNATURE):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if PDF_HEADER.match(data[:16]):
        return "pdf"
    return None


def _parse_pdf(data: bytes) -> dict[str, Any]:
    header = PDF_HEADER.match(data[:16])
    if header is None:
        _reject("malformed_pdf", "The PDF header is invalid.")
    if b"%%EOF" not in data[-4096:]:
        _reject("malformed_pdf", "The PDF end-of-file marker is missing.")
    if re.search(rb"/Encrypt\b", data):
        _reject("encrypted_pdf", "Encrypted PDFs are not inspected in this milestone.")

    page_count = len(PDF_PAGES.findall(data)) or None
    boxes: list[tuple[float, float]] = []
    for match in PDF_BOXES.finditer(data):
        x0, y0, x1, y1 = map(float, match.groups())
        width, height = abs(x1 - x0), abs(y1 - y0)
        if width > 0 and height > 0:
            boxes.append((width, height))

    text = bool(
        re.search(rb"\bBT\b[\s\S]{0,200000}?\bET\b", data)
        or re.search(rb"\bTj\b|\bTJ\b|/Font\b", data)
    )
    images = bool(re.search(rb"/Subtype\s*/Image\b", data))
    object_streams = bool(re.search(rb"/Type\s*/ObjStm\b", data))
    if text and images:
        classification, confidence = "hybrid", "medium"
    elif text:
        classification, confidence = "digital", "medium"
    elif images:
        classification, confidence = "scanned", "medium"
    else:
        classification, confidence = "unknown", "low"

    warnings: list[dict[str, Any]] = []
    if page_count is None:
        warnings.append(
            _warning(
                "pdf_page_count_uncertain",
                "review_required",
                "No visible page markers were found; page count is unknown.",
                evidence=["pageObjectMarkers=0"],
            )
        )
    if classification == "unknown":
        warnings.append(
            _warning(
                "pdf_classification_uncertain",
                "review_required",
                "The PDF could not be safely classified.",
                evidence=[
                    f"hasTextEvidence={str(text).lower()}",
                    f"hasImageEvidence={str(images).lower()}",
                    f"hasObjectStreams={str(object_streams).lower()}",
                ],
            )
        )
    if object_streams:
        warnings.append(
            _warning(
                "pdf_object_streams_present",
                "info",
                "Compressed object streams may hide structural evidence.",
                evidence=["/Type /ObjStm"],
            )
        )

    pages = []
    for index in range(page_count or 0):
        box = boxes[index] if index < len(boxes) else (boxes[0] if boxes else None)
        pages.append(
            {
                "pageIndex": index,
                "width": box[0] if box else None,
                "height": box[1] if box else None,
                "unit": "points",
                "orientation": _orientation_label(*box) if box else None,
                "dpiEstimate": None,
            }
        )

    action = {
        "digital": "preserve_vector_pdf",
        "scanned": "review_before_raster_processing",
        "hybrid": "review_before_raster_processing",
        "unknown": "manual_review_required",
    }[classification]
    return {
        "document": {
            "pdfVersion": header.group(1).decode("ascii"),
            "pageCount": page_count,
            "pageCountMethod": (
                "uncompressed_page_object_markers" if page_count else "unknown"
            ),
            "classification": classification,
            "classificationConfidence": confidence,
            "encrypted": False,
            "structuralEvidence": {
                "hasTextOperatorsOrFonts": text,
                "hasImageXObjects": images,
                "hasObjectStreams": object_streams,
                "mediaBoxCount": len(boxes),
            },
        },
        "pages": pages,
        "imageMetadata": None,
        "qualityFindings": _quality_findings(
            width=None,
            height=None,
            dpi=None,
            page_index=None,
            vector_pdf=classification == "digital",
        ),
        "warnings": warnings,
        "recommendedAction": action,
    }


def _parse_png(data: bytes) -> dict[str, Any]:
    offset = len(PNG_SIGNATURE)
    ihdr: bytes | None = None
    physical: tuple[int, int, int] | None = None
    exif: int | None = None
    saw_idat = saw_iend = False
    chunk_index = 0
    while offset < len(data):
        if len(data) - offset < 12:
            _reject("malformed_png", "A PNG chunk is truncated.")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(data):
            _reject("malformed_png", "A PNG chunk length is invalid.")
        payload = data[offset + 8 : offset + 8 + length]
        expected = struct.unpack(">I", data[offset + 8 + length : end])[0]
        actual = zlib.crc32(payload, zlib.crc32(kind)) & 0xFFFFFFFF
        if actual != expected:
            _reject(
                "malformed_png",
                "A PNG chunk CRC is invalid.",
                chunkType=kind.decode("latin-1"),
            )
        if chunk_index == 0 and kind != b"IHDR":
            _reject("malformed_png", "The PNG IHDR chunk must be first.")
        if kind == b"IHDR":
            if ihdr is not None or length != 13:
                _reject("malformed_png", "The PNG IHDR chunk is invalid.")
            ihdr = payload
        elif kind == b"pHYs" and length == 9:
            physical = (
                struct.unpack(">I", payload[:4])[0],
                struct.unpack(">I", payload[4:8])[0],
                payload[8],
            )
        elif kind == b"eXIf":
            exif = _tiff_orientation(payload)
        elif kind == b"IDAT":
            saw_idat = True
        elif kind == b"IEND":
            if length != 0:
                _reject("malformed_png", "The PNG IEND chunk is invalid.")
            saw_iend, offset = True, end
            break
        offset, chunk_index = end, chunk_index + 1

    if ihdr is None or not saw_idat or not saw_iend:
        _reject("malformed_png", "The PNG is missing IHDR, IDAT, or IEND.")
    if offset != len(data):
        _reject("malformed_png", "Unexpected bytes follow PNG IEND.")

    width, height, depth, color, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", ihdr
    )
    if not width or not height:
        _reject("malformed_png", "PNG dimensions must be positive.")
    if compression != 0 or filtering != 0 or interlace not in {0, 1}:
        _reject("malformed_png", "Unsupported PNG structural parameters.")

    dpi = _png_dpi(physical)
    return _image_result(
        kind="png",
        width=width,
        height=height,
        dpi=dpi,
        exif=exif,
        structural={
            "pngBitDepth": depth,
            "pngColorType": color,
            "pngInterlaceMethod": interlace,
        },
        encoding={
            "format": "png",
            "bitDepth": depth,
            "colorType": color,
            "interlaced": interlace == 1,
        },
    )


def _parse_jpeg(data: bytes) -> dict[str, Any]:
    if not data.startswith(b"\xff\xd8"):
        _reject("malformed_jpeg", "The JPEG SOI marker is missing.")
    offset = 2
    width = height = precision = components = None
    dpi: dict[str, Any] | None = None
    exif: int | None = None
    saw_scan = False

    while offset < len(data):
        if data[offset] != 0xFF:
            _reject("malformed_jpeg", "Unexpected bytes outside a JPEG segment.")
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker, offset = data[offset], offset + 1
        if marker == 0xD9:
            break
        if marker == 0xDA:
            if offset + 2 > len(data):
                _reject("malformed_jpeg", "The JPEG SOS is truncated.")
            length = struct.unpack(">H", data[offset : offset + 2])[0]
            if length < 2 or offset + length > len(data):
                _reject("malformed_jpeg", "The JPEG SOS is invalid.")
            offset, saw_scan = offset + length, True
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            _reject("malformed_jpeg", "A JPEG segment is truncated.")
        length = struct.unpack(">H", data[offset : offset + 2])[0]
        if length < 2 or offset + length > len(data):
            _reject("malformed_jpeg", "A JPEG segment length is invalid.")
        payload = data[offset + 2 : offset + length]

        if marker == 0xE0 and payload.startswith(b"JFIF\x00") and len(payload) >= 12:
            unit = payload[7]
            x, y = struct.unpack(">HH", payload[8:12])
            if unit == 1 and x and y:
                dpi = _dpi(float(x), float(y), "jfif")
            elif unit == 2 and x and y:
                dpi = _dpi(x * 2.54, y * 2.54, "jfif")
        elif marker == 0xE1 and payload.startswith(b"Exif\x00\x00"):
            exif = _tiff_orientation(payload[6:])
        elif marker in {
            0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
            0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
        }:
            if len(payload) < 6:
                _reject("malformed_jpeg", "The JPEG SOF is truncated.")
            precision = payload[0]
            height, width = struct.unpack(">HH", payload[1:5])
            components = payload[5]
        offset += length

    if not width or not height:
        _reject("malformed_jpeg", "No JPEG frame dimensions were found.")
    if not saw_scan or data.find(b"\xff\xd9", offset) < 0:
        _reject("malformed_jpeg", "The JPEG is missing a valid scan or end marker.")

    return _image_result(
        kind="jpeg",
        width=width,
        height=height,
        dpi=dpi,
        exif=exif,
        structural={
            "jpegPrecision": precision,
            "jpegComponents": components,
            "hasStartOfScan": True,
        },
        encoding={
            "format": "jpeg",
            "samplePrecision": precision,
            "components": components,
            "compressed": True,
        },
    )


def _image_result(
    *,
    kind: str,
    width: int,
    height: int,
    dpi: dict[str, Any] | None,
    exif: int | None,
    structural: dict[str, Any],
    encoding: dict[str, Any],
) -> dict[str, Any]:
    orientation = _orientation_details(exif)
    display_width, display_height = (
        (height, width) if orientation["swapsDimensions"] else (width, height)
    )
    warnings = [
        _warning(
            "pixel_quality_analysis_limited",
            "info",
            "Pixel quality remains unassessed without an approved decoder.",
            page_index=0,
            evidence=[f"format={kind}", f"dpiKnown={str(dpi is not None).lower()}"],
        )
    ]
    if exif not in {None, 1}:
        warnings.insert(
            0,
            _warning(
                "display_orientation_from_metadata",
                "info",
                "Display dimensions use EXIF orientation; source bytes were not changed.",
                page_index=0,
                evidence=[
                    f"exifOrientation={exif}",
                    f"encoded={width}x{height}",
                    f"display={display_width}x{display_height}",
                ],
            ),
        )
    return {
        "document": {
            "pdfVersion": None,
            "pageCount": 1,
            "pageCountMethod": "single_image",
            "classification": "not_applicable",
            "classificationConfidence": "not_applicable",
            "encrypted": False,
            "structuralEvidence": structural,
        },
        "pages": [{
            "pageIndex": 0,
            "width": display_width,
            "height": display_height,
            "unit": "pixels",
            "orientation": _orientation_label(display_width, display_height),
            "dpiEstimate": dpi,
        }],
        "imageMetadata": {
            "encodedWidthPixels": width,
            "encodedHeightPixels": height,
            "displayWidthPixels": display_width,
            "displayHeightPixels": display_height,
            "exifOrientation": orientation,
            "dpiEstimate": dpi,
            "encoding": encoding,
        },
        "qualityFindings": _quality_findings(
            width=display_width,
            height=display_height,
            dpi=dpi,
            page_index=0,
            vector_pdf=False,
        ),
        "warnings": warnings,
        "recommendedAction": "review_quality_before_restoration",
    }


def _quality_findings(
    *,
    width: int | None,
    height: int | None,
    dpi: dict[str, Any] | None,
    page_index: int | None,
    vector_pdf: bool,
) -> list[dict[str, Any]]:
    findings = []
    for kind in QUALITY_TYPES:
        status, confidence = "not_assessed", "none"
        evidence = ["pixel_decoder_not_available"]
        if vector_pdf and kind in {"low_resolution", "compression"}:
            status, evidence = "not_applicable", ["vector_pdf_content"]
        elif kind == "crop" and width and height:
            ratio = width / height
            evidence = [f"displayAspectRatio={ratio:.4f}", "page_boundary_not_detected"]
            if ratio < 0.45 or ratio > 2.2:
                status, confidence = "probable", "low"
                evidence[1] = "extreme_aspect_ratio"
        elif kind == "low_resolution" and width and height:
            low_pixels = min(width, height) < 1200
            low_dpi = bool(dpi and min(dpi["x"], dpi["y"]) < 150)
            if low_pixels or low_dpi:
                status, confidence = "probable", "medium"
            elif dpi is not None:
                status, confidence = "unlikely", "low"
            evidence = [
                f"displayDimensions={width}x{height}",
                f"dpi={dpi if dpi is not None else 'unknown'}",
            ]
        findings.append({
            "type": kind,
            "status": status,
            "confidence": confidence,
            "pageIndex": page_index,
            "region": None,
            "evidence": evidence,
        })
    return findings


def _tiff_orientation(tiff: bytes) -> int | None:
    if len(tiff) < 8 or tiff[:2] not in {b"II", b"MM"}:
        return None
    order = "<" if tiff[:2] == b"II" else ">"
    try:
        if struct.unpack(order + "H", tiff[2:4])[0] != 42:
            return None
        offset = struct.unpack(order + "I", tiff[4:8])[0]
        if offset + 2 > len(tiff):
            return None
        count = struct.unpack(order + "H", tiff[offset : offset + 2])[0]
        for index in range(count):
            start = offset + 2 + index * 12
            if start + 12 > len(tiff):
                return None
            tag, field_type, value_count = struct.unpack(
                order + "HHI", tiff[start : start + 8]
            )
            if tag == 0x0112 and field_type == 3 and value_count == 1:
                value = struct.unpack(order + "H", tiff[start + 8 : start + 10])[0]
                return value if 1 <= value <= 8 else None
    except (struct.error, OverflowError):
        return None
    return None


def _orientation_details(value: int | None) -> dict[str, Any]:
    rotation, mirrored, swaps = {
        1: (0, False, False), 2: (0, True, False),
        3: (180, False, False), 4: (180, True, False),
        5: (90, True, True), 6: (90, False, True),
        7: (270, True, True), 8: (270, False, True),
    }.get(value or 1, (0, False, False))
    return {
        "exifValue": value,
        "rotationDegrees": rotation,
        "mirrored": mirrored,
        "swapsDimensions": swaps,
        "appliedToSource": False,
    }


def _png_dpi(physical: tuple[int, int, int] | None) -> dict[str, Any] | None:
    if physical is None or physical[2] != 1 or not physical[0] or not physical[1]:
        return None
    return _dpi(physical[0] * 0.0254, physical[1] * 0.0254, "png_pHYs")


def _dpi(x: float, y: float, source: str) -> dict[str, Any]:
    return {"x": round(x, 3), "y": round(y, 3), "unit": "dpi", "source": source}


def _orientation_label(width: float, height: float) -> str:
    if width == height:
        return "square"
    return "landscape" if width > height else "portrait"


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


def _reject(code: str, message: str, **details: Any) -> None:
    raise InputInspectionError(code, message, details=details)
