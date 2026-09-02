from __future__ import annotations

import hashlib
import sys

import cv2
import numpy as np

from st_score_restore.pdf_pipeline import (
    PIPELINE_VERSION,
    RENDERER_BINDING,
    RENDERER_BINDING_VERSION,
    RENDERER_NAME,
    PdfPipelineConfig,
    PdfPipelineError,
    process_pdf_bytes,
)

EXPECTED_BINDING_VERSION = "5.13.0"


def _jpeg_bytes() -> bytes:
    image = np.full((96, 72, 3), 245, dtype=np.uint8)
    for y in range(18, 82, 10):
        cv2.line(image, (4, y), (67, y), (20, 20, 20), 1)
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        raise RuntimeError("Stage 3 validator JPEG encoding failed")
    return bytes(encoded)


def _stream(payload: bytes, extra: bytes = b"") -> bytes:
    suffix = b" " + extra if extra else b""
    return b"<< /Length " + str(len(payload)).encode("ascii") + suffix + b" >>\nstream\n" + payload + b"\nendstream"


def _assemble_pdf(objects: list[bytes]) -> bytes:
    chunks = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(sum(len(chunk) for chunk in chunks))
        chunks.append(str(index).encode("ascii") + b" 0 obj\n" + body + b"\nendobj\n")
    xref_offset = sum(len(chunk) for chunk in chunks)
    xref = [b"xref\n0 " + str(len(objects) + 1).encode("ascii") + b"\n", b"0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    trailer = b"trailer\n<< /Size " + str(len(objects) + 1).encode("ascii") + b" /Root 1 0 R >>\nstartxref\n" + str(xref_offset).encode("ascii") + b"\n%%EOF\n"
    return b"".join(chunks + xref + [trailer])


def _two_page_pdf() -> bytes:
    jpeg = _jpeg_bytes()
    return _assemble_pdf([
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 6 0 R] /Count 2 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 300] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>",
        _stream(jpeg, b"/Type /XObject /Subtype /Image /Width 72 /Height 96 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode"),
        _stream(b"q\n200 0 0 300 0 0 cm\n/Im0 Do\nQ"),
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 300] /Resources << >> /Contents 7 0 R >>",
        _stream(b"10 10 m\n190 290 l\n1 w\nS"),
    ])


