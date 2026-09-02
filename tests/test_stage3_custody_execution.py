from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

import cv2
import numpy as np

from st_score_restore.stage3_custody_execution import (
    Stage3CustodyExecutionError,
    run_authorized_pdf_pipeline_execution,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"
BEETHOVEN = "dataset.item.imslp799143-beethoven-op48-no3.v1"
BARLEY = "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1"
CHOPIN = "dataset.item.imslp82860-chopin-op69.v2"
C17A = "dataset.item.wikimedia-guitar-technical-exercise-no1.v1"


def _load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _catalog_for(item_id: str, data: bytes, *, grant_pdf_pipeline: bool = False) -> dict:
    catalog = _load_catalog()
    source = next(item for item in catalog["items"] if item["datasetItemId"] == item_id)
    item = deepcopy(source)
    digest = hashlib.sha256(data).hexdigest()
    item["artifact"]["sha256"] = digest
    item["artifact"]["byteSize"] = len(data)
    if item["privacy"]["deidentifiedArtifactSha256"] is not None:
        item["privacy"]["deidentifiedArtifactSha256"] = digest
    if grant_pdf_pipeline:
        item["permissions"]["pdf_pipeline_evaluation"] = {
            "status": "granted",
            "authorizationReference": "evidence:opq_11111111111111111111111111111111",
            "authorizedBy": "actor.purpose:opq_22222222222222222222222222222222",
            "authorizedOn": "2026-09-02",
            "expiresOn": None,
            "restrictions": [],
            "revokedOn": None,
            "revocationReference": None,
        }
    catalog["items"] = [item]
    return catalog


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


def _assemble_pdf(objects: list[bytes]) -> bytes:
    chunks = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(sum(len(chunk) for chunk in chunks))
        chunks.append(str(index).encode("ascii") + b" 0 obj\n" + body + b"\nendobj\n")
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


def _raster_pdf() -> bytes:
    jpeg = _jpeg_bytes()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 300] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>",
        _stream(
            jpeg,
            b"/Type /XObject /Subtype /Image /Width 72 /Height 96 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode",
        ),
        _stream(b"q\n200 0 0 300 0 0 cm\n/Im0 Do\nQ"),
    ]
    return _assemble_pdf(objects)


def _vector_pdf() -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 300] /Resources << /Font << >> >> /Contents 4 0 R >>",
        _stream(b"10 10 m\n190 290 l\n2 w\nS"),
    ]
    return _assemble_pdf(objects)


