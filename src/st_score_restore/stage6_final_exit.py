"""Fail-closed validation for the Stage 6 S6-09 final-exit acceptance."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

SCHEMA_VERSION = "1.0.0"
ACCEPTANCE_ID = "stage6.final-exit-acceptance.v1"
ACCEPTANCE_DECISION = "PASS"
ACCEPTED_ON = "2026-09-06"
AUTHORITY_REFERENCE = "authority:project-governance-owner-20260906-stage6-s6-09"
ACCEPTANCE_SOURCE = "explicit_user_authorization"
ENTRY_MAIN_SHA = "3c4753f97fb191f259a0ed3b2ddfe658e3ad124d"
S6_08_AUTHORIZATION_DIGEST = "32f2fb177411cfa4139a659ec614c7117371ace67147cd059234a926b536ccba"
S6_08_CURRENT_TRUTH_PATH = "docs/live/ST_SCORE_RESTORE_STAGE6_S6_08_CURRENT_TRUTH.json"
S6_08_CURRENT_TRUTH_GIT_BLOB_SHA1 = "2b33081a12df3da923a9ebe42347bebe1d994102"
EXPECTED_ACCEPTANCE_SHA256 = "4f4f24624b30a88f52285788a1a6c3fd6f64097f51648fce7b33fc8c219b6406"
NEXT_SAFE_BOUNDARY = "separate_explicit_stage7_entry_authorization"


class Stage6FinalExitError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage6FinalExitError(message)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def git_blob_sha1(payload: bytes) -> str:
    framed = b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
    return hashlib.sha1(framed).hexdigest()


def validate_stage6_final_exit(
    s6_08_current_truth: Mapping[str, Any],
    acceptance: Mapping[str, Any],
) -> dict[str, Any]:
    _require(isinstance(s6_08_current_truth, Mapping), "S6-08 current truth must be an object")
    _require(isinstance(acceptance, Mapping), "Stage 6 final acceptance must be an object")

    stage6 = s6_08_current_truth.get("stage6") or {}
    _require(
        stage6.get("state") == "ACTIVE_INTEGRATION_SECURITY_REGRESSION_COMPLETE_PROVIDER_UNSELECTED",
        "S6-08 current state is not final-exit eligible",
    )
    for key in (
        "entry_eligible",
        "entry_authorized",
        "started",
        "production_identity_contract_implemented",
        "production_secrets_kms_iam_contract_implemented",
        "production_network_security_contract_implemented",
        "production_storage_deployment_contracts_implemented",
        "synthetic_operational_drills_complete",
        "integration_security_regression_authorized",
        "integration_security_regression_complete",
    ):
        _require(stage6.get(key) is True, f"S6-08 current truth missing required Stage 6 assertion: {key}")
    for key in (
        "provider_specific_identity_adapter_activated",
        "provider_specific_secrets_kms_iam_activated",
        "provider_specific_network_adapter_activated",
        "provider_specific_storage_deployment_adapter_activated",
        "production_distributed_stress_validation_complete",
        "production_load_or_soak_validated",
        "independent_penetration_test_or_security_signoff_complete",
        "production_operational_drills_authorized",
        "production_deployment_authorized",
        "s6_09_final_exit_authorized",
    ):
        _require(stage6.get(key) is False, f"S6-08 boundary drifted before final exit: {key}")
    _require(
        stage6.get("next_safe_boundary") == "separate_explicit_s6_09_final_exit_authorization",
        "S6-08 next-safe-boundary drifted",
    )

    _require(
        (s6_08_current_truth.get("s6_08_authorization") or {}).get("authorization_digest")
        == S6_08_AUTHORIZATION_DIGEST,
        "S6-08 authorization digest drifted",
    )
    regression = s6_08_current_truth.get("integration_security_regression") or {}
    for key in (
        "synthetic_only",
        "trusted_edge_identity_iam_kms_storage_chain_passed",
        "legacy_identity_header_bypass_denied",
        "cross_tenant_job_access_denied",
        "identity_conflict_revocation_signature_denied",
        "cross_environment_secret_kms_denied",
        "security_audit_dependency_fail_closed",
        "edge_and_private_topology_bypass_denied",
        "storage_queue_deployment_fail_closed",
        "s6_07_operational_regression_replay_passed",
        "integration_security_regression_complete",
    ):
        _require(regression.get(key) is True, f"S6-08 regression prerequisite missing: {key}")
    for key in (
        "provider_calls_performed",
        "live_resources_created",
        "production_state_mutated",
        "production_deployment_performed",
        "provider_specific_security_certification_complete",
        "independent_penetration_test_or_security_signoff_complete",
    ):
        _require(regression.get(key) is False, f"S6-08 regression boundary drifted: {key}")

    provider = s6_08_current_truth.get("provider") or {}
    _require(provider.get("selection_status") == "UNSELECTED", "provider must remain UNSELECTED")
    _require(provider.get("provider_specific_activation_authorized") is False, "provider activation was prematurely authorized")
    _require(provider.get("live_resource_creation_authorized") is False, "live resource creation was prematurely authorized")
    deployment = s6_08_current_truth.get("deployment") or {}
    _require(deployment.get("production_deployment_authorized") is False, "production deployment was prematurely authorized")
    _require(deployment.get("production_deployment_performed") is False, "production deployment was unexpectedly performed")
    stage7 = s6_08_current_truth.get("stage7") or {}
    _require(stage7 == {"entry_authorized": False, "preview_release_authorized": False, "started": False}, "Stage 7 boundary drifted")

    assertions = s6_08_current_truth.get("assertions") or {}
    _require(assertions.get("historical_evidence_immutable") is True, "historical evidence immutability must remain true")
    for key in (
        "real_or_derivative_bytes_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "raw_secrets_or_key_material_in_ordinary_git",
        "provider_selection_finalized",
        "live_resource_creation_authorized",
        "production_state_mutation_authorized",
        "production_operational_drills_authorized",
        "production_deployment_authorized",
        "production_load_or_soak_tests_authorized",
        "production_penetration_test_authorized",
        "production_concurrency_targets_or_failure_budgets_established",
        "threshold_changes_authorized",
        "resource_limit_changes_authorized",
        "held_out_retuning_authorized",
        "model_training_authorized",
        "publication_authorized",
        "stage7_entry_authorized",
        "color_management_validated",
        "color_fidelity_certified",
        "temporary_pr154_merge_authorized",
    ):
        _require(assertions.get(key) is False, f"unsafe S6-08 assertion before final exit: {key}")

    required_equal = {
        "schemaVersion": SCHEMA_VERSION,
        "acceptanceId": ACCEPTANCE_ID,
        "decision": ACCEPTANCE_DECISION,
        "acceptedOn": ACCEPTED_ON,
        "decisionAuthorityReference": AUTHORITY_REFERENCE,
        "acceptanceSourceCode": ACCEPTANCE_SOURCE,
        "acceptedPurpose": "stage7-entry-eligibility-only",
        "stage6ExitPass": True,
        "stage7EntryEligible": True,
        "stage7EntryAuthorized": False,
        "stage7Started": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }
    for key, expected in required_equal.items():
        _require(acceptance.get(key) == expected, f"{key} must equal {expected!r}")

    expected_entry = {
        "mainSha": ENTRY_MAIN_SHA,
        "s6_08AuthorizationDigest": S6_08_AUTHORIZATION_DIGEST,
        "s6_08CurrentTruthPath": S6_08_CURRENT_TRUTH_PATH,
        "s6_08CurrentTruthGitBlobSha1": S6_08_CURRENT_TRUTH_GIT_BLOB_SHA1,
        "repositoryValidationRunId": 34051744861,
        "repositoryValidationRunNumber": 481,
        "stage4GovernanceRunId": 34051744885,
        "stage4GovernanceRunNumber": 92,
        "stage5GovernanceRunId": 34051744870,
        "stage5GovernanceRunNumber": 84,
        "stage6GovernanceRunId": 34051744866,
        "stage6GovernanceRunNumber": 43,
        "ciStatus": "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows",
    }
    _require(dict(acceptance.get("entryCheckpoint") or {}) == expected_entry, "Stage 6 final entry checkpoint drifted")

    readiness = acceptance.get("acceptedReadinessState") or {}
    _require(readiness.get("decision") == "STAGE6_COMPLETE_PASS_PROVIDER_NEUTRAL", "unexpected Stage 6 readiness decision")
    _require(readiness.get("readinessPrerequisitesSatisfied") is True, "Stage 6 readiness prerequisites must be satisfied")
    _require(readiness.get("blockerCount") == 0 and readiness.get("blockerCodes") == [], "Stage 6 final exit cannot retain Stage-6 blockers")
    for key in (
        "productionIdentityContractImplemented",
        "productionSecretsKmsIamContractImplemented",
        "productionNetworkSecurityContractImplemented",
        "productionStorageDeploymentContractsImplemented",
        "syntheticOperationalDrillsComplete",
        "integrationSecurityRegressionComplete",
        "failClosedSecurityBoundariesVerified",
        "providerNeutralStage6DeliverableComplete",
    ):
        _require(readiness.get(key) is True, f"Stage 6 final readiness assertion missing: {key}")
    _require(readiness.get("providerSelectionStatus") == "UNSELECTED", "final exit must preserve provider UNSELECTED")
    for key in (
        "providerSpecificAdaptersActivated",
        "liveProductionResourcesCreated",
        "productionDistributedStressValidationComplete",
        "productionLoadOrSoakValidated",
        "independentPenetrationTestOrSecuritySignoffComplete",
        "productionOperationalDrillsComplete",
        "productionDeploymentPerformed",
    ):
        _require(readiness.get(key) is False, f"Stage 6 final exit over-claims: {key}")

    limitations = acceptance.get("acceptedLimitations")
    _require(isinstance(limitations, list) and len(limitations) >= 5, "Stage 6 accepted limitations are incomplete")
    joined = " ".join(str(item) for item in limitations)
    for phrase in (
        "provider-neutral",
        "UNSELECTED",
        "Production distributed stress/load/soak validation",
        "does not authorize Stage 7",
        "colorManagementValidated",
    ):
        _require(phrase in joined, f"Stage 6 accepted limitations lost boundary: {phrase}")

    claims = acceptance.get("claims") or {}
    expected_claims = {
        "productionDeploymentAuthorized",
        "productionDeploymentPerformed",
        "providerSelectionFinalized",
        "providerSpecificActivationAuthorized",
        "liveResourceCreationAuthorized",
        "productionOperationalDrillsAuthorized",
        "productionLoadOrSoakAuthorized",
        "productionPenetrationTestAuthorized",
        "previewReleaseAuthorized",
        "stage7EntryAuthorized",
        "productionThresholdChangesAuthorized",
        "productionResourceLimitChangesAuthorized",
        "heldOutRetuningAuthorized",
        "modelTrainingAuthorized",
        "publicationAuthorized",
        "colorManagementValidated",
        "colorFidelityCertified",
        "omrCorrectnessEstablished",
        "restorationEffectivenessEstablished",
        "productionAvailabilityOrScalabilityEstablished",
        "providerSpecificSecurityCertified",
    }
    _require(set(claims) == expected_claims, "Stage 6 final claims fields drifted")
    for key in expected_claims:
        _require(claims.get(key) is False, f"Stage 6 final acceptance contains unauthorized claim: {key}")

    _require(canonical_sha256(acceptance) == EXPECTED_ACCEPTANCE_SHA256, "Stage 6 final acceptance canonical digest changed")
    return {
        "stage6State": "COMPLETE_PASS_PROVIDER_NEUTRAL",
        "stage6ExitPass": True,
        "stage7EntryEligible": True,
        "stage7EntryAuthorized": False,
        "stage7Started": False,
        "providerSelectionStatus": "UNSELECTED",
        "productionDeploymentAuthorized": False,
        "acceptanceDigest": EXPECTED_ACCEPTANCE_SHA256,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "ACCEPTANCE_ID",
    "EXPECTED_ACCEPTANCE_SHA256",
    "NEXT_SAFE_BOUNDARY",
    "S6_08_CURRENT_TRUTH_GIT_BLOB_SHA1",
    "Stage6FinalExitError",
    "canonical_sha256",
    "git_blob_sha1",
    "validate_stage6_final_exit",
]
