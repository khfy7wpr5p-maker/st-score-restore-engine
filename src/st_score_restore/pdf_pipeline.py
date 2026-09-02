"""Stage 3 deterministic multi-page PDF rendering and page-policy pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from importlib.metadata import version as package_version
import json
import math
from types import MappingProxyType
from typing import Any, Mapping

import cv2
import numpy as np
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c

from .input_inspection import InputInspectionError, inspect_bytes
from .quality_analysis import QualityAnalysisConfig, analyze_quality_bytes

SCHEMA_VERSION = "1.0.0"
PIPELINE_VERSION = "0.1.0"
RENDERER_NAME = "pdfium"
RENDERER_BINDING = "pypdfium2"
RENDERER_BINDING_VERSION = package_version("pypdfium2")


class PdfPipelineError(ValueError):
    """Stable fail-closed rejection for Stage 3 PDF processing."""

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
class PdfPipelineConfig:
    """Bounded engineering defaults for deterministic Stage 3 rendering."""

    render_dpi: int = 200
    max_pages: int = 64
    max_page_pixels: int = 40_000_000
    max_total_render_pixels: int = 160_000_000
    max_render_dimension: int = 8_000
    max_object_depth: int = 15

    def __post_init__(self) -> None:
        limits = {
            "render_dpi": (72, 300),
            "max_pages": (1, 512),
            "max_page_pixels": (1_000_000, 100_000_000),
            "max_total_render_pixels": (1_000_000, 500_000_000),
            "max_render_dimension": (512, 16_000),
            "max_object_depth": (1, 50),
        }
        for name, (minimum, maximum) in limits.items():
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                self._invalid(name)
            if not minimum <= value <= maximum:
                self._invalid(name)
        if self.max_total_render_pixels < self.max_page_pixels:
            self._invalid("max_total_render_pixels")

    @staticmethod
    def _invalid(name: str) -> None:
        raise PdfPipelineError(
            "invalid_configuration",
            f"Invalid Stage 3 PDF pipeline configuration field: {name}.",
        )

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any] | None,
    ) -> "PdfPipelineConfig":
        if value is None:
            return cls()
        if not isinstance(value, Mapping):
            raise PdfPipelineError(
                "invalid_configuration",
                "Stage 3 PDF pipeline configuration must be an object.",
            )
        known = set(cls.__dataclass_fields__)
        unknown = sorted(str(key) for key in value if key not in known)
        if unknown:
            raise PdfPipelineError(
                "invalid_configuration",
                "Unknown Stage 3 PDF pipeline configuration fields.",
                details={"fields": unknown},
            )
        return cls(**dict(value))

    def digest(self) -> str:
        return _canonical_sha256(asdict(self))


@dataclass(frozen=True)
class PdfPipelineResult:
    """Public-safe manifest plus in-memory rendered derivative bytes."""

    manifest: Mapping[str, Any]
    rendered_pages: Mapping[int, bytes]

    def page_bytes(self, page_index: int) -> bytes | None:
        return self.rendered_pages.get(page_index)


def process_pdf_bytes(
    data: bytes,
    *,
    source_name: str | None = None,
    config: PdfPipelineConfig | Mapping[str, Any] | None = None,
    quality_config: QualityAnalysisConfig | Mapping[str, Any] | None = None,
) -> PdfPipelineResult:
    """Process one immutable PDF without rasterizing pages that contain vector evidence."""

    if not isinstance(data, bytes) or not data:
        raise PdfPipelineError(
            "invalid_source",
            "A non-empty immutable PDF byte sequence is required.",
        )
    resolved = (
        config
        if isinstance(config, PdfPipelineConfig)
        else PdfPipelineConfig.from_mapping(config)
    )

    try:
        inspected = inspect_bytes(data, source_name=source_name)
    except InputInspectionError as exc:
        raise PdfPipelineError(exc.code, exc.message, details=exc.details) from exc

    artifact = inspected["artifact"]
    inspection = inspected["analysis"]
    if inspection["inputKind"] != "pdf":
        raise PdfPipelineError(
            "unsupported_media_type",
            "Stage 3 PDF pipeline accepts PDF sources only.",
            details={"inputKind": inspection["inputKind"]},
        )

    source_digest = artifact["digest"]["value"]
    try:
        document = pdfium.PdfDocument(data)
    except Exception as exc:  # PDFium error classes vary across binding versions.
        raise PdfPipelineError(
            "pdfium_open_failed",
            "PDFium could not open the inspected PDF.",
            details={"exceptionType": type(exc).__name__},
        ) from exc

    rendered_pages: dict[int, bytes] = {}
    page_records: list[dict[str, Any]] = []
    total_render_pixels = 0
    try:
        page_count = len(document)
        if page_count < 1:
            raise PdfPipelineError("empty_pdf", "The PDF contains no pages.")
        if page_count > resolved.max_pages:
            raise PdfPipelineError(
                "pdf_page_limit_exceeded",
                "The PDF exceeds the configured Stage 3 page limit.",
                details={"pageCount": page_count, "maxPages": resolved.max_pages},
            )

        for page_index in range(page_count):
            page = document[page_index]
            try:
                width_points, height_points = page.get_size()
                classification, object_counts = _classify_page(
                    page,
                    max_depth=resolved.max_object_depth,
                )
                record: dict[str, Any] = {
                    "pageIndex": page_index,
                    "widthPoints": _round_number(width_points),
                    "heightPoints": _round_number(height_points),
                    "pageClassification": classification,
                    "objectEvidence": object_counts,
                    "sourceFallbackAvailable": True,
                    "vectorContentRasterized": False,
                }

                if classification in {"vector_only", "hybrid"}:
                    record.update(
                        {
                            "status": "preserved_vector_page",
                            "policy": "preserve_vector",
                            "render": None,
                            "qualityAnalysis": None,
                            "reviewRequired": classification == "hybrid",
                        }
                    )
                    page_records.append(record)
                    continue

                if classification != "raster_only":
                    record.update(
                        {
                            "status": "original_fallback_review",
                            "policy": "fail_closed_original_fallback",
                            "render": None,
                            "qualityAnalysis": None,
                            "reviewRequired": True,
                            "reasonCode": "page_content_unclassified",
                        }
                    )
                    page_records.append(record)
                    continue

                width_px, height_px = _predicted_render_size(
                    width_points,
                    height_points,
                    resolved.render_dpi,
                )
                predicted_pixels = width_px * height_px
                fallback_code = _render_limit_code(
                    width_px=width_px,
                    height_px=height_px,
                    page_pixels=predicted_pixels,
                    total_after=total_render_pixels + predicted_pixels,
                    config=resolved,
                )
                if fallback_code is not None:
                    record.update(
                        {
                            "status": "original_fallback_review",
                            "policy": "fail_closed_original_fallback",
                            "render": None,
                            "qualityAnalysis": None,
                            "reviewRequired": True,
                            "reasonCode": fallback_code,
                            "predictedRender": {
                                "widthPixels": width_px,
                                "heightPixels": height_px,
                                "pixelCount": predicted_pixels,
                                "dpi": resolved.render_dpi,
                            },
                        }
                    )
                    page_records.append(record)
                    continue

                png_bytes, actual_width, actual_height = _render_page_png(
                    page,
                    dpi=resolved.render_dpi,
                )
                actual_pixels = actual_width * actual_height
                total_render_pixels += actual_pixels
                derivative_sha = hashlib.sha256(png_bytes).hexdigest()
                quality = analyze_quality_bytes(
                    png_bytes,
                    source_name=_page_source_name(source_name, page_index),
                    config=quality_config,
                )
                rendered_pages[page_index] = png_bytes
                record.update(
                    {
                        "status": "rendered_raster_page",
                        "policy": "render_raster_only",
                        "reviewRequired": False,
                        "render": {
                            "mediaType": "image/png",
                            "dpi": resolved.render_dpi,
                            "widthPixels": actual_width,
                            "heightPixels": actual_height,
                            "pixelCount": actual_pixels,
                            "sha256": derivative_sha,
                            "derivedFromSourceSha256": source_digest,
                            "derivedFromPageIndex": page_index,
                        },
                        "qualityAnalysis": quality,
                    }
                )
                page_records.append(record)
            finally:
                page.close()
    finally:
        document.close()

    manifest: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "pipelineVersion": PIPELINE_VERSION,
        "status": "completed",
        "source": {
            "sha256": source_digest,
            "byteSize": artifact["byteSize"],
            "sourceName": artifact.get("sourceName"),
            "immutable": True,
            "inputInspectionClassification": inspection["document"]["classification"],
        },
        "renderer": {
            "name": RENDERER_NAME,
            "binding": RENDERER_BINDING,
            "bindingVersion": RENDERER_BINDING_VERSION,
            "renderPolicy": "raster_only_pages",
        },
        "configuration": {
            "digest": resolved.digest(),
            "values": asdict(resolved),
            "heldOutTuningUsed": False,
            "calibrationState": "uncalibrated_engineering_defaults",
        },
        "pageCount": len(page_records),
        "pageCountSource": "pdfium",
        "pageOrderPreserved": [page["pageIndex"] for page in page_records]
        == list(range(len(page_records))),
        "sourceBytesModified": False,
        "originalFallbackAvailable": True,
        "vectorPagesRasterized": False,
        "renderedPageCount": len(rendered_pages),
        "totalRenderedPixels": total_render_pixels,
        "pages": page_records,
        "claims": {
            "omrPerformed": False,
            "musicalCorrectnessEstablished": False,
            "restorationEffectivenessEstablished": False,
            "calibrationAuthorized": False,
            "trainingAuthorized": False,
        },
    }
    manifest_digest = _canonical_sha256(manifest)
    manifest["manifestDigest"] = {
        "algorithm": "sha256",
        "value": manifest_digest,
    }
    return PdfPipelineResult(
        manifest=MappingProxyType(manifest),
        rendered_pages=MappingProxyType(dict(rendered_pages)),
    )


def _classify_page(page: Any, *, max_depth: int) -> tuple[str, dict[str, int]]:
    counts = {
        "text": 0,
        "path": 0,
        "image": 0,
        "shading": 0,
        "form": 0,
        "unknown": 0,
    }
    type_map = {
        pdfium_c.FPDF_PAGEOBJ_TEXT: "text",
        pdfium_c.FPDF_PAGEOBJ_PATH: "path",
        pdfium_c.FPDF_PAGEOBJ_IMAGE: "image",
        pdfium_c.FPDF_PAGEOBJ_SHADING: "shading",
        pdfium_c.FPDF_PAGEOBJ_FORM: "form",
    }
    try:
        for obj in page.get_objects(max_depth=max_depth):
            counts[type_map.get(obj.type, "unknown")] += 1
    except Exception as exc:
        raise PdfPipelineError(
            "pdf_page_object_inspection_failed",
            "PDFium could not inspect page objects safely.",
            details={"exceptionType": type(exc).__name__},
        ) from exc

    vector_count = counts["text"] + counts["path"] + counts["shading"]
    image_count = counts["image"]
    if vector_count and image_count:
        return "hybrid", counts
    if vector_count:
        return "vector_only", counts
    if image_count:
        return "raster_only", counts
    return "unknown_or_empty", counts


def _predicted_render_size(width_points: float, height_points: float, dpi: int) -> tuple[int, int]:
    if not all(math.isfinite(float(v)) and float(v) > 0 for v in (width_points, height_points)):
        raise PdfPipelineError(
            "invalid_pdf_page_geometry",
            "PDF page geometry is not finite and positive.",
        )
    scale = dpi / 72.0
    return max(1, math.ceil(width_points * scale)), max(1, math.ceil(height_points * scale))


def _render_limit_code(
    *,
    width_px: int,
    height_px: int,
    page_pixels: int,
    total_after: int,
    config: PdfPipelineConfig,
) -> str | None:
    if width_px > config.max_render_dimension or height_px > config.max_render_dimension:
        return "render_dimension_limit_exceeded"
    if page_pixels > config.max_page_pixels:
        return "render_page_pixel_limit_exceeded"
    if total_after > config.max_total_render_pixels:
        return "render_total_pixel_limit_exceeded"
    return None


def _render_page_png(page: Any, *, dpi: int) -> tuple[bytes, int, int]:
    scale = dpi / 72.0
    try:
        bitmap = page.render(
            scale=scale,
            rotation=0,
            draw_annots=False,
            force_bitmap_format=pdfium_c.FPDFBitmap_BGR,
        )
        try:
            image = np.asarray(bitmap.to_numpy()).copy()
        finally:
            bitmap.close()
    except Exception as exc:
        raise PdfPipelineError(
            "pdf_page_render_failed",
            "PDFium failed to render a raster-only PDF page.",
            details={"exceptionType": type(exc).__name__},
        ) from exc

    if image.ndim != 3 or image.shape[2] != 3:
        raise PdfPipelineError(
            "unexpected_pdfium_bitmap",
            "PDFium returned an unexpected bitmap format.",
            details={"shape": list(image.shape)},
        )
    ok, encoded = cv2.imencode(
        ".png",
        image,
        [cv2.IMWRITE_PNG_COMPRESSION, 9],
    )
    if not ok:
        raise PdfPipelineError(
            "pdf_page_png_encode_failed",
            "Rendered PDF page could not be encoded as PNG.",
        )
    return bytes(encoded), int(image.shape[1]), int(image.shape[0])


def _page_source_name(source_name: str | None, page_index: int) -> str:
    base = source_name or "source.pdf"
    return f"{base}.page-{page_index + 1}.png"


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _round_number(value: float) -> float:
    return round(float(value), 6)
