from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_manifest import load_json_object  # noqa: E402
from tools.evaluate_stage1_corpus_readiness import evaluate_corpus_readiness  # noqa: E402


class Stage1CC14RealCorpusTests(unittest.TestCase):
    def test_repository_realized_corpus_is_structurally_ready(self) -> None:
        catalog = load_json_object(
            ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v1.json"
        )
        result = evaluate_corpus_readiness(catalog, as_of=date(2026, 8, 25))
        self.assertEqual(result["state"], "ready")
        self.assertEqual(result["reasonCodes"], [])
        self.assertEqual(result["counts"], {"development": 1, "held_out": 1})
        self.assertEqual(
            result["sourceFamilyCounts"], {"development": 1, "held_out": 1}
        )

        items = {item["split"]: item for item in catalog["items"]}
        self.assertNotEqual(
            items["development"]["sourceFamilyId"],
            items["held_out"]["sourceFamilyId"],
        )
        self.assertNotEqual(
            items["development"]["artifact"]["sha256"],
            items["held_out"]["artifact"]["sha256"],
        )
        self.assertEqual(
            items["held_out"]["permissions"]["held_out_evaluation"]["status"],
            "granted",
        )
        self.assertEqual(
            items["held_out"]["permissions"]["quality_evaluation"]["status"],
            "not_requested",
        )


if __name__ == "__main__":
    unittest.main()
