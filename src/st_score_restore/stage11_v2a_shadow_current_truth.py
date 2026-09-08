"""Fail-closed current-truth validator for the Stage 11 V2a shadow job handoff."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .stage11_v2a_shadow_handoff import (
    CONTRACT_ID,
    EXPECTED_PACKAGE_SHA256,
    EXPECTED_PACKAGE_SIZE_BYTES,
    shadow_job_handoff_contract,
    validate_shadow_job_evidence,
)

ARTIFACT_TYPE = "stage11_v2a_shadow_current_truth"
SCHEMA_VERSION = "1.0.0"
EXPECTED_STATE = "SHADOW_JOB_HANDOFF_VALIDATED"
EXPECTED_BASE_MAIN_SHA = "2c50333eab663d22a817bc2b8cfa4594aa60925b"
EXPECTED_BRANCH = "stage11-v2a-shadow-job-handoff"
EXPECTED_EVIDENCE_PATH = "evidence/stage11/v2a/v2a-shadow-job-handoff-evidence.v1.json"
EXPECTED_NEXT_BOUNDARY = "approved-nonheldout-shadow-corpus-observation"


class Stage11V2aShadowCurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aShadowCurrentTruthError(message)


def validate_stage11_v2a_shadow_current_truth(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == ARTIFACT_TYPE, "shadow truth artifact type mismatch")
    _require(payload.get("schemaVersion") == SCHEMA_VERSION, "shadow truth schema mismatch")
    _require(payload.get("state") == EXPECTED_STATE, "shadow truth state mismatch")
    _require(payload.get("baseMainSha") == EXPECTED_BASE_MAIN_SHA, "shadow truth base main mismatch")
    _require(payload.get("implementationBranch") == EXPECTED_BRANCH, "shadow truth branch mismatch")
    _require(payload.get("contractId") == CONTRACT_ID, "shadow truth contract mismatch")
    _require(payload.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "shadow truth package mismatch")
    _require(int(payload.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "shadow truth package size mismatch")
    _require(payload.get("evidenceRepoPath") == EXPECTED_EVIDENCE_PATH, "shadow truth evidence path mismatch")
    _require(payload.get("nextSafeBoundary") == EXPECTED_NEXT_BOUNDARY, "shadow truth next boundary mismatch")
    _require(payload.get("contract") == shadow_job_handoff_contract(), "shadow truth contract snapshot mismatch")

    implementation = payload.get("implementation") or {}
    for key in (
        "shadowObserverReady",
        "explicitShadowJobServiceSubclassReady",
        "atomicCurrentAttemptObservationReady",
        "idempotentShadowRunKeyReady",
        "shadowArtifactsStoredWithNonPrimaryRoles",
        "shadowArtifactsUnselectable",
        "auditEventReady",
        "existingHttpApiUntouched",
        "openApiUntouched",
        "runApiUntouched",
        "repositoryTestsReady",
        "executionEvidenceImported",
    ):
        _require(implementation.get(key) is True, f"shadow truth implementation flag missing: {key}")

    execution = payload.get("execution") or {}
    _require(execution.get("exactFrozenPackageExecuted") is True, "shadow truth exact package execution missing")
    _require(execution.get("sourceDataKind") == "synthetic_only", "shadow truth acceptance execution must be synthetic-only")
    _require(execution.get("inputShape") == [700, 900], "shadow truth input shape mismatch")
    _require(int(execution.get("tileCount", 0)) == 4, "shadow truth tile count mismatch")
    _require(str(execution.get("shadowCandidateSha256") or "") == "7a3033100e433236293700673d847701960252669634a07507069ad045678c60", "shadow truth output SHA mismatch")
    _require(float(execution.get("meanAbsDiff", -1.0)) >= 0.0, "shadow truth meanAbsDiff missing")
    _require(float(execution.get("maxAbsDiff", -1.0)) >= 0.0, "shadow truth maxAbsDiff missing")
    changed = float(execution.get("changedPixelFraction", -1.0))
    _require(0.0 <= changed <= 1.0, "shadow truth changedPixelFraction invalid")
    _require(execution.get("qualityDecisionMade") is False, "shadow execution cannot make quality decisions")

    safety = payload.get("safety") or {}
    for key in (
        "checkpointWeightsImmutable",
        "optimizerForbidden",
        "backpropagationForbidden",
        "heldoutAccessForbidden",
        "privateStudentUserDataForbidden",
        "realUserDataForbidden",
        "shadowSelectionForbidden",
        "primaryCandidateReplacementForbidden",
        "safetyReportReplacementForbidden",
        "automaticPromotionForbidden",
        "networkRouteRegistrationForbidden",
    ):
        _require(safety.get(key) is True, f"shadow truth safety assertion missing: {key}")

    authorization = payload.get("authorization") or {}
    _require(authorization.get("shadowIntegrationValidationAuthorized") is True, "shadow validation authorization missing")
    for key in (
        "productionInferenceAuthorized",
        "productionPromotionAuthorized",
        "realUserRolloutAuthorized",
        "finalProductionModelSelectionAuthorized",
        "stage12EntryAuthorized",
    ):
        _require(authorization.get(key) is False, f"shadow truth authorization must remain false: {key}")

    return {
        "state": EXPECTED_STATE,
        "shadowJobHandoffValidated": True,
        "exactFrozenPackageExecuted": True,
        "existingHttpApiUntouched": True,
        "nextSafeBoundary": EXPECTED_NEXT_BOUNDARY,
        "productionInferenceAuthorized": False,
        "realUserRolloutAuthorized": False,
        "stage12EntryAuthorized": False,
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_stage11_v2a_shadow_current_truth(payload)


def validate_truth_with_evidence(truth_path: Path, evidence_path: Path) -> dict[str, Any]:
    result = load_and_validate(truth_path)
    evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    validate_shadow_job_evidence(evidence)
    _require(evidence.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "truth/evidence package mismatch")
    return result
