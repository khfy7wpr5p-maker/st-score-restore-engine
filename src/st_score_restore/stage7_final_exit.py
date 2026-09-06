"""Fail-closed validation for the Stage 7 provider-neutral final exit."""

from __future__ import annotations

from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage7_entry_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    validate_stage7_entry_authorization,
)

SCHEMA_VERSION = "1.0.0"
ACCEPTANCE_ID = "stage7.final-exit-acceptance.v1"
ACCEPTANCE_DECISION = "PASS"
ACCEPTED_ON = "2026-09-06"
AUTHORITY_REFERENCE = "authority:project-governance-owner-20260906-stage7-final-exit-01"
ACCEPTANCE_SOURCE = "explicit_user_authorization"
ENTRY_MAIN_SHA = "0b8a4a4f9407f592a8bade20321f7dcaa5f58cde"
STAGE7_AUTHORIZATION_GIT_BLOB_SHA1 = "c42b5a0837f508147715e1de35c5fb3a5a5d3f68"
PREVIEW_CONTRACT_PATH = "api/stage7-preview-contract.v1.json"
PREVIEW_CONTRACT_GIT_BLOB_SHA1 = "6bbb53f9d711a9deb7e69f4741ca39204d1cc092"
EXPECTED_ACCEPTANCE_SHA256 = "e6318a0dc69498eabfb70db21bb2b1818e1ac7b8250bd190b0640a6d9b096bd5"
NEXT_SAFE_BOUNDARY = "separate_explicit_preview_release_activation_or_stage8_entry_authorization"


class Stage7FinalExitError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage7FinalExitError(message)


def _validate_preview_contract(raw: Mapping[str, Any]) -> None:
    _require(raw.get("schemaVersion") == "1.0.0", "preview contract schema drifted")
    _require(raw.get("contractVersion") == "stage7.preview-contract.v1", "preview contract version drifted")
    _require(raw.get("channel") == "preview", "preview channel drifted")
    _require(raw.get("profile") == "provider-neutral", "preview profile drifted")
    _require(raw.get("activationAuthorized") is False, "preview activation was prematurely authorized")
    routing = raw.get("routing") or {}
    _require(routing.get("hardSafetyPrecedence") is True, "hard safety precedence missing")
    _require(routing.get("unknownEvidenceRoute") == "review", "unknown evidence must fail safe to review")
    _require(routing.get("activationNotAuthorizedRoute") == "original", "closed activation gate must route original")
    _require(routing.get("killSwitchRoute") == "original", "kill switch must route original")
    _require(routing.get("rollbackTarget") == "original", "rollback target must be original")
    obs = raw.get("observability") or {}
    for key in ("artifactBytesAllowed", "rawPrivateMetricsAllowed", "secretsAllowed", "freeTextAllowed"):
        _require(obs.get(key) is False, f"privacy-safe observability boundary drifted: {key}")
    claims = raw.get("claims") or {}
    for key in (
        "omrCorrectnessClaimed",
        "musicalTruthClaimed",
        "universalRestorationEffectivenessClaimed",
        "productionSecurityCertified",
        "productionScaleValidated",
    ):
        _require(claims.get(key) is False, f"preview contract contains unsupported claim: {key}")
    excluded = raw.get("excludedScope") or {}
    for key in (
        "realUserCohort",
        "providerSelection",
        "providerSpecificActivation",
        "liveResourceCreation",
        "productionDeployment",
        "productionLoadSoak",
        "productionPenetrationTesting",
        "thresholdChanges",
        "resourceLimitChanges",
        "modelTraining",
        "modelPublication",
        "stage8Entry",
    ):
        _require(excluded.get(key) is True, f"preview excluded scope weakened: {key}")


