"""Fail-closed Stage 10 entry authorization validation."""

from __future__ import annotations

from typing import Any, Mapping

AUTHORIZATION_ID = "stage10.entry-st-restore-selector-foundation-authorization.v1"
DECISION = "AUTHORIZE_STAGE10_ENTRY_AND_PROVIDER_NEUTRAL_ST_RESTORE_SELECTOR_FOUNDATION"
STAGE9A_TRUTH_PATH = "docs/live/ST_SCORE_RESTORE_STAGE9A_FINAL_EXIT_CURRENT_TRUTH.json"
STAGE9A_TRUTH_BLOB_SHA = "d17b54ae17649d3acc8b702e59c7541ba54b0538"
STAGE9A_FINAL_MAIN_SHA = "8394afefc1b7edf2ba210f7e417bb4a3e1391f35"
STAGE9A_STATE = "COMPLETE_PASS_PROVIDER_NEUTRAL_MSPM_EVIDENCE_AND_SAFE_ROUTING_FOUNDATION"


class Stage10EntryAuthorizationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage10EntryAuthorizationError(message)


def validate_stage10_entry_authorization(
    authorization: Mapping[str, Any],
    stage9a_truth: Mapping[str, Any],
) -> dict[str, Any]:
    _require(isinstance(authorization, Mapping), "authorization must be an object")
    _require(isinstance(stage9a_truth, Mapping), "Stage 9A current truth must be an object")
    _require(authorization.get("authorizationId") == AUTHORIZATION_ID, "unexpected authorization id")
    _require(authorization.get("decision") == DECISION, "unexpected Stage 10 authorization decision")
    _require(authorization.get("authorizationSourceCode") == "explicit_user_authorization", "explicit authorization missing")

    binding = authorization.get("stage9aFinalExitBinding")
    _require(isinstance(binding, Mapping), "Stage 9A binding missing")
    expected = {
        "currentTruthPath": STAGE9A_TRUTH_PATH,
        "currentTruthGitBlobSha": STAGE9A_TRUTH_BLOB_SHA,
        "stage9aFinalMainSha": STAGE9A_FINAL_MAIN_SHA,
        "stage9aState": STAGE9A_STATE,
        "stage9aExitPass": True,
        "stage10EntryEligible": True,
    }
    for key, value in expected.items():
        _require(binding.get(key) == value, f"Stage 9A binding mismatch: {key}")

    stage9a = stage9a_truth.get("stage9a")
    stage10 = stage9a_truth.get("stage10")
    _require(isinstance(stage9a, Mapping) and isinstance(stage10, Mapping), "Stage 9A/10 current truth missing")
    _require(stage9a.get("state") == STAGE9A_STATE, "Stage 9A state mismatch")
    _require(stage9a.get("exit_pass") is True, "Stage 9A exit must pass")
    _require(stage10.get("entry_eligible") is True, "Stage 10 must be entry eligible")
    _require(stage10.get("entry_authorized") is False, "baseline truth must predate Stage 10 authorization")
    _require(stage10.get("started") is False, "baseline truth must predate Stage 10 start")

    scope = authorization.get("scope")
    _require(isinstance(scope, Mapping), "Stage 10 scope missing")
    for field in (
        "stage10EntryAuthorized",
        "stage10Started",
        "providerNeutralSelectorFoundationWorkAuthorized",
        "engineEligibilityPlanningAuthorized",
        "stage9RecommendationConsumptionAuthorized",
        "originalAwareSelectionDecisionAuthorized",
        "stage9aEvidenceEnforcementAuthorized",
        "failSafeReviewOriginalFallbackAuthorized",
        "syntheticSelectorDrillsAuthorized",
        "explainableReasonCodesAuthorized",
    ):
        _require(scope.get(field) is True, f"authorized Stage 10 scope missing: {field}")

    for field in (
        "liveSelectorActivationAuthorized",
        "automaticFinalSelectionAuthorized",
        "realUserSelectorCohortAuthorized",
        "stage11EntryAuthorized",
        "stage11ModelTrainingAuthorized",
        "docresRuntimeDependencyApproved",
        "docresModelArtifactApproved",
        "providerSpecificActivationAuthorized",
        "liveResourceCreationAuthorized",
        "productionDeploymentAuthorized",
        "productionLoadSoakAuthorized",
        "datasetCollectionAuthorized",
        "userDocumentTrainingUseAuthorized",
        "modelTrainingAuthorized",
        "modelPublicationAuthorized",
        "modelArtifactDownloadAuthorized",
        "networkFetchAuthorized",
        "thresholdChangesAuthorized",
        "resourceLimitChangesAuthorized",
        "heldOutRetuningAuthorized",
    ):
        _require(scope.get(field) is False, f"unauthorized scope expansion: {field}")

    safety = authorization.get("safetyBoundaries")
    _require(isinstance(safety, Mapping), "Stage 10 safety boundaries missing")
    for field in (
        "historicalEvidenceImmutable",
        "sourceArtifactImmutable",
        "derivedArtifactsRequireProvenance",
        "originalAlwaysSelectable",
        "selectorCannotBypassMusicSafety",
        "selectorCannotBypassStage9Comparator",
        "hardDeterministicVetoCannotBeOverridden",
        "hardSemanticVetoCannotBeOverridden",
        "reviewRequiredCannotBecomeAutomaticVariantSelection",
        "missingOrMalformedComparatorEvidenceFailsSafe",
        "missingOrIncompleteStage9aEvidenceFailsSafe",
        "selectorDecisionIsNotTeacherApproval",
        "selectorDecisionIsNotOMRTruth",
        "selectorDecisionIsNotHumanMusicalTruth",
        "providerNeutralityRequired",
    ):
        _require(safety.get(field) is True, f"Stage 10 safety invariant missing: {field}")

    _require(
        authorization.get("nextSafeBoundary")
        == "separate_stage10_final_exit_acceptance_then_stage11_entry_authorization",
        "unexpected Stage 10 continuation boundary",
    )

    return {
        "result": "PASS",
        "authorizationId": AUTHORIZATION_ID,
        "stage9aState": STAGE9A_STATE,
        "stage10EntryAuthorized": True,
        "stage10Started": True,
        "liveSelectorActivationAuthorized": False,
        "automaticFinalSelectionAuthorized": False,
        "stage11EntryAuthorized": False,
    }


__all__ = [
    "AUTHORIZATION_ID",
    "DECISION",
    "Stage10EntryAuthorizationError",
    "validate_stage10_entry_authorization",
]
