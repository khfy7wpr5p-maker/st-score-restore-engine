from __future__ import annotations

import hashlib
import unittest

import cv2
import numpy as np

from st_score_restore.pdf_pipeline import (
    PdfPipelineConfig,
    PdfPipelineError,
    process_pdf_bytes,
)


def _jpeg_bytes() -> bytes:
    image = np.full((96, 72, 3), 245, dtype=np.uint8)
    for y in range(18, 82, 10):
        cv2.line(image, (4, y), (67, y), (20, 20, 20), 1)
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        raise AssertionError("synthetic JPEG encoding failed")
    return bytes(encoded)


def _stream(payload: bytes, extra: bytes = b"") -> bytes:
    suffix = b" " + extra if extra else b""
    return (
        b"<< /Length "
        + str(len(payload)).encode("ascii")
        + suffix
        + b" >>\nstream\n"
        + payload
        + b"\nendstream"
    )


def _build_two_page_pdf(*, raster_width: int = 200, raster_height: int = 300) -> bytes:
    jpeg = _jpeg_bytes()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 6 0 R] /Count 2 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 "
            + str(raster_width).encode("ascii")
            + b" "
            + str(raster_height).encode("ascii")
            + b"] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>"
        ),
        _stream(
            jpeg,
            b"/Type /XObject /Subtype /Image /Width 72 /Height 96 "
            b"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode",
        ),
        _stream(
            b"q\n"
            + str(raster_width).encode("ascii")
            + b" 0 0 "
            + str(raster_height).encode("ascii")
            + b" 0 0 cm\n/Im0 Do\nQ"
        ),
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 300] /Resources << >> /Contents 7 0 R >>",
        _stream(b"10 10 m\n190 290 l\n1 w\nS"),
    ]
    return _assemble_pdf(objects)


def _build_vector_only_pdf() -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 300] /Resources << >> /Contents 4 0 R >>",
        _stream(b"10 10 m\n190 290 l\n2 w\nS"),
    ]
    return _assemble_pdf(objects)


def _build_hybrid_pdf() -> bytes:
    jpeg = _jpeg_bytes()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 300] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>",
        _stream(
            jpeg,
            b"/Type /XObject /Subtype /Image /Width 72 /Height 96 "
            b"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode",
        ),
        _stream(b"q\n200 0 0 300 0 0 cm\n/Im0 Do\nQ\n10 10 m\n190 290 l\n1 w\nS"),
    ]
    return _assemble_pdf(objects)


