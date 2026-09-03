from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.dataset_contract_common import canonical_sha256
from st_score_restore.stage4_wikimedia_expanded_execution_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    Stage4WikimediaExpandedExecutionAuthorizationError,
    expanded_execution_authorized_for,
    validate_wikimedia_expanded_execution_authorization,
)

ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION = ROOT / "evidence/stage4/governance/expanded-development-calibration-execution-authorization.v1.json"
BB_PURPOSE = ROOT / "evidence/stage4/governance/purpose-grants.v1.json"
BB_ACCEPTANCE = ROOT / "evidence/stage4/reference-labels/development-reference-bundle-acceptance.v1.json"
BB_COMPLETION = ROOT / "evidence/stage4/reference-labels/development-human-label-completion.v1.json"
WIKI_PURPOSE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/purpose-grant.v1.json"
WIKI_ACCEPTANCE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-bundle-acceptance.v1.json"
WIKI_COMPLETION = ROOT / "evidence/stage4/corpus-expansion/wikimedia/human-label-completion.v1.json"
WIKI_WORK_PACKAGE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class WikimediaExpandedExecutionAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authorization = load(AUTHORIZATION)
        self.bb_purpose = load(BB_PURPOSE)
        self.bb_acceptance = load(BB_ACCEPTANCE)
        self.bb_completion = load(BB_COMPLETION)
        self.wiki_purpose = load(WIKI_PURPOSE)
        self.wiki_acceptance = load(WIKI_ACCEPTANCE)
        self.wiki_completion = load(WIKI_COMPLETION)
        self.wiki_work_package = load(WIKI_WORK_PACKAGE)

    def validate(self, authorization: dict | None = None) -> dict:
        return validate_wikimedia_expanded_execution_authorization(
            self.authorization if authorization is None else authorization,
            self.bb_purpose,
            self.bb_acceptance,
            self.bb_completion,
            self.wiki_purpose,
            self.wiki_acceptance,
            self.wiki_completion,
            self.wiki_work_package,
        )

    def test_committed_authorization_is_exact_and_non_executing(self) -> None:
        value = self.validate()
        self.assertEqual(canonical_sha256(value), AUTHORIZATION_CANONICAL_SHA256)
        self.assertEqual(value["scope"]["datasetItemCount"], 3)
        self.assertEqual(value["scope"]["sourceFamilyCount"], 3)
        self.assertEqual(value["scope"]["referenceRecordCount"], 49)
        self.assertTrue(value["assertions"]["realDataCalibrationExecutionAuthorized"])
        self.assertFalse(value["assertions"]["realDataCalibrationExecuted"])
        self.assertFalse(value["scope"]["heldOutIncluded"])
        self.assertFalse(value["scope"]["heldOutEvaluationAuthorized"])
        self.assertFalse(value["scope"]["heldOutTuningAuthorized"])
        self.assertFalse(value["assertions"]["productionThresholdChangeAuthorized"])
        self.assertFalse(value["assertions"]["productionResourceLimitChangeAuthorized"])
        self.assertFalse(value["assertions"]["stage4ExitPass"])
        self.assertFalse(value["assertions"]["stage5EntryAuthorized"])

    def test_all_three_exact_items_are_authorized_after_authorization_date(self) -> None:
        for item in self.authorization["scope"]["datasetItems"]:
            self.assertTrue(
                expanded_execution_authorized_for(
                    self.authorization,
                    self.bb_purpose,
                    self.bb_acceptance,
                    self.bb_completion,
                    self.wiki_purpose,
                    self.wiki_acceptance,
                    self.wiki_completion,
                    self.wiki_work_package,
                    dataset_item_id=item["datasetItemId"],
                    artifact_sha256=item["artifactSha256"],
                    source_family_id=item["sourceFamilyId"],
                    execution_date="2026-09-03",
                )
            )

    def test_wrong_environment_or_artifact_is_not_authorized(self) -> None:
        wiki = self.authorization["scope"]["datasetItems"][2]
        self.assertFalse(
            expanded_execution_authorized_for(
                self.authorization,
                self.bb_purpose,
                self.bb_acceptance,
                self.bb_completion,
                self.wiki_purpose,
                self.wiki_acceptance,
                self.wiki_completion,
                self.wiki_work_package,
                dataset_item_id=wiki["datasetItemId"],
                artifact_sha256=wiki["artifactSha256"],
                source_family_id=wiki["sourceFamilyId"],
                execution_date="2026-09-03",
                environment="production",
            )
        )
        self.assertFalse(
            expanded_execution_authorized_for(
                self.authorization,
                self.bb_purpose,
                self.bb_acceptance,
                self.bb_completion,
                self.wiki_purpose,
                self.wiki_acceptance,
                self.wiki_completion,
                self.wiki_work_package,
                dataset_item_id=wiki["datasetItemId"],
                artifact_sha256="0" * 64,
                source_family_id=wiki["sourceFamilyId"],
                execution_date="2026-09-03",
            )
        )

    def test_missing_wikimedia_item_is_rejected(self) -> None:
        mutated = deepcopy(self.authorization)
        mutated["scope"]["datasetItems"] = mutated["scope"]["datasetItems"][:2]
        mutated["scope"]["datasetItemCount"] = 2
        mutated["scope"]["sourceFamilyCount"] = 2
        mutated["scope"]["referenceRecordCount"] = 42
        with self.assertRaises(Stage4WikimediaExpandedExecutionAuthorizationError):
            self.validate(mutated)

    def test_held_out_or_downstream_gate_cannot_be_opened(self) -> None:
        for mutation in (
            ("scope", "heldOutIncluded", True),
            ("scope", "heldOutEvaluationAuthorized", True),
            ("scope", "heldOutTuningAuthorized", True),
            ("assertions", "realDataCalibrationExecuted", True),
            ("assertions", "productionThresholdChangeAuthorized", True),
            ("assertions", "productionResourceLimitChangeAuthorized", True),
            ("assertions", "stage4ExitPass", True),
            ("assertions", "stage5EntryAuthorized", True),
        ):
            mutated = deepcopy(self.authorization)
            section, key, value = mutation
            mutated[section][key] = value
            with self.subTest(section=section, key=key):
                with self.assertRaises(Stage4WikimediaExpandedExecutionAuthorizationError):
                    self.validate(mutated)

    def test_wikimedia_acceptance_must_remain_immutable(self) -> None:
        mutated_acceptance = deepcopy(self.wiki_acceptance)
        mutated_acceptance["assertions"]["realDataCalibrationExecutionAuthorized"] = True
        with self.assertRaises(Exception):
            validate_wikimedia_expanded_execution_authorization(
                self.authorization,
                self.bb_purpose,
                self.bb_acceptance,
                self.bb_completion,
                self.wiki_purpose,
                mutated_acceptance,
                self.wiki_completion,
                self.wiki_work_package,
            )


if __name__ == "__main__":
    unittest.main()
