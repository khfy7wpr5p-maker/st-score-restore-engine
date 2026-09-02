from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage3_custody_execution import Stage3CustodyExecutionError
from st_score_restore.stage3_purpose_grants import (
    APPROVED_GRANT_CANONICAL_SHA256,
    Stage3PurposeGrantError,
    run_purpose_granted_pdf_pipeline_execution,
    validate_stage3_purpose_grants,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"
GRANT_PATH = ROOT / "evidence" / "stage3" / "governance" / "purpose-grants.v1.json"
BEETHOVEN = "dataset.item.imslp799143-beethoven-op48-no3.v1"
BARLEY = "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1"
CHOPIN = "dataset.item.imslp82860-chopin-op69.v2"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Stage3PurposeGrantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = _json(CATALOG_PATH)
        self.grants = _json(GRANT_PATH)

    def test_committed_overlay_is_exactly_approved(self) -> None:
        validated = validate_stage3_purpose_grants(self.grants)
        self.assertEqual("stage3.purpose-grants.beethoven-barley.v1", validated["grantSetId"])
        self.assertEqual(2, len(validated["grants"]))
        self.assertEqual(
            "3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8",
            APPROVED_GRANT_CANONICAL_SHA256,
        )
        self.assertFalse(validated["assertions"]["historicalCatalogModified"])
        self.assertFalse(validated["assertions"]["trainingAuthorized"])
        self.assertFalse(validated["assertions"]["calibrationAuthorized"])
        self.assertFalse(validated["assertions"]["publicationAuthorized"])
        self.assertFalse(validated["assertions"]["externalExportAuthorized"])

    def test_tampered_overlay_fails_closed(self) -> None:
        tampered = deepcopy(self.grants)
        tampered["grants"][0]["permission"]["restrictions"][-1]["allowed"] = True
        with self.assertRaises(Stage3PurposeGrantError):
            validate_stage3_purpose_grants(tampered)

    def test_beethoven_grant_advances_to_exact_byte_gate(self) -> None:
        with self.assertRaises(Stage3CustodyExecutionError) as caught:
            run_purpose_granted_pdf_pipeline_execution(
                self.catalog,
                self.grants,
                dataset_item_id=BEETHOVEN,
                data=b"not-the-admitted-beethoven-pdf",
                purpose="pdf_pipeline_evaluation",
                execution_date="2026-09-02",
            )
        self.assertEqual("exact_sha256_mismatch", caught.exception.code)

    def test_barley_grant_advances_to_exact_byte_gate(self) -> None:
        with self.assertRaises(Stage3CustodyExecutionError) as caught:
            run_purpose_granted_pdf_pipeline_execution(
                self.catalog,
                self.grants,
                dataset_item_id=BARLEY,
                data=b"not-the-admitted-barley-pdf",
                purpose="pdf_pipeline_evaluation",
                execution_date="2026-09-02",
            )
        self.assertEqual("exact_sha256_mismatch", caught.exception.code)

    def test_overlay_does_not_apply_to_held_out(self) -> None:
        with self.assertRaises(Stage3CustodyExecutionError) as caught:
            run_purpose_granted_pdf_pipeline_execution(
                self.catalog,
                self.grants,
                dataset_item_id=CHOPIN,
                data=b"not-the-admitted-chopin-pdf",
                purpose="held_out_evaluation",
                execution_date="2026-09-02",
            )
        self.assertEqual("purpose_grant_split_not_allowed", caught.exception.code)

    def test_overlay_cannot_override_non_not_requested_catalog_state(self) -> None:
        catalog = deepcopy(self.catalog)
        item = next(value for value in catalog["items"] if value["datasetItemId"] == BEETHOVEN)
        item["permissions"]["pdf_pipeline_evaluation"]["status"] = "denied"
        with self.assertRaises(Stage3CustodyExecutionError) as caught:
            run_purpose_granted_pdf_pipeline_execution(
                catalog,
                self.grants,
                dataset_item_id=BEETHOVEN,
                data=b"irrelevant",
                purpose="pdf_pipeline_evaluation",
                execution_date="2026-09-02",
            )
        self.assertEqual("purpose_grant_cannot_override_catalog_state", caught.exception.code)


if __name__ == "__main__":
    unittest.main()
