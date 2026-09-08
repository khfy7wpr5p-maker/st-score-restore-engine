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
SCHEMA_VERSION = "1.1.0"
EXPECTED_STATE = "EXECUTION_COMPLETED_CANDIDATE_PACKAGED"
EXPECTED_BASE_MAIN_SHA = "b39b7d56aac5fccb12332d0336070bee80523cef"
EXPECTED_BRANCH = "stage11-v2a-package-evidence-acceptance"
EXPECTED_PACKAGE_SHA256 = "7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234"
EXPECTED_PACKAGE_SIZE_BYTES = 7817857
EXPECTED_EVIDENCE_REPO_PATH = "evidence/stage11/v2a/v2a-candidate-package-evidence.v1.json"
EXPECTED_DRIVE_FOLDER_ID = "1oBL1P_6slQ0j5aOguCLzJYIKAgQXnCXL"
EXPECTED_DRIVE_EVIDENCE_FILE_ID = "1d6WRb43tItsdjTtarAHkwccdn2dKWP8D"
EXPECTED_DRIVE_PACKAGE_FILE_ID = "1oJ9lOEpq7trDD8XZpVwCzQzMQ2mk-wWD"


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
        "executionEvidenceImported",
        "drivePackageStored",
        "driveEvidenceStored",
    ):
        _require(implementation.get(key) is True, f"implementation flag must be true: {key}")

    execution = payload.get("execution") or {}
    _require(execution.get("completed") is True, "packaging execution must be completed")
    _require(execution.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "package SHA mismatch")
    _require(int(execution.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "package size mismatch")
    _require(execution.get("evidenceRepoPath") == EXPECTED_EVIDENCE_REPO_PATH, "evidence repo path mismatch")
    _require(str(execution.get("evidencePath") or "").endswith("candidate_package_evidence.v1.json"), "Drive evidence path mismatch")
    _require(str(execution.get("packagePath") or "").endswith("v2a_candidate_512.torchscript.pt"), "Drive package path mismatch")
    _require(execution.get("driveFolderId") == EXPECTED_DRIVE_FOLDER_ID, "Drive package folder mismatch")
    _require(execution.get("driveEvidenceFileId") == EXPECTED_DRIVE_EVIDENCE_FILE_ID, "Drive evidence file mismatch")
    _require(execution.get("drivePackageFileId") == EXPECTED_DRIVE_PACKAGE_FILE_ID, "Drive package file mismatch")

    environment = execution.get("environment") or {}
    _require(environment.get("device") == "CPU", "packaging must have executed on CPU")
    _require(bool(environment.get("python")), "Python execution version missing")
    _require(bool(environment.get("torch")), "Torch execution version missing")

    smoke = execution.get("smokeTest") or {}
    _require(smoke.get("inputShape") == [1, 1, 512, 512], "smoke input shape mismatch")
    _require(smoke.get("outputShape") == [1, 1, 512, 512], "smoke output shape mismatch")
    _require(smoke.get("finite") is True, "smoke output must be finite")
    _require(float(smoke.get("outputMin", -1.0)) >= 0.0, "smoke output below zero")
    _require(float(smoke.get("outputMax", 2.0)) <= 1.0, "smoke output above one")
    _require(float(smoke.get("repeatMaxAbsDiff", 1.0)) <= 1e-7, "repeat determinism failed")
    _require(float(smoke.get("reloadMaxAbsDiff", 1.0)) <= 1e-5, "TorchScript reload parity failed")

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
        "executionCompleted": True,
        "candidateCheckpointFrozen": True,
        "portableCandidateCreated": True,
        "candidatePackagingAuthorized": True,
        "packageSha256": EXPECTED_PACKAGE_SHA256,
        "packageSizeBytes": EXPECTED_PACKAGE_SIZE_BYTES,
        "evidenceRepoPath": EXPECTED_EVIDENCE_REPO_PATH,
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_stage11_v2a_packaging_current_truth(payload)
