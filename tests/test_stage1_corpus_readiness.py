from __future__ import annotations

import copy
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from dataset_test_item_helpers import item, permission  # noqa: E402
from st_score_restore.dataset_contract_constants import DatasetManifestError  # noqa: E402
from st_score_restore.dataset_manifest import load_json_object  # noqa: E402
from tools.evaluate_stage1_corpus_readiness import (  # noqa: E402
    evaluate_corpus_readiness,
    parse_date,
    validate_repository_contract,
)


class Stage1CorpusReadinessTests(unittest.TestCase):
    AS_OF = date(2026, 8, 25)

    def catalog(self, *items: dict) -> dict:
        return {
            "schemaVersion": "1.3.0",
            "entryDecisionId": "adr-0013-stage-1-entry-v1",
            "catalogId": "dataset.catalog.c13-readiness-test.v1",
            "descriptionCode": "c13-readiness-test",
            "items": list(items),
        }

    def development(self, *, digest: str = "a" * 64, family: str = "source.family.c13-dev.v1") -> dict:
        return item(
            item_id="dataset.item.c13-dev.v1",
            family_id=family,
            split="development",
            artifact_state="external_available",
            granted_purpose="quality_evaluation",
            artifact_sha=digest,
        )

    def held_out(self, *, digest: str = "b" * 64, family: str = "source.family.c13-held.v1") -> dict:
        return item(
            item_id="dataset.item.c13-held.v1",
            family_id=family,
            split="held_out",
            artifact_state="external_available",
            granted_purpose="held_out_evaluation",
            artifact_sha=digest,
        )

    def test_repository_contract_and_current_real_catalog_are_blocked_only_by_missing_held_out(self) -> None:
        validate_repository_contract()
        catalog = load_json_object(
            ROOT / "evidence" / "stage1c" / "imslp799143" / "catalog.v1.json"
        )
        result = evaluate_corpus_readiness(catalog, as_of=self.AS_OF)
        self.assertEqual(result["state"], "blocked")
        self.assertEqual(result["counts"], {"development": 1, "held_out": 0})
        self.assertEqual(result["reasonCodes"], ["missing_held_out_item"])

    def test_distinct_development_and_held_out_items_are_structurally_ready(self) -> None:
        result = evaluate_corpus_readiness(
            self.catalog(self.development(), self.held_out()), as_of=self.AS_OF
        )
        self.assertEqual(result["state"], "ready")
        self.assertEqual(result["reasonCodes"], [])
        self.assertEqual(result["sourceFamilyCounts"], {"development": 1, "held_out": 1})

    def test_identical_artifact_digest_across_splits_is_rejected_by_base_contract(self) -> None:
        with self.assertRaises(DatasetManifestError):
            evaluate_corpus_readiness(
                self.catalog(
                    self.development(digest="c" * 64),
                    self.held_out(digest="c" * 64),
                ),
                as_of=self.AS_OF,
            )

    def test_missing_development_item_blocks(self) -> None:
        result = evaluate_corpus_readiness(self.catalog(self.held_out()), as_of=self.AS_OF)
        self.assertEqual(result["state"], "blocked")
        self.assertIn("missing_development_item", result["reasonCodes"])

    def test_expired_held_out_catalog_is_rejected_by_base_contract(self) -> None:
        held = self.held_out()
        held["permissions"]["held_out_evaluation"] = permission(
            "expired", authorized_on="2026-08-01", expires_on="2026-08-20"
        )
        with self.assertRaises(DatasetManifestError):
            evaluate_corpus_readiness(
                self.catalog(self.development(), held), as_of=self.AS_OF
            )

    def test_extra_active_purpose_blocks(self) -> None:
        dev = self.development()
        dev["permissions"]["demonstration"] = permission("granted")
        result = evaluate_corpus_readiness(
            self.catalog(dev, self.held_out()), as_of=self.AS_OF
        )
        self.assertEqual(result["state"], "blocked")
        self.assertIn("active_purpose_set_not_exact", result["reasonCodes"])
        self.assertIn("unauthorized_active_purpose", result["reasonCodes"])

    def test_metadata_only_planning_item_does_not_create_false_coverage(self) -> None:
        planning = item(item_id="dataset.item.c13-plan.v1", family_id="source.family.c13-plan.v1")
        result = evaluate_corpus_readiness(
            self.catalog(self.development(), self.held_out(), planning), as_of=self.AS_OF
        )
        self.assertEqual(result["state"], "ready")
        self.assertEqual(result["counts"], {"development": 1, "held_out": 1})

    def test_evaluation_is_deterministic_and_non_mutating(self) -> None:
        catalog = self.catalog(self.development(), self.held_out())
        original = copy.deepcopy(catalog)
        first = evaluate_corpus_readiness(catalog, as_of=self.AS_OF)
        second = evaluate_corpus_readiness(catalog, as_of=self.AS_OF)
        self.assertEqual(first, second)
        self.assertEqual(catalog, original)

    def test_date_parser_is_strict(self) -> None:
        self.assertEqual(parse_date("2026-08-25"), self.AS_OF)
        with self.assertRaises(ValueError):
            parse_date("2026-8-25")


if __name__ == "__main__":
    unittest.main()
