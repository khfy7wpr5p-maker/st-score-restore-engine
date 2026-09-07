from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from st_score_restore.stage11_entry_authorization import (
    Stage11AuthorizationError,
    validate_stage11_entry_authorization,
)
from st_score_restore.stage11_foundation_current_truth import (
    Stage11CurrentTruthError,
    validate_stage11_foundation_current_truth,
)
from st_score_restore.st_restore_image_model import (
    ImageModelContractError,
    build_selector_capability_descriptor,
    build_training_readiness_manifest,
    run_synthetic_image_model_drills,
    run_synthetic_research_candidate,
    validate_release_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage11FoundationTests(unittest.TestCase):
    def test_entry_authorization_valid(self):
        auth = load("evidence/stage11/stage11-entry-authorization.v1.json")
        stage10 = load("docs/live/ST_SCORE_RESTORE_STAGE10_FINAL_EXIT_CURRENT_TRUTH.json")
        result = validate_stage11_entry_authorization(auth, stage10)
        self.assertTrue(result["valid"])
        self.assertFalse(result["trainingAuthorized"])

    def test_entry_authorization_rejects_training_scope_expansion(self):
        auth = load("evidence/stage11/stage11-entry-authorization.v1.json")
        stage10 = load("docs/live/ST_SCORE_RESTORE_STAGE10_FINAL_EXIT_CURRENT_TRUTH.json")
        mutated = deepcopy(auth)
        mutated["scope"]["modelTrainingAuthorized"] = True
        with self.assertRaises(Stage11AuthorizationError):
            validate_stage11_entry_authorization(mutated, stage10)

    def test_training_readiness_is_non_executing(self):
        result = build_training_readiness_manifest(
            objectives=("denoising", "dewarping", "structure_preservation")
        )
        self.assertEqual(result["architectureFamily"], "UNSELECTED")
        self.assertFalse(result["modelTrainingAuthorized"])
        self.assertFalse(result["trainingExecuted"])
        self.assertFalse(result["modelWeightsEstablished"])

    def test_training_readiness_rejects_dataset_or_training_authorization(self):
        with self.assertRaises(ImageModelContractError):
            build_training_readiness_manifest(
                objectives=("denoising",), dataset_collection_authorized=True
            )
        with self.assertRaises(ImageModelContractError):
            build_training_readiness_manifest(
                objectives=("denoising",), model_training_authorized=True
            )
        with self.assertRaises(ImageModelContractError):
            build_training_readiness_manifest(
                objectives=("denoising",), dataset_manifest_digest="sha256:real-data"
            )

    def test_selector_descriptor_keeps_untrained_model_skipped(self):
        descriptor = build_selector_capability_descriptor()
        self.assertEqual(descriptor["approvalState"], "unapproved")
        self.assertEqual(descriptor["availabilityState"], "unavailable")
        self.assertFalse(descriptor["enabled"])

    def test_synthetic_candidate_has_provenance_and_safety_handoff(self):
        source = {"artifactId": "source-1", "contentDigest": "sha256:source"}

        def executor(received):
            self.assertEqual(received["artifactId"], "source-1")
            return {
                "artifactId": "candidate-1",
                "contentDigest": "sha256:candidate",
                "configDigest": "sha256:config",
            }

        result = run_synthetic_research_candidate(
            source_descriptor=source, executor=executor
        )
        self.assertEqual(result["derivedFrom"]["artifactId"], "source-1")
        self.assertTrue(result["provenanceComplete"])
        self.assertTrue(result["syntheticOnly"])
        self.assertFalse(result["modelWeightsUsed"])
        self.assertTrue(result["safetyHandoff"]["requiresStage9aPreservationEvidence"])
        self.assertTrue(result["safetyHandoff"]["requiresStage9Comparator"])
        self.assertTrue(result["safetyHandoff"]["requiresStage10Selector"])

    def test_release_manifest_can_be_reviewed_but_not_released(self):
        manifest = {
            "modelId": "future-model",
            "modelVersion": "0.0.0-research",
            "architectureFamily": "future-unspecified",
            "weightsDigest": "sha256:placeholder",
            "trainingDataManifestDigest": "sha256:placeholder-data",
            "evaluationEvidenceDigest": "sha256:placeholder-eval",
            "calibrationEvidenceDigest": "sha256:placeholder-calibration",
            "disableRollbackPlanId": "rollback-plan-placeholder",
            "productionInferenceAuthorized": False,
            "realUserCohortAuthorized": False,
            "modelPublicationAuthorized": False,
            "automaticFinalSelectionAuthorized": False,
        }
        result = validate_release_manifest(manifest)
        self.assertTrue(result["manifestValidForFoundationReview"])
        self.assertFalse(result["releaseEligible"])
        self.assertFalse(result["productionInferenceAuthorized"])

    def test_release_manifest_rejects_production_scope(self):
        manifest = {
            "modelId": "future-model",
            "modelVersion": "1",
            "architectureFamily": "cnn",
            "weightsDigest": "sha256:w",
            "trainingDataManifestDigest": "sha256:d",
            "evaluationEvidenceDigest": "sha256:e",
            "calibrationEvidenceDigest": "sha256:c",
            "disableRollbackPlanId": "r1",
            "productionInferenceAuthorized": True,
        }
        with self.assertRaises(ImageModelContractError):
            validate_release_manifest(manifest)

    def test_foundation_current_truth_valid(self):
        truth = load("docs/live/ST_SCORE_RESTORE_STAGE11_FOUNDATION_CURRENT_TRUTH.json")
        result = validate_stage11_foundation_current_truth(truth)
        self.assertTrue(result["valid"])
        self.assertFalse(result["stage11ExitPass"])

    def test_foundation_current_truth_rejects_silent_training_or_stage12_start(self):
        truth = load("docs/live/ST_SCORE_RESTORE_STAGE11_FOUNDATION_CURRENT_TRUTH.json")
        mutated = deepcopy(truth)
        mutated["stage11"]["model_training_authorized"] = True
        with self.assertRaises(Stage11CurrentTruthError):
            validate_stage11_foundation_current_truth(mutated)

        mutated = deepcopy(truth)
        mutated["stage12"]["started"] = True
        with self.assertRaises(Stage11CurrentTruthError):
            validate_stage11_foundation_current_truth(mutated)

    def test_synthetic_drills_pass_without_model_or_production(self):
        result = run_synthetic_image_model_drills()
        self.assertTrue(result["syntheticCandidatePass"])
        self.assertTrue(result["trainingRemainsUnauthorized"])
        self.assertTrue(result["selectorWillSkipUntrainedModel"])
        self.assertFalse(result["productionInferenceAuthorized"])
        self.assertFalse(result["stage12EntryAuthorized"])


if __name__ == "__main__":
    unittest.main()
