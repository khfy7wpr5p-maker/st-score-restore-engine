"""Fail-closed validator for Stage 11 V2a synthetic consumer integration truth."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .stage11_v2a_consumer_adapter import (
    CONTRACT_ID,
    EXPECTED_PACKAGE_SHA256,
    EXPECTED_PACKAGE_SIZE_BYTES,
)

ARTIFACT_TYPE = "stage11_v2a_consumer_adapter_current_truth"
SCHEMA_VERSION = "1.0.0"
EXPECTED_STATE = "SYNTHETIC_CONSUMER_INTEGRATION_PASS"
EXPECTED_BASE_MAIN_SHA = "1ef01bc74f5248c774b92ab3ebef2a7fea697a83"
EXPECTED_BRANCH = "stage11-v2a-consumer-adapter-validation"
EXPECTED_CHECKPOINT_SHA256 = "15afc73233c91a80a7ef1285cb631d5d3acd681e9cfed9a93b35642bf39fff4c"
EXPECTED_DRIVE_FOLDER_ID = "1oBL1P_6slQ0j5aOguCLzJYIKAgQXnCXL"
EXPECTED_DRIVE_EVIDENCE_ID = "1cznegKPNxAN0xrByg9T4FVCatwkHBgSf"
EXPECTED_DRIVE_PACKAGE_ID = "1oJ9lOEpq7trDD8XZpVwCzQzMQ2mk-wWD"


class Stage11V2aConsumerAdapterCurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aConsumerAdapterCurrentTruthError(message)


def validate_stage11_v2a_consumer_adapter_current_truth(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == ARTIFACT_TYPE, "artifact type mismatch")
    _require(payload.get("schemaVersion") == SCHEMA_VERSION, "schema version mismatch")
    _require(payload.get("state") == EXPECTED_STATE, "unexpected consumer adapter state")
    _require(payload.get("baseMainSha") == EXPECTED_BASE_MAIN_SHA, "base main SHA mismatch")
    _require(payload.get("implementationBranch") == EXPECTED_BRANCH, "implementation branch mismatch")

    candidate = payload.get("candidate") or {}
    _require(candidate.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "candidate package SHA mismatch")
    _require(int(candidate.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "candidate package size mismatch")
    _require(candidate.get("packageFormat") == "torchscript-trace", "candidate package format mismatch")
    _require(candidate.get("checkpointSha256") == EXPECTED_CHECKPOINT_SHA256, "candidate checkpoint mismatch")
    _require(candidate.get("frozen") is True, "candidate must remain frozen")

    adapter = payload.get("adapter") or {}
    _require(adapter.get("contractId") == CONTRACT_ID, "consumer adapter contract mismatch")
    _require(adapter.get("input") == "2-D grayscale uint8 or float", "consumer input contract mismatch")
    _require(adapter.get("floatRange") == [0.0, 1.0], "float input range mismatch")
    _require(adapter.get("uint8Range") == [0, 255], "uint8 input range mismatch")
    _require(int(adapter.get("patchSize", 0)) == 512, "patch size mismatch")
    _require(int(adapter.get("overlap", -1)) == 64, "overlap mismatch")
    _require(int(adapter.get("stride", 0)) == 448, "stride mismatch")
    _require(float(adapter.get("paddingValue", -1.0)) == 1.0, "padding value mismatch")
    _require(adapter.get("overlapMerge") == "arithmetic-mean", "overlap merge mismatch")
    _require(adapter.get("outputShapePreserved") is True, "output shape preservation required")
    _require(adapter.get("outputRange") == [0.0, 1.0], "output range mismatch")

    execution = payload.get("execution") or {}
    _require(execution.get("completed") is True, "consumer adapter execution must be completed")
    _require(execution.get("sourceDataKind") == "synthetic_only", "consumer adapter source must be synthetic only")
    _require(float(execution.get("repeatMaxAbsDiff", 1.0)) == 0.0, "repeat evidence mismatch")
    _require(float(execution.get("direct512ParityMaxAbsDiff", 1.0)) == 0.0, "direct 512 parity evidence mismatch")
    _require(execution.get("evidenceRepoPath") == "evidence/stage11/v2a/v2a-consumer-adapter-evidence.v1.json", "evidence repo path mismatch")
    _require(execution.get("driveFolderId") == EXPECTED_DRIVE_FOLDER_ID, "Drive folder custody mismatch")
    _require(execution.get("driveEvidenceFileId") == EXPECTED_DRIVE_EVIDENCE_ID, "Drive evidence custody mismatch")
    _require(execution.get("drivePackageFileId") == EXPECTED_DRIVE_PACKAGE_ID, "Drive package custody mismatch")
    cases = execution.get("cases")
    _require(isinstance(cases, list) and len(cases) == 3, "three synthetic execution cases required")

    safety = payload.get("safety") or {}
    for key in (
        "consumedHeldoutRetuningForbidden",
        "privateStudentUserDataForbidden",
        "syntheticInputsOnly",
    ):
        _require(safety.get(key) is True, f"required safety assertion missing: {key}")
    for key in ("heldOutAccessed", "optimizerCreated", "backpropagationExecuted", "weightsMutated"):
        _require(safety.get(key) is False, f"unsafe execution flag must remain false: {key}")

    authorization = payload.get("authorization") or {}
    _require(authorization.get("developmentConsumerIntegrationValidationAuthorized") is True, "development consumer validation authorization missing")
    for key in (
        "productionInferenceAuthorized",
        "productionPromotionAuthorized",
        "finalProductionModelSelectionAuthorized",
        "stage12EntryAuthorized",
    ):
        _require(authorization.get(key) is False, f"authorization must remain false: {key}")

    next_boundary = str(payload.get("nextSafeBoundary") or "")
    _require("staging-only API" in next_boundary, "next safe boundary must remain staging-only")
    _require("Stage 12 remain closed" in next_boundary, "Stage 12 closure must remain explicit")

    return {
        "state": EXPECTED_STATE,
        "syntheticConsumerIntegrationPassed": True,
        "candidatePackageFrozen": True,
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
        "nextBoundary": "staging-only-api-adapter",
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_stage11_v2a_consumer_adapter_current_truth(payload)
