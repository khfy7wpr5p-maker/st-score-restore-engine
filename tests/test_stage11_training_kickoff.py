from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from st_score_restore.stage11_training_authorization import Stage11TrainingAuthorizationError, validate_stage11_training_authorization
from st_score_restore.stage11_training_dataset import Stage11TrainingDatasetError, build_experiment_plan, build_training_manifest, run_training_kickoff_drills
from st_score_restore.stage11_training_kickoff_current_truth import Stage11TrainingKickoffTruthError, validate_stage11_training_kickoff_current_truth

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage11TrainingKickoffTests(unittest.TestCase):
    def test_authorization_valid_and_private_data_closed(self):
        result = validate_stage11_training_authorization(
            load("evidence/stage11/training/stage11-training-dataset-authorization.v1.json"),
            load("docs/live/ST_SCORE_RESTORE_STAGE11_FOUNDATION_CURRENT_TRUTH.json"),
        )
        self.assertTrue(result["trainingAuthorized"])
        self.assertFalse(result["privateDataAuthorized"])
        self.assertFalse(result["stage12Authorized"])

    def test_authorization_rejects_private_or_production_expansion(self):
        auth = load("evidence/stage11/training/stage11-training-dataset-authorization.v1.json")
        foundation = load("docs/live/ST_SCORE_RESTORE_STAGE11_FOUNDATION_CURRENT_TRUTH.json")
        for key in ("privateDocumentTrainingUseAuthorized", "productionInferenceAuthorized", "stage12EntryAuthorized"):
            mutated = deepcopy(auth)
            mutated["scope"][key] = True
            with self.assertRaises(Stage11TrainingAuthorizationError):
                validate_stage11_training_authorization(mutated, foundation)

    def test_manifest_blocks_held_out_and_private_without_consent(self):
        base = {
            "datasetItemId": "x", "sourceFamilyId": "f", "artifactSha256": "sha256:x",
            "split": "train", "rightsStatus": "approved", "privacyClass": "none",
            "trainingPermissionStatus": "granted", "artifactAccessState": "accessible",
        }
        held = dict(base, split="held_out")
        with self.assertRaises(Stage11TrainingDatasetError):
            build_training_manifest([held])
        private = dict(base, privacyClass="private")
        with self.assertRaises(Stage11TrainingDatasetError):
            build_training_manifest([private])

    def test_manifest_not_executable_without_accessible_bytes(self):
        item = {
            "datasetItemId": "x", "sourceFamilyId": "f", "artifactSha256": "sha256:x",
            "split": "train", "rightsStatus": "approved", "privacyClass": "none",
            "trainingPermissionStatus": "granted", "artifactAccessState": "custody_only_not_mounted",
        }
        manifest = build_training_manifest([item])
        self.assertFalse(manifest["trainingExecutable"])
        plan = build_experiment_plan(training_manifest=manifest)
        self.assertEqual(plan["baselineArchitecture"], "residual_unet")
        self.assertEqual(plan["challengerArchitecture"], "hybrid_cnn_transformer")
        self.assertFalse(plan["weightsEstablished"])

    def test_truth_valid_and_cannot_claim_training_started(self):
        truth = load("docs/live/ST_SCORE_RESTORE_STAGE11_TRAINING_KICKOFF_CURRENT_TRUTH.json")
        result = validate_stage11_training_kickoff_current_truth(truth)
        self.assertTrue(result["trainingAuthorized"])
        self.assertFalse(result["trainingStarted"])
        mutated = deepcopy(truth)
        mutated["stage11"]["training_started"] = True
        with self.assertRaises(Stage11TrainingKickoffTruthError):
            validate_stage11_training_kickoff_current_truth(mutated)

    def test_synthetic_kickoff_drills(self):
        result = run_training_kickoff_drills()
        self.assertTrue(result["admissionPass"])
        self.assertTrue(result["trainingAuthorized"])
        self.assertFalse(result["trainingExecutable"])
        self.assertFalse(result["weightsEstablished"])


if __name__ == "__main__":
    unittest.main()
