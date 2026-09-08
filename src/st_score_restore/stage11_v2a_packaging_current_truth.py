"""Fail-closed current-truth validator for Stage 11 V2a candidate packaging."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .stage11_v2a_packaging import (
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_CONFIG_SHA256,
    EXPECTED_DATASET_MD5,
    EXPECTED_MODEL_STATE_SHA256,
    EXPECTED_SOURCE_V2_CHECKPOINT_SHA256,
    PACKAGE_CONTRACT_ID,
)

ARTIFACT_TYPE = "stage11_v2a_packaging_current_truth"
SCHEMA_VERSION = "1.0.0"
EXPECTED_STATE = "IMPLEMENTATION_READY_EXECUTION_PENDING"
EXPECTED_BASE_MAIN_SHA = "775a4b2b1d542b54ee03c901109e7ad7496f6f3f"
EXPECTED_BRANCH = "stage11-v2a-candidate-packaging"


class Stage11V2aPackagingCurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aPackagingCurrentTruthError(message)


def validate_stage11_v2a_packaging_current_truth(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == ARTIFACT_TYPE, "artifact type mismatch")
    _require(payload.get("schemaVersion") == SCHEMA_VERSION, "schema version mismatch")
    _require(payload.get("baseMainSha") == EXPECTED_BASE_MAIN_SHA, "base main SHA mismatch")
    _require(payload.get("implementationBranch") == EXPECTED_BRANCH, "implementation branch mismatch")
    _require(payload.get("state") == EXPECTED_STATE, "unexpected packaging state")

    candidate = payload.get("candidate") or {}
    _require(candidate.get("checkpointSha256") == EXPECTED_CHECKPOINT_SHA256, "candidate checkpoint mismatch")
    _require(candidate.get("configSha256") == EXPECTED_CONFIG_SHA256, "candidate config mismatch")
    _require(candidate.get("datasetMd5") == EXPECTED_DATASET_MD5, "candidate dataset mismatch")
    _require(candidate.get("sourceV2CheckpointSha256") == EXPECTED_SOURCE_V2_CHECKPOINT_SHA256, "source V2 checkpoint mismatch")
    _require(candidate.get("modelStateSha256") == EXPECTED_MODEL_STATE_SHA256, "candidate model-state mismatch")
    _require(candidate.get("frozen") is True, "candidate must remain frozen")

    contract = payload.get("contract") or {}
    _require(contract.get("id") == PACKAGE_CONTRACT_ID, "package contract id mismatch")
    _require(contract.get("format") == "torchscript-trace", "package format mismatch")
    _require(contract.get("inputShape") == [1, 1, 512, 512], "package input shape mismatch")
    _require(contract.get("inputRange") == [0.0, 1.0], "package input range mismatch")
    _require(contract.get("outputShapeMustEqualInput") is True, "output shape preservation required")
    _require(contract.get("outputRange") == [0.0, 1.0], "package output range mismatch")
    _require(float(contract.get("repeatMaxAbsDiff")) == 1e-7, "repeat tolerance mismatch")
    _require(float(contract.get("reloadMaxAbsDiff")) == 1e-5, "reload tolerance mismatch")

    implementation = payload.get("implementation") or {}
    for key in (
        "packagingContractReady",
        "packagingRuntimeReady",
        "cpuPackagingNotebookReady",
        "checkpointShaVerificationReady",
        "modelStateShaVerificationReady",
        "torchscriptReloadParityReady",
        "heldoutAccessForbidden",
    ):
        _require(implementation.get(key) is True, f"implementation flag must be true: {key}")

    execution = payload.get("execution") or {}
    _require(execution.get("completed") is False, "packaging execution must remain pending until real evidence exists")
    _require(execution.get("packageSha256") is None, "package SHA must remain null before execution")
    _require(execution.get("packageSizeBytes") is None, "package size must remain null before execution")
    _require(str(execution.get("evidencePath") or "").endswith("candidate_package_evidence.v1.json"), "evidence path mismatch")
    _require(str(execution.get("packagePath") or "").endswith("v2a_candidate_512.torchscript.pt"), "package path mismatch")

    authorization = payload.get("authorization") or {}
    _require(authorization.get("candidatePackagingAuthorized") is True, "candidate packaging must be authorized")
    for key in ("productionInferenceAuthorized", "productionPromotionAuthorized", "finalProductionModelSelectionAuthorized", "stage12EntryAuthorized"):
        _require(authorization.get(key) is False, f"authorization must remain false: {key}")

    safety = payload.get("safety") or {}
    for key in (
        "checkpointWeightsImmutable",
        "optimizerForbidden",
        "backpropagationForbidden",
        "consumedHeldoutAccessForbidden",
        "privateStudentUserDataForbidden",
        "omrCorrectnessNotImplied",
        "musicalTruthNotImplied",
    ):
        _require(safety.get(key) is True, f"safety assertion missing: {key}")

    _require(payload.get("notebook") == "notebooks/stage11_v2a_frozen_candidate_packaging_colab.ipynb", "notebook path mismatch")
    _require(payload.get("runtime") == "tools/stage11_v2a_candidate_packaging.py", "runtime path mismatch")

    return {
        "state": EXPECTED_STATE,
        "implementationReady": True,
        "executionCompleted": False,
        "candidateCheckpointFrozen": True,
        "candidatePackagingAuthorized": True,
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_stage11_v2a_packaging_current_truth(payload)
