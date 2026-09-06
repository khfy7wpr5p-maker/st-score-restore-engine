"""Fail-closed Stage 7 provider-neutral preview-readiness authorization.

Stage 7 entry is authorized only against the immutable Stage 6 provider-neutral
final-exit current truth. This module deliberately does not authorize preview
activation, a real user cohort, provider selection, live resources, production
deployment, production drills, threshold/resource changes, training, publication,
or Stage 8 entry.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256

SCHEMA_VERSION = "1.0.0"
AUTHORIZATION_ID = "stage7.entry-preview-readiness-authorization.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_STAGE7_ENTRY_AND_PROVIDER_NEUTRAL_PREVIEW_READINESS"
AUTHORIZED_ON = "2026-09-06"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260906-stage7-entry-01"
AUTHORIZATION_SOURCE_CODE = "explicit_user_authorization"
AUTHORIZATION_CANONICAL_SHA256 = "3af639aee6c1ebcb73f87e3d78c55da70980f4684a58feac25bff7f732572dd5"
STAGE6_FINAL_EXIT_CURRENT_TRUTH_PATH = "docs/live/ST_SCORE_RESTORE_STAGE6_FINAL_EXIT_CURRENT_TRUTH.json"
STAGE6_FINAL_EXIT_CURRENT_TRUTH_GIT_BLOB_SHA = "7754cc08829f3d8ff807c9501621ddf672934978"
STAGE6_FINAL_EXIT_MAIN_SHA = "ed5cd2657466e171165d99dba0955e57a0c3a306"
STAGE7_AUTHORIZATION_BASE_MAIN_SHA = "432646f5ac24a30cc733b8e80243518031c32fe0"
STAGE7_PURPOSE = "provider_neutral_preview_release_capability_and_readiness"
NEXT_SAFE_BOUNDARY = "separate_explicit_preview_release_activation_or_stage8_entry_authorization"


class Stage7EntryAuthorizationError(ValueError):
    """Stage 7 authorization is malformed, stale, or broader than approved."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage7EntryAuthorizationError(message)


def _validate_stage6_final_truth(stage6_truth: Mapping[str, Any]) -> None:
    stage6 = stage6_truth.get("stage6", {})
    stage7 = stage6_truth.get("stage7", {})
    provider = stage6_truth.get("provider", {})
    deployment = stage6_truth.get("deployment", {})
    assertions = stage6_truth.get("assertions", {})

    _require(stage6.get("state") == "COMPLETE_PASS_PROVIDER_NEUTRAL", "Stage 6 is not provider-neutral COMPLETE/PASS")
    _require(stage6.get("exit_pass") is True, "Stage 6 final exit PASS missing")
    _require(stage6.get("provider_neutral_stage6_deliverable_complete") is True, "Stage 6 provider-neutral deliverable missing")
    _require(stage6.get("next_safe_boundary") == "separate_explicit_stage7_entry_authorization", "Stage 6 next safe boundary drifted")
    _require(stage7.get("entry_eligible") is True, "Stage 7 entry eligibility missing")
    _require(stage7.get("entry_authorized") is False, "historical Stage 6 current truth was rewritten to authorize Stage 7")
    _require(stage7.get("preview_release_authorized") is False, "historical Stage 6 current truth was rewritten to authorize preview release")
    _require(stage7.get("started") is False, "historical Stage 6 current truth was rewritten to start Stage 7")
    _require(provider.get("selection_status") == "UNSELECTED", "provider selection unexpectedly changed")
    _require(provider.get("provider_specific_activation_authorized") is False, "provider-specific activation unexpectedly authorized")
    _require(provider.get("live_resource_creation_authorized") is False, "live resource creation unexpectedly authorized")
    _require(deployment.get("production_deployment_authorized") is False, "production deployment unexpectedly authorized")
    _require(deployment.get("production_deployment_performed") is False, "production deployment unexpectedly performed")
    _require(assertions.get("historical_evidence_immutable") is True, "historical evidence immutability missing")
    _require(assertions.get("real_or_derivative_bytes_in_ordinary_git") is False, "real/derivative bytes entered ordinary Git")
    _require(assertions.get("raw_private_metrics_in_ordinary_git") is False, "raw private metrics entered ordinary Git")
    _require(assertions.get("production_deployment_authorized") is False, "production deployment already authorized")
    _require(assertions.get("preview_release_authorized") is False, "preview release already authorized")
    _require(assertions.get("model_training_authorized") is False, "model training already authorized")
    _require(assertions.get("publication_authorized") is False, "publication already authorized")
    _require(assertions.get("omr_correctness_established") is False, "OMR correctness was incorrectly established")
    _require(assertions.get("color_management_validated") is False, "color-management boundary was broadened")
    _require(assertions.get("color_fidelity_certified") is False, "color-fidelity boundary was broadened")


