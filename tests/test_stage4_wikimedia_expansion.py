from __future__ import annotations

import json
from pathlib import Path
import unittest

from st_score_restore.dataset_contract_common import canonical_sha256
from tools import validate_stage4_wikimedia_expansion as validator

ROOT = Path(__file__).resolve().parents[1]
GRANT = ROOT / "evidence/stage4/corpus-expansion/wikimedia/purpose-grant.v1.json"
WORK_PACKAGE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"


class Stage4WikimediaExpansionTests(unittest.TestCase):
    def test_repository_expansion_contract_passes(self) -> None:
        self.assertEqual(validator.main(), 0)

    def test_grant_digest_is_frozen(self) -> None:
        grant = json.loads(GRANT.read_text(encoding="utf-8"))
        self.assertEqual(canonical_sha256(grant), validator.WIKIMEDIA_GRANT_DIGEST)

    def test_work_package_is_empty_human_review_only(self) -> None:
        package = json.loads(WORK_PACKAGE.read_text(encoding="utf-8"))
        self.assertEqual(package["state"], "awaiting_human_labels")
        self.assertEqual(package["reviewScope"]["reviewMethodRequired"], "human_expert_review")
        self.assertFalse(package["reviewScope"]["modelPredictionsAllowedAsReference"])
        reviews = package["item"]["pages"][0]["reviews"]
        self.assertEqual(len(reviews), 7)
        self.assertEqual({row["findingType"] for row in reviews}, validator.FINDINGS)
        for row in reviews:
            self.assertIsNone(row["referenceLabel"])
            self.assertIsNone(row["reviewerReference"])
            self.assertIsNone(row["provenanceReference"])
            self.assertIsNone(row["reviewedOn"])

    def test_held_out_boundary_remains_closed(self) -> None:
        package = json.loads(WORK_PACKAGE.read_text(encoding="utf-8"))
        exclusion = package["heldOutExclusions"][0]
        self.assertEqual(exclusion["datasetItemId"], validator.HELD_OUT_ID)
        self.assertFalse(exclusion["includedInDevelopmentReview"])
        self.assertFalse(exclusion["candidateDerivationAuthorized"])
        self.assertFalse(package["assertions"]["expansionCalibrationExecutionAuthorized"])
        self.assertFalse(package["assertions"]["stage5EntryAuthorized"])


if __name__ == "__main__":
    unittest.main()
