from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

import cv2
import numpy as np

from st_score_restore.stage2_custody_execution import (
    APPROVED_CUSTODY_ENVIRONMENT,
    CustodyExecutionError,
    run_authorized_quality_execution,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"

C17A = "dataset.item.wikimedia-guitar-technical-exercise-no1.v1"
C17B = "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1"
BEETHOVEN = "dataset.item.imslp799143-beethoven-op48-no3.v1"
C17D = "dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1"


def _load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _encode_png(image: np.ndarray) -> bytes:
    ok, payload = cv2.imencode(".png", image)
    if not ok:
        raise AssertionError("PNG encoding failed")
    return bytes(payload)


def _encode_jpeg(image: np.ndarray) -> bytes:
    ok, payload = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise AssertionError("JPEG encoding failed")
    return bytes(payload)


def _staff_page() -> np.ndarray:
    image = np.full((800, 1000), 245, dtype=np.uint8)
    for start in (180, 430):
        for offset in range(5):
            y = start + offset * 12
            cv2.line(image, (80, y), (920, y), 0, 2)
    cv2.rectangle(image, (30, 30), (969, 769), 80, 3)
    return image


def _catalog_for(item_id: str, data: bytes) -> dict:
    catalog = _load_catalog()
    source = next(item for item in catalog["items"] if item["datasetItemId"] == item_id)
    item = deepcopy(source)
    digest = hashlib.sha256(data).hexdigest()
    item["artifact"]["sha256"] = digest
    item["artifact"]["byteSize"] = len(data)
    if item["privacy"]["deidentifiedArtifactSha256"] is not None:
        item["privacy"]["deidentifiedArtifactSha256"] = digest
    catalog["items"] = [item]
    return catalog


def _minimal_digital_pdf() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Page /Font << >> >> endobj\n"
        b"%%EOF\n"
    )


def _minimal_scanned_pdf() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Page /Subtype /Image >> endobj\n"
        b"%%EOF\n"
    )


