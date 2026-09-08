"""Stage 11 V2a frozen-candidate packaging contract.

This module contains no production inference path and does not require PyTorch. It defines
and validates the evidence contract for packaging the already frozen V2a checkpoint into a
portable candidate artifact. Execution happens separately in Colab/CPU and must not tune
weights or touch the consumed held-out set.
"""
from __future__ import annotations

from typing import Any, Mapping

EXPECTED_CHECKPOINT_SHA256 = "15afc73233c91a80a7ef1285cb631d5d3acd681e9cfed9a93b35642bf39fff4c"
EXPECTED_CONFIG_SHA256 = "1250731992c01c238dd2376a95ced1d1c6f76dcdf87deb473ec94a0aa58f7818"
EXPECTED_DATASET_MD5 = "7237318e381e6e0848ec30eb82decb83"
EXPECTED_SOURCE_V2_CHECKPOINT_SHA256 = "363cb63bff2367c1119a4eea449a19d468a802160f45b4fe1f2d98ab04fb894b"
EXPECTED_MODEL_STATE_SHA256 = "1d8becbebfb2b86beb21b4f757c6dacb01354c981bc7216b6e988fc74fd2d32b"
PACKAGE_CONTRACT_ID = "stage11.v2a.frozen-candidate-package.v1"
PACKAGE_EVIDENCE_TYPE = "stage11_v2a_candidate_package_evidence"
PACKAGE_SCHEMA_VERSION = "stage11.v2a.package-evidence.v1"
PATCH_SIZE = 512
CHANNELS = 1


class Stage11V2aPackagingError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aPackagingError(message)


def candidate_package_contract() -> dict[str, Any]:
    return {
        "contractId": PACKAGE_CONTRACT_ID,
        "checkpointSha256": EXPECTED_CHECKPOINT_SHA256,
        "configSha256": EXPECTED_CONFIG_SHA256,
        "datasetMd5": EXPECTED_DATASET_MD5,
        "sourceV2CheckpointSha256": EXPECTED_SOURCE_V2_CHECKPOINT_SHA256,
        "modelStateSha256": EXPECTED_MODEL_STATE_SHA256,
        "modelFamily": "Residual U-Net",
        "baseChannels": 32,
        "input": {
            "dtype": "float32",
            "layout": "NCHW",
            "channels": CHANNELS,
            "patchHeight": PATCH_SIZE,
            "patchWidth": PATCH_SIZE,
            "whiteValue": 1.0,
            "inkValue": 0.0,
            "range": [0.0, 1.0],
        },
        "output": {
            "dtype": "float32",
            "layout": "NCHW",
            "shapeMustEqualInput": True,
            "range": [0.0, 1.0],
            "finiteRequired": True,
        },
        "packaging": {
            "format": "torchscript-trace",
            "fixedValidationPatch": [1, CHANNELS, PATCH_SIZE, PATCH_SIZE],
            "repeatMaxAbsDiff": 1e-7,
            "reloadMaxAbsDiff": 1e-5,
            "weightsMayMutate": False,
            "optimizerAllowed": False,
            "backpropagationAllowed": False,
            "heldoutAccessAllowed": False,
        },
        "authorization": {
            "candidatePackagingAuthorized": True,
            "productionInferenceAuthorized": False,
            "productionPromotionAuthorized": False,
            "stage12EntryAuthorized": False,
        },
    }


def validate_candidate_package_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == PACKAGE_EVIDENCE_TYPE, "artifact type mismatch")
    _require(payload.get("schemaVersion") == PACKAGE_SCHEMA_VERSION, "schema version mismatch")
    _require(payload.get("status") == "completed", "package evidence must be completed")
    _require(payload.get("contractId") == PACKAGE_CONTRACT_ID, "package contract mismatch")
    _require(payload.get("checkpointSha256") == EXPECTED_CHECKPOINT_SHA256, "checkpoint SHA mismatch")
    _require(payload.get("configSha256") == EXPECTED_CONFIG_SHA256, "config SHA mismatch")
    _require(payload.get("datasetMd5") == EXPECTED_DATASET_MD5, "dataset MD5 mismatch")
    _require(payload.get("sourceV2CheckpointSha256") == EXPECTED_SOURCE_V2_CHECKPOINT_SHA256, "source V2 checkpoint mismatch")
    _require(payload.get("modelStateSha256Before") == EXPECTED_MODEL_STATE_SHA256, "model state before mismatch")
    _require(payload.get("modelStateSha256After") == EXPECTED_MODEL_STATE_SHA256, "model state after mismatch")
    _require(payload.get("weightsMutated") is False, "packaging mutated model weights")
    _require(payload.get("optimizerCreated") is False, "optimizer creation is forbidden")
    _require(payload.get("backpropagationExecuted") is False, "backpropagation is forbidden")
    _require(payload.get("heldOutAccessed") is False, "consumed held-out access is forbidden")

    package = payload.get("package") or {}
    package_sha = str(package.get("sha256") or "")
    _require(len(package_sha) == 64 and all(ch in "0123456789abcdef" for ch in package_sha), "package SHA-256 invalid")
    _require(int(package.get("sizeBytes", 0)) > 0, "package must be non-empty")
    _require(package.get("format") == "torchscript-trace", "package format mismatch")

    smoke = payload.get("smokeTest") or {}
    _require(smoke.get("inputShape") == [1, 1, 512, 512], "smoke input shape mismatch")
    _require(smoke.get("outputShape") == [1, 1, 512, 512], "smoke output shape mismatch")
    _require(smoke.get("finite") is True, "smoke output contains non-finite values")
    _require(float(smoke.get("outputMin", -1.0)) >= 0.0, "smoke output below zero")
    _require(float(smoke.get("outputMax", 2.0)) <= 1.0, "smoke output above one")
    _require(float(smoke.get("repeatMaxAbsDiff", 1.0)) <= 1e-7, "eager repeat determinism failed")
    _require(float(smoke.get("reloadMaxAbsDiff", 1.0)) <= 1e-5, "TorchScript reload parity failed")

    authorization = payload.get("authorization") or {}
    _require(authorization.get("candidatePackagingAuthorized") is True, "candidate packaging authorization missing")
    _require(authorization.get("productionInferenceAuthorized") is False, "production inference remains forbidden")
    _require(authorization.get("productionPromotionAuthorized") is False, "production promotion remains forbidden")
    _require(authorization.get("stage12EntryAuthorized") is False, "Stage 12 remains forbidden")

    return {
        "status": "pass",
        "checkpointSha256": EXPECTED_CHECKPOINT_SHA256,
        "packageSha256": package_sha,
        "portableCandidateCreated": True,
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
    }
