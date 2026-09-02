from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage4_execution_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    Stage4ExecutionAuthorizationError,
    execution_authorized_for,
    summarize_stage4_execution_authorization,
    validate_stage4_execution_authorization,
)

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "evidence/stage4/governance/real-development-calibration-execution-authorization.v1.json"
PURPOSE = ROOT / "evidence/stage4/governance/purpose-grants.v1.json"
ACCEPTANCE = ROOT / "evidence/stage4/reference-labels/development-reference-bundle-acceptance.v1.json"
COMPLETION = ROOT / "evidence/stage4/reference-labels/development-human-label-completion.v1.json"


class Stage4ExecutionAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.auth = json.loads(AUTH.read_text(encoding="utf-8"))
        self.purpose = json.loads(PURPOSE.read_text(encoding="utf-8"))
        self.acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
        self.completion = json.loads(COMPLETION.read_text(encoding="utf-8"))

    def validate(self, value: dict) -> dict:
        return validate_stage4_execution_authorization(
            value, self.purpose, self.acceptance, self.completion
        )

    def test_exact_authorization_validates(self) -> None:
        value = self.validate(self.auth)
        self.assertTrue(value["assertions"]["realDataCalibrationExecutionAuthorized"])
        self.assertFalse(value["scope"]["heldOutIncluded"])
        summary = summarize_stage4_execution_authorization(
            self.auth, self.purpose, self.acceptance, self.completion
        )
        self.assertEqual(summary["authorizationDigest"]["value"], AUTHORIZATION_CANONICAL_SHA256)
        self.assertEqual(summary["datasetItemCount"], 2)
        self.assertEqual(summary["referenceRecordCount"], 42)
        self.assertFalse(summary["stage4ExitPass"])
        self.assertFalse(summary["stage5EntryAuthorized"])

    def test_exact_beethoven_and_barley_are_authorized(self) -> None:
        self.assertTrue(execution_authorized_for(
            self.auth, self.purpose, self.acceptance, self.completion,
            dataset_item_id="dataset.item.imslp799143-beethoven-op48-no3.v1",
            artifact_sha256="c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c",
            source_family_id="source.family.imslp799143-beethoven-op48-no3.v1",
            execution_date="2026-09-03",
        ))
        self.assertTrue(execution_authorized_for(
            self.auth, self.purpose, self.acceptance, self.completion,
            dataset_item_id="dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1",
            artifact_sha256="6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e",
            source_family_id="source.family.barley-mnoah-your-face-your-tongue-your-wit.v1",
            execution_date="2026-09-03",
        ))

    def test_wrong_identity_or_environment_is_not_authorized(self) -> None:
        self.assertFalse(execution_authorized_for(
            self.auth, self.purpose, self.acceptance, self.completion,
            dataset_item_id="dataset.item.imslp799143-beethoven-op48-no3.v1",
            artifact_sha256="0" * 64,
            source_family_id="source.family.imslp799143-beethoven-op48-no3.v1",
            execution_date="2026-09-03",
        ))
        self.assertFalse(execution_authorized_for(
            self.auth, self.purpose, self.acceptance, self.completion,
            dataset_item_id="dataset.item.imslp799143-beethoven-op48-no3.v1",
            artifact_sha256="c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c",
            source_family_id="source.family.imslp799143-beethoven-op48-no3.v1",
            execution_date="2026-09-03",
            environment="github_actions",
        ))

    def test_held_out_cannot_be_smuggled_into_scope(self) -> None:
        value = deepcopy(self.auth)
        value["scope"]["heldOutIncluded"] = True
        with self.assertRaises(Stage4ExecutionAuthorizationError):
            self.validate(value)

    def test_held_out_evaluation_or_tuning_cannot_be_authorized(self) -> None:
        for key in ("heldOutEvaluationAuthorized", "heldOutTuningAuthorized"):
            value = deepcopy(self.auth)
            value["scope"][key] = True
            with self.assertRaises(Stage4ExecutionAuthorizationError):
                self.validate(value)

    def test_production_changes_training_publication_and_exit_cannot_be_authorized(self) -> None:
        for key in (
            "productionThresholdChangeAuthorized",
            "productionResourceLimitChangeAuthorized",
            "modelTrainingAuthorized",
            "publicationAuthorized",
            "stage4ExitPass",
            "stage5EntryAuthorized",
        ):
            value = deepcopy(self.auth)
            value["assertions"][key] = True
            with self.assertRaises(Stage4ExecutionAuthorizationError):
                self.validate(value)

    def test_raw_metrics_cannot_be_allowed_in_ordinary_git(self) -> None:
        value = deepcopy(self.auth)
        value["scope"]["rawObservationMetricsAllowedInOrdinaryGit"] = True
        with self.assertRaises(Stage4ExecutionAuthorizationError):
            self.validate(value)

    def test_reference_acceptance_binding_is_required(self) -> None:
        value = deepcopy(self.auth)
        value["referenceBundleAcceptanceDigest"]["value"] = "0" * 64
        with self.assertRaises(Stage4ExecutionAuthorizationError):
            self.validate(value)


if __name__ == "__main__":
    unittest.main()
