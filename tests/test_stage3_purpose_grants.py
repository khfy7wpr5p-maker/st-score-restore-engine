from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from st_score_restore.dataset_contract_common import canonical_sha256
from st_score_restore.stage3_purpose_grants import (
    AUTHORIZED_DATASET_ITEMS,
    CATALOG_CANONICAL_SHA256,
    PURPOSE,
    Stage3PurposeGrantError,
    apply_stage3_purpose_grants,
    run_authorized_pdf_pipeline_execution_with_grants,
    validate_stage3_purpose_grants,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"
GRANTS_PATH = ROOT / "evidence" / "stage3" / "purpose-grants" / "pdf-pipeline-evaluation.2026-09-02.v1.json"


def _catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _grants() -> dict:
    return json.loads(GRANTS_PATH.read_text(encoding="utf-8"))


class Stage3PurposeGrantTests(unittest.TestCase):
    def test_real_grant_set_validates_without_mutating_historical_catalog(self) -> None:
        catalog = _catalog()
        before = deepcopy(catalog)
        normalized = validate_stage3_purpose_grants(
            catalog,
            _grants(),
            execution_date="2026-09-02",
        )
        self.assertEqual(CATALOG_CANONICAL_SHA256, canonical_sha256(catalog))
        self.assertEqual(before, catalog)
        self.assertEqual(
            set(AUTHORIZED_DATASET_ITEMS),
            {item["datasetItemId"] for item in normalized["grants"]},
        )
        self.assertFalse(normalized["assertions"]["historicalCatalogsModified"])

    def test_overlay_changes_only_pdf_pipeline_permission_for_two_targets(self) -> None:
        catalog = _catalog()
        overlaid = apply_stage3_purpose_grants(
            catalog,
            _grants(),
            execution_date="2026-09-02",
        )
        original_by_id = {item["datasetItemId"]: item for item in catalog["items"]}
        overlay_by_id = {item["datasetItemId"]: item for item in overlaid["items"]}
        for item_id, original in original_by_id.items():
            observed = overlay_by_id[item_id]
            if item_id in AUTHORIZED_DATASET_ITEMS:
                self.assertEqual("not_requested", original["permissions"][PURPOSE]["status"])
                self.assertEqual("granted", observed["permissions"][PURPOSE]["status"])
                restrictions = {
                    item["type"]: item
                    for item in observed["permissions"][PURPOSE]["restrictions"]
                }
                self.assertEqual({"type": "external_export", "allowed": False}, restrictions["external_export"])
                original_other = deepcopy(original["permissions"])
                overlay_other = deepcopy(observed["permissions"])
                original_other.pop(PURPOSE)
                overlay_other.pop(PURPOSE)
                self.assertEqual(original_other, overlay_other)
            else:
                self.assertEqual(original, observed)
        self.assertEqual(CATALOG_CANONICAL_SHA256, canonical_sha256(catalog))

    def test_digest_mismatch_fails_closed(self) -> None:
        grants = _grants()
        grants["grants"][0]["artifactSha256"] = "0" * 64
        with self.assertRaises(Stage3PurposeGrantError) as caught:
            validate_stage3_purpose_grants(_catalog(), grants, execution_date="2026-09-02")
        self.assertEqual("grant_artifact_mismatch", caught.exception.code)

    def test_removed_export_block_fails_closed(self) -> None:
        grants = _grants()
        grants["grants"][0]["permission"]["restrictions"] = [
            item
            for item in grants["grants"][0]["permission"]["restrictions"]
            if item["type"] != "external_export"
        ]
        with self.assertRaises(Stage3PurposeGrantError) as caught:
            validate_stage3_purpose_grants(_catalog(), grants, execution_date="2026-09-02")
        self.assertEqual("grant_restriction_mismatch", caught.exception.code)

    def test_grant_set_cannot_add_a_third_item(self) -> None:
        grants = _grants()
        extra = deepcopy(grants["grants"][0])
        extra["datasetItemId"] = "dataset.item.imslp82860-chopin-op69.v2"
        grants["grants"].append(extra)
        with self.assertRaises(Stage3PurposeGrantError) as caught:
            validate_stage3_purpose_grants(_catalog(), grants, execution_date="2026-09-02")
        self.assertEqual("grant_item_set_mismatch", caught.exception.code)

    def test_wrapper_applies_overlay_before_existing_custody_boundary(self) -> None:
        catalog = _catalog()
        with patch("st_score_restore.stage3_purpose_grants.run_authorized_pdf_pipeline_execution") as runner:
            sentinel = object()
            runner.return_value = sentinel
            result = run_authorized_pdf_pipeline_execution_with_grants(
                catalog,
                _grants(),
                dataset_item_id="dataset.item.imslp799143-beethoven-op48-no3.v1",
                data=b"opaque-real-byte-placeholder",
                execution_date="2026-09-02",
            )
        self.assertIs(sentinel, result)
        call = runner.call_args
        overlaid = call.args[0]
        item = next(
            item
            for item in overlaid["items"]
            if item["datasetItemId"] == "dataset.item.imslp799143-beethoven-op48-no3.v1"
        )
        self.assertEqual("granted", item["permissions"][PURPOSE]["status"])
        self.assertEqual(PURPOSE, call.kwargs["purpose"])
        self.assertEqual("2026-09-02", call.kwargs["execution_date"])


if __name__ == "__main__":
    unittest.main()
