import json
import unittest
from pathlib import Path

from st_score_restore.stage11_deepscores_dense import (
    Stage11DeepScoresDenseError,
    degradation_recipe,
    source_family_id,
    split_source_families,
    validate_registration,
    validate_tar_member_name,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = ROOT / "evidence" / "stage11" / "training" / "deepscoresv2-dense-drive-source-registration.v1.json"


class Stage11DeepScoresDenseTests(unittest.TestCase):
    def test_registration_is_rights_approved_but_checksum_pending(self):
        payload = json.loads(REGISTRATION.read_text(encoding="utf-8"))
        result = validate_registration(payload)
        self.assertTrue(result["rightsApproved"])
        self.assertTrue(result["commercialTrainingAllowed"])
        self.assertTrue(result["driveArchivePresent"])
        self.assertFalse(result["checksumVerified"])

    def test_registration_rejects_noncommercial_or_wrong_license(self):
        payload = json.loads(REGISTRATION.read_text(encoding="utf-8"))
        payload["rightsReview"]["licenseId"] = "CC-BY-NC-4.0"
        with self.assertRaises(Stage11DeepScoresDenseError):
            validate_registration(payload)

    def test_tar_member_validation_rejects_traversal_and_absolute_paths(self):
        self.assertEqual(validate_tar_member_name("ds2_dense/images/a.png"), "ds2_dense/images/a.png")
        for candidate in ("../escape", "/absolute/path", "a/../../escape"):
            with self.subTest(candidate=candidate):
                with self.assertRaises(Stage11DeepScoresDenseError):
                    validate_tar_member_name(candidate)

    def test_source_family_groups_font_and_page_variants(self):
        self.assertEqual(
            source_family_id("lg-214197992-aug-gonville--page-1025.png"),
            "lg-214197992",
        )
        self.assertEqual(
            source_family_id("lg-214197992-aug-gutenberg1939--page-1089.png"),
            "lg-214197992",
        )

    def test_official_test_family_is_never_admitted_to_train_or_dev(self):
        official_train = [f"lg-{i}-aug-gonville--page-1.png" for i in range(1, 21)]
        official_train.append("lg-1-aug-lilyjazz--page-2.png")
        official_test = ["lg-1-aug-emmentaler--page-3.png", "lg-100-aug-beethoven--page-1.png"]
        split = split_source_families(official_train, official_test, development_percent=20)
        admitted = split["train"] + split["development"]
        self.assertFalse(any(source_family_id(name) == "lg-1" for name in admitted))
        self.assertEqual(len(split["leakageExcludedFromOfficialTrain"]), 2)
        self.assertTrue(split["sourceFamilyLeakagePrevented"])

    def test_degradation_recipe_is_deterministic_and_bounded(self):
        first = degradation_recipe("lg-1-aug-beethoven--page-1.png", 3)
        second = degradation_recipe("lg-1-aug-beethoven--page-1.png", 3)
        self.assertEqual(first, second)
        self.assertGreaterEqual(first["jpegQuality"], 52)
        self.assertLessEqual(first["jpegQuality"], 95)
        self.assertTrue(first["thinSymbolPreservationRequired"])


if __name__ == "__main__":
    unittest.main()