def validate_stage7_final_exit(
    stage6_final_truth: Mapping[str, Any],
    stage7_authorization: Mapping[str, Any],
    preview_contract: Mapping[str, Any],
    acceptance: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage7_entry_authorization(stage7_authorization, stage6_final_truth)
    _validate_preview_contract(preview_contract)
    _require(isinstance(acceptance, Mapping), "Stage 7 final acceptance must be an object")

    required_equal = {
        "schemaVersion": SCHEMA_VERSION,
        "acceptanceId": ACCEPTANCE_ID,
        "decision": ACCEPTANCE_DECISION,
        "acceptedOn": ACCEPTED_ON,
        "decisionAuthorityReference": AUTHORITY_REFERENCE,
        "acceptanceSourceCode": ACCEPTANCE_SOURCE,
        "acceptedPurpose": "stage8-entry-eligibility-only",
        "stage7ExitPass": True,
        "stage8EntryEligible": True,
        "stage8EntryAuthorized": False,
        "stage8Started": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }
    for key, expected in required_equal.items():
        _require(acceptance.get(key) == expected, f"{key} must equal {expected!r}")

    checkpoint = acceptance.get("entryCheckpoint") or {}
    expected_checkpoint = {
        "mainSha": ENTRY_MAIN_SHA,
        "stage7AuthorizationDigest": AUTHORIZATION_CANONICAL_SHA256,
        "stage7AuthorizationGitBlobSha1": STAGE7_AUTHORIZATION_GIT_BLOB_SHA1,
        "previewContractPath": PREVIEW_CONTRACT_PATH,
        "previewContractGitBlobSha1": PREVIEW_CONTRACT_GIT_BLOB_SHA1,
        "pr176HeadSha": "7afb685ef1f59d56b9e059e5081ff759d5d41b9c",
        "pr176RepositoryValidationRunId": 34053444752,
        "pr176RepositoryValidationRunNumber": 486,
        "pr176Stage4GovernanceRunId": 34053444759,
        "pr176Stage4GovernanceRunNumber": 97,
        "pr176Stage5GovernanceRunId": 34053444753,
        "pr176Stage5GovernanceRunNumber": 89,
        "pr176Stage6GovernanceRunId": 34053444765,
        "pr176Stage6GovernanceRunNumber": 48,
        "pr176Stage7GovernanceRunId": 34053444785,
        "pr176Stage7GovernanceRunNumber": 1,
        "postMergeRepositoryValidationRunId": 34053541542,
        "postMergeRepositoryValidationRunNumber": 487,
        "postMergeStage4GovernanceRunId": 34053541549,
        "postMergeStage4GovernanceRunNumber": 98,
        "postMergeStage5GovernanceRunId": 34053541533,
        "postMergeStage5GovernanceRunNumber": 90,
        "postMergeStage6GovernanceRunId": 34053541701,
        "postMergeStage6GovernanceRunNumber": 49,
        "postMergeStage7GovernanceRunId": 34053541529,
        "postMergeStage7GovernanceRunNumber": 2,
        "ciStatus": "success_python_3_11_and_3_12_for_repository_stage4_stage5_stage6_and_stage7_exact_head_and_post_merge",
    }
    _require(dict(checkpoint) == expected_checkpoint, "Stage 7 final entry checkpoint drifted")

    readiness = acceptance.get("acceptedReadinessState") or {}
    _require(readiness.get("decision") == "STAGE7_COMPLETE_PASS_PROVIDER_NEUTRAL_PREVIEW_CAPABILITY", "unexpected Stage 7 readiness decision")
    _require(readiness.get("readinessPrerequisitesSatisfied") is True, "Stage 7 readiness prerequisites missing")
    _require(readiness.get("blockerCount") == 0 and readiness.get("blockerCodes") == [], "Stage 7 final exit retains blockers")
    for key in (
        "previewContractImplemented",
        "versionedPreviewProfileImplemented",
        "originalFallbackImplemented",
        "killSwitchContractImplemented",
        "rollbackToOriginalImplemented",
        "hardSafetyPrecedenceImplemented",
        "userFacingSafetyStatusContractImplemented",
        "privacySafeObservabilityContractImplemented",
        "syntheticPreviewReleaseDrillsComplete",
        "providerNeutralStage7DeliverableComplete",
    ):
        _require(readiness.get(key) is True, f"Stage 7 readiness assertion missing: {key}")
    _require(readiness.get("providerSelectionStatus") == "UNSELECTED", "provider selection must remain UNSELECTED")
    for key in (
        "previewReleaseActivationAuthorized",
        "previewReleaseActivated",
        "realUserCohortAuthorized",
        "providerSpecificAdaptersActivated",
        "liveProductionResourcesCreated",
        "productionDeploymentAuthorized",
        "productionDeploymentPerformed",
        "productionLoadOrSoakValidated",
        "independentPenetrationTestOrSecuritySignoffComplete",
    ):
        _require(readiness.get(key) is False, f"Stage 7 final readiness over-claims: {key}")

    limitations = acceptance.get("acceptedLimitations")
    _require(isinstance(limitations, list) and len(limitations) >= 6, "Stage 7 limitations are incomplete")
    joined = " ".join(str(item) for item in limitations)
    for phrase in (
        "provider-neutral",
        "real user cohort",
        "UNSELECTED",
        "Production deployment",
        "OMR correctness",
        "does not authorize Stage 8",
    ):
        _require(phrase in joined, f"Stage 7 limitations lost boundary: {phrase}")

    claims = acceptance.get("claims") or {}
    expected_claims = {
        "previewReleaseActivationAuthorized",
        "previewReleaseActivated",
        "realUserCohortAuthorized",
        "providerSelectionFinalized",
        "providerSpecificActivationAuthorized",
        "liveResourceCreationAuthorized",
        "productionDeploymentAuthorized",
        "productionDeploymentPerformed",
        "productionLoadOrSoakAuthorized",
        "productionPenetrationTestAuthorized",
        "productionThresholdChangesAuthorized",
        "productionResourceLimitChangesAuthorized",
        "heldOutRetuningAuthorized",
        "modelTrainingAuthorized",
        "modelPublicationAuthorized",
        "stage8EntryAuthorized",
        "colorManagementValidated",
        "colorFidelityCertified",
        "omrCorrectnessEstablished",
        "musicalTruthEstablished",
        "restorationEffectivenessEstablished",
        "productionAvailabilityOrScalabilityEstablished",
        "providerSpecificSecurityCertified",
    }
    _require(set(claims) == expected_claims, "Stage 7 final claims fields drifted")
    for key in expected_claims:
        _require(claims.get(key) is False, f"Stage 7 final acceptance contains unauthorized claim: {key}")

    _require(canonical_sha256(acceptance) == EXPECTED_ACCEPTANCE_SHA256, "Stage 7 final acceptance canonical digest changed")
    return {
        "stage7State": "COMPLETE_PASS_PROVIDER_NEUTRAL_PREVIEW_CAPABILITY",
        "stage7ExitPass": True,
        "stage8EntryEligible": True,
        "stage8EntryAuthorized": False,
        "stage8Started": False,
        "previewReleaseActivationAuthorized": False,
        "providerSelectionStatus": "UNSELECTED",
        "productionDeploymentAuthorized": False,
        "acceptanceDigest": EXPECTED_ACCEPTANCE_SHA256,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "ACCEPTANCE_ID",
    "EXPECTED_ACCEPTANCE_SHA256",
    "NEXT_SAFE_BOUNDARY",
    "Stage7FinalExitError",
    "validate_stage7_final_exit",
]
