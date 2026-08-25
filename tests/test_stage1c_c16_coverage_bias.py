from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from st_score_restore.dataset_manifest import load_dataset_catalog, load_dataset_snapshot
from tools.evaluate_stage1_coverage_bias import (
    CATALOG_PATH,
    REPORT_PATH,
    SNAPSHOT_PATH,
    CoverageBiasError,
    build_coverage_bias_report,
    canonical_json,
    verify_committed_report,
)


class Stage1CC16CoverageBiasTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_dataset_catalog(CATALOG_PATH)
        self.snapshot = load_dataset_snapshot(SNAPSHOT_PATH, catalog=self.catalog)

    def test_repository_report_is_deterministic_and_explicitly_insufficient(self) -> None:
        report = build_coverage_bias_report(self.catalog, self.snapshot)
        committed = verify_committed_report(report)
        self.assertEqual(canonical_json(report), canonical_json(committed))
        self.assertEqual(report["sufficiency"]["state"], "insufficient")
        self.assertTrue(report["sufficiency"]["requiresCorpusExpansion"])
        self.assertFalse(report["sufficiency"]["stage1ExitSupported"])
        self.assertFalse(report["sufficiency"]["stage2EntrySupported"])

    def test_current_frozen_counts_and_gaps_are_exact(self) -> None:
        report = build_coverage_bias_report(self.catalog, self.snapshot)
        self.assertEqual(report["counts"]["itemCount"], 2)
        self.assertEqual(report["counts"]["pageCounts"], {
            "development": 4,
            "held_out": 8,
            "total": 12,
        })
        self.assertEqual(report["counts"]["notationItemCounts"]["staff"], 2)
        self.assertEqual(report["counts"]["notationItemCounts"]["guitar_tab"], 0)
        self.assertEqual(
            report["counts"]["notationItemCounts"]["combined_staff_tab"], 0
        )
        self.assertEqual(report["counts"]["inputKindItemCounts"]["scanned_pdf"], 2)
        self.assertEqual(report["counts"]["inputKindItemCounts"]["phone_photo"], 0)
        self.assertEqual(report["counts"]["degradationItemCounts"]["none"], 2)
        self.assertEqual(
            report["gapCodes"],
            [
                "coverage.missing-combined-staff-tab",
                "coverage.missing-degraded-source",
                "coverage.missing-guitar-tab",
                "coverage.missing-phone-photo",
                "coverage.single-item-development",
                "coverage.single-item-held-out",
                "coverage.two-item-corpus",
            ],
        )

    def test_evaluation_is_non_mutating(self) -> None:
        catalog_before = copy.deepcopy(self.catalog)
        snapshot_before = copy.deepcopy(self.snapshot)
        first = build_coverage_bias_report(self.catalog, self.snapshot)
        second = build_coverage_bias_report(self.catalog, self.snapshot)
        self.assertEqual(first, second)
        self.assertEqual(self.catalog, catalog_before)
        self.assertEqual(self.snapshot, snapshot_before)

    def test_snapshot_digest_drift_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.snapshot)
        mutated["version"] = "1.0.1"
        with self.assertRaisesRegex(CoverageBiasError, "unexpected frozen snapshot digest"):
            build_coverage_bias_report(self.catalog, mutated)

    def test_catalog_outside_frozen_snapshot_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.catalog)
        extra = copy.deepcopy(mutated["items"][0])
        extra["datasetItemId"] = "dataset.item.extra-unfrozen.v1"
        extra["sourceFamilyId"] = "source.family.extra-unfrozen.v1"
        mutated["items"].append(extra)
        with self.assertRaises(CoverageBiasError):
            build_coverage_bias_report(mutated, self.snapshot)

    def test_committed_report_duplicate_keys_fail_closed(self) -> None:
        report = build_coverage_bias_report(self.catalog, self.snapshot)
        serialized = json.dumps(report, ensure_ascii=False, separators=(",", ":"))
        duplicate = (
            '{"sufficiency":{"state":"sufficient","stage1ExitSupported":true},'
            + serialized[1:]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "coverage-report.json"
            path.write_text(duplicate, encoding="utf-8")
            with self.assertRaisesRegex(
                CoverageBiasError, "committed C16 report is not strict JSON"
            ):
                verify_committed_report(report, path=path)

    def test_safety_assertions_never_claim_downstream_evidence(self) -> None:
        report = build_coverage_bias_report(self.catalog, self.snapshot)
        assertions = report["assertions"]
        self.assertTrue(assertions["heldOutFrozen"])
        self.assertFalse(assertions["trainingUseActivated"])
        self.assertFalse(assertions["representativenessEstablished"])
        self.assertFalse(assertions["absenceOfBiasEstablished"])
        self.assertFalse(assertions["restorationEffectivenessEstablished"])
        self.assertFalse(assertions["omrImprovementEstablished"])


if __name__ == "__main__":
    unittest.main()
