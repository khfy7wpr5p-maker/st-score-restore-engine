"""Fail-closed Stage 8 DocRes optional-candidate entry authorization.

Stage 8 is intentionally bounded to a disabled-by-default candidate adapter
contract and synthetic safety-handoff evidence. No external DocRes package,
model artifact, live runtime, network fetch, user cohort, production deployment,
training, publication, or Stage 9 comparator selection is authorized here.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256

SCHEMA_VERSION = "1.0.0"
AUTHORIZATION_ID = "stage8.entry-docres-optional-candidate-authorization.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_STAGE8_ENTRY_AND_DOCRES_OPTIONAL_CANDIDATE_CONTRACT"
AUTHORIZED_ON = "2026-09-06"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260906-stage8-entry-01"
AUTHORIZATION_SOURCE_CODE = "explicit_user_authorization"
AUTHORIZATION_CANONICAL_SHA256 = "3a43c86e07e3075a00c68b0b81792a3ba40ce0e284c02464a56f2ac731253465"
STAGE7_CURRENT_TRUTH_PATH = "docs/live/ST_SCORE_RESTORE_STAGE7_FINAL_EXIT_CURRENT_TRUTH.json"
STAGE7_CURRENT_TRUTH_GIT_BLOB_SHA = "c7c57d4084b8c2cd0cb91974ba266864ecb7e643"
STAGE7_FINAL_MAIN_SHA = "8d6e16ca50dcb2f13b8c9a5e20053e9fb2e76806"
STAGE8_PURPOSE = "docres_optional_candidate_contract_and_synthetic_safety_handoff"
NEXT_SAFE_BOUNDARY = "separate_exact_docres_dependency_model_runtime_approval_or_stage9_entry_authorization"


class Stage8EntryAuthorizationError(ValueError):
    """Stage 8 authorization is malformed, stale, or broader than approved."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage8EntryAuthorizationError(message)


def _validate_stage7_final_truth(stage7_truth: Mapping[str, Any]) -> None:
    stage7 = stage7_truth.get("stage7", {})
    stage8 = stage7_truth.get("stage8", {})
    provider = stage7_truth.get("provider", {})
    deployment = stage7_truth.get("deployment", {})
    assertions = stage7_truth.get("assertions", {})

    _require(
        stage7.get("state") == "COMPLETE_PASS_PROVIDER_NEUTRAL_PREVIEW_CAPABILITY",
        "Stage 7 is not COMPLETE/PASS",
    )
    _require(stage7.get("exit_pass") is True, "Stage 7 final exit PASS missing")
    _require(stage7.get("preview_release_activation_authorized") is False, "preview activation unexpectedly authorized")
    _require(stage7.get("preview_release_activated") is False, "preview release unexpectedly active")
    _require(stage7.get("real_user_cohort_authorized") is False, "real user cohort unexpectedly authorized")
    _require(stage8.get("entry_eligible") is True, "Stage 8 entry eligibility missing")
    _require(stage8.get("entry_authorized") is False, "historical Stage 7 truth was rewritten to authorize Stage 8")
    _require(stage8.get("started") is False, "historical Stage 7 truth was rewritten to start Stage 8")
    _require(provider.get("selection_status") == "UNSELECTED", "provider selection unexpectedly changed")
    _require(provider.get("provider_specific_activation_authorized") is False, "provider activation unexpectedly authorized")
    _require(provider.get("live_resource_creation_authorized") is False, "live resource creation unexpectedly authorized")
    _require(deployment.get("production_deployment_authorized") is False, "production deployment unexpectedly authorized")
    _require(deployment.get("production_deployment_performed") is False, "production deployment unexpectedly performed")
    _require(assertions.get("historical_evidence_immutable") is True, "historical evidence immutability missing")
    _require(assertions.get("source_artifact_immutable") is True, "source immutability missing")
    _require(assertions.get("real_or_derivative_bytes_in_ordinary_git") is False, "real/derivative bytes entered ordinary Git")
    _require(assertions.get("raw_private_metrics_in_ordinary_git") is False, "raw private metrics entered ordinary Git")
    _require(assertions.get("model_training_authorized") is False, "model training already authorized")
    _require(assertions.get("model_publication_authorized") is False, "model publication already authorized")
    _require(assertions.get("omr_correctness_established") is False, "OMR correctness was incorrectly established")
    _require(assertions.get("musical_truth_established") is False, "musical truth was incorrectly established")