class Stage3CustodyExecutionTests(unittest.TestCase):
    def test_development_real_permission_state_fails_closed(self) -> None:
        raw = _raster_pdf()
        catalog = _catalog_for(BEETHOVEN, raw)
        with self.assertRaises(Stage3CustodyExecutionError) as caught:
            run_authorized_pdf_pipeline_execution(
                catalog,
                dataset_item_id=BEETHOVEN,
                data=raw,
                purpose="pdf_pipeline_evaluation",
                execution_date="2026-09-02",
            )
        self.assertEqual("purpose_permission_not_valid", caught.exception.code)

    def test_development_executes_only_with_explicit_pdf_pipeline_permission(self) -> None:
        raw = _raster_pdf()
        catalog = _catalog_for(BEETHOVEN, raw, grant_pdf_pipeline=True)
        result = run_authorized_pdf_pipeline_execution(
            catalog,
            dataset_item_id=BEETHOVEN,
            data=raw,
            purpose="pdf_pipeline_evaluation",
            execution_date="2026-09-02",
        )
        receipt = result.to_public_dict()
        self.assertEqual("completed", receipt["status"])
        self.assertEqual("pdf_pipeline_evaluation", receipt["purpose"])
        self.assertEqual("development", receipt["split"])
        self.assertEqual(1, receipt["pageSummary"]["renderedPageCount"])
        self.assertFalse(receipt["pageSummary"]["vectorPagesRasterized"])
        self.assertTrue(receipt["assertions"]["exactDigestMatched"])
        self.assertFalse(receipt["assertions"]["heldOutThresholdTuningUsed"])
        self.assertNotIn("pages", receipt)
        self.assertNotIn("metrics", receipt)
        self.assertNotIn("findings", receipt)
        self.assertIsNotNone(result.restricted_manifest_for_custody())
        self.assertIsNotNone(result.restricted_page_bytes_for_custody(0))

    def test_held_out_uses_existing_held_out_evaluation_permission(self) -> None:
        raw = _raster_pdf()
        catalog = _catalog_for(CHOPIN, raw)
        result = run_authorized_pdf_pipeline_execution(
            catalog,
            dataset_item_id=CHOPIN,
            data=raw,
            purpose="held_out_evaluation",
            execution_date="2026-09-02",
        )
        receipt = result.to_public_dict()
        self.assertEqual("held_out", receipt["split"])
        self.assertEqual("held_out_evaluation", receipt["purpose"])
        self.assertFalse(receipt["assertions"]["heldOutThresholdTuningUsed"])
        self.assertFalse(receipt["assertions"]["calibrationAuthorized"])

    def test_held_out_cannot_request_pdf_pipeline_evaluation(self) -> None:
        raw = _raster_pdf()
        catalog = _catalog_for(CHOPIN, raw)
        with self.assertRaises(Stage3CustodyExecutionError) as caught:
            run_authorized_pdf_pipeline_execution(
                catalog,
                dataset_item_id=CHOPIN,
                data=raw,
                purpose="pdf_pipeline_evaluation",
                execution_date="2026-09-02",
            )
        self.assertEqual("purpose_not_authorized_for_split", caught.exception.code)

    def test_exact_digest_mismatch_fails_before_pipeline(self) -> None:
        raw = _raster_pdf()
        catalog = _catalog_for(BEETHOVEN, raw, grant_pdf_pipeline=True)
        with self.assertRaises(Stage3CustodyExecutionError) as caught:
            run_authorized_pdf_pipeline_execution(
                catalog,
                dataset_item_id=BEETHOVEN,
                data=raw + b"x",
                purpose="pdf_pipeline_evaluation",
                execution_date="2026-09-02",
            )
        self.assertEqual("exact_sha256_mismatch", caught.exception.code)

    def test_non_pdf_catalog_item_is_rejected(self) -> None:
        raw = b"not-a-pdf"
        catalog = _catalog_for(C17A, raw)
        with self.assertRaises(Stage3CustodyExecutionError) as caught:
            run_authorized_pdf_pipeline_execution(
                catalog,
                dataset_item_id=C17A,
                data=raw,
                purpose="pdf_pipeline_evaluation",
                execution_date="2026-09-02",
            )
        self.assertEqual("non_pdf_dataset_item", caught.exception.code)

    def test_digital_vector_pdf_is_preserved_without_derivative(self) -> None:
        raw = _vector_pdf()
        catalog = _catalog_for(BARLEY, raw, grant_pdf_pipeline=True)
        result = run_authorized_pdf_pipeline_execution(
            catalog,
            dataset_item_id=BARLEY,
            data=raw,
            purpose="pdf_pipeline_evaluation",
            execution_date="2026-09-02",
        )
        receipt = result.to_public_dict()
        self.assertEqual(0, receipt["pageSummary"]["renderedPageCount"])
        self.assertEqual(1, receipt["pageSummary"]["classificationCounts"]["vector_only"])
        self.assertFalse(receipt["pageSummary"]["vectorPagesRasterized"])
        self.assertIsNone(result.restricted_page_bytes_for_custody(0))

    def test_public_receipt_is_deterministic_and_redacted(self) -> None:
        raw = _raster_pdf()
        catalog = _catalog_for(BEETHOVEN, raw, grant_pdf_pipeline=True)
        kwargs = dict(
            dataset_item_id=BEETHOVEN,
            data=raw,
            purpose="pdf_pipeline_evaluation",
            execution_date="2026-09-02",
        )
        first = run_authorized_pdf_pipeline_execution(catalog, **kwargs).to_public_dict()
        second = run_authorized_pdf_pipeline_execution(catalog, **kwargs).to_public_dict()
        self.assertEqual(first, second)
        self.assertEqual(first["receiptDigest"], second["receiptDigest"])
        serialized = json.dumps(first, sort_keys=True)
        self.assertNotIn('"qualityAnalysis"', serialized)
        self.assertNotIn('"pages"', serialized)
        self.assertNotIn('"metrics"', serialized)
        self.assertNotIn('"findings"', serialized)


if __name__ == "__main__":
    unittest.main()
