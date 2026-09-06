"""Fail-closed Stage 8 final-exit acceptance validation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .docres_optional_candidate import run_synthetic_docres_candidate_drills
from .stage8_entry_authorization import validate_stage8_entry_authorization

SCHEMA_VERSION = "1.0.0"
ACCEPTANCE_ID = "stage8.final-exit-acceptance.v1"
ACCEPTANCE_DECISION = "PASS"
ACCEPTED_ON = "2026-09-06"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260906-stage8-final-exit-01"
ACCEPTANCE_SOURCE_CODE = "explicit_user_authorization"
ACCEPTANCE_CANONICAL_SHA256 = "dae574d1ab8e56df8b5b2350d20e1caf7383f939fd52fe9c21e4ab242b1bb94f"
READINESS_DECISION = "STAGE8_COMPLETE_PASS_DOCRES_OPTIONAL_CANDIDATE_CONTRACT"
NEXT_SAFE_BOUNDARY = "separate_exact_docres_dependency_model_runtime_approval_or_stage9_entry_authorization"


class Stage8FinalExitError(ValueError):
    """Stage 8 final exit is malformed, unsupported, or over-claims readiness."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage8FinalExitError(message)


def _validate_docres_contract(contract: Mapping[str, Any]) -> None:
    _require(contract.get("schemaVersion") == "1.0.0", "DocRes contract schema drifted")
    _require(contract.get("contractVersion") == "stage8.docres-optional-candidate.v1", "DocRes contract version drifted")
    _require(contract.get("engineRole") == "optional_restoration_candidate", "DocRes engine role drifted")
    _require(contract.get("engineName") == "docres", "DocRes engine name drifted")
    _require(contract.get("adapterProfile") == "disabled-by-default", "DocRes adapter is not disabled-by-default")
    runtime = contract.get("runtime", {})
    _require(runtime.get("dependencyStatus") == "UNAPPROVED", "DocRes dependency was silently approved")
    _require(runtime.get("modelArtifactStatus") == "UNAPPROVED", "DocRes model artifact was silently approved")
    for field in ("externalPackageInstallationAuthorized", "networkFetchAuthorized", "liveRuntimeActivationAuthorized"):
        _require(runtime.get(field) is False, f"{field} unexpectedly authorized")
    _require(runtime.get("syntheticExecutionAuthorized") is True, "synthetic execution proof missing")
    source = contract.get("sourceBoundary", {})
    for field in ("sourceArtifactImmutable", "sourceOverwriteForbidden", "derivedCandidateRequiresProvenance", "originalFallbackRequired"):
        _require(source.get(field) is True, f"source boundary {field} missing")
    handoff = contract.get("safetyHandoff", {})
    _require(handoff.get("musicSafetyValidationRequired") is True, "Music Safety handoff missing")
    _require(handoff.get("hardRejectRoute") == "original", "hard reject must route to original")
    _require(handoff.get("reviewRequiredRoute") == "review", "review-required route drifted")
    _require(handoff.get("unknownVerdictRoute") == "review", "unknown verdict must route to review")
    _require(handoff.get("passRoute") == "validated_candidate_hold", "pass route drifted")
    _require(handoff.get("stage9ComparatorSelectionAuthorized") is False, "Stage 9 comparator was silently authorized")
    _require(handoff.get("automaticFinalSelectionAuthorized") is False, "automatic final selection was silently authorized")
    for value in contract.get("claims", {}).values():
        _require(value is False, "unsupported DocRes claim became true")
    excluded = contract.get("excludedScope", {})
    for field in (
        "realUserDocresCohort", "liveDocresRuntime", "externalModelDownload", "productionDeployment",
        "productionLoadSoak", "productionPenetrationTesting", "thresholdChanges", "resourceLimitChanges",
        "heldOutRetuning", "modelTraining", "modelPublication", "stage9Entry",
    ):
        _require(excluded.get(field) is True, f"excluded scope {field} drifted")


