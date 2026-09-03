"""Fail-closed Stage 5 framework/start and local implementation authorization."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256

SCHEMA_VERSION = "1.0.0"
AUTHORIZATION_ID = "stage5.framework-start-authorization.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_STAGE5_FRAMEWORK_START_AND_LOCAL_IMPLEMENTATION_EXECUTION"
AUTHORIZED_ON = "2026-09-03"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260903-10"
AUTHORIZATION_SOURCE_CODE = "explicit_user_authorization"
ENTRY_AUTHORIZATION_DIGEST = "8d1ba1859dac429548d95a6a232e8d59cca1ff3df192ec8cc409c2e6183d1f9c"
ENTRY_PRODUCTION_MAIN_SHA = "0423f523eafa97073a34f35946dfd4c29f1e8766"
AUTHORIZATION_CANONICAL_SHA256 = "3fd05edf58e4a3a6215ffbecc796a0f436cd145875c1e8c06e3a26e87496e608"
STAGE5_PURPOSE = "accessible_teacher_review_interface"
NEXT_SAFE_BOUNDARY = "stage5_browser_ui_implementation_and_local_qa"


class Stage5StartAuthorizationError(ValueError):
    """Stage 5 start authorization is malformed, stale, or over-authorizing."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage5StartAuthorizationError(message)


def validate_stage5_start_authorization(
    raw: Mapping[str, Any],
    entry_authorization_raw: Mapping[str, Any],
    entry_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    _require(
        canonical_sha256(entry_authorization_raw) == ENTRY_AUTHORIZATION_DIGEST,
        "Stage 5 entry authorization canonical digest drifted",
    )
    _require(entry_authorization_raw.get("decision") == "AUTHORIZE_STAGE5_ENTRY", "Stage 5 entry authorization missing")
    entry_scope = entry_authorization_raw.get("scope", {})
    _require(entry_scope.get("stage5EntryAuthorized") is True, "Stage 5 entry authorization flag missing")
    _require(entry_scope.get("stage5Started") is False, "historical Stage 5 entry authorization was rewritten")

    stage4 = entry_current_truth_raw.get("stage4", {})
    stage5 = entry_current_truth_raw.get("stage5", {})
    assertions = entry_current_truth_raw.get("assertions", {})
    _require(stage4.get("state") == "COMPLETE_PASS", "Stage 4 current truth is not COMPLETE_PASS")
    _require(stage4.get("exit_pass") is True, "Stage 4 current truth PASS missing")
    _require(stage5.get("entry_eligible") is True, "Stage 5 is not entry-eligible")
    _require(stage5.get("entry_authorized") is True, "Stage 5 entry is not authorized")
    _require(stage5.get("started") is False, "historical entry current truth was rewritten to start Stage 5")
    _require(assertions.get("historical_evidence_immutable") is True, "historical evidence immutability missing")
    _require(assertions.get("production_threshold_changes_authorized") is False, "production threshold change unexpectedly authorized")
    _require(assertions.get("production_resource_limit_changes_authorized") is False, "production resource change unexpectedly authorized")
    _require(assertions.get("held_out_retuning_authorized") is False, "held-out retuning unexpectedly authorized")

    _require(isinstance(raw, Mapping), "Stage 5 start authorization must be an object")
    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schemaVersion",
            "authorizationId",
            "decision",
            "authorizedOn",
            "decisionAuthorityReference",
            "authorizationSourceCode",
            "stage5EntryAuthorizationDigest",
            "stage5EntryProductionCheckpoint",
            "stage5Purpose",
            "scope",
            "safetyBoundaries",
            "nextSafeBoundary",
        },
        "Stage 5 start authorization top-level fields drifted",
    )
    _require(value["schemaVersion"] == SCHEMA_VERSION, "authorization schema drifted")
    _require(value["authorizationId"] == AUTHORIZATION_ID, "authorization id drifted")
    _require(value["decision"] == AUTHORIZATION_DECISION, "authorization decision drifted")
    _require(value["authorizedOn"] == AUTHORIZED_ON, "authorization date drifted")
    _require(value["decisionAuthorityReference"] == DECISION_AUTHORITY_REFERENCE, "decision authority drifted")
    _require(value["authorizationSourceCode"] == AUTHORIZATION_SOURCE_CODE, "authorization source drifted")
    _require(
        value["stage5EntryAuthorizationDigest"] == {"algorithm": "sha256", "value": ENTRY_AUTHORIZATION_DIGEST},
        "Stage 5 entry authorization binding drifted",
    )
    _require(
        value["stage5EntryProductionCheckpoint"] == {
            "mainSha": ENTRY_PRODUCTION_MAIN_SHA,
            "entryAuthorized": True,
            "repositoryValidationRunNumber": 401,
            "stage4GovernanceRunNumber": 12,
            "stage5GovernanceRunNumber": 4,
            "python311": "success",
            "python312": "success",
        },
        "Stage 5 entry production checkpoint drifted",
    )
    _require(value["stage5Purpose"] == STAGE5_PURPOSE, "Stage 5 purpose drifted")
    _require(
        value["scope"] == {
            "stage5EntryEligible": True,
            "stage5EntryAuthorized": True,
            "stage5FrameworkAuthorized": True,
            "stage5Started": True,
            "teacherReviewInterfaceImplementationAuthorized": True,
            "teacherReviewInterfaceExecutionAuthorized": True,
            "localAccessibilityVerificationAuthorized": True,
            "localDisplayQaAuthorized": True,
            "productionDeploymentAuthorized": False,
            "identityNetworkInfrastructureAuthorized": False,
            "previewReleaseAuthorized": False,
            "productionThresholdChangesAuthorized": False,
            "productionResourceLimitChangesAuthorized": False,
            "heldOutRetuningAuthorized": False,
            "modelTrainingAuthorized": False,
            "publicationAuthorized": False,
        },
        "Stage 5 start scope drifted or over-authorized",
    )
    _require(
        value["safetyBoundaries"] == {
            "historicalEvidenceImmutable": True,
            "realOrDerivativeBytesInOrdinaryGit": False,
            "rawPrivateMetricsInOrdinaryGit": False,
            "stage4FinalPassMustRemainTrue": True,
            "productionDeploymentRequiresSeparateAuthorization": True,
            "stage6EntryAuthorized": False,
        },
        "Stage 5 start safety boundaries drifted",
    )
    _require(value["nextSafeBoundary"] == NEXT_SAFE_BOUNDARY, "next safe boundary drifted")
    _require(canonical_sha256(value) == AUTHORIZATION_CANONICAL_SHA256, "Stage 5 start authorization canonical digest drifted")
    return value


