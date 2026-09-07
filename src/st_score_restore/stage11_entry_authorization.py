"""Fail-closed validation for Stage 11 entry authorization."""

from __future__ import annotations

from typing import Any, Mapping

AUTHORIZATION_ID = "stage11.entry-st-restore-image-model-foundation-authorization.v1"
DECISION = "AUTHORIZE_STAGE11_ENTRY_AND_PROVIDER_NEUTRAL_IMAGE_MODEL_FOUNDATION_ONLY"
STAGE10_STATE = "COMPLETE_PASS_PROVIDER_NEUTRAL_ST_RESTORE_SELECTOR_FOUNDATION"
STAGE10_MAIN_SHA = "d3429cc877ae000206de8102713c8259d8b50897"
STAGE10_TRUTH_BLOB_SHA = "ed19ad779408ec0acf96cba1d16d434aa53d28ec"
NEXT_SAFE_BOUNDARY = "separate_stage11_training_and_dataset_authorization"


class Stage11AuthorizationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11AuthorizationError(message)


def validate_stage11_entry_authorization(
    authorization: Mapping[str, Any],
    stage10_truth: Mapping[str, Any],
) -> dict[str, Any]:
    _require(authorization.get("authorizationId") == AUTHORIZATION_ID, "authorization id mismatch")
    _require(authorization.get("decision") == DECISION, "decision mismatch")
    _require(authorization.get("authorizationSourceCode") == "explicit_user_authorization", "explicit authorization missing")

    binding = authorization.get("stage10FinalExitBinding")
    _require(isinstance(binding, Mapping), "Stage 10 binding missing")
    _require(binding.get("stage10FinalMainSha") == STAGE10_MAIN_SHA, "Stage 10 main binding drifted")
    _require(binding.get("currentTruthGitBlobSha") == STAGE10_TRUTH_BLOB_SHA, "Stage 10 truth blob binding drifted")
    _require(binding.get("stage10State") == STAGE10_STATE, "Stage 10 state binding drifted")
    _require(binding.get("stage10ExitPass") is True, "Stage 10 exit must pass")
    _require(binding.get("stage11EntryEligible") is True, "Stage 11 entry must be eligible")

    _require(stage10_truth.get("stage10", {}).get("state") == STAGE10_STATE, "Stage 10 current truth mismatch")
    _require(stage10_truth.get("stage10", {}).get("exit_pass") is True, "Stage 10 current truth exit not pass")
    _require(stage10_truth.get("stage11", {}).get("entry_eligible") is True, "Stage 11 not eligible in current truth")

    scope = authorization.get("scope")
    _require(isinstance(scope, Mapping), "scope missing")
    for key in (
        "stage11EntryAuthorized",
        "stage11Started",
        "providerNeutralImageModelFoundationAuthorized",
        "modelInterfaceContractAuthorized",
        "trainingReadinessManifestAuthorized",
        "releaseManifestValidationAuthorized",
        "selectorCapabilityDescriptorAuthorized",
        "syntheticResearchExecutorAuthorized",
        "syntheticDrillsAuthorized",
    ):
        _require(scope.get(key) is True, f"authorized scope missing: {key}")

    for key in (
        "architectureFamilySelectionAuthorized",
        "datasetCollectionAuthorized",
        "userDocumentTrainingUseAuthorized",
        "modelTrainingAuthorized",
        "heldOutRetuningAuthorized",
        "modelWeightCreationAuthorized",
        "modelArtifactDownloadAuthorized",
        "networkFetchAuthorized",
        "modelPublicationAuthorized",
        "productionInferenceAuthorized",
        "realUserCohortAuthorized",
        "providerSpecificActivationAuthorized",
        "liveResourceCreationAuthorized",
        "productionDeploymentAuthorized",
        "automaticFinalSelectionAuthorized",
        "stage12EntryAuthorized",
    ):
        _require(scope.get(key) is False, f"unauthorized scope expansion: {key}")

    boundaries = authorization.get("safetyBoundaries")
    _require(isinstance(boundaries, Mapping), "safety boundaries missing")
    for key, value in boundaries.items():
        _require(value is True, f"safety boundary must remain true: {key}")

    _require(authorization.get("nextSafeBoundary") == NEXT_SAFE_BOUNDARY, "next safe boundary drifted")
    return {
        "valid": True,
        "state": "STAGE11_ENTRY_AUTHORIZED_FOUNDATION_ONLY",
        "trainingAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }
