from __future__ import annotations

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import unittest

from st_score_restore.stage4_purpose_grants import (
    APPROVED_GRANT_CANONICAL_SHA256,
    Stage4PurposeGrantError,
    purpose_permission_granted_for,
    validate_stage4_purpose_grants,
)

ROOT = Path(__file__).resolve().parents[1]
GRANTS = ROOT / "evidence" / "stage4" / "governance" / "purpose-grants.v1.json"


class Stage4PurposeGrantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = json.loads(GRANTS.read_text(encoding="utf-8"))

    def test_approved_overlay_validates(self) -> None:
        value = validate_stage4_purpose_grants(self.raw)
        self.assertEqual(value["grantSetId"], "stage4.purpose-grants.beethoven-barley-safety-calibration.v1")
        self.assertEqual(APPROVED_GRANT_CANONICAL_SHA256, "4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc")

    def test_exact_development_artifacts_are_granted(self) -> None:
        for item_id, sha256 in (
            ("dataset.item.imslp799143-beethoven-op48-no3.v1", "c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c"),
            ("dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1", "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e"),
        ):
            self.assertTrue(
                purpose_permission_granted_for(
                    self.raw,
                    dataset_item_id=item_id,
                    artifact_sha256=sha256,
                    execution_date=date(2026, 9, 2),
                )
            )

    def test_wrong_digest_or_environment_fails_closed(self) -> None:
        self.assertFalse(
            purpose_permission_granted_for(
                self.raw,
                dataset_item_id="dataset.item.imslp799143-beethoven-op48-no3.v1",
                artifact_sha256="0" * 64,
                execution_date="2026-09-02",
            )
        )
        self.assertFalse(
            purpose_permission_granted_for(
                self.raw,
                dataset_item_id="dataset.item.imslp799143-beethoven-op48-no3.v1",
                artifact_sha256="c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c",
                execution_date="2026-09-02",
                environment="production_online",
            )
        )

    def test_cannot_expand_to_held_out_or_training(self) -> None:
        mutated = deepcopy(self.raw)
        mutated["grants"][0]["datasetItemId"] = "dataset.item.imslp82860-chopin-op69.v2"
        with self.assertRaises(Stage4PurposeGrantError):
            validate_stage4_purpose_grants(mutated)

        mutated = deepcopy(self.raw)
        mutated["grants"][0]["purpose"] = "model_training"
        with self.assertRaises(Stage4PurposeGrantError):
            validate_stage4_purpose_grants(mutated)

    def test_chopin_remains_held_out_only(self) -> None:
        held_out = validate_stage4_purpose_grants(self.raw)["heldOutBinding"]
        self.assertEqual(held_out["purpose"], "held_out_evaluation")
        self.assertFalse(held_out["candidateDerivationAuthorized"])


if __name__ == "__main__":
    unittest.main()