def _assemble_pdf(objects: list[bytes]) -> bytes:
    chunks = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(sum(len(chunk) for chunk in chunks))
        chunks.append(
            str(index).encode("ascii")
            + b" 0 obj\n"
            + body
            + b"\nendobj\n"
        )
    xref_offset = sum(len(chunk) for chunk in chunks)
    xref = [b"xref\n0 " + str(len(objects) + 1).encode("ascii") + b"\n"]
    xref.append(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        xref.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    trailer = (
        b"trailer\n<< /Size "
        + str(len(objects) + 1).encode("ascii")
        + b" /Root 1 0 R >>\nstartxref\n"
        + str(xref_offset).encode("ascii")
        + b"\n%%EOF\n"
    )
    return b"".join(chunks + xref + [trailer])


class PdfPipelineTests(unittest.TestCase):
    def test_multipage_raster_and_vector_policy(self) -> None:
        source = _build_two_page_pdf()
        result = process_pdf_bytes(source, source_name="synthetic.pdf")
        manifest = result.manifest

        self.assertEqual(manifest["source"]["sha256"], hashlib.sha256(source).hexdigest())
        self.assertTrue(manifest["source"]["immutable"])
        self.assertEqual(manifest["pageCount"], 2)
        self.assertTrue(manifest["pageOrderPreserved"])
        self.assertFalse(manifest["sourceBytesModified"])
        self.assertFalse(manifest["vectorPagesRasterized"])
        self.assertEqual(manifest["renderedPageCount"], 1)

        first, second = manifest["pages"]
        self.assertEqual(first["pageIndex"], 0)
        self.assertEqual(first["pageClassification"], "raster_only")
        self.assertEqual(first["status"], "rendered_raster_page")
        self.assertEqual(first["policy"], "render_raster_only")
        self.assertIsNotNone(result.page_bytes(0))
        self.assertEqual(
            first["render"]["sha256"],
            hashlib.sha256(result.page_bytes(0) or b"").hexdigest(),
        )
        self.assertEqual(
            first["render"]["derivedFromSourceSha256"],
            manifest["source"]["sha256"],
        )
        self.assertEqual(first["qualityAnalysis"]["status"], "analyzed")

        self.assertEqual(second["pageIndex"], 1)
        self.assertEqual(second["pageClassification"], "vector_only")
        self.assertEqual(second["status"], "preserved_vector_page")
        self.assertEqual(second["policy"], "preserve_vector")
        self.assertIsNone(result.page_bytes(1))
        self.assertFalse(second["vectorContentRasterized"])

    def test_vector_only_pdf_is_never_rasterized(self) -> None:
        source = _build_vector_only_pdf()
        result = process_pdf_bytes(source)
        self.assertEqual(result.manifest["renderedPageCount"], 0)
        self.assertEqual(result.manifest["pages"][0]["status"], "preserved_vector_page")
        self.assertFalse(result.manifest["vectorPagesRasterized"])

    def test_hybrid_page_is_preserved_for_review(self) -> None:
        source = _build_hybrid_pdf()
        result = process_pdf_bytes(source)
        page = result.manifest["pages"][0]
        self.assertEqual(page["pageClassification"], "hybrid")
        self.assertEqual(page["status"], "preserved_vector_page")
        self.assertEqual(page["policy"], "preserve_vector")
        self.assertTrue(page["reviewRequired"])
        self.assertFalse(page["vectorContentRasterized"])
        self.assertIsNone(result.page_bytes(0))

    def test_page_count_limit_fails_closed(self) -> None:
        with self.assertRaises(PdfPipelineError) as caught:
            process_pdf_bytes(
                _build_two_page_pdf(),
                config=PdfPipelineConfig(max_pages=1),
            )
        self.assertEqual(caught.exception.code, "pdf_page_limit_exceeded")

    def test_render_dimension_limit_uses_original_fallback(self) -> None:
        source = _build_two_page_pdf(raster_width=5000, raster_height=5000)
        result = process_pdf_bytes(
            source,
            config=PdfPipelineConfig(max_render_dimension=1000),
        )
        first = result.manifest["pages"][0]
        self.assertEqual(first["status"], "original_fallback_review")
        self.assertEqual(first["reasonCode"], "render_dimension_limit_exceeded")
        self.assertIsNone(result.page_bytes(0))
        self.assertEqual(result.manifest["renderedPageCount"], 0)

    def test_manifest_and_render_are_deterministic(self) -> None:
        source = _build_two_page_pdf()
        first = process_pdf_bytes(source)
        second = process_pdf_bytes(source)
        self.assertEqual(first.manifest["manifestDigest"], second.manifest["manifestDigest"])
        self.assertEqual(first.manifest, second.manifest)
        self.assertEqual(first.page_bytes(0), second.page_bytes(0))

    def test_non_pdf_is_rejected(self) -> None:
        image = np.full((32, 32, 3), 255, dtype=np.uint8)
        ok, encoded = cv2.imencode(".png", image)
        self.assertTrue(ok)
        with self.assertRaises(PdfPipelineError) as caught:
            process_pdf_bytes(bytes(encoded))
        self.assertEqual(caught.exception.code, "unsupported_media_type")

    def test_invalid_configuration_rejected(self) -> None:
        with self.assertRaises(PdfPipelineError) as caught:
            PdfPipelineConfig(render_dpi=600)
        self.assertEqual(caught.exception.code, "invalid_configuration")


if __name__ == "__main__":
    unittest.main()
