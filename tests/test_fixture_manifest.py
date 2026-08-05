"""Regression tests for fixture metadata, consent, and usage rules."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.fixture_manifest import (  # noqa: E402
    FixtureCatalogError,
    load_catalog,
    validate_catalog,
)


class FixtureManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (ROOT / "fixtures" / "catalog.v1.json").open(
            "r", encoding="utf-8"
        ) as handle:
            cls.catalog = json.load(handle)

    def test_repository_catalog_is_valid_and_complete(self) -> None:
        result = load_catalog(ROOT / "fixtures" / "catalog.v1.json")
        self.assertEqual("1.0.0", result["schemaVersion"])
        self.assertGreaterEqual(len(result["fixtures"]), 7)

    def test_teacher_approval_does_not_imply_training_consent(self) -> None:
        candidate = copy.deepcopy(self.catalog)
        fixture = candidate["fixtures"][0]
        fixture["consent"]["teacherApproval"] = True
        fixture["consent"]["trainingConsent"] = "not_requested"
        fixture["permittedUses"]["training"] = True
        with self.assertRaisesRegex(FixtureCatalogError, "training requires"):
            validate_catalog(candidate)

    def test_available_artifact_requires_digest_and_size(self) -> None:
        candidate = copy.deepcopy(self.catalog)
        fixture = candidate["fixtures"][0]
        fixture["artifact"]["state"] = "available"
        fixture["artifact"]["relativePath"] = "fixtures/public/clean-score.pdf"
        fixture["artifact"]["sha256"] = None
        fixture["artifact"]["byteSize"] = 100
        fixture["review"]["status"] = "approved"
        fixture["review"]["reviewedBy"] = "fixture-review-board"
        fixture["review"]["reviewedOn"] = "2026-08-05"
        fixture["retention"]["policy"] = "repository_permanent"
        fixture["retention"]["storageLocation"] = "fixtures/public"
        fixture["permittedUses"]["testing"] = True
        with self.assertRaisesRegex(FixtureCatalogError, "requires path, sha256"):
            validate_catalog(candidate)

    def test_identifiable_personal_data_cannot_be_published(self) -> None:
        candidate = copy.deepcopy(self.catalog)
        fixture = candidate["fixtures"][0]
        fixture["privacy"]["containsPersonalData"] = True
        fixture["privacy"]["deidentified"] = False
        fixture["privacy"]["privacyReviewStatus"] = "approved"
        fixture["review"]["status"] = "approved"
        fixture["review"]["reviewedBy"] = "fixture-review-board"
        fixture["review"]["reviewedOn"] = "2026-08-05"
        fixture["permittedUses"]["publication"] = True
        with self.assertRaisesRegex(FixtureCatalogError, "identifiable personal data"):
            validate_catalog(candidate)

    def test_catalog_requires_all_degradation_categories(self) -> None:
        candidate = copy.deepcopy(self.catalog)
        for fixture in candidate["fixtures"]:
            fixture["degradations"] = [
                item for item in fixture["degradations"] if item != "glare"
            ] or ["none"]
        with self.assertRaisesRegex(FixtureCatalogError, "missing degradation"):
            validate_catalog(candidate)

    def test_duplicate_regression_ids_are_rejected(self) -> None:
        candidate = copy.deepcopy(self.catalog)
        candidate["fixtures"][1]["annotations"]["regressionId"] = candidate[
            "fixtures"
        ][0]["annotations"]["regressionId"]
        with self.assertRaisesRegex(FixtureCatalogError, "duplicate regressionId"):
            validate_catalog(candidate)


if __name__ == "__main__":
    unittest.main()