def _hybrid_pdf() -> bytes:
    jpeg = _jpeg_bytes()
    return _assemble_pdf([
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 300] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>",
        _stream(jpeg, b"/Type /XObject /Subtype /Image /Width 72 /Height 96 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode"),
        _stream(b"q\n200 0 0 300 0 0 cm\n/Im0 Do\nQ\n10 10 m\n190 290 l\n1 w\nS"),
    ])


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    require(PIPELINE_VERSION == "0.1.0", "Stage 3 pipeline version drifted")
    require(RENDERER_NAME == "pdfium", "Stage 3 renderer identity drifted")
    require(RENDERER_BINDING == "pypdfium2", "Stage 3 renderer binding drifted")
    require(RENDERER_BINDING_VERSION == EXPECTED_BINDING_VERSION, f"Stage 3 renderer binding version drifted: {RENDERER_BINDING_VERSION}")

    source = _two_page_pdf()
    first = process_pdf_bytes(source, source_name="stage3-validator.pdf")
    second = process_pdf_bytes(source, source_name="stage3-validator.pdf")
    manifest = first.manifest

    require(first.manifest == second.manifest, "Stage 3 manifest is not deterministic")
    require(first.page_bytes(0) == second.page_bytes(0), "Stage 3 raster derivative is not deterministic")
    require(manifest.get("source", {}).get("sha256") == hashlib.sha256(source).hexdigest(), "Stage 3 manifest lost exact source SHA-256 binding")
    require(manifest.get("sourceBytesModified") is False, "Stage 3 modifies source bytes")
    require(manifest.get("originalFallbackAvailable") is True, "Stage 3 lost original fallback")
    require(manifest.get("vectorPagesRasterized") is False, "Stage 3 silently rasterizes vector pages")
    require(manifest.get("pageOrderPreserved") is True, "Stage 3 page order is not preserved")
    require(manifest.get("pageCount") == 2, "Stage 3 PDFium page count is not deterministic")
    require(manifest.get("renderedPageCount") == 1, "Stage 3 expected exactly one raster-only derivative")

    pages = manifest.get("pages", [])
    if len(pages) == 2:
        raster_page, vector_page = pages
        require(raster_page.get("pageIndex") == 0, "Stage 3 raster page index drifted")
        require(raster_page.get("pageClassification") == "raster_only", "Stage 3 raster page classification drifted")
        require(raster_page.get("status") == "rendered_raster_page", "Stage 3 raster-only page was not rendered")
        require(raster_page.get("policy") == "render_raster_only", "Stage 3 raster rendering policy drifted")
        require(raster_page.get("render", {}).get("derivedFromPageIndex") == 0, "Stage 3 derivative lost page provenance")
        require(raster_page.get("render", {}).get("derivedFromSourceSha256") == manifest.get("source", {}).get("sha256"), "Stage 3 derivative lost source provenance")
        require(raster_page.get("qualityAnalysis", {}).get("status") == "analyzed", "Stage 3 derivative did not enter quality analysis")
        require(vector_page.get("pageIndex") == 1, "Stage 3 vector page index drifted")
        require(vector_page.get("pageClassification") == "vector_only", "Stage 3 vector page classification drifted")
        require(vector_page.get("status") == "preserved_vector_page", "Stage 3 vector page was not preserved")
        require(vector_page.get("render") is None, "Stage 3 vector page unexpectedly has a raster derivative")
        require(vector_page.get("vectorContentRasterized") is False, "Stage 3 vector page records rasterization")
    else:
        failures.append(f"Stage 3 expected two page records, got {len(pages)}")

    hybrid = process_pdf_bytes(_hybrid_pdf(), source_name="stage3-hybrid-validator.pdf")
    hybrid_page = hybrid.manifest.get("pages", [{}])[0]
    require(hybrid_page.get("pageClassification") == "hybrid", "Stage 3 hybrid page classification drifted")
    require(hybrid_page.get("status") == "preserved_vector_page", "Stage 3 hybrid page was not preserved")
    require(hybrid_page.get("reviewRequired") is True, "Stage 3 hybrid page lost review requirement")
    require(hybrid_page.get("render") is None, "Stage 3 hybrid page was silently rasterized")
    require(hybrid_page.get("vectorContentRasterized") is False, "Stage 3 hybrid page records vector rasterization")

    configuration = manifest.get("configuration", {})
    require(configuration.get("heldOutTuningUsed") is False, "Stage 3 unexpectedly claims held-out tuning")
    require(configuration.get("calibrationState") == "uncalibrated_engineering_defaults", "Stage 3 calibration boundary drifted")
    claims = manifest.get("claims", {})
    for key in ("omrPerformed", "musicalCorrectnessEstablished", "restorationEffectivenessEstablished", "calibrationAuthorized", "trainingAuthorized"):
        require(claims.get(key) is False, f"Stage 3 contains unsupported positive claim: {key}")

    try:
        process_pdf_bytes(source, config=PdfPipelineConfig(max_pages=1))
    except PdfPipelineError as exc:
        require(exc.code == "pdf_page_limit_exceeded", "Stage 3 page-limit failure code drifted")
    else:
        failures.append("Stage 3 page-limit gate did not fail closed")

    if failures:
        print("Stage 3 multi-page PDF pipeline validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 3 multi-page PDF pipeline validation: PASS")
    print(f"- pipeline version: {PIPELINE_VERSION}")
    print(f"- renderer: {RENDERER_NAME} via {RENDERER_BINDING} {RENDERER_BINDING_VERSION}")
    print("- deterministic source/page identity: PASS")
    print("- raster-only rendering: PASS")
    print("- vector/hybrid preservation / no silent rasterization: PASS")
    print("- original fallback / bounded page limit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
