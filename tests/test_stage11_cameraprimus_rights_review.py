from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from st_score_restore.stage11_cameraprimus_rights_review import (
    Stage11CameraPrIMuSRightsReviewError,
    validate_stage11_cameraprimus_rights_review,
)


ROOT = Path(__file__).resolve().parents[1]
RIGHTS_PATH = ROOT / "evidence/stage11/training/cameraprimus-rights-review.v1.json"


class CameraPrIMuSRightsReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(RIGHTS_PATH.read_text(encoding="utf-8"))

    def test_current_rights_review_is_valid(self) -> None:
        result = validate_stage11_cameraprimus_rights_review(copy.deepcopy(self.payload))
        self.assertTrue(result["reviewComplete"])
        self.assertFalse(result["commercialTrainingAdmissionAllowed"])

    def test_commercial_admission_cannot_be_silently_enabled(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["commercialTrainingAdmissionAllowed"] = True
        with self.assertRaises(Stage11CameraPrIMuSRightsReviewError):
            validate_stage11_cameraprimus_rights_review(payload)

    def test_paper_license_cannot_be_recast_as_dataset_license(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["reasoning"]["paperLicenseDoesNotAutomaticallyLicenseDatasetPackage"] = False
        with self.assertRaises(Stage11CameraPrIMuSRightsReviewError):
            validate_stage11_cameraprimus_rights_review(payload)

    def test_public_label_cannot_authorize_commercial_training(self) -> None:
        payload = copy.deepcopy(self.payload)
        item = next(e for e in payload["evidence"] if e["source"] == "towards_universal_omr_ismir_2024")
        item["sufficientForCommercialTrainingAdmission"] = True
        with self.assertRaises(Stage11CameraPrIMuSRightsReviewError):
            validate_stage11_cameraprimus_rights_review(payload)


if __name__ == "__main__":
    unittest.main()