class Stage2CustodyExecutionTests(unittest.TestCase):
    def test_development_raster_executes_after_exact_byte_and_permission_gates(self):
        raw = _encode_png(_staff_page())
        catalog = _catalog_for(C17A, raw)

        result = run_authorized_quality_execution(
            catalog,
            dataset_item_id=C17A,
            data=raw,
            purpose="quality_evaluation",
            execution_date="2026-09-02",
        )
        receipt = result.to_public_dict()
        private = result.restricted_report_for_custody()

        self.assertEqual("analyzed", receipt["status"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), receipt["sourceDigest"]["value"])
        self.assertEqual(len(raw), receipt["byteSize"])
        self.assertTrue(receipt["assertions"]["exactDigestMatched"])
        self.assertTrue(receipt["assertions"]["purposePermissionValid"])
        self.assertFalse(receipt["reportHandling"]["detailedReportExported"])
        self.assertNotIn("metrics", receipt)
        self.assertNotIn("findings", receipt)
        self.assertIsNotNone(private)
        assert private is not None
        self.assertIn("metrics", private)
        self.assertEqual(
            private["reportDigest"]["value"],
            receipt["reportDigest"]["value"],
        )

    def test_exact_digest_mismatch_fails_before_analysis(self):
        raw = _encode_png(_staff_page())
        catalog = _catalog_for(C17A, raw)
        changed = raw + b"x"

        with self.assertRaises(CustodyExecutionError) as context:
            run_authorized_quality_execution(
                catalog,
                dataset_item_id=C17A,
                data=changed,
                purpose="quality_evaluation",
                execution_date="2026-09-02",
            )
        self.assertEqual("exact_sha256_mismatch", context.exception.code)

    def test_held_out_cannot_be_run_as_development_quality_evaluation(self):
        raw = _encode_jpeg(_staff_page())
        catalog = _catalog_for(C17D, raw)

        with self.assertRaises(CustodyExecutionError) as context:
            run_authorized_quality_execution(
                catalog,
                dataset_item_id=C17D,
                data=raw,
                purpose="quality_evaluation",
                execution_date="2026-09-02",
            )
        self.assertEqual("purpose_not_authorized_for_split", context.exception.code)

    def test_held_out_restricted_receipt_never_exports_detailed_metrics(self):
        raw = _encode_jpeg(_staff_page())
        catalog = _catalog_for(C17D, raw)

        result = run_authorized_quality_execution(
            catalog,
            dataset_item_id=C17D,
            data=raw,
            purpose="held_out_evaluation",
            execution_date="2026-09-02",
        )
        receipt = result.to_public_dict()

        self.assertEqual("analyzed", receipt["status"])
        self.assertEqual("held_out", receipt["split"])
        self.assertEqual("managed_restricted", receipt["storageClass"])
        self.assertEqual(
            "explicitly_blocked",
            receipt["reportHandling"]["externalExportState"],
        )
        self.assertTrue(receipt["reportHandling"]["custodyOnly"])
        self.assertFalse(receipt["reportHandling"]["detailedReportPublic"])
        self.assertFalse(receipt["assertions"]["publicationAuthorized"])
        self.assertNotIn("metrics", receipt)
        self.assertNotIn("findings", receipt)
        self.assertIsNotNone(result.restricted_report_for_custody())

    def test_environment_allowlist_is_enforced(self):
        raw = _encode_png(_staff_page())
        catalog = _catalog_for(C17A, raw)
        item = catalog["items"][0]
        permission = item["permissions"]["quality_evaluation"]
        permission["restrictions"] = [
            restriction
            for restriction in permission["restrictions"]
            if restriction["type"] != "environment_allowlist"
        ]
        permission["restrictions"].append(
            {
                "type": "environment_allowlist",
                "values": [APPROVED_CUSTODY_ENVIRONMENT],
            }
        )

        with self.assertRaises(CustodyExecutionError) as context:
            run_authorized_quality_execution(
                catalog,
                dataset_item_id=C17A,
                data=raw,
                purpose="quality_evaluation",
                execution_date="2026-09-02",
                environment="other_offline",
            )
        self.assertEqual("environment_restriction_violation", context.exception.code)

    def test_digital_pdf_is_executed_as_vector_not_applicable(self):
        raw = _minimal_digital_pdf()
        catalog = _catalog_for(C17B, raw)

        result = run_authorized_quality_execution(
            catalog,
            dataset_item_id=C17B,
            data=raw,
            purpose="quality_evaluation",
            execution_date="2026-09-02",
        )
        receipt = result.to_public_dict()

        self.assertEqual("not_applicable_vector_pdf", receipt["status"])
        self.assertIsNotNone(receipt["reportDigest"])
        private = result.restricted_report_for_custody()
        self.assertIsNotNone(private)
        assert private is not None
        self.assertEqual("not_applicable_vector_pdf", private["status"])

    def test_scanned_pdf_defers_to_stage3_without_becoming_execution_failure(self):
        raw = _minimal_scanned_pdf()
        catalog = _catalog_for(BEETHOVEN, raw)

        result = run_authorized_quality_execution(
            catalog,
            dataset_item_id=BEETHOVEN,
            data=raw,
            purpose="quality_evaluation",
            execution_date="2026-09-02",
        )
        receipt = result.to_public_dict()

        self.assertEqual("deferred_stage3_renderer", receipt["status"])
        self.assertEqual("pdf_renderer_not_available", receipt["analysisErrorCode"])
        self.assertIsNone(receipt["reportDigest"])
        self.assertIsNone(result.restricted_report_for_custody())

    def test_public_receipt_is_deterministic_for_same_inputs(self):
        raw = _encode_png(_staff_page())
        catalog = _catalog_for(C17A, raw)

        first = run_authorized_quality_execution(
            catalog,
            dataset_item_id=C17A,
            data=raw,
            purpose="quality_evaluation",
            execution_date="2026-09-02",
        ).to_public_dict()
        second = run_authorized_quality_execution(
            catalog,
            dataset_item_id=C17A,
            data=raw,
            purpose="quality_evaluation",
            execution_date="2026-09-02",
        ).to_public_dict()

        self.assertEqual(first, second)
        self.assertEqual(first["receiptDigest"], second["receiptDigest"])


if __name__ == "__main__":
    unittest.main()
