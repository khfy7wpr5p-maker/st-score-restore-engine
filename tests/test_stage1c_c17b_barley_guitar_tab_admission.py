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

EVIDENCE_DIR = ROOT / "evidence" / "stage1c" / "imslp911664-c17b-guitar-tab"
CATALOG_PATH = EVIDENCE_DIR / "catalog.v1.json"
REQUEST_PATH = EVIDENCE_DIR / "admission-request.v1.json"
PROFILE_PATH = ROOT / "evidence" / "stage1c" / "imslp799143" / "managed-standard-verification.v1.json"


class Stage1CC17BBarleyGuitarTabAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_json_object(CATALOG_PATH)
        self.request = load_json_object(REQUEST_PATH)
        self.profile = load_json_object(PROFILE_PATH)
        self.item = self.catalog["items"][0]

    def test_exact_artifact_and_taxonomy_are_bound(self) -> None:
        self.assertEqual(self.item["artifact"]["sha256"], "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e")
        self.assertEqual(self.item["artifact"]["byteSize"], 84689)
        self.assertEqual(self.item["input"]["kind"], "digital_pdf")
        self.assertEqual(self.item["input"]["mediaType"], "application/pdf")
        self.assertEqual(self.item["input"]["notationKinds"], ["guitar_tab"])
        self.assertEqual(self.item["input"]["pageCount"], 2)
        self.assertEqual(self.item["split"], "development")
        self.assertEqual(self.request["expectedItemSha256"], canonical_sha256(self.item))
        self.assertEqual(canonical_sha256(self.item), "6fc7fec810847acb06c54b8a036557e9f3fd402b673a57a0b1ce8b729a5b6310")

    def test_committed_admission_is_eligible(self) -> None:
        result = evaluate_admission(self.request, catalog=self.catalog, profile_record=self.profile)
        self.assertEqual(result, {"decision": "eligible", "reasonCodes": []})

    def test_tampered_digest_is_blocked(self) -> None:
        request = copy.deepcopy(self.request)
        request["expectedItemSha256"] = "f" * 64
        result = evaluate_admission(request, catalog=self.catalog, profile_record=self.profile)
        self.assertEqual(result["decision"], "blocked")
        self.assertIn("item_sha256_mismatch", result["reasonCodes"])

    def test_only_quality_evaluation_is_granted(self) -> None:
        granted = sorted(p for p, permission in self.item["permissions"].items() if permission["status"] == "granted")
        self.assertEqual(granted, ["quality_evaluation"])
        self.assertFalse(self.item["assertions"]["originalBytesInGit"])
        self.assertFalse(self.item["assertions"]["stage1TrainingExecutionAuthorized"])

    def test_repository_evidence_directory_contains_no_artifact_bytes(self) -> None:
        forbidden = {".png", ".jpg", ".jpeg", ".pdf"}
        found = [p.name for p in EVIDENCE_DIR.iterdir() if p.is_file() and p.suffix.lower() in forbidden]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
