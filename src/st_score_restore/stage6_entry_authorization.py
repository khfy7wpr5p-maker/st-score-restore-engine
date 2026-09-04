"""Fail-closed Stage 6 entry and governance-start authorization.

This module binds explicit Stage 6 entry authorization to the production-effective
Stage 5 COMPLETE/PASS checkpoint. It authorizes only provider-neutral Stage 6
governance, architecture and contract work. Provider-specific trust-boundary
selection, production identity/network/storage implementation, operational
resource creation, deployment, preview release, training and threshold/resource
changes remain separately unauthorized.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256

SCHEMA_VERSION = "1.0.0"
AUTHORIZATION_ID = "stage6.entry-governance-authorization.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_STAGE6_ENTRY_AND_GOVERNANCE_START"
AUTHORIZED_ON = "2026-09-04"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260904-stage6-entry-01"
AUTHORIZATION_SOURCE_CODE = "explicit_user_authorization"
STAGE5_FINAL_ACCEPTANCE_DIGEST = "467eaf11c451d114d3ef41afd44c87cf2dce5cb68f89a5d6cfc45a81e1eed9fc"
CURRENT_MAIN_SHA = "0f006f678c63302a2e433e6401fd168c1a0ffa4c"
STAGE5_FINAL_EXIT_MAIN_SHA = "19aaa35ac212b2a1698cd23b622bfd59c1e721b4"
REPOSITORY_VALIDATION_RUN_NUMBER = 438
STAGE4_GOVERNANCE_RUN_NUMBER = 49
STAGE5_GOVERNANCE_RUN_NUMBER = 41
AUTHORIZATION_CANONICAL_SHA256 = "58d781f3c6b22ac8350f2f94a6902f76b6310fdf62486aa90c18382566a9e9b3"
STAGE6_PURPOSE = "identity_network_and_production_infrastructure_governance"
NEXT_SAFE_BOUNDARY = "separate_explicit_s6_02_trust_boundary_decision_package_authorization"


class Stage6EntryAuthorizationError(ValueError):
    """Stage 6 authorization is malformed, stale, or broader than approved."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage6EntryAuthorizationError(message)


