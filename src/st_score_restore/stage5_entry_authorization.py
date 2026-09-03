"""Fail-closed Stage 5 entry governance authorization.

This module converts the production-effective Stage 4 COMPLETE/PASS state into
Stage 5 entry authorization only. It does not start Stage 5, authorize teacher
review interface implementation or execution, alter thresholds/resource limits,
reuse held-out data for tuning, or authorize Stage 6 / release / training /
publication work.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256

SCHEMA_VERSION = "1.0.0"
AUTHORIZATION_ID = "stage5.entry-governance-authorization.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_STAGE5_ENTRY"
AUTHORIZED_ON = "2026-09-03"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260903-09"
AUTHORIZATION_SOURCE_CODE = "explicit_user_authorization"
STAGE4_FINAL_ACCEPTANCE_DIGEST = "41923c6c05c7ea015841fd77da7377aad30261a569d287246eb832f856ad599c"
STAGE4_PRODUCTION_MAIN_SHA = "1fb047a4f9314e0414063f8a75bd1526a586f2ca"
STAGE4_REPOSITORY_VALIDATION_RUN_NUMBER = 397
STAGE4_GOVERNANCE_RUN_NUMBER = 8
AUTHORIZATION_CANONICAL_SHA256 = "8d1ba1859dac429548d95a6a232e8d59cca1ff3df192ec8cc409c2e6183d1f9c"
STAGE5_PURPOSE = "accessible_teacher_review_interface"
NEXT_SAFE_BOUNDARY = "separate_explicit_stage5_framework_start_authorization"


class Stage5EntryAuthorizationError(ValueError):
    """Stage 5 entry authorization is malformed, stale, or over-authorizing."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage5EntryAuthorizationError(message)