def validate_stage8_final_exit(
    raw: Mapping[str, Any],
    stage8_authorization_raw: Mapping[str, Any],
    stage7_final_current_truth_raw: Mapping[str, Any],
    docres_contract_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage8_entry_authorization(stage8_authorization_raw, stage7_final_current_truth_raw)
    _validate_docres_contract(docres_contract_raw)
    drill = run_synthetic_docres_candidate_drills()
    _require(drill.get("result") == "PASS", "Stage 8 synthetic DocRes drills did not PASS")
    _require(drill.get("liveDocresRuntimeActivated") is False, "live DocRes runtime was activated")
    _require(drill.get("stage9ComparatorSelectionPerformed") is False, "Stage 9 comparator selection was performed")

    _require(isinstance(raw, Mapping), "Stage 8 final-exit acceptance must be an object")
    value = deepcopy(dict(raw))
    _require(value.get("schemaVersion") == SCHEMA_VERSION, "acceptance schema drifted")
    _require(value.get("acceptanceId") == ACCEPTANCE_ID, "acceptance id drifted")
    _require(value.get("decision") == ACCEPTANCE_DECISION, "acceptance decision drifted")
    _require(value.get("acceptedOn") == ACCEPTED_ON, "acceptance date drifted")
    _require(value.get("decisionAuthorityReference") == DECISION_AUTHORITY_REFERENCE, "decision authority drifted")
    _require(value.get("acceptanceSourceCode") == ACCEPTANCE_SOURCE_CODE, "acceptance source drifted")

    checkpoint = value.get("entryCheckpoint", {})
    expected_checkpoint = {
        "mainSha": "0d85d18053a84648902f3b5fd9147782bf4c28b4",
        "stage8AuthorizationDigest": "3a43c86e07e3075a00c68b0b81792a3ba40ce0e284c02464a56f2ac731253465",
        "stage8AuthorizationGitBlobSha1": "2ed284fe68dc1e55731f478c3f6c917cfb0037aa",
        "docresContractPath": "api/stage8-docres-candidate-contract.v1.json",
        "docresContractGitBlobSha1": "47824d168cd55fb3b2059afa076205df9115a129",
        "pr179HeadSha": "065b1ba4917bad097faa7515376a0f76ab8963b3",
        "pr179RepositoryValidationRunId": 34055538744,
        "pr179RepositoryValidationRunNumber": 492,
        "pr179Stage4GovernanceRunId": 34055538732,
        "pr179Stage4GovernanceRunNumber": 103,
        "pr179Stage5GovernanceRunId": 34055538731,
        "pr179Stage5GovernanceRunNumber": 95,
        "pr179Stage6GovernanceRunId": 34055538717,
        "pr179Stage6GovernanceRunNumber": 54,
        "pr179Stage7GovernanceRunId": 34055538734,
        "pr179Stage7GovernanceRunNumber": 7,
        "pr179Stage8GovernanceRunId": 34055538746,
        "pr179Stage8GovernanceRunNumber": 1,
        "postMergeRepositoryValidationRunId": 34055597755,
        "postMergeRepositoryValidationRunNumber": 493,
        "postMergeStage4GovernanceRunId": 34055597822,
        "postMergeStage4GovernanceRunNumber": 104,
        "postMergeStage5GovernanceRunId": 34055597768,
        "postMergeStage5GovernanceRunNumber": 96,
        "postMergeStage6GovernanceRunId": 34055597770,
        "postMergeStage6GovernanceRunNumber": 55,
        "postMergeStage7GovernanceRunId": 34055597766,
        "postMergeStage7GovernanceRunNumber": 8,
        "postMergeStage8GovernanceRunId": 34055597771,
        "postMergeStage8GovernanceRunNumber": 2,
        "ciStatus": "success_python_3_11_and_3_12_for_repository_stage4_stage5_stage6_stage7_and_stage8_exact_head_and_post_merge",
    }
    _require(checkpoint == expected_checkpoint, "Stage 8 CI/evidence checkpoint drifted")

    readiness = value.get("acceptedReadinessState", {})
    _require(readiness.get("decision") == READINESS_DECISION, "Stage 8 readiness decision drifted")
    _require(readiness.get("readinessPrerequisitesSatisfied") is True, "readiness prerequisites missing")
    _require(readiness.get("blockerCount") == 0 and readiness.get("blockerCodes") == [], "unexpected Stage 8 blocker")
    for field in (
        "optionalCandidateContractImplemented", "disabledByDefaultAdapterImplemented", "immutableSourceBoundaryImplemented",
        "provenanceBoundaryImplemented", "musicSafetyHandoffImplemented", "syntheticDocresCandidateDrillsComplete",
        "providerNeutralStage8DeliverableComplete",
    ):
        _require(readiness.get(field) is True, f"readiness proof {field} missing")
    _require(readiness.get("dependencyStatus") == "UNAPPROVED", "dependency status over-claimed")
    _require(readiness.get("modelArtifactStatus") == "UNAPPROVED", "model artifact status over-claimed")
    for field in (
        "externalPackageInstallationAuthorized", "modelArtifactDownloadAuthorized", "modelWeightsUseAuthorized",
        "networkFetchAuthorized", "liveDocresRuntimeActivationAuthorized", "realUserDocresCohortAuthorized",
        "providerSpecificActivationAuthorized", "liveResourceCreationAuthorized", "productionDeploymentAuthorized",
        "productionDeploymentPerformed", "productionLoadOrSoakValidated",
        "independentPenetrationTestOrSecuritySignoffComplete", "stage9ComparatorSelectionAuthorized",
    ):
        _require(readiness.get(field) is False, f"{field} unexpectedly true")

    _require(value.get("acceptedPurpose") == "stage9-entry-eligibility-only", "accepted purpose drifted")
    _require(value.get("stage8ExitPass") is True, "Stage 8 exit PASS missing")
    _require(value.get("stage9EntryEligible") is True, "Stage 9 entry eligibility missing")
    _require(value.get("stage9EntryAuthorized") is False, "Stage 9 entry unexpectedly authorized")
    _require(value.get("stage9Started") is False, "Stage 9 unexpectedly started")
    for field, claim in value.get("claims", {}).items():
        _require(claim is False, f"unsupported claim {field} became true")
    _require(value.get("nextSafeBoundary") == NEXT_SAFE_BOUNDARY, "next safe boundary drifted")
    _require(canonical_sha256(value) == ACCEPTANCE_CANONICAL_SHA256, "Stage 8 final-exit acceptance digest drifted")
    return value


def summarize_stage8_final_exit(
    raw: Mapping[str, Any],
    stage8_authorization_raw: Mapping[str, Any],
    stage7_final_current_truth_raw: Mapping[str, Any],
    docres_contract_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage8_final_exit(raw, stage8_authorization_raw, stage7_final_current_truth_raw, docres_contract_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "decision": "PASS",
        "readinessState": READINESS_DECISION,
        "acceptanceDigest": {"algorithm": "sha256", "value": ACCEPTANCE_CANONICAL_SHA256},
        "stage8ExitPass": True,
        "stage9EntryEligible": True,
        "stage9EntryAuthorized": False,
        "docresRuntimeDependencyApproved": False,
        "liveDocresRuntimeActivationAuthorized": False,
        "stage9ComparatorSelectionAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "ACCEPTANCE_CANONICAL_SHA256",
    "READINESS_DECISION",
    "Stage8FinalExitError",
    "summarize_stage8_final_exit",
    "validate_stage8_final_exit",
]