def validate_stage8_entry_authorization(
    raw: Mapping[str, Any],
    stage7_final_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_stage7_final_truth(stage7_final_current_truth_raw)
    _require(isinstance(raw, Mapping), "Stage 8 entry authorization must be an object")
    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schemaVersion",
            "authorizationId",
            "decision",
            "authorizedOn",
            "decisionAuthorityReference",
            "authorizationSourceCode",
            "stage7FinalExitBinding",
            "stage8Purpose",
            "scope",
            "safetyBoundaries",
            "nextSafeBoundary",
        },
        "Stage 8 entry authorization top-level fields drifted",
    )
    _require(value["schemaVersion"] == SCHEMA_VERSION, "authorization schema drifted")
    _require(value["authorizationId"] == AUTHORIZATION_ID, "authorization id drifted")
    _require(value["decision"] == AUTHORIZATION_DECISION, "authorization decision drifted")
    _require(value["authorizedOn"] == AUTHORIZED_ON, "authorization date drifted")
    _require(value["decisionAuthorityReference"] == DECISION_AUTHORITY_REFERENCE, "decision authority drifted")
    _require(value["authorizationSourceCode"] == AUTHORIZATION_SOURCE_CODE, "authorization source drifted")
    _require(value["stage8Purpose"] == STAGE8_PURPOSE, "Stage 8 purpose drifted")
    _require(
        value["stage7FinalExitBinding"] == {
            "currentTruthPath": STAGE7_CURRENT_TRUTH_PATH,
            "currentTruthGitBlobSha": STAGE7_CURRENT_TRUTH_GIT_BLOB_SHA,
            "stage7FinalMainSha": STAGE7_FINAL_MAIN_SHA,
            "stage7State": "COMPLETE_PASS_PROVIDER_NEUTRAL_PREVIEW_CAPABILITY",
            "stage7ExitPass": True,
            "stage8EntryEligible": True,
        },
        "Stage 7 final-exit binding drifted",
    )

    expected_scope = {
        "stage8EntryAuthorized": True,
        "stage8Started": True,
        "docresOptionalCandidateContractWorkAuthorized": True,
        "docresAdapterBoundaryWorkAuthorized": True,
        "syntheticDocresCandidateDrillsAuthorized": True,
        "musicSafetyValidationHandoffWorkAuthorized": True,
        "dependencyAndLicenseReviewDocumentationAuthorized": True,
        "externalPackageInstallationAuthorized": False,
        "docresRuntimeDependencyApproved": False,
        "modelArtifactDownloadAuthorized": False,
        "modelWeightsUseAuthorized": False,
        "networkFetchAuthorized": False,
        "liveDocresRuntimeActivationAuthorized": False,
        "realUserDocresCohortAuthorized": False,
        "providerSpecificActivationAuthorized": False,
        "liveResourceCreationAuthorized": False,
        "productionDeploymentAuthorized": False,
        "productionLoadSoakAuthorized": False,
        "productionPenetrationTestAuthorized": False,
        "thresholdChangesAuthorized": False,
        "resourceLimitChangesAuthorized": False,
        "heldOutRetuningAuthorized": False,
        "modelTrainingAuthorized": False,
        "modelPublicationAuthorized": False,
        "stage9EntryAuthorized": False,
    }
    _require(value["scope"] == expected_scope, "Stage 8 scope drifted or over-authorized")

    expected_boundaries = {
        "historicalEvidenceImmutable": True,
        "sourceArtifactImmutable": True,
        "derivedArtifactsRequireProvenance": True,
        "candidateMustRemainOptional": True,
        "candidateCannotOverwriteOriginal": True,
        "candidateRequiresMusicSafetyValidation": True,
        "unknownOrUnsafeCandidateRoutesToOriginalOrReview": True,
        "stage9ComparatorSelectionAuthorized": False,
        "realOrDerivativeBytesInOrdinaryGit": False,
        "rawPrivateMetricsInOrdinaryGit": False,
        "rawSecretsOrKeyMaterialInOrdinaryGit": False,
        "omrCorrectnessClaimAuthorized": False,
        "musicalTruthClaimAuthorized": False,
        "universalRestorationEffectivenessClaimAuthorized": False,
        "productionSecurityCertificationAuthorized": False,
        "colorManagementValidated": False,
        "colorFidelityCertified": False,
    }
    _require(value["safetyBoundaries"] == expected_boundaries, "Stage 8 safety boundaries drifted")
    _require(value["nextSafeBoundary"] == NEXT_SAFE_BOUNDARY, "next safe boundary drifted")
    _require(canonical_sha256(value) == AUTHORIZATION_CANONICAL_SHA256, "Stage 8 authorization digest drifted")
    return value


def summarize_stage8_entry_authorization(
    raw: Mapping[str, Any],
    stage7_final_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage8_entry_authorization(raw, stage7_final_current_truth_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "decision": AUTHORIZATION_DECISION,
        "authorizationDigest": {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "stage7ExitPass": True,
        "stage8EntryEligible": True,
        "stage8EntryAuthorized": True,
        "stage8Started": True,
        "docresRuntimeDependencyApproved": False,
        "liveDocresRuntimeActivationAuthorized": False,
        "stage9EntryAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "AUTHORIZATION_CANONICAL_SHA256",
    "AUTHORIZATION_DECISION",
    "AUTHORIZATION_ID",
    "NEXT_SAFE_BOUNDARY",
    "Stage8EntryAuthorizationError",
    "summarize_stage8_entry_authorization",
    "validate_stage8_entry_authorization",
]
