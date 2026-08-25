from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_manifest import load_json_object  # noqa: E402
from tools.evaluate_stage1c_artifact_admission import evaluate_admission  # noqa: E402

EVIDENCE_DIR = (
    ROOT / "evidence" / "stage1c" / "wikimedia-guitar-technical-exercise-no1"
)
CATALOG_PATH = EVIDENCE_DIR / "catalog.v1.json"
REQUEST_PATH = EVIDENCE_DIR / "admission-request.v1.json"
PROFILE_PATH = (
    ROOT
    / "evidence"
    / "stage1c"
    / "imslp799143"
    / "managed-standard-verification.v1.json"
)
HIGH_ASSURANCE_COMPAT_PATH = (
    ROOT / "examples" / "stage1c-high-assurance-compatibility.v1.json"
)


class Stage1CC17GuitarTabAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_json_object(CATALOG_PATH)
        self.request = load_json_object(REQUEST_PATH)
        self.profile = load_json_object(PROFILE_PATH)
        self.item = self.catalog["items"][0]

    def test_exact_candidate_metadata_is_bound(self) -> None:
        self.assertEqual(
            self.item["artifact"]["sha256"],
            "36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb",
        )
        self.assertEqual(self.item["artifact"]["byteSize"], 34636)
        self.assertEqual(self.item["input"]["kind"], "png")
        self.assertEqual(self.item["input"]["mediaType"], "image/png")
        self.assertEqual(
            set(self.item["input"]["notationKinds"]),
            {"guitar_tab", "combined_staff_tab"},
        )
        self.assertEqual(self.item["split"], "development")
        granted = sorted(
            purpose
            for purpose, permission in self.item["permissions"].items()
            if permission["status"] == "granted"
        )
        self.assertEqual(granted, ["quality_evaluation"])
        self.assertFalse(self.item["assertions"]["originalBytesInGit"])
        self.assertFalse(
            self.item["assertions"]["stage1TrainingExecutionAuthorized"]
        )

    def test_committed_admission_is_eligible(self) -> None:
        result = evaluate_admission(
            self.request,
            catalog=self.catalog,
            profile_record=self.profile,
        )
        self.assertEqual(result, {"decision": "eligible", "reasonCodes": []})

    def test_tampered_item_digest_is_blocked(self) -> None:
        request = copy.deepcopy(self.request)
        request["expectedItemSha256"] = "f" * 64
        result = evaluate_admission(
            request,
            catalog=self.catalog,
            profile_record=self.profile,
        )
        self.assertEqual(result["decision"], "blocked")
        self.assertIn("item_sha256_mismatch", result["reasonCodes"])

    def test_storage_profile_mismatch_is_blocked(self) -> None:
        request = copy.deepcopy(self.request)
        request["expectedStorageProfile"] = "high_assurance_vault"
        result = evaluate_admission(
            request,
            catalog=self.catalog,
            profile_record=self.profile,
        )
        self.assertEqual(result["decision"], "blocked")
        self.assertIn("storage_profile_mismatch", result["reasonCodes"])

    def test_real_phone_photo_remains_blocked_without_real_vault_verification(self) -> None:
        compatibility = load_json_object(HIGH_ASSURANCE_COMPAT_PATH)
        self.assertEqual(compatibility["eligibilityClass"], "sensitive_custody")
        self.assertEqual(compatibility["storageProfile"], "high_assurance_vault")
        self.assertFalse(compatibility["claims"]["realVaultVerified"])
        self.assertFalse(
            compatibility["claims"]["artifactOnboardingAuthorized"]
        )

    def test_repository_evidence_directory_contains_no_artifact_bytes(self) -> None:
        forbidden = {".png", ".jpg", ".jpeg", ".pdf"}
        found = [
            path.name
            for path in EVIDENCE_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in forbidden
        ]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
