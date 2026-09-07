"""Fail-closed validation for bounded Stage 11 training authorization."""

from __future__ import annotations

from typing import Any, Mapping

AUTH_ID = "stage11.training-dataset-authorization.v1"
DECISION = "AUTHORIZE_STAGE11_BOUNDED_DATASET_ADMISSION_AND_MODEL_TRAINING"


class Stage11TrainingAuthorizationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11TrainingAuthorizationError(message)


def validate_stage11_training_authorization(auth: Mapping[str, Any], foundation: Mapping[str, Any]) -> dict[str, Any]:
    _require(auth.get("authorizationId") == AUTH_ID, "training authorization id mismatch")
    _require(auth.get("decision") == DECISION, "training authorization decision mismatch")
    binding = auth.get("foundationBinding") or {}
    _require(binding.get("currentTruthGitBlobSha") == "844e72bf496fd727e4e00b38d8f8c8c1ed493a2d", "foundation truth binding mismatch")
    stage11 = foundation.get("stage11") or {}
    _require(stage11.get("state") == "FOUNDATION_COMPLETE_AWAITING_SEPARATE_TRAINING_AUTHORIZATION", "foundation state mismatch")
    scope = auth.get("scope") or {}
    for key in (
        "datasetAdmissionAuthorized",
        "rightsClearedPublicDatasetCollectionAuthorized",
        "syntheticDerivationAuthorized",
        "architectureExperimentSelectionAuthorized",
        "modelTrainingAuthorized",
        "modelWeightCreationAuthorized",
        "developmentEvaluationAuthorized",
    ):
        _require(scope.get(key) is True, f"required training scope missing: {key}")
    for key in (
        "userDocumentTrainingUseAuthorized",
        "studentDocumentTrainingUseAuthorized",
        "privateDocumentTrainingUseAuthorized",
        "heldOutRetuningAuthorized",
        "networkFetchAuthorized",
        "externalModelArtifactDownloadAuthorized",
        "modelPublicationAuthorized",
        "productionInferenceAuthorized",
        "realUserCohortAuthorized",
        "automaticFinalSelectionAuthorized",
        "stage12EntryAuthorized",
    ):
        _require(scope.get(key) is False, f"unauthorized scope expansion: {key}")
    candidates = auth.get("initialTrainingCandidateDatasetItems") or []
    excluded = auth.get("explicitlyExcludedFromTraining") or []
    _require(len(candidates) == 3, "expected three initial development candidates")
    _require(len(excluded) == 2, "expected two held-out exclusions")
    _require(not set(candidates).intersection(excluded), "training and held-out sets overlap")
    return {"valid": True, "trainingAuthorized": True, "privateDataAuthorized": False, "stage12Authorized": False}
