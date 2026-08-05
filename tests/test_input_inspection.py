from __future__ import annotations

import hashlib
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.input_inspection import (  # noqa: E402
    InputInspectionError,
    inspect_bytes,
    inspect_path,
)


def png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return (
        struct.pack(">I", len(payload))
        + chunk_type
        + payload
        + struct.pack(">I", crc)
    )


def make_png(width: int = 1600, height: int = 2200, dpi: int = 300) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    ppm = round(dpi / 0.0254)
    phys = struct.pack(">IIB", ppm, ppm, 1)
    raw = b"\x00" + b"\xff" * width
    idat = zlib.compress(raw * height)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"pHYs", phys)
        + png_chunk(b"IDAT", idat)
        + png_chunk(b"IEND", b"")
    )


def make_tiff_orientation(value: int) -> bytes:
    return (
        b"II"
        + struct.pack("<H", 42)
        + struct.pack("<I", 8)
        + struct.pack("<H", 1)
        + struct.pack("<HHI", 0x0112, 3, 1)
        + struct.pack("<H", value)
        + b"\x00\x00"
        + struct.pack("<I", 0)
    )


def segment(marker: int, payload: bytes) -> bytes:
    return b"\xff" + bytes([marker]) + struct.pack(">H", len(payload) + 2) + payload


def make_jpeg(
    width: int = 1600,
    height: int = 2200,
    *,
    orientation: int | None = None,
) -> bytes:
    jfif = b"JFIF\x00" + b"\x01\x02" + b"\x01" + struct.pack(">HH", 300, 300) + b"\x00\x00"
    parts = [b"\xff\xd8", segment(0xE0, jfif)]
    if orientation is not None:
        parts.append(segment(0xE1, b"Exif\x00\x00" + make_tiff_orientation(orientation)))
    sof = bytes([8]) + struct.pack(">HH", height, width) + b"\x01" + b"\x01\x11\x00"
    parts.append(segment(0xC0, sof))
    parts.append(segment(0xDA, b"\x01\x01\x00\x00\x3f\x00"))
    parts.append(b"\x00\xff\xd9")
    return b"".join(parts)


