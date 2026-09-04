"""Fail-closed Stage 6 S6-02 production trust-boundary decision package.

S6-02 freezes the production security boundary and provider-selection criteria.
It authorizes provider-specific evaluation only. It does not select a provider,
create live resources, implement production identity/network/storage/KMS, deploy,
start Stage 7, retune thresholds/resources, train models, or publish artifacts.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage6_entry_current_truth import validate_stage6_entry_current_truth

SCHEMA_VERSION = "1.0.0"
DECISION_ID = "stage6.s6-02.production-trust-boundary-decision.v1"
DECISION = "APPROVE_S6_02_PRODUCTION_TRUST_BOUNDARY_DECISION_PACKAGE"
APPROVED_ON = "2026-09-04"
AUTHORITY_REFERENCE = "authority:project-governance-owner-20260904-stage6-s6-02-01"
AUTHORIZATION_SOURCE_CODE = "explicit_user_authorization"
ENTRY_AUTHORIZATION_DIGEST = "58d781f3c6b22ac8350f2f94a6902f76b6310fdf62486aa90c18382566a9e9b3"
ENTRY_CURRENT_MAIN_SHA = "1addd8f8f403c1d038a951842b114eb487bfa044"
DECISION_CANONICAL_SHA256 = "9485e51f1398c6cff2d9be9264eb8acdf47f8c4ca0fc750062fd9e80298e3865"
NEXT_SAFE_BOUNDARY = "separate_explicit_s6_03_identity_authz_implementation_authorization"


class Stage6TrustBoundaryDecisionError(ValueError):
    """S6-02 decision evidence is malformed, stale, or over-authorized."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage6TrustBoundaryDecisionError(message)