def summarize_stage5_start_authorization(
    raw: Mapping[str, Any],
    entry_authorization_raw: Mapping[str, Any],
    entry_current_truth_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_stage5_start_authorization(raw, entry_authorization_raw, entry_current_truth_raw)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "decision": AUTHORIZATION_DECISION,
        "authorizationDigest": {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "stage5EntryAuthorized": True,
        "stage5FrameworkAuthorized": True,
        "stage5Started": True,
        "teacherReviewInterfaceImplementationAuthorized": True,
        "teacherReviewInterfaceExecutionAuthorized": True,
        "productionDeploymentAuthorized": False,
        "stage6EntryAuthorized": False,
        "nextSafeBoundary": NEXT_SAFE_BOUNDARY,
    }


__all__ = [
    "AUTHORIZATION_CANONICAL_SHA256",
    "AUTHORIZATION_DECISION",
    "AUTHORIZATION_ID",
    "AUTHORIZED_ON",
    "DECISION_AUTHORITY_REFERENCE",
    "ENTRY_AUTHORIZATION_DIGEST",
    "NEXT_SAFE_BOUNDARY",
    "SCHEMA_VERSION",
    "STAGE5_PURPOSE",
    "Stage5StartAuthorizationError",
    "summarize_stage5_start_authorization",
    "validate_stage5_start_authorization",
]