def validate_stage7_entry_authorization(
    raw: Mapping[str, Any],
    stage6_final_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_stage6_final_truth(stage6_final_current_truth_raw)
    _require(isinstance(raw, Mapping), "Stage 7 entry authorization must be an object")
    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schemaVersion",
            "authorizationId",
            "decision",
            "authorizedOn",
            "decisionAuthorityReference",
            "authorizationSourceCode",
            "stage6FinalExitBinding",
            "stage7Purpose",
            "scope",
            "safetyBoundaries",
            "nextSafeBoundary",
        },
        "Stage 7 entry authorization top-level fields drifted",
    )
    _require(value["schemaVersion"] == SCHEMA_VERSION, "authorization schema drifted")
    _require(value["authorizationId"] == AUTHORIZATION_ID, "authorization id drifted")
    _require(value["decision"] == AUTHORIZATION_DECISION, "authorization decision drifted")
    _require(value["authorizedOn"] == AUTHORIZED_ON, "authorization date drifted")
    _require(value["decisionAuthorityReference"] == DECISION_AUTHORITY_REFERENCE, "decision authority drifted")
    _require(value["authorizationSourceCode"] == AUTHORIZATION_SOURCE_CODE, "authorization source drifted")
    _require(value["stage7Purpose"] == STAGE7_PURPOSE, "Stage 7 purpose drifted")
    _require(
        value["stage6FinalExitBinding"] == {
            "currentTruthPath": STAGE6_FINAL_EXIT_CURRENT_TRUTH_PATH,
            "currentTruthGitBlobSha": STAGE6_FINAL_EXIT_CURRENT_TRUTH_GIT_BLOB_SHA,
            "stage6FinalExitMainSha": STAGE6_FINAL_EXIT_MAIN_SHA,
            "stage7EntryAuthorizationBaseMainSha": STAGE7_AUTHORIZATION_BASE_MAIN_SHA,
            "stage6State": "COMPLETE_PASS_PROVIDER_NEUTRAL",
            "stage6ExitPass": True,
            "stage7EntryEligible": True,
        },
        "Stage 6 final-exit binding drifted",
    )
    _require(
        value["scope"] == {
            "stage7EntryAuthorized": True,
            "stage7Started": True,
            "providerNeutralPreviewContractWorkAuthorized": True,
            "userFacingSafetyStatusContractWorkAuthorized": True,
            "privacySafeObservabilityContractWorkAuthorized": True,
            "syntheticPreviewReleaseDrillsAuthorized": True,
            "stage7ExitReadinessEvaluationAuthorized": True,
            "previewReleaseActivationAuthorized": False,
            "realUserCohortAuthorized": False,
            "providerSelectionAuthorized": False,
            "providerSpecificAdapterActivationAuthorized": False,
            "liveResourceCreationAuthorized": False,
            "productionDeploymentAuthorized": False,
            "productionOperationalDrillsAuthorized": False,
            "productionLoadSoakAuthorized": False,
            "productionPenetrationTestAuthorized": False,
            "thresholdChangesAuthorized": False,
            "resourceLimitChangesAuthorized": False,
            "heldOutRetuningAuthorized": False,
            "modelTrainingAuthorized": False,
            "modelPublicationAuthorized": False,
            "stage8EntryAuthorized": False,
        },
        "Stage 7 scope drifted or over-authorized",
    )
    _require(
        value["safetyBoundaries"] == {
            "historicalEvidenceImmutable": True,
            "sourceArtifactImmutable": True,
            "derivedArtifactsRequireProvenance": True,
            "realOrDerivativeBytesInOrdinaryGit": False,
            "rawPrivateMetricsInOrdinaryGit": False,
            "rawSecretsOrKeyMaterialInOrdinaryGit": False,
            "omrCorrectnessClaimAuthorized": False,
            "universalRestorationEffectivenessClaimAuthorized": False,
            "productionSecurityCertificationAuthorized": False,
            "colorManagementValidated": False,
            "colorFidelityCertified": False,
            "unsafeOrUncertainCandidateMayRouteToOriginalOrReview": True,
        },
        "Stage 7 safety boundaries drifted",
    )
    _require(value["nextSafeBoundary"] == NEXT_SAFE_BOUNDARY, "next safe boundary drifted")
    _require(canonical_sha256(value) == AUTHORIZATION_CANONICAL_SHA256, "Stage 7 entry authorization canonical digest drifted")
    return value


def summarize_stage7_entry_authorization(
    raw: Mapping[str, Any],
    stage6_final_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage7_entry_authorization(raw, stage6_final_current_truth_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "decision": AUTHORIZATION_DECISION,
        "authorizationDigest": {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "stage6ExitPass": True,
        "stage7EntryEligible": True,
        "stage7EntryAuthorized": True,
        "stage7Started": True,
        "providerNeutralPreviewReadinessAuthorized": True,
        "previewReleaseActivationAuthorized": False,
        "stage8EntryAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "AUTHORIZATION_CANONICAL_SHA256",
    "AUTHORIZATION_DECISION",
    "AUTHORIZATION_ID",
    "NEXT_SAFE_BOUNDARY",
    "Stage7EntryAuthorizationError",
    "summarize_stage7_entry_authorization",
    "validate_stage7_entry_authorization",
]