def validate_stage6_trust_boundary_decision(
    raw: Mapping[str, Any],
    entry_current_truth_raw: Mapping[str, Any],
    entry_authorization_raw: Mapping[str, Any],
    stage5_final_acceptance_raw: Mapping[str, Any],
    historical_stage5_final_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_entry_current_truth(
        entry_current_truth_raw,
        entry_authorization_raw,
        stage5_final_acceptance_raw,
        historical_stage5_final_truth_raw,
    )

    _require(isinstance(raw, Mapping), "S6-02 decision must be an object")
    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schemaVersion",
            "decisionId",
            "decision",
            "approvedOn",
            "decisionAuthorityReference",
            "authorizationSourceCode",
            "stage6EntryAuthorizationDigest",
            "stage6EntryCurrentTruthBinding",
            "identityStrategy",
            "providerDecision",
            "productionTrustBoundary",
            "scope",
            "safetyBoundaries",
            "nextSafeBoundary",
        },
        "S6-02 top-level fields drifted",
    )
    _require(value["schemaVersion"] == SCHEMA_VERSION, "S6-02 schema drifted")
    _require(value["decisionId"] == DECISION_ID, "S6-02 decision id drifted")
    _require(value["decision"] == DECISION, "S6-02 decision drifted")
    _require(value["approvedOn"] == APPROVED_ON, "S6-02 approval date drifted")
    _require(value["decisionAuthorityReference"] == AUTHORITY_REFERENCE, "S6-02 authority drifted")
    _require(value["authorizationSourceCode"] == AUTHORIZATION_SOURCE_CODE, "S6-02 authorization source drifted")
    _require(
        value["stage6EntryAuthorizationDigest"] == {
            "algorithm": "sha256",
            "value": ENTRY_AUTHORIZATION_DIGEST,
        },
        "Stage 6 entry authorization binding drifted",
    )

    binding = value["stage6EntryCurrentTruthBinding"]
    _require(binding.get("mainSha") == ENTRY_CURRENT_MAIN_SHA, "S6-02 current-main binding drifted")
    _require(binding.get("checkpointType") == "stage6_entry_governance_authorization_current_truth_overlay", "S6-02 checkpoint type drifted")
    _require(binding.get("stage6State") == "ACTIVE_GOVERNANCE_PROVIDER_NEUTRAL_ONLY", "S6-02 entry state drifted")
    _require(binding.get("repositoryValidationRunNumber") == 442, "repository validation binding drifted")
    _require(binding.get("stage4GovernanceRunNumber") == 53, "Stage 4 governance binding drifted")
    _require(binding.get("stage5GovernanceRunNumber") == 45, "Stage 5 governance binding drifted")
    _require(binding.get("stage6GovernanceRunNumber") == 4, "Stage 6 governance binding drifted")
    _require(binding.get("python311") == "success" and binding.get("python312") == "success", "S6-02 entry CI was not green")

    identity = value["identityStrategy"]
    _require(identity.get("architecture") == "shared_capable_identity_plane", "identity architecture drifted")
    _require(identity.get("initialRelyingParties") == ["st-score-restore"], "initial relying-party boundary drifted")
    _require(identity.get("futureRelyingPartyIntegrationRequiresSeparateAuthorization") is True, "future relying-party authorization boundary weakened")
    _require(identity.get("productionCallerSuppliedActorIdAllowed") is False, "caller-supplied production actor identity was allowed")
    _require(identity.get("productionStaticApiKeysAllowed") is False, "static API keys were allowed as production identity")

    provider = value["providerDecision"]
    _require(provider.get("providerSelectionStatus") == "UNSELECTED", "a provider was selected without decision evidence")
    _require(provider.get("providerSpecificEvaluationAuthorized") is True, "provider evaluation authorization missing")
    _require(provider.get("providerSpecificImplementationAuthorized") is False, "provider implementation was prematurely authorized")

    boundary = value["productionTrustBoundary"]
    _require(boundary["edge"].get("builtInStdlibServerPublicExposureAllowed") is False, "built-in HTTP server was approved for public exposure")
    _require(boundary["identity"].get("callerSuppliedIdentityHeadersTrusted") is False, "caller-supplied identity headers were trusted")
    _require(boundary["identity"].get("staticApiKeysAcceptedAsProductionUserIdentity") is False, "static API keys were accepted as production identity")
    _require(boundary["network"].get("quarantineOutboundNetworkAllowed") is False, "quarantine outbound network was enabled")
    _require(boundary["audit"].get("artifactBytesSecretsNamesEmailsOrFreeTextPersonalDataAllowed") is False, "private payloads were allowed in audit")
    _require(boundary["deployment"].get("liveProductionDeploymentAuthorizedByThisDecision") is False, "S6-02 authorized live deployment")
    _require(boundary["failureMode"].get("failClosedOnInvalidIdentityAuthorizationKeyStorageOrAuditEvidence") is True, "fail-closed boundary weakened")

    scope = value["scope"]
    _require(scope.get("s6_02DecisionPackageAuthorized") is True, "S6-02 decision-package authorization missing")
    _require(scope.get("providerSpecificEvaluationAuthorized") is True, "provider-specific evaluation authorization missing")
    for field in (
        "providerSelectionFinalized",
        "productionIdentityImplementationAuthorized",
        "productionSecretsKmsIamImplementationAuthorized",
        "productionNetworkImplementationAuthorized",
        "productionStorageDeploymentImplementationAuthorized",
        "productionOperationalDrillsAuthorized",
        "productionDeploymentAuthorized",
        "stage7EntryAuthorized",
        "modelTrainingAuthorized",
        "thresholdOrResourceLimitChangesAuthorized",
    ):
        _require(scope.get(field) is False, f"S6-02 over-authorized {field}")

    safety = value["safetyBoundaries"]
    _require(safety.get("historicalEvidenceImmutable") is True, "historical evidence immutability missing")
    _require(safety.get("realOrDerivativeBytesInOrdinaryGit") is False, "real/derivative bytes entered ordinary Git")
    _require(safety.get("rawPrivateMetricsInOrdinaryGit") is False, "raw private metrics entered ordinary Git")
    _require(safety.get("stage5FinalPassMustRemainTrue") is True, "Stage 5 PASS preservation missing")
    _require(safety.get("stage5ColorManagementValidatedMustRemainFalse") is True, "Stage 5 color boundary widened")
    _require(safety.get("colorFidelityCertificationAuthorized") is False, "color fidelity was prematurely authorized")
    _require(safety.get("temporaryPr154MergeAuthorized") is False, "temporary PR #154 was authorized")
    _require(safety.get("noProviderMayBeInventedWithoutDecisionEvidence") is True, "provider evidence rule missing")
    _require(safety.get("noLiveResourceCreationAuthorized") is True, "live resource creation was authorized")

    _require(value["nextSafeBoundary"] == NEXT_SAFE_BOUNDARY, "S6-02 next safe boundary drifted")
    _require(canonical_sha256(value) == DECISION_CANONICAL_SHA256, "S6-02 canonical digest drifted")
    return value


def summarize_stage6_trust_boundary_decision(
    raw: Mapping[str, Any],
    entry_current_truth_raw: Mapping[str, Any],
    entry_authorization_raw: Mapping[str, Any],
    stage5_final_acceptance_raw: Mapping[str, Any],
    historical_stage5_final_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_trust_boundary_decision(
        raw,
        entry_current_truth_raw,
        entry_authorization_raw,
        stage5_final_acceptance_raw,
        historical_stage5_final_truth_raw,
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "decision": DECISION,
        "decisionDigest": {"algorithm": "sha256", "value": DECISION_CANONICAL_SHA256},
        "identityArchitecture": "shared_capable_identity_plane",
        "initialRelyingParties": ["st-score-restore"],
        "providerSelectionStatus": "UNSELECTED",
        "productionImplementationAuthorized": False,
        "productionDeploymentAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "DECISION",
    "DECISION_CANONICAL_SHA256",
    "DECISION_ID",
    "NEXT_SAFE_BOUNDARY",
    "SCHEMA_VERSION",
    "Stage6TrustBoundaryDecisionError",
    "summarize_stage6_trust_boundary_decision",
    "validate_stage6_trust_boundary_decision",
]
