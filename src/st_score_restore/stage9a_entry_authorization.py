"""Fail-closed Stage 9A entry authorization validation."""

from __future__ import annotations

from typing import Any, Mapping

AUTHORIZATION_ID = "stage9a.entry-mspm-capability-authorization.v1"
DECISION = "AUTHORIZE_STAGE9A_ENTRY_AND_PROVIDER_NEUTRAL_MSPM_CAPABILITY"
STAGE9_TRUTH_PATH = "docs/live/ST_SCORE_RESTORE_STAGE9_FINAL_EXIT_CURRENT_TRUTH.json"
STAGE9_TRUTH_BLOB_SHA = "398b1d97995665f6df1393fb870e54b7e7536c47"
STAGE9_FINAL_MAIN_SHA = "49e85fdac88eb93a2f25f8cdf466421dad2e498c"
STAGE9_STATE = "COMPLETE_PASS_PROVIDER_NEUTRAL_MULTI_ENGINE_COMPARATOR_FOUNDATION"


class Stage9AEntryAuthorizationError(ValueError):
    """Raised when Stage 9A authorization is absent, inconsistent, or scope-expanded."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage9AEntryAuthorizationError(message)


def validate_stage9a_entry_authorization(
    authorization: Mapping[str, Any],
    stage9_truth: Mapping[str, Any],
) -> dict[str, Any]:
    _require(isinstance(authorization, Mapping), "authorization must be an object")
    _require(isinstance(stage9_truth, Mapping), "Stage 9 current truth must be an object")
    _require(authorization.get("authorizationId") == AUTHORIZATION_ID, "unexpected authorization id")
    _require(authorization.get("decision") == DECISION, "unexpected Stage 9A authorization decision")
    _require(authorization.get("authorizationSourceCode") == "explicit_user_authorization", "explicit authorization missing")

    binding = authorization.get("stage9FinalExitBinding")
    _require(isinstance(binding, Mapping), "Stage 9 binding missing")
    expected_binding = {
        "currentTruthPath": STAGE9_TRUTH_PATH,
        "currentTruthGitBlobSha": STAGE9_TRUTH_BLOB_SHA,
        "stage9FinalMainSha": STAGE9_FINAL_MAIN_SHA,
        "stage9State": STAGE9_STATE,
        "stage9ExitPass": True,
        "stage9aEntryEligible": True,
    }
    for key, expected in expected_binding.items():
        _require(binding.get(key) == expected, f"Stage 9 binding mismatch: {key}")

    stage9 = stage9_truth.get("stage9")
    stage9a = stage9_truth.get("stage9a")
    _require(isinstance(stage9, Mapping) and isinstance(stage9a, Mapping), "Stage 9/9A current truth missing")
    _require(stage9.get("state") == STAGE9_STATE, "Stage 9 state mismatch")
    _require(stage9.get("exit_pass") is True, "Stage 9 exit must pass")
    _require(stage9a.get("entry_eligible") is True, "Stage 9A must be entry eligible")
    _require(stage9a.get("entry_authorized") is False, "baseline Stage 9 truth must predate Stage 9A authorization")
    _require(stage9a.get("started") is False, "baseline Stage 9 truth must predate Stage 9A start")

    scope = authorization.get("scope")
    _require(isinstance(scope, Mapping), "Stage 9A scope missing")
    for field in (
        "stage9aEntryAuthorized",
        "stage9aStarted",
        "mspmEvidenceContractWorkAuthorized",
        "extensibleSymbolTaxonomyWorkAuthorized",
        "providerNeutralEvidenceAdapterWorkAuthorized",
        "comparatorHandoffWorkAuthorized",
        "syntheticPreservationDrillsAuthorized",
        "failSafeAbstentionAndOriginalFallbackWorkAuthorized",
        "explainableRiskCodeWorkAuthorized",
    ):
        _require(scope.get(field) is True, f"authorized Stage 9A scope missing: {field}")

    forbidden_true = (
        "datasetCollectionAuthorized",
        "userDocumentTrainingUseAuthorized",
        "modelTrainingAuthorized",
        "modelPublicationAuthorized",
        "productionInferenceAuthorized",
        "automaticFinalSelectionAuthorized",
        "stage10EntryAuthorized",
        "stage10SelectorActivationAuthorized",
        "docresRuntimeDependencyApproved",
        "modelArtifactDownloadAuthorized",
        "networkFetchAuthorized",
        "providerSpecificActivationAuthorized",
        "liveResourceCreationAuthorized",
        "productionDeploymentAuthorized",
        "productionLoadSoakAuthorized",
        "thresholdChangesAuthorized",
        "resourceLimitChangesAuthorized",
        "heldOutRetuningAuthorized",
    )
    for field in forbidden_true:
        _require(scope.get(field) is False, f"unauthorized scope expansion: {field}")

    safety = authorization.get("safetyBoundaries")
    _require(isinstance(safety, Mapping), "Stage 9A safety boundaries missing")
    for field in (
        "historicalEvidenceImmutable",
        "sourceArtifactImmutable",
        "derivedArtifactsRequireProvenance",
        "deterministicSafetyRemainsIndependent",
        "hardDeterministicVetoCannotBeOverridden",
        "hardSemanticVetoCannotBeOverridden",
        "originalAlwaysSelectable",
        "uncertainOrUnavailableSemanticEvidenceFailsSafe",
        "mspmEvidenceIsNotOMRTruth",
        "mspmEvidenceIsNotHumanMusicalTruth",
        "mspmCannotApproveCandidateByItself",
        "noOpaqueUniversalPreservationScore",
    ):
        _require(safety.get(field) is True, f"Stage 9A safety invariant missing: {field}")

    _require(
        authorization.get("nextSafeBoundary")
        == "separate_stage9a_final_exit_acceptance_then_stage10_entry_authorization",
        "unexpected Stage 9A continuation boundary",
    )

    return {
        "result": "PASS",
        "authorizationId": AUTHORIZATION_ID,
        "stage9State": STAGE9_STATE,
        "stage9aEntryAuthorized": True,
        "stage9aStarted": True,
        "modelTrainingAuthorized": False,
        "productionInferenceAuthorized": False,
        "stage10EntryAuthorized": False,
    }


__all__ = [
    "AUTHORIZATION_ID",
    "DECISION",
    "Stage9AEntryAuthorizationError",
    "validate_stage9a_entry_authorization",
]
