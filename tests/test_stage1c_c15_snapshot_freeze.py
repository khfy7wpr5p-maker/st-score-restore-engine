from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_manifest import (  # noqa: E402
    canonical_sha256,
    load_dataset_catalog,
)
from tools.build_stage1_snapshot import (  # noqa: E402
    CATALOG_PATH,
    SNAPSHOT_PATH,
    build_snapshot,
    canonical_json,
    verify_committed_snapshot,
)

EXPECTED_CATALOG_SHA256 = "059c40b619d3c7815f14377cc8b26fce9a6b0522f2419f481bd93b15ed60e937"
EXPECTED_SNAPSHOT_SHA256 = "b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476"
EXPECTED_ITEM_SHA256 = {
    "dataset.item.imslp799143-beethoven-op48-no3.v1": "c1f06342ba4932e2a087e76d424fbb253d63fa19bf7dc7f07196fbe99026b23f",
    "dataset.item.imslp82860-chopin-op69.v1": "b8aab0a86924043c038c44f3f7346199628ae101e520c7f023d934485db3e58b",
}


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

    def test_committed_snapshot_is_exact_digest_bound_freeze(self) -> None:
        catalog = load_dataset_catalog(CATALOG_PATH)
        expected = build_snapshot(catalog)
        committed = verify_committed_snapshot(expected, catalog=catalog, path=SNAPSHOT_PATH)
        self.assertEqual(canonical_sha256(catalog), EXPECTED_CATALOG_SHA256)
        self.assertEqual(canonical_sha256(committed), EXPECTED_SNAPSHOT_SHA256)
        self.assertEqual(
            {
                assignment["datasetItemId"]: assignment["itemSha256"]
                for assignment in committed["assignments"]
            },
            EXPECTED_ITEM_SHA256,
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
