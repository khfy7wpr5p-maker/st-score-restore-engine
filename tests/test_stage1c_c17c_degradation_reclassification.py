from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_manifest import canonical_sha256, load_json_object  # noqa: E402
from tools.evaluate_stage1c_artifact_admission import evaluate_admission  # noqa: E402

EVIDENCE_DIR = ROOT / "evidence" / "stage1c" / "imslp82860-c17c-noise"
CATALOG_PATH = EVIDENCE_DIR / "catalog.v2.json"
REQUEST_PATH = EVIDENCE_DIR / "admission-request.v2.json"
PROFILE_PATH = (
    ROOT
    / "evidence"
    / "stage1c"
    / "imslp82860"
    / "managed-standard-verification.v1.json"
)
HISTORICAL_CATALOG_PATH = (
    ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v1.json"
)


class Stage1CC17CDegradationReclassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_json_object(CATALOG_PATH)
        self.request = load_json_object(REQUEST_PATH)
        self.profile = load_json_object(PROFILE_PATH)
        self.item = self.catalog["items"][0]

    def test_exact_artifact_identity_and_conservative_noise_label(self) -> None:
        self.assertEqual(
            self.item["artifact"]["sha256"],
            "b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3",
        )
        self.assertEqual(self.item["artifact"]["byteSize"], 1114479)
        self.assertEqual(
            self.item["datasetItemId"], "dataset.item.imslp82860-chopin-op69.v2"
        )
        self.assertEqual(
            self.item["sourceFamilyId"],
            "source.family.imslp82860-chopin-op69.v1",
        )
        self.assertEqual(self.item["input"]["kind"], "scanned_pdf")
        self.assertEqual(self.item["input"]["pageCount"], 8)
        self.assertEqual(self.item["input"]["notationKinds"], ["staff"])
        self.assertEqual(self.item["input"]["degradations"], ["noise"])
        self.assertEqual(self.item["split"], "held_out")
        granted = sorted(
            purpose
            for purpose, permission in self.item["permissions"].items()
            if permission["status"] == "granted"
        )
        self.assertEqual(granted, ["held_out_evaluation"])
        self.assertFalse(self.item["assertions"]["originalBytesInGit"])
        self.assertFalse(
            self.item["assertions"]["stage1TrainingExecutionAuthorized"]
        )

    def test_metadata_v2_canonical_digest_is_bound(self) -> None:
        self.assertEqual(
            canonical_sha256(self.item),
            "6a75bd7d8348c6ba6e47a4bdbc16a1fc9a3f3ec23fb79a36ad7c123608d3ff36",
        )
        self.assertEqual(
            self.request["expectedItemSha256"], canonical_sha256(self.item)
        )

    def test_metadata_v2_admission_is_eligible(self) -> None:
        result = evaluate_admission(
            self.request,
            catalog=self.catalog,
            profile_record=self.profile,
        )
        self.assertEqual(result, {"decision": "eligible", "reasonCodes": []})

    def test_historical_c16_catalog_remains_unchanged(self) -> None:
        historical = load_json_object(HISTORICAL_CATALOG_PATH)
        held_out = next(
            item
            for item in historical["items"]
            if item["datasetItemId"] == "dataset.item.imslp82860-chopin-op69.v1"
        )
        self.assertEqual(held_out["input"]["degradations"], ["none"])
        self.assertEqual(
            held_out["artifact"]["sha256"], self.item["artifact"]["sha256"]
        )

    def test_tampered_degradation_metadata_invalidates_c11_digest(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        catalog["items"][0]["input"]["degradations"] = ["none"]
        result = evaluate_admission(
            self.request,
            catalog=catalog,
            profile_record=self.profile,
        )
        self.assertEqual(result["decision"], "blocked")
        self.assertIn("item_sha256_mismatch", result["reasonCodes"])

    def test_repository_evidence_directory_contains_no_artifact_bytes(self) -> None:
        forbidden = {".png", ".jpg", ".jpeg", ".pdf", ".tif", ".tiff"}
        found = [
            path.name
            for path in EVIDENCE_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in forbidden
        ]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
