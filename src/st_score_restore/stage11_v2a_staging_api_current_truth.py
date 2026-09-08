"""Fail-closed validator for the Stage 11 V2a staging request/response truth."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .stage11_v2a_consumer_adapter import EXPECTED_PACKAGE_SHA256, EXPECTED_PACKAGE_SIZE_BYTES
from .stage11_v2a_staging_api import CONTRACT_ID

ARTIFACT_TYPE = "stage11_v2a_staging_api_current_truth"
SCHEMA_VERSION = "1.0.0"
EXPECTED_STATE = "STAGING_REQUEST_RESPONSE_PASS"
EXPECTED_BASE_MAIN_SHA = "fecce4e668169305c1a043e0fafca0d941eca94b"
EXPECTED_BRANCH = "stage11-v2a-staging-api-validation"
EXPECTED_REQUEST_SHA = "cfbf82cab845b8b4d2ce3b8d98f76eb9d44326916536a9384a116246f303f352"
EXPECTED_RESPONSE_SHA = "7a3033100e433236293700673d847701960252669634a07507069ad045678c60"
EXPECTED_DRIVE_EVIDENCE_ID = "1gcjHQoSYR9zwXu0G7V5X3-JBzHHG7-pW"


class Stage11V2aStagingApiCurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aStagingApiCurrentTruthError(message)


def validate_stage11_v2a_staging_api_current_truth(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == ARTIFACT_TYPE, "artifact type mismatch")
    _require(payload.get("schemaVersion") == SCHEMA_VERSION, "schema version mismatch")
    _require(payload.get("state") == EXPECTED_STATE, "unexpected staging API state")
    _require(payload.get("baseMainSha") == EXPECTED_BASE_MAIN_SHA, "base main SHA mismatch")
    _require(payload.get("implementationBranch") == EXPECTED_BRANCH, "implementation branch mismatch")

    candidate = payload.get("candidate") or {}
    _require(candidate.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "package SHA mismatch")
    _require(int(candidate.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "package size mismatch")
    _require(candidate.get("frozen") is True, "candidate must remain frozen")

    contract = payload.get("contract") or {}
    _require(contract.get("id") == CONTRACT_ID, "staging contract mismatch")
    _require(contract.get("requestMediaType") == "image/png", "request media type mismatch")
    _require(contract.get("responseMediaType") == "image/png", "response media type mismatch")
    _require(contract.get("grayscaleOnly") is True, "grayscale-only contract required")
    _require(contract.get("networkRouteRegistered") is False, "network route must remain unregistered")
    _require(contract.get("existingHttpApiModified") is False, "existing HTTP API must remain unchanged")

    execution = payload.get("execution") or {}
    _require(execution.get("completed") is True, "staging execution must be completed")
    _require(execution.get("sourceDataKind") == "synthetic_only", "acceptance source must be synthetic-only")
    _require(execution.get("inputShape") == [700, 900], "input shape mismatch")
    _require(execution.get("outputShape") == [700, 900], "output shape mismatch")
    _require(int(execution.get("tileCount", 0)) == 4, "tile count mismatch")
    _require(execution.get("requestSha256") == EXPECTED_REQUEST_SHA, "request SHA mismatch")
    _require(execution.get("responseSha256") == EXPECTED_RESPONSE_SHA, "response SHA mismatch")
    _require(execution.get("repeatResponseSha256") == EXPECTED_RESPONSE_SHA, "repeat response SHA mismatch")
    _require(execution.get("repeatMetadataEqual") is True, "repeat metadata mismatch")
    _require(execution.get("finite") is True, "response must be finite")
    _require(execution.get("driveEvidenceFileId") == EXPECTED_DRIVE_EVIDENCE_ID, "Drive evidence custody mismatch")

    safety = payload.get("safety") or {}
    _require(safety.get("syntheticInputsOnlyForAcceptance") is True, "synthetic acceptance guard missing")
    _require(safety.get("consumedHeldoutRetuningForbidden") is True, "held-out retuning guard missing")
    for key in ("heldOutAccessed", "optimizerCreated", "backpropagationExecuted", "weightsMutated", "realUserDataUsed", "networkRouteRegistered", "existingHttpApiModified"):
        _require(safety.get(key) is False, f"unsafe staging flag must remain false: {key}")

    authorization = payload.get("authorization") or {}
    _require(authorization.get("stagingRequestResponseValidationAuthorized") is True, "staging validation authorization missing")
    for key in ("productionInferenceAuthorized", "productionPromotionAuthorized", "realUserRolloutAuthorized", "finalProductionModelSelectionAuthorized", "stage12EntryAuthorized"):
        _require(authorization.get(key) is False, f"authorization must remain false: {key}")

    next_boundary = str(payload.get("nextSafeBoundary") or "")
    _require("shadow-mode" in next_boundary, "next boundary must remain shadow-mode")
    _require("do not expose a new public route" in next_boundary, "public-route prohibition missing")
    return {
        "state": EXPECTED_STATE,
        "stagingRequestResponseValidated": True,
        "networkRouteRegistered": False,
        "productionInferenceAuthorized": False,
        "realUserRolloutAuthorized": False,
        "stage12EntryAuthorized": False,
        "nextBoundary": "shadow-mode-application-service-handoff",
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    return validate_stage11_v2a_staging_api_current_truth(json.loads(Path(path).read_text(encoding="utf-8")))
