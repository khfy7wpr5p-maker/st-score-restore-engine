"""Deterministic candidate encoders for PNG, JPEG, and single-page PDF."""

from __future__ import annotations

import cv2
import numpy as np

from .restoration_types import RestorationConfig, RestorationError


def encode_candidate(
    gray: np.ndarray,
    output_format: str,
    config: RestorationConfig,
) -> tuple[bytes, str]:
    if output_format == "png":
        success, data = cv2.imencode(
            ".png",
            gray,
            [cv2.IMWRITE_PNG_COMPRESSION, 9],
        )
        media_type = "image/png"
    elif output_format == "jpeg":
        success, data = cv2.imencode(
            ".jpg",
            gray,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                config.jpeg_quality,
                cv2.IMWRITE_JPEG_PROGRESSIVE,
                0,
                cv2.IMWRITE_JPEG_OPTIMIZE,
                0,
            ],
        )
        media_type = "image/jpeg"
    else:
        success, data = cv2.imencode(
            ".jpg",
            gray,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                config.jpeg_quality,
                cv2.IMWRITE_JPEG_PROGRESSIVE,
                0,
                cv2.IMWRITE_JPEG_OPTIMIZE,
                0,
            ],
        )
        if not success:
            raise RestorationError(
                "output_encode_failed",
                "JPEG encoding for PDF failed.",
            )
        return _single_page_pdf(
            bytes(data),
            gray.shape[1],
            gray.shape[0],
            config.output_dpi,
        ), "application/pdf"
    if not success:
        raise RestorationError(
            "output_encode_failed",
            "OpenCV output encoding failed.",
        )
    return bytes(data), media_type


def output_format_from_suffix(suffix: str) -> str:
    try:
        return {
            ".png": "png",
            ".jpg": "jpeg",
            ".jpeg": "jpeg",
            ".pdf": "pdf",
        }[suffix.lower()]
    except KeyError as error:
        raise RestorationError(
            "unsupported_output_format",
            "Output suffix must be .png, .jpg, .jpeg, or .pdf.",
        ) from error


def _single_page_pdf(
    jpeg: bytes,
    width: int,
    height: int,
    dpi: int,
) -> bytes:
    page_width = width * 72 / dpi
    page_height = height * 72 / dpi
    stream = (
        f"q\n{page_width:.6f} 0 0 {page_height:.6f} 0 0 cm\n/Im0 Do\nQ\n"
    ).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 "
            f"{page_width:.6f} {page_height:.6f}] /Resources << /XObject "
            f"<< /Im0 4 0 R >> >> /Contents 5 0 R >>"
        ).encode("ascii"),
        (
            f"<< /Type /XObject /Subtype /Image /Width {width} /Height {height} "
            f"/ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /DCTDecode "
            f"/Length {len(jpeg)} >>\nstream\n"
        ).encode("ascii")
        + jpeg
        + b"\nendstream",
        f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
        + stream
        + b"endstream",
    ]
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for index, item in enumerate(objects, 1):
        offsets.append(len(output))
        output += f"{index} 0 obj\n".encode("ascii") + item + b"\nendobj\n"
    xref = len(output)
    output += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii")
    for offset in offsets:
        output += f"{offset:010d} 00000 n \n".encode("ascii")
    output += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n"
    ).encode("ascii")
    return bytes(output)
