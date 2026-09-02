from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_manifest import canonical_sha256, load_json_object
from tools.build_stage1_expanded_snapshot import (
    CATALOG_PATH,
    REPORT_PATH,
    SNAPSHOT_PATH,
    build_all,
    canonical_json,
)


class Stage1CExpandedSnapshotV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.snapshot, self.report = build_all()
        self.items = self.catalog["items"]
        self.ids = {item["datasetItemId"] for item in self.items}

    def test_exact_five_item_membership_and_c17c_dedup(self) -> None:
        self.assertEqual(
            self.ids,
            {
                "dataset.item.imslp799143-beethoven-op48-no3.v1",
                "dataset.item.wikimedia-guitar-technical-exercise-no1.v1",
                "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1",
                "dataset.item.imslp82860-chopin-op69.v2",
                "dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1",
            },
        )
        self.assertNotIn("dataset.item.imslp82860-chopin-op69.v1", self.ids)
        self.assertEqual(len(self.items), 5)
        self.assertEqual(self.report["counts"]["realItemCount"], 5)
        self.assertEqual(self.report["counts"]["syntheticItemCount"], 0)

    def test_split_source_family_and_digest_isolation(self) -> None:
        development = [item for item in self.items if item["split"] == "development"]
        held_out = [item for item in self.items if item["split"] == "held_out"]
        self.assertEqual(len(development), 3)
        self.assertEqual(len(held_out), 2)

        development_families = {item["sourceFamilyId"] for item in development}
        held_out_families = {item["sourceFamilyId"] for item in held_out}
        self.assertEqual(len(development_families), 3)
        self.assertEqual(len(held_out_families), 2)
        self.assertTrue(development_families.isdisjoint(held_out_families))

        artifact_digests = [item["artifact"]["sha256"] for item in self.items]
        self.assertEqual(len(artifact_digests), len(set(artifact_digests)))

    def test_coverage_closed_without_claiming_stage_exit(self) -> None:
        targets = {target["code"]: target["state"] for target in self.report["coverageTargets"]}
        self.assertEqual(
            targets,
            {
                "notation.staff": "covered",
                "notation.guitar_tab": "covered",
                "notation.combined_staff_tab": "covered",
                "capture.scanned_pdf": "covered",
                "capture.phone_photo": "covered",
                "degradation.non_none": "covered",
            },
        )
        self.assertEqual(self.report["gapCodes"], [])
        self.assertEqual(self.report["sufficiency"]["state"], "review_required")
        self.assertFalse(self.report["sufficiency"]["stage1ExitSupported"])
        self.assertFalse(self.report["sufficiency"]["stage2EntrySupported"])
        self.assertFalse(self.report["assertions"]["representativenessEstablished"])
        self.assertFalse(self.report["assertions"]["absenceOfBiasEstablished"])
        self.assertFalse(self.report["assertions"]["restorationEffectivenessEstablished"])
        self.assertFalse(self.report["assertions"]["omrImprovementEstablished"])

    def test_committed_v2_evidence_matches_builder_exactly(self) -> None:
        expected = (
            (CATALOG_PATH, self.catalog),
            (SNAPSHOT_PATH, self.snapshot),
            (REPORT_PATH, self.report),
        )
        for path, value in expected:
            self.assertTrue(path.is_file(), path)
            self.assertEqual(canonical_json(load_json_object(path)), canonical_json(value), path)

        self.assertEqual(canonical_sha256(self.catalog), "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3")
        self.assertEqual(canonical_sha256(self.snapshot), "c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7")
        self.assertEqual(canonical_sha256(self.report), "45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834")

    def test_historical_c15_c16_files_remain_byte_identical(self) -> None:
        expected_git_blob_ids = {
            "evidence/stage1c/corpus/catalog.v1.json": "0f1df0a1de96f5aebfa8e917b5f7e2bc1ac457ab",
            "evidence/stage1c/corpus/snapshot.freeze.v1.json": "f50dfcfadb321bf4c695c2e58333e737b2968392",
            "evidence/stage1c/corpus/coverage-bias-report.v1.json": "65e5cae71b3d222be5a081b0cb6b5d41954de3e3",
        }
        for relative, expected_blob in expected_git_blob_ids.items():
            actual_blob = subprocess.check_output(
                ["git", "hash-object", relative], cwd=ROOT, text=True
            ).strip()
            self.assertEqual(actual_blob, expected_blob, relative)

    def test_stage1_evidence_tree_contains_no_real_artifact_bytes(self) -> None:
        tracked = subprocess.check_output(
            ["git", "ls-files", "evidence/stage1c"], cwd=ROOT, text=True
        ).splitlines()
        forbidden = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
        offenders = [path for path in tracked if Path(path).suffix.lower() in forbidden]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