def validate_stage6_entry_authorization(
    raw: Mapping[str, Any],
    stage5_final_acceptance_raw: Mapping[str, Any],
    stage5_final_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    _require(
        canonical_sha256(stage5_final_acceptance_raw) == STAGE5_FINAL_ACCEPTANCE_DIGEST,
        "Stage 5 final acceptance canonical digest drifted",
    )
    _require(stage5_final_acceptance_raw.get("decision") == "PASS", "Stage 5 final decision is not PASS")
    _require(stage5_final_acceptance_raw.get("stage5ExitPass") is True, "Stage 5 final PASS flag missing")
    _require(stage5_final_acceptance_raw.get("stage6EntryEligible") is True, "Stage 6 eligibility missing")
    _require(stage5_final_acceptance_raw.get("stage6EntryAuthorized") is False, "historical Stage 5 final acceptance was rewritten")
    _require(stage5_final_acceptance_raw.get("stage6Started") is False, "historical Stage 5 final acceptance was rewritten to start Stage 6")

    stage5 = stage5_final_current_truth_raw.get("stage5", {})
    stage6 = stage5_final_current_truth_raw.get("stage6", {})
    assertions = stage5_final_current_truth_raw.get("assertions", {})
    _require(stage5.get("state") == "COMPLETE_PASS", "Stage 5 current truth is not COMPLETE_PASS")
    _require(stage5.get("exit_pass") is True, "Stage 5 current truth PASS missing")
    _require(stage5.get("final_acceptance_digest") == STAGE5_FINAL_ACCEPTANCE_DIGEST, "Stage 5 current-truth digest drifted")
    _require(stage5.get("color_management_validated") is False, "Stage 5 color-management boundary was broadened")
    _require(stage5.get("color_fidelity_certified") is False, "Stage 5 color-fidelity boundary was broadened")
    _require(stage6.get("entry_eligible") is True, "Stage 6 current truth is not entry-eligible")
    _require(stage6.get("entry_authorized") is False, "historical Stage 5 final current truth was rewritten")
    _require(stage6.get("started") is False, "historical Stage 5 final current truth was rewritten to start Stage 6")
    _require(assertions.get("historical_evidence_immutable") is True, "historical evidence immutability missing")
    _require(assertions.get("real_or_derivative_bytes_in_ordinary_git") is False, "real/derivative bytes entered ordinary Git")
    _require(assertions.get("raw_private_metrics_in_ordinary_git") is False, "raw private metrics entered ordinary Git")
    _require(assertions.get("production_deployment_authorized") is False, "production deployment was already authorized")
    _require(assertions.get("preview_release_authorized") is False, "preview release was already authorized")
    _require(assertions.get("model_training_authorized") is False, "model training was already authorized")

    _require(isinstance(raw, Mapping), "Stage 6 entry authorization must be an object")
    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schemaVersion",
            "authorizationId",
            "decision",
            "authorizedOn",
            "decisionAuthorityReference",
            "authorizationSourceCode",
            "stage5FinalAcceptanceDigest",
            "stage5ProductionCheckpoint",
            "stage6Purpose",
            "scope",
            "safetyBoundaries",
            "nextSafeBoundary",
        },
        "Stage 6 entry authorization top-level fields drifted",
    )
    _require(value["schemaVersion"] == SCHEMA_VERSION, "authorization schema drifted")
    _require(value["authorizationId"] == AUTHORIZATION_ID, "authorization id drifted")
    _require(value["decision"] == AUTHORIZATION_DECISION, "authorization decision drifted")
    _require(value["authorizedOn"] == AUTHORIZED_ON, "authorization date drifted")
    _require(value["decisionAuthorityReference"] == DECISION_AUTHORITY_REFERENCE, "decision authority drifted")
    _require(value["authorizationSourceCode"] == AUTHORIZATION_SOURCE_CODE, "authorization source drifted")
    _require(
        value["stage5FinalAcceptanceDigest"] == {"algorithm": "sha256", "value": STAGE5_FINAL_ACCEPTANCE_DIGEST},
        "Stage 5 final acceptance binding drifted",
    )
    _require(
        value["stage5ProductionCheckpoint"] == {
            "currentMainSha": CURRENT_MAIN_SHA,
            "stage5FinalExitMainSha": STAGE5_FINAL_EXIT_MAIN_SHA,
            "stage5FinalExitPass": True,
            "repositoryValidationRunNumber": REPOSITORY_VALIDATION_RUN_NUMBER,
            "stage4GovernanceRunNumber": STAGE4_GOVERNANCE_RUN_NUMBER,
            "stage5GovernanceRunNumber": STAGE5_GOVERNANCE_RUN_NUMBER,
            "python311": "success",
            "python312": "success",
        },
        "Stage 5 production checkpoint drifted",
    )
    _require(value["stage6Purpose"] == STAGE6_PURPOSE, "Stage 6 purpose drifted")
    _require(
        value["scope"] == {
            "stage6EntryEligible": True,
            "stage6EntryAuthorized": True,
            "stage6GovernanceFrameworkAuthorized": True,
            "stage6Started": True,
            "providerNeutralArchitectureAndContractWorkAuthorized": True,
            "providerSpecificTrustBoundaryDecisionPackageAuthorized": False,
            "productionIdentityImplementationAuthorized": False,
            "productionSecretsKmsIamImplementationAuthorized": False,
            "productionNetworkImplementationAuthorized": False,
            "productionStorageDeploymentImplementationAuthorized": False,
            "productionOperationalDrillsAuthorized": False,
            "productionDeploymentAuthorized": False,
            "previewReleaseAuthorized": False,
            "productionThresholdChangesAuthorized": False,
            "productionResourceLimitChangesAuthorized": False,
            "heldOutRetuningAuthorized": False,
            "modelTrainingAuthorized": False,
            "publicationAuthorized": False,
        },
        "Stage 6 entry scope drifted or over-authorized",
    )
    _require(
        value["safetyBoundaries"] == {
            "historicalEvidenceImmutable": True,
            "realOrDerivativeBytesInOrdinaryGit": False,
            "rawPrivateMetricsInOrdinaryGit": False,
            "stage5FinalPassMustRemainTrue": True,
            "stage5ColorManagementValidatedMustRemainFalse": True,
            "colorFidelityCertificationAuthorized": False,
            "temporaryPr154MergeAuthorized": False,
            "providerSpecificStage6WorkRequiresSeparateAuthorization": True,
            "stage7EntryAuthorized": False,
        },
        "Stage 6 safety boundaries drifted",
    )
    _require(value["nextSafeBoundary"] == NEXT_SAFE_BOUNDARY, "next safe boundary drifted")
    _require(canonical_sha256(value) == AUTHORIZATION_CANONICAL_SHA256, "Stage 6 entry authorization canonical digest drifted")
    return value


def summarize_stage6_entry_authorization(
    raw: Mapping[str, Any],
    stage5_final_acceptance_raw: Mapping[str, Any],
    stage5_final_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage6_entry_authorization(raw, stage5_final_acceptance_raw, stage5_final_current_truth_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "decision": AUTHORIZATION_DECISION,
        "authorizationDigest": {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "stage5ExitPass": True,
        "stage6EntryEligible": True,
        "stage6EntryAuthorized": True,
        "stage6Started": True,
        "providerSpecificStage6WorkAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "AUTHORIZATION_CANONICAL_SHA256",
    "AUTHORIZATION_DECISION",
    "AUTHORIZATION_ID",
    "AUTHORIZED_ON",
    "DECISION_AUTHORITY_REFERENCE",
    "NEXT_SAFE_BOUNDARY",
    "SCHEMA_VERSION",
    "STAGE5_FINAL_ACCEPTANCE_DIGEST",
    "STAGE6_PURPOSE",
    "Stage6EntryAuthorizationError",
    "summarize_stage6_entry_authorization",
    "validate_stage6_entry_authorization",
]
