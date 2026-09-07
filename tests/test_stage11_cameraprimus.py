from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from st_score_restore.stage11_cameraprimus import (
    Stage11CameraPrIMuSError,
    build_manifest,
    source_family_id,
    split_for_family,
    validate_manifest,
)


class Stage11CameraPrIMuSTests(unittest.TestCase):
    def _pair(self, root: Path, sample_id: str, *, with_target: bool = True) -> None:
        folder = root / sample_id
        folder.mkdir(parents=True)
        (folder / f"{sample_id}_distorted.jpg").write_bytes((sample_id + "-distorted").encode())
        if with_target:
            (folder / f"{sample_id}.png").write_bytes((sample_id + "-clean").encode())
        (folder / f"{sample_id}.agnostic").write_text("notehead-L3", encoding="utf-8")
        (folder / f"{sample_id}.semantic").write_text("note-C4_quarter", encoding="utf-8")
        (folder / f"{sample_id}.mei").write_text("<mei/>", encoding="utf-8")

    def test_source_family_groups_variants(self) -> None:
        self.assertEqual(source_family_id("230006252-1_1_1"), "230006252-1")
        self.assertEqual(source_family_id("230006252-1_9_2"), "230006252-1")
        self.assertEqual(split_for_family("230006252-1"), split_for_family("230006252-1"))

    def test_manifest_pairs_and_fail_closed_rights_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._pair(root, "230006252-1_1_1")
            self._pair(root, "230006610-1_3_1")
            manifest = build_manifest(root)
            self.assertEqual(manifest["pairCount"], 2)
            self.assertFalse(manifest["trainingExecutable"])
            self.assertEqual(manifest["blockingReasonCodes"], ["CAMERAPRIMUS_RIGHTS_REVIEW_NOT_APPROVED"])
            summary = validate_manifest(manifest)
            self.assertEqual(summary["pairCount"], 2)

    def test_rights_approved_manifest_is_executable_when_pairs_accessible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._pair(root, "230006252-1_1_1")
            manifest = build_manifest(root, rights_status="approved")
            self.assertTrue(manifest["trainingExecutable"])
            self.assertEqual(manifest["blockingReasonCodes"], [])

    def test_missing_target_is_rejected_not_silently_admitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._pair(root, "230006252-1_1_1")
            self._pair(root, "230006610-1_3_1", with_target=False)
            manifest = build_manifest(root)
            self.assertEqual(manifest["pairCount"], 1)
            self.assertEqual(manifest["rejectedCount"], 1)
            self.assertEqual(manifest["rejected"][0]["reason"], "missing_source_or_target")

    def test_manifest_detects_source_family_split_leakage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._pair(root, "230006252-1_1_1")
            manifest = build_manifest(root)
            clone = dict(manifest)
            clone["pairs"] = [dict(manifest["pairs"][0]), dict(manifest["pairs"][0])]
            clone["pairs"][1]["pairId"] = "230006252-1_other"
            clone["pairs"][1]["split"] = "held_out" if clone["pairs"][0]["split"] != "held_out" else "train"
            clone["splitCounts"] = {
                split: sum(pair["split"] == split for pair in clone["pairs"])
                for split in ("development", "held_out", "train")
            }
            with self.assertRaises(Stage11CameraPrIMuSError):
                validate_manifest(clone)


if __name__ == "__main__":
    unittest.main()