def validate_stage5_entry_authorization(
    raw: Mapping[str, Any],
    stage4_final_acceptance_raw: Mapping[str, Any],
    stage4_final_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    _require(
        canonical_sha256(stage4_final_acceptance_raw) == STAGE4_FINAL_ACCEPTANCE_DIGEST,
        "Stage 4 final acceptance canonical digest drifted",
    )
    _require(stage4_final_acceptance_raw.get("decision") == "PASS", "Stage 4 final decision is not PASS")
    _require(stage4_final_acceptance_raw.get("stage4ExitPass") is True, "Stage 4 final PASS flag missing")
    _require(stage4_final_acceptance_raw.get("stage5EntryEligible") is True, "Stage 5 eligibility missing")
    _require(stage4_final_acceptance_raw.get("stage5EntryAuthorized") is False, "historical Stage 4 final acceptance was rewritten")
    _require(stage4_final_acceptance_raw.get("stage5Started") is False, "historical Stage 4 final acceptance was rewritten to start Stage 5")

    stage4 = stage4_final_current_truth_raw.get("stage4", {})
    stage5 = stage4_final_current_truth_raw.get("stage5", {})
    assertions = stage4_final_current_truth_raw.get("assertions", {})
    _require(stage4.get("state") == "COMPLETE_PASS", "Stage 4 current truth is not COMPLETE_PASS")
    _require(stage4.get("exit_pass") is True, "Stage 4 current truth PASS missing")
    _require(stage5.get("entry_eligible") is True, "Stage 5 current truth is not entry-eligible")
    _require(stage5.get("entry_authorized") is False, "historical Stage 4 final current truth was rewritten")
    _require(stage5.get("started") is False, "historical Stage 4 final current truth was rewritten to start Stage 5")
    _require(assertions.get("historical_evidence_immutable") is True, "historical evidence immutability missing")
    _require(assertions.get("real_or_derivative_bytes_in_ordinary_git") is False, "real/derivative bytes entered ordinary Git")
    _require(assertions.get("raw_private_metrics_in_ordinary_git") is False, "raw private metrics entered ordinary Git")
    _require(assertions.get("held_out_retuning_authorized") is False, "held-out retuning was authorized")

    _require(isinstance(raw, Mapping), "Stage 5 entry authorization must be an object")
    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schemaVersion",
            "authorizationId",
            "decision",
            "authorizedOn",
            "decisionAuthorityReference",
            "authorizationSourceCode",
            "stage4FinalAcceptanceDigest",
            "stage4ProductionCheckpoint",
            "stage5Purpose",
            "scope",
            "safetyBoundaries",
            "nextSafeBoundary",
        },
        "Stage 5 entry authorization top-level fields drifted",
    )
    _require(value["schemaVersion"] == SCHEMA_VERSION, "authorization schema drifted")
    _require(value["authorizationId"] == AUTHORIZATION_ID, "authorization id drifted")
    _require(value["decision"] == AUTHORIZATION_DECISION, "authorization decision drifted")
    _require(value["authorizedOn"] == AUTHORIZED_ON, "authorization date drifted")
    _require(value["decisionAuthorityReference"] == DECISION_AUTHORITY_REFERENCE, "decision authority drifted")
    _require(value["authorizationSourceCode"] == AUTHORIZATION_SOURCE_CODE, "authorization source drifted")
    _require(
        value["stage4FinalAcceptanceDigest"] == {"algorithm": "sha256", "value": STAGE4_FINAL_ACCEPTANCE_DIGEST},
        "Stage 4 final acceptance binding drifted",
    )
    _require(
        value["stage4ProductionCheckpoint"] == {
            "mainSha": STAGE4_PRODUCTION_MAIN_SHA,
            "finalExitPass": True,
            "repositoryValidationRunNumber": STAGE4_REPOSITORY_VALIDATION_RUN_NUMBER,
            "stage4GovernanceRunNumber": STAGE4_GOVERNANCE_RUN_NUMBER,
            "python311": "success",
            "python312": "success",
        },
        "Stage 4 production checkpoint drifted",
    )
    _require(value["stage5Purpose"] == STAGE5_PURPOSE, "Stage 5 purpose drifted")
    _require(
        value["scope"] == {
            "stage5EntryEligible": True,
            "stage5EntryAuthorized": True,
            "stage5Started": False,
            "teacherReviewInterfaceImplementationAuthorized": False,
            "teacherReviewInterfaceExecutionAuthorized": False,
            "productionDeploymentAuthorized": False,
            "identityNetworkInfrastructureAuthorized": False,
            "previewReleaseAuthorized": False,
            "productionThresholdChangesAuthorized": False,
            "productionResourceLimitChangesAuthorized": False,
            "heldOutRetuningAuthorized": False,
            "modelTrainingAuthorized": False,
            "publicationAuthorized": False,
        },
        "Stage 5 entry scope drifted or over-authorized",
    )
    _require(
        value["safetyBoundaries"] == {
            "historicalEvidenceImmutable": True,
            "realOrDerivativeBytesInOrdinaryGit": False,
            "rawPrivateMetricsInOrdinaryGit": False,
            "stage4FinalPassMustRemainTrue": True,
            "stage5StartRequiresSeparateAuthorization": True,
            "stage6EntryAuthorized": False,
        },
        "Stage 5 safety boundaries drifted",
    )
    _require(value["nextSafeBoundary"] == NEXT_SAFE_BOUNDARY, "next safe boundary drifted")
    _require(canonical_sha256(value) == AUTHORIZATION_CANONICAL_SHA256, "Stage 5 entry authorization canonical digest drifted")
    return value


def summarize_stage5_entry_authorization(
    raw: Mapping[str, Any],
    stage4_final_acceptance_raw: Mapping[str, Any],
    stage4_final_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage5_entry_authorization(raw, stage4_final_acceptance_raw, stage4_final_current_truth_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "decision": AUTHORIZATION_DECISION,
        "authorizationDigest": {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "stage4ExitPass": True,
        "stage5EntryEligible": True,
        "stage5EntryAuthorized": True,
        "stage5Started": False,
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
    "STAGE4_FINAL_ACCEPTANCE_DIGEST",
    "STAGE5_PURPOSE",
    "Stage5EntryAuthorizationError",
    "summarize_stage5_entry_authorization",
    "validate_stage5_entry_authorization",
]
