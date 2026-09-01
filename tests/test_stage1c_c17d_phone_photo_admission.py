from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_contract_constants import DatasetManifestError  # noqa: E402
from st_score_restore.dataset_manifest import canonical_sha256, load_json_object  # noqa: E402
from tools.evaluate_stage1c_artifact_admission import evaluate_admission  # noqa: E402

EVIDENCE_DIR = ROOT / "evidence" / "stage1c" / "nearer-my-god-to-thee-c17d"
CATALOG_PATH = EVIDENCE_DIR / "catalog.v1.json"
REQUEST_PATH = EVIDENCE_DIR / "admission-request.v1.json"
PROFILE_PATH = EVIDENCE_DIR / "managed-restricted-verification.v1.json"
HISTORICAL_C16_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "coverage-bias-report.v1.json"


class Stage1CC17DPhonePhotoAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_json_object(CATALOG_PATH)
        self.request = load_json_object(REQUEST_PATH)
        self.profile = load_json_object(PROFILE_PATH)
        self.item = self.catalog["items"][0]

    def test_exact_phone_photo_derivative_metadata_is_bound(self) -> None:
        self.assertEqual(
            self.item["artifact"]["sha256"],
            "abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5",
        )
        self.assertEqual(self.item["artifact"]["byteSize"], 647003)
        self.assertEqual(self.item["input"]["kind"], "phone_photo")
        self.assertEqual(self.item["input"]["mediaType"], "image/jpeg")
        self.assertEqual(self.item["input"]["notationKinds"], ["staff"])
        self.assertEqual(self.item["input"]["pageCount"], 1)
        self.assertEqual(self.item["input"]["degradations"], ["none"])
        self.assertEqual(self.item["eligibilityClass"], "restricted_corpus")
        self.assertEqual(self.item["retention"]["storageClass"], "managed_restricted")
        self.assertEqual(self.item["split"], "held_out")
        self.assertEqual(self.item["privacy"]["classification"], "deidentified")
        self.assertEqual(self.item["privacy"]["deidentificationMethodCode"], "metadata_scrub")
        self.assertEqual(
            self.item["privacy"]["deidentifiedArtifactSha256"],
            self.item["artifact"]["sha256"],
        )
        granted = sorted(
            purpose
            for purpose, permission in self.item["permissions"].items()
            if permission["status"] == "granted"
        )
        self.assertEqual(granted, ["held_out_evaluation"])
        self.assertFalse(self.item["assertions"]["originalBytesInGit"])
        self.assertFalse(self.item["assertions"]["stage1TrainingExecutionAuthorized"])

    def test_canonical_item_and_profile_digests_are_bound(self) -> None:
        self.assertEqual(
            canonical_sha256(self.item),
            "6df8229e1a23160a21845c73ea195943287b03af77245132dfe2b53078d952bf",
        )
        self.assertEqual(self.request["expectedItemSha256"], canonical_sha256(self.item))
        self.assertEqual(
            canonical_sha256(self.profile),
            "24003f0776816f8282bb6967fc1946fba5f15bb86cca6000f96819d22eb32f4a",
        )
        self.assertEqual(
            self.request["profileVerificationSha256"], canonical_sha256(self.profile)
        )

    def test_c17d_admission_is_eligible(self) -> None:
        result = evaluate_admission(
            self.request,
            catalog=self.catalog,
            profile_record=self.profile,
        )
        self.assertEqual(result, {"decision": "eligible", "reasonCodes": []})

    def test_restricted_profile_or_privacy_tampering_fails_closed(self) -> None:
        catalog = copy.deepcopy(self.catalog)
        catalog["items"][0]["eligibilityClass"] = "open_corpus"
        with self.assertRaises(DatasetManifestError):
            evaluate_admission(
                self.request,
                catalog=catalog,
                profile_record=self.profile,
            )

        catalog = copy.deepcopy(self.catalog)
        catalog["items"][0]["privacy"]["classification"] = "none"
        catalog["items"][0]["privacy"]["reviewStatus"] = "not_required"
        catalog["items"][0]["privacy"]["reviewedBy"] = None
        catalog["items"][0]["privacy"]["reviewedOn"] = None
        catalog["items"][0]["privacy"]["evidenceReference"] = None
        catalog["items"][0]["privacy"]["deidentificationMethodCode"] = None
        catalog["items"][0]["privacy"]["deidentifiedArtifactSha256"] = None
        result = evaluate_admission(
            self.request,
            catalog=catalog,
            profile_record=self.profile,
        )
        self.assertEqual(result["decision"], "blocked")
        self.assertIn("item_sha256_mismatch", result["reasonCodes"])

    def test_historical_c16_remains_immutable_and_insufficient(self) -> None:
        historical = load_json_object(HISTORICAL_C16_PATH)
        self.assertEqual(
            historical["snapshotSha256"],
            "b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476",
        )
        self.assertEqual(historical["sufficiency"]["state"], "insufficient")
        self.assertIn("coverage.missing-phone-photo", historical["gapCodes"])
        self.assertFalse(historical["sufficiency"]["stage1ExitSupported"])
        self.assertFalse(historical["sufficiency"]["stage2EntrySupported"])

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