def make_pdf(kind: str) -> bytes:
    content = [b"%PDF-1.7\n", b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"]
    content.append(b"2 0 obj << /Type /Pages /Count 1 /Kids [3 0 R] >> endobj\n")
    resources = b""
    stream = b""
    if kind in {"digital", "hybrid"}:
        resources += b"/Font << /F1 5 0 R >> "
        stream += b"BT /F1 12 Tf (music) Tj ET "
    if kind in {"scanned", "hybrid"}:
        resources += b"/XObject << /Im0 6 0 R >> "
        stream += b"q 100 0 0 100 0 0 cm /Im0 Do Q "
    content.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        + b"/Resources << "
        + resources
        + b">> /Contents 4 0 R >> endobj\n"
    )
    content.append(
        b"4 0 obj << /Length "
        + str(len(stream)).encode("ascii")
        + b" >> stream\n"
        + stream
        + b"\nendstream endobj\n"
    )
    if kind in {"digital", "hybrid"}:
        content.append(b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    if kind in {"scanned", "hybrid"}:
        content.append(
            b"6 0 obj << /Type /XObject /Subtype /Image /Width 100 /Height 100 "
            b"/ColorSpace /DeviceGray /BitsPerComponent 8 /Length 0 >> stream\n"
            b"\nendstream endobj\n"
        )
    content.append(b"trailer << /Root 1 0 R >>\n%%EOF\n")
    return b"".join(content)


class InputInspectionTests(unittest.TestCase):
    def test_png_is_deterministic_and_reports_dimensions_and_dpi(self) -> None:
        data = make_png()
        first = inspect_bytes(data, source_name="page.png")
        second = inspect_bytes(data, source_name="page.png")
        self.assertEqual(first, second)
        self.assertEqual(
            first["artifact"]["digest"]["value"],
            hashlib.sha256(data).hexdigest(),
        )
        self.assertTrue(first["artifact"]["immutable"])
        self.assertEqual(first["analysis"]["pages"][0]["width"], 1600)
        self.assertEqual(first["analysis"]["pages"][0]["height"], 2200)
        self.assertAlmostEqual(
            first["analysis"]["pages"][0]["dpiEstimate"]["x"],
            300,
            delta=0.05,
        )
        self.assertFalse(first["analysis"]["restorationPerformed"])

    def test_jpeg_exif_orientation_changes_display_view_not_source(self) -> None:
        data = make_jpeg(width=2200, height=1600, orientation=6)
        result = inspect_bytes(data, source_name="phone.jpg")
        metadata = result["analysis"]["imageMetadata"]
        self.assertEqual(metadata["encodedWidthPixels"], 2200)
        self.assertEqual(metadata["encodedHeightPixels"], 1600)
        self.assertEqual(metadata["displayWidthPixels"], 1600)
        self.assertEqual(metadata["displayHeightPixels"], 2200)
        self.assertEqual(metadata["exifOrientation"]["rotationDegrees"], 90)
        self.assertFalse(metadata["exifOrientation"]["appliedToSource"])

    def test_digital_pdf_is_preserved_as_vector(self) -> None:
        result = inspect_bytes(make_pdf("digital"), source_name="score.pdf")
        document = result["analysis"]["document"]
        self.assertEqual(document["classification"], "digital")
        self.assertEqual(document["pageCount"], 1)
        self.assertEqual(result["analysis"]["recommendedAction"], "preserve_vector_pdf")

    def test_scanned_pdf_is_identified(self) -> None:
        result = inspect_bytes(make_pdf("scanned"), source_name="scan.pdf")
        self.assertEqual(result["analysis"]["document"]["classification"], "scanned")
        self.assertEqual(
            result["analysis"]["recommendedAction"],
            "review_before_raster_processing",
        )

    def test_hybrid_pdf_is_identified(self) -> None:
        result = inspect_bytes(make_pdf("hybrid"), source_name="hybrid.pdf")
        self.assertEqual(result["analysis"]["document"]["classification"], "hybrid")

    def test_extension_mismatch_is_a_warning_not_a_rewrite(self) -> None:
        result = inspect_bytes(make_png(20, 40, 72), source_name="wrong.jpg")
        self.assertFalse(result["analysis"]["extensionMatchesContent"])
        codes = {warning["code"] for warning in result["analysis"]["warnings"]}
        self.assertIn("extension_content_mismatch", codes)

    def test_source_name_does_not_expose_parent_path(self) -> None:
        result = inspect_bytes(make_png(20, 40, 72), source_name="/private/student/page.png")
        self.assertEqual(result["artifact"]["sourceName"], "page.png")

    def test_path_inspection_preserves_exact_bytes(self) -> None:
        data = make_png(40, 60, 150)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "source.png"
            path.write_bytes(data)
            before = path.read_bytes()
            result = inspect_path(path)
            after = path.read_bytes()
        self.assertEqual(before, after)
        self.assertEqual(result["artifact"]["byteSize"], len(data))

    def test_malformed_pdf_is_rejected_with_actionable_code(self) -> None:
        with self.assertRaises(InputInspectionError) as context:
            inspect_bytes(b"%PDF-1.7\n/Type /Page\n", source_name="bad.pdf")
        self.assertEqual(context.exception.code, "malformed_pdf")

    def test_encrypted_pdf_is_rejected(self) -> None:
        data = make_pdf("digital").replace(
            b"trailer << /Root 1 0 R >>",
            b"trailer << /Root 1 0 R /Encrypt 9 0 R >>",
        )
        with self.assertRaises(InputInspectionError) as context:
            inspect_bytes(data, source_name="locked.pdf")
        self.assertEqual(context.exception.code, "encrypted_pdf")

    def test_unsupported_input_is_rejected_with_digest_evidence(self) -> None:
        data = b"not a supported document"
        with self.assertRaises(InputInspectionError) as context:
            inspect_bytes(data, source_name="page.txt")
        self.assertEqual(context.exception.code, "unsupported_media_type")
        self.assertEqual(
            context.exception.details["sha256"],
            hashlib.sha256(data).hexdigest(),
        )

    def test_oversized_input_is_rejected_before_processing(self) -> None:
        with self.assertRaises(InputInspectionError) as context:
            inspect_bytes(b"x" * 11, max_bytes=10)
        self.assertEqual(context.exception.code, "oversized_input")

    def test_png_crc_corruption_is_rejected(self) -> None:
        data = bytearray(make_png(8, 8, 72))
        data[20] ^= 0x01
        with self.assertRaises(InputInspectionError) as context:
            inspect_bytes(bytes(data), source_name="broken.png")
        self.assertEqual(context.exception.code, "malformed_png")


if __name__ == "__main__":
    unittest.main()
