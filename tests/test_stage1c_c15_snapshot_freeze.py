from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_manifest import load_dataset_catalog  # noqa: E402
from tools.build_stage1_snapshot import (  # noqa: E402
    CATALOG_PATH,
    build_snapshot,
    canonical_json,
)


class Stage1CC15SnapshotFreezeTests(unittest.TestCase):
    def test_candidate_is_deterministic_non_mutating_and_split_frozen(self) -> None:
        catalog = load_dataset_catalog(CATALOG_PATH)
        original = copy.deepcopy(catalog)
        first = build_snapshot(catalog)
        second = build_snapshot(catalog)
        self.assertEqual(canonical_json(first), canonical_json(second))
        self.assertEqual(catalog, original)
        self.assertTrue(first["heldOutFrozen"])
        self.assertFalse(first["trainingUseActivated"])
        self.assertEqual(first["revokedItemIds"], [])
        self.assertEqual(first["coverage"]["realItemCount"], 2)
        self.assertEqual(first["coverage"]["syntheticItemCount"], 0)
        self.assertEqual(
            [assignment["split"] for assignment in first["assignments"]],
            ["development", "held_out"],
        )
        self.assertEqual(
            [assignment["datasetItemId"] for assignment in first["assignments"]],
            sorted(assignment["datasetItemId"] for assignment in first["assignments"]),
        )

    def test_snapshot_records_coverage_gaps_without_claiming_coverage_pass(self) -> None:
        snapshot = build_snapshot(load_dataset_catalog(CATALOG_PATH))
        self.assertEqual(
            snapshot["coverage"]["gapCodes"],
            ["coverage.single-item-per-split", "coverage.two-item-corpus"],
        )
        self.assertIn("coverage-not-yet-accepted", snapshot["review"]["noteCodes"])


if __name__ == "__main__":
    unittest.main()
