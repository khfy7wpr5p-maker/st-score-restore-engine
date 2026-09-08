"""Fail-closed current truth for the Stage 11 V2a non-held-out shadow-corpus observation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .stage11_v2a_shadow_corpus import (
    CONTRACT_ID,
    EXPECTED_PACKAGE_SHA256,
    EXPECTED_PACKAGE_SIZE_BYTES,
    FIRST_REAL_DATASET_ITEM_ID,
    FIRST_REAL_SOURCE_FAMILY_ID,
    shadow_corpus_contract,
    validate_shadow_corpus_execution_evidence,
)

ARTIFACT_TYPE = "stage11_v2a_shadow_corpus_current_truth"
SCHEMA_VERSION = "1.0.0"
EXPECTED_STATE = "NONHELDOUT_SHADOW_CORPUS_OBSERVED"
EXPECTED_BASE_MAIN_SHA = "fd9f382c6130e4edb5b872b016da5e30081241ff"
EXPECTED_BRANCH = "stage11-v2a-nonheldout-shadow-corpus"
EXPECTED_EVIDENCE_PATH = "evidence/stage11/v2a/v2a-shadow-corpus-evidence.v1.json"
EXPECTED_NEXT_BOUNDARY = "broaden-nonheldout-shadow-corpus-source-family-coverage"


class Stage11V2aShadowCorpusCurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aShadowCorpusCurrentTruthError(message)


def validate_stage11_v2a_shadow_corpus_current_truth(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == ARTIFACT_TYPE, "shadow corpus truth artifact type mismatch")
    _require(payload.get("schemaVersion") == SCHEMA_VERSION, "shadow corpus truth schema mismatch")
    _require(payload.get("state") == EXPECTED_STATE, "shadow corpus truth state mismatch")
    _require(payload.get("baseMainSha") == EXPECTED_BASE_MAIN_SHA, "shadow corpus truth base main mismatch")
    _require(payload.get("implementationBranch") == EXPECTED_BRANCH, "shadow corpus truth branch mismatch")
    _require(payload.get("contractId") == CONTRACT_ID, "shadow corpus truth contract mismatch")
    _require(payload.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "shadow corpus truth package mismatch")
    _require(int(payload.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "shadow corpus truth package size mismatch")
    _require(payload.get("evidenceRepoPath") == EXPECTED_EVIDENCE_PATH, "shadow corpus truth evidence path mismatch")
    _require(payload.get("nextSafeBoundary") == EXPECTED_NEXT_BOUNDARY, "shadow corpus truth next boundary mismatch")
    _require(payload.get("contract") == shadow_corpus_contract(), "shadow corpus truth contract snapshot mismatch")

    execution = payload.get("execution") or {}
    _require(execution.get("completed") is True, "shadow corpus execution must be completed")
    _require(execution.get("sourceDataKind") == "nonheldout_test_only", "shadow corpus truth source kind mismatch")
    _require(execution.get("datasetItemId") == FIRST_REAL_DATASET_ITEM_ID, "shadow corpus truth dataset item mismatch")
    _require(execution.get("sourceFamilyId") == FIRST_REAL_SOURCE_FAMILY_ID, "shadow corpus truth source family mismatch")
    _require(execution.get("split") == "development", "shadow corpus truth must remain development-only")
    _require(int(execution.get("pageObservationCount", 0)) == 4, "shadow corpus truth page count mismatch")
    _require(int(execution.get("sourceFamilyCount", 0)) == 1, "shadow corpus truth source-family count mismatch")
    _require(execution.get("qualityDecisionMade") is False, "shadow corpus truth cannot make quality decisions")
    _require(execution.get("automaticPromotionPerformed") is False, "shadow corpus truth cannot promote")

    implementation = payload.get("implementation") or {}
    for key in (
        "developmentOpenCorpusEligibilityGateReady",
        "heldOutFailClosedReady",
        "exactSourceIdentityGateReady",
        "rasterOnlyPdfTransportReady",
        "shapeLockedOpenCvComparatorReady",
        "exactFrozenV2aObserverReady",
        "observationalMetricsReady",
        "committedRealExecutionEvidenceReady",
        "repositoryValidationReady",
    ):
        _require(implementation.get(key) is True, f"shadow corpus truth implementation flag missing: {key}")

    safety = payload.get("safety") or {}
    for key in (
        "heldOutAccessForbidden",
        "trainingForbidden",
        "tuningForbidden",
        "optimizerForbidden",
        "backpropagationForbidden",
        "weightMutationForbidden",
        "privateStudentUserDataForbidden",
        "shadowSelectionForbidden",
        "automaticPromotionForbidden",
        "productionInferenceForbidden",
        "stage12EntryForbidden",
    ):
        _require(safety.get(key) is True, f"shadow corpus truth safety assertion missing: {key}")

    authorization = payload.get("authorization") or {}
    _require(authorization.get("shadowCorpusObservationAuthorized") is True, "shadow corpus observation authorization missing")
    for key in (
        "trainingAuthorized",
        "tuningAuthorized",
        "productionInferenceAuthorized",
        "productionPromotionAuthorized",
        "realUserRolloutAuthorized",
        "finalProductionModelSelectionAuthorized",
        "stage12EntryAuthorized",
    ):
        _require(authorization.get(key) is False, f"shadow corpus truth authorization must remain false: {key}")

    return {
        "state": EXPECTED_STATE,
        "realNonheldoutCorpusObserved": True,
        "pageObservationCount": 4,
        "sourceFamilyCount": 1,
        "nextSafeBoundary": EXPECTED_NEXT_BOUNDARY,
        "productionInferenceAuthorized": False,
        "realUserRolloutAuthorized": False,
        "stage12EntryAuthorized": False,
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_stage11_v2a_shadow_corpus_current_truth(payload)


def validate_truth_with_evidence(truth_path: Path, evidence_path: Path) -> dict[str, Any]:
    result = load_and_validate(truth_path)
    evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    evidence_result = validate_shadow_corpus_execution_evidence(evidence)
    _require(evidence_result["pageObservationCount"] == result["pageObservationCount"], "truth/evidence page count mismatch")
    _require(evidence_result["sourceFamilyCount"] == result["sourceFamilyCount"], "truth/evidence source family mismatch")
    return result
