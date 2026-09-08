"""Staging-only request/response adapter for the frozen Stage 11 V2a candidate.

This module is deliberately transport-neutral and is not registered in ``http_api.py``.
It defines a bounded grayscale-PNG request contract around the already validated consumer
adapter. It cannot authorize production inference, real-user rollout, training or Stage 12.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from .stage11_v2a_consumer_adapter import (
    EXPECTED_PACKAGE_SHA256,
    EXPECTED_PACKAGE_SIZE_BYTES,
    TorchScriptConsumerAdapter,
)

CONTRACT_ID = "stage11.v2a.staging-api.synthetic-request-response.v1"
EVIDENCE_TYPE = "stage11_v2a_staging_api_evidence"
EVIDENCE_SCHEMA_VERSION = "stage11.v2a.staging-api-evidence.v1"
PNG_MEDIA_TYPE = "image/png"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 16_000_000
MAX_DIMENSION = 8192
PNG_COMPRESSION = 3


class Stage11V2aStagingApiError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aStagingApiError(message)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def staging_api_contract() -> dict[str, Any]:
    return {
        "contractId": CONTRACT_ID,
        "candidate": {
            "packageSha256": EXPECTED_PACKAGE_SHA256,
            "packageSizeBytes": EXPECTED_PACKAGE_SIZE_BYTES,
            "frozen": True,
        },
        "request": {
            "mediaType": PNG_MEDIA_TYPE,
            "grayscaleOnly": True,
            "bitDepth": 8,
            "maxInputBytes": MAX_INPUT_BYTES,
            "maxPixels": MAX_PIXELS,
            "maxDimension": MAX_DIMENSION,
            "sourceDataKinds": ["synthetic_only", "nonheldout_test_only"],
            "requiredMetadata": ["requestId", "sourceDataKind"],
        },
        "response": {
            "mediaType": PNG_MEDIA_TYPE,
            "grayscaleOnly": True,
            "bitDepth": 8,
            "shapePreserved": True,
            "sha256Included": True,
            "packageSha256Included": True,
        },
        "execution": {
            "networkRouteRegistered": False,
            "existingHttpApiModified": False,
            "trainingAllowed": False,
            "heldoutAccessAllowed": False,
            "realUserDataAllowed": False,
        },
        "authorization": {
            "stagingRequestResponseValidationAuthorized": True,
            "productionInferenceAuthorized": False,
            "productionPromotionAuthorized": False,
            "realUserRolloutAuthorized": False,
            "stage12EntryAuthorized": False,
        },
    }


def validate_request_metadata(metadata: Mapping[str, Any]) -> dict[str, str]:
    _require(isinstance(metadata, Mapping), "staging request metadata must be an object")
    request_id = str(metadata.get("requestId") or "").strip()
    source_kind = str(metadata.get("sourceDataKind") or "").strip()
    _require(1 <= len(request_id) <= 128, "staging requestId length invalid")
    _require(all(ch.isalnum() or ch in "-_.:" for ch in request_id), "staging requestId contains unsupported characters")
    _require(source_kind in {"synthetic_only", "nonheldout_test_only"}, "unsupported staging sourceDataKind")
    return {"requestId": request_id, "sourceDataKind": source_kind}


def decode_grayscale_png(payload: bytes) -> np.ndarray:
    _require(isinstance(payload, (bytes, bytearray)), "staging request body must be bytes")
    raw = bytes(payload)
    _require(len(raw) >= len(PNG_SIGNATURE), "staging PNG body is too short")
    _require(len(raw) <= MAX_INPUT_BYTES, "staging PNG exceeds byte limit")
    _require(raw.startswith(PNG_SIGNATURE), "staging request must be a PNG")
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("OpenCV is required for Stage 11 staging PNG transport validation") from exc
    encoded = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_UNCHANGED)
    _require(image is not None, "staging PNG decode failed")
    _require(image.ndim == 2, "staging PNG must be native grayscale; color/alpha inputs are rejected")
    _require(image.dtype == np.uint8, "staging PNG must be 8-bit grayscale")
    height, width = (int(image.shape[0]), int(image.shape[1]))
    _require(height > 0 and width > 0, "staging PNG dimensions must be positive")
    _require(height <= MAX_DIMENSION and width <= MAX_DIMENSION, "staging PNG dimension limit exceeded")
    _require(height * width <= MAX_PIXELS, "staging PNG pixel limit exceeded")
    return image


def encode_grayscale_png(image: Any) -> bytes:
    value = np.asarray(image)
    _require(value.ndim == 2, "staging response must be a 2-D grayscale array")
    if value.dtype == np.uint8:
        output = value
    elif np.issubdtype(value.dtype, np.floating):
        float_value = value.astype(np.float32, copy=False)
        _require(bool(np.isfinite(float_value).all()), "staging response contains non-finite values")
        _require(float(float_value.min()) >= 0.0 and float(float_value.max()) <= 1.0, "staging response outside [0,1]")
        output = np.rint(float_value * 255.0).clip(0, 255).astype(np.uint8)
    else:
        raise Stage11V2aStagingApiError("staging response dtype must be uint8 or float")
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("OpenCV is required for Stage 11 staging PNG transport validation") from exc
    success, encoded = cv2.imencode(".png", output, [cv2.IMWRITE_PNG_COMPRESSION, PNG_COMPRESSION])
    _require(bool(success), "staging PNG encode failed")
    raw = bytes(encoded.tobytes())
    _require(raw.startswith(PNG_SIGNATURE), "staging response PNG signature missing")
    return raw


def process_staging_request(
    body: bytes,
    metadata: Mapping[str, Any],
    restore_fn: Callable[[np.ndarray], tuple[np.ndarray, Mapping[str, Any]]],
) -> tuple[bytes, dict[str, Any]]:
    request = validate_request_metadata(metadata)
    source = decode_grayscale_png(body)
    restored, restore_meta = restore_fn(source)
    restored_value = np.asarray(restored, dtype=np.float32)
    _require(restored_value.shape == source.shape, "staging restore output shape mismatch")
    _require(bool(np.isfinite(restored_value).all()), "staging restore output contains non-finite values")
    _require(float(restored_value.min()) >= 0.0 and float(restored_value.max()) <= 1.0, "staging restore output outside [0,1]")
    response_body = encode_grayscale_png(restored_value)
    decoded_response = decode_grayscale_png(response_body)
    _require(decoded_response.shape == source.shape, "encoded staging response shape mismatch")
    response = {
        "contractId": CONTRACT_ID,
        "requestId": request["requestId"],
        "sourceDataKind": request["sourceDataKind"],
        "requestMediaType": PNG_MEDIA_TYPE,
        "responseMediaType": PNG_MEDIA_TYPE,
        "inputShape": list(source.shape),
        "outputShape": list(decoded_response.shape),
        "inputBytes": len(body),
        "outputBytes": len(response_body),
        "requestSha256": sha256_bytes(bytes(body)),
        "responseSha256": sha256_bytes(response_body),
        "packageSha256": EXPECTED_PACKAGE_SHA256,
        "finite": True,
        "outputMin": float(restored_value.min()),
        "outputMax": float(restored_value.max()),
        "tileCount": int((restore_meta or {}).get("tileCount", 0)),
        "networkRouteRegistered": False,
        "existingHttpApiModified": False,
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
    }
    return response_body, response


class TorchScriptStagingService:
    """In-process staging service around the exact frozen package; no network exposure."""

    def __init__(self, package_path: Path):
        self.adapter = TorchScriptConsumerAdapter(Path(package_path))

    def restore(self, image_u8: np.ndarray) -> tuple[np.ndarray, Mapping[str, Any]]:
        return self.adapter.restore(image_u8)

    def handle(self, body: bytes, metadata: Mapping[str, Any]) -> tuple[bytes, dict[str, Any]]:
        return process_staging_request(body, metadata, self.restore)


def validate_staging_api_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == EVIDENCE_TYPE, "staging API evidence type mismatch")
    _require(payload.get("schemaVersion") == EVIDENCE_SCHEMA_VERSION, "staging API evidence schema mismatch")
    _require(payload.get("status") == "completed", "staging API evidence must be completed")
    _require(payload.get("contractId") == CONTRACT_ID, "staging API contract mismatch")
    _require(payload.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "staging API package SHA mismatch")
    _require(int(payload.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "staging API package size mismatch")
    _require(payload.get("sourceDataKind") == "synthetic_only", "staging API acceptance evidence must be synthetic-only")
    _require(payload.get("heldOutAccessed") is False, "held-out access is forbidden")
    _require(payload.get("optimizerCreated") is False, "optimizer creation is forbidden")
    _require(payload.get("backpropagationExecuted") is False, "backpropagation is forbidden")
    _require(payload.get("weightsMutated") is False, "weights must remain frozen")
    _require(payload.get("networkRouteRegistered") is False, "staging evidence cannot register a network route")
    _require(payload.get("existingHttpApiModified") is False, "existing HTTP API must remain untouched")
    _require(payload.get("realUserDataUsed") is False, "real-user data is forbidden")

    execution = payload.get("execution") or {}
    _require(execution.get("requestId") == "stage11-synthetic-staff-001", "staging execution request ID mismatch")
    _require(execution.get("inputShape") == [700, 900], "staging execution input shape mismatch")
    _require(execution.get("outputShape") == [700, 900], "staging execution output shape mismatch")
    _require(int(execution.get("tileCount", 0)) == 4, "staging execution tile count mismatch")
    _require(execution.get("finite") is True, "staging execution output must be finite")
    _require(float(execution.get("outputMin", -1.0)) >= 0.0, "staging execution output below zero")
    _require(float(execution.get("outputMax", 2.0)) <= 1.0, "staging execution output above one")
    for key in ("requestSha256", "responseSha256"):
        value = str(execution.get(key) or "")
        _require(len(value) == 64 and all(ch in "0123456789abcdef" for ch in value), f"invalid {key}")
    _require(int(execution.get("inputBytes", 0)) > 0, "staging execution input bytes missing")
    _require(int(execution.get("outputBytes", 0)) > 0, "staging execution output bytes missing")
    _require(execution.get("repeatResponseSha256") == execution.get("responseSha256"), "staging response bytes are not deterministic on repeat")
    _require(execution.get("repeatMetadataEqual") is True, "staging response metadata is not deterministic on repeat")

    authorization = payload.get("authorization") or {}
    _require(authorization.get("stagingRequestResponseValidationAuthorized") is True, "staging validation authorization missing")
    for key in ("productionInferenceAuthorized", "productionPromotionAuthorized", "realUserRolloutAuthorized", "stage12EntryAuthorized"):
        _require(authorization.get(key) is False, f"authorization must remain false: {key}")
    _require(payload.get("contract") == staging_api_contract(), "staging API contract snapshot mismatch")
    return {
        "status": "pass",
        "stagingRequestResponseValidated": True,
        "packageSha256": EXPECTED_PACKAGE_SHA256,
        "productionInferenceAuthorized": False,
        "realUserRolloutAuthorized": False,
        "stage12EntryAuthorized": False,
    }
