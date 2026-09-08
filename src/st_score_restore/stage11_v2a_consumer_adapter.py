"""Development-only consumer adapter for the frozen Stage 11 V2a TorchScript candidate.

The adapter is intentionally not a production authorization boundary. It verifies the exact
packaged bytes, accepts only grayscale arrays, tiles arbitrary image sizes into the frozen
512x512 package contract, stitches overlapping outputs deterministically, and forbids any
training/held-out semantics.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

EXPECTED_PACKAGE_SHA256 = "7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234"
EXPECTED_PACKAGE_SIZE_BYTES = 7_817_857
PACKAGE_FORMAT = "torchscript-trace"
CONTRACT_ID = "stage11.v2a.consumer-adapter.synthetic-integration.v1"
EVIDENCE_TYPE = "stage11_v2a_consumer_adapter_evidence"
EVIDENCE_SCHEMA_VERSION = "stage11.v2a.consumer-adapter-evidence.v1"
PATCH_SIZE = 512
OVERLAP = 64
STRIDE = PATCH_SIZE - OVERLAP
DIRECT_PARITY_TOLERANCE = 1e-6
REPEAT_TOLERANCE = 1e-7


class Stage11V2aConsumerAdapterError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aConsumerAdapterError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_grayscale(image: Any) -> np.ndarray:
    """Normalize a 2-D grayscale input without silently rescaling unknown numeric ranges."""
    value = np.asarray(image)
    _require(value.ndim == 2, "consumer input must be a 2-D grayscale array")
    _require(value.size > 0, "consumer input cannot be empty")
    if value.dtype == np.uint8:
        result = value.astype(np.float32) / 255.0
    elif np.issubdtype(value.dtype, np.floating):
        result = value.astype(np.float32, copy=False)
        _require(bool(np.isfinite(result).all()), "consumer float input contains non-finite values")
        minimum = float(result.min())
        maximum = float(result.max())
        _require(minimum >= 0.0 and maximum <= 1.0, "consumer float input must already be in [0,1]")
    else:
        raise Stage11V2aConsumerAdapterError("consumer input dtype must be uint8 or floating point")
    _require(bool(np.isfinite(result).all()), "normalized consumer input contains non-finite values")
    return result


def axis_starts(length: int, *, patch_size: int = PATCH_SIZE, stride: int = STRIDE) -> list[int]:
    _require(length > 0, "axis length must be positive")
    _require(patch_size > 0, "patch size must be positive")
    _require(0 < stride <= patch_size, "stride must be in (0, patch_size]")
    starts = [0]
    while starts[-1] + patch_size < length:
        starts.append(starts[-1] + stride)
    return starts


def build_tile_plan(height: int, width: int) -> list[tuple[int, int]]:
    return [(y, x) for y in axis_starts(height) for x in axis_starts(width)]


def extract_padded_patch(image: np.ndarray, y: int, x: int) -> np.ndarray:
    _require(image.ndim == 2, "tile source must be grayscale")
    height, width = image.shape
    _require(0 <= y < height and 0 <= x < width, "tile origin outside image")
    patch = np.ones((PATCH_SIZE, PATCH_SIZE), dtype=np.float32)
    visible = image[y:min(y + PATCH_SIZE, height), x:min(x + PATCH_SIZE, width)]
    patch[: visible.shape[0], : visible.shape[1]] = visible
    return patch


def stitch_tiles(
    output_shape: Sequence[int],
    tile_outputs: Sequence[np.ndarray],
    tile_plan: Sequence[tuple[int, int]],
) -> np.ndarray:
    _require(len(output_shape) == 2, "output shape must contain height and width")
    height, width = (int(output_shape[0]), int(output_shape[1]))
    _require(height > 0 and width > 0, "output shape must be positive")
    _require(len(tile_outputs) == len(tile_plan) and len(tile_plan) > 0, "tile output/plan mismatch")
    accumulator = np.zeros((height, width), dtype=np.float64)
    weights = np.zeros((height, width), dtype=np.float64)
    for output, (y, x) in zip(tile_outputs, tile_plan):
        value = np.asarray(output, dtype=np.float32)
        _require(value.shape == (PATCH_SIZE, PATCH_SIZE), "tile output shape mismatch")
        _require(bool(np.isfinite(value).all()), "tile output contains non-finite values")
        _require(float(value.min()) >= 0.0 and float(value.max()) <= 1.0, "tile output outside [0,1]")
        visible_height = min(PATCH_SIZE, height - y)
        visible_width = min(PATCH_SIZE, width - x)
        accumulator[y:y + visible_height, x:x + visible_width] += value[:visible_height, :visible_width]
        weights[y:y + visible_height, x:x + visible_width] += 1.0
    _require(bool((weights > 0).all()), "tile stitching left uncovered output pixels")
    restored = (accumulator / weights).astype(np.float32)
    _require(bool(np.isfinite(restored).all()), "stitched output contains non-finite values")
    _require(float(restored.min()) >= 0.0 and float(restored.max()) <= 1.0, "stitched output outside [0,1]")
    return restored


def run_tiled_adapter(image: Any, infer_patch: Callable[[np.ndarray], np.ndarray]) -> tuple[np.ndarray, dict[str, Any]]:
    normalized = normalize_grayscale(image)
    plan = build_tile_plan(*normalized.shape)
    outputs = [infer_patch(extract_padded_patch(normalized, y, x)) for y, x in plan]
    restored = stitch_tiles(normalized.shape, outputs, plan)
    return restored, {
        "inputShape": list(normalized.shape),
        "outputShape": list(restored.shape),
        "tileCount": len(plan),
        "finite": bool(np.isfinite(restored).all()),
        "outputMin": float(restored.min()),
        "outputMax": float(restored.max()),
        "outputMean": float(restored.mean()),
    }


class TorchScriptConsumerAdapter:
    """CPU development adapter around the exact frozen TorchScript package."""

    def __init__(self, package_path: Path):
        package_path = Path(package_path)
        if not package_path.exists():
            raise FileNotFoundError(package_path)
        _require(package_path.stat().st_size == EXPECTED_PACKAGE_SIZE_BYTES, "candidate package size mismatch")
        actual_sha = sha256_file(package_path)
        _require(actual_sha == EXPECTED_PACKAGE_SHA256, f"candidate package SHA mismatch: {actual_sha}")
        try:
            import torch
        except ImportError as exc:  # pragma: no cover - regular repository runtime does not require torch
            raise RuntimeError("PyTorch is required only for Stage 11 candidate adapter execution") from exc
        self._torch = torch
        self.package_path = package_path
        self.model = torch.jit.load(str(package_path), map_location="cpu").eval()

    def infer_patch(self, patch: np.ndarray) -> np.ndarray:
        value = np.asarray(patch, dtype=np.float32)
        _require(value.shape == (PATCH_SIZE, PATCH_SIZE), "package patch must be 512x512")
        _require(bool(np.isfinite(value).all()), "package patch contains non-finite values")
        _require(float(value.min()) >= 0.0 and float(value.max()) <= 1.0, "package patch outside [0,1]")
        tensor = self._torch.from_numpy(value).unsqueeze(0).unsqueeze(0)
        with self._torch.inference_mode():
            output = self.model(tensor)
        _require(list(output.shape) == [1, 1, PATCH_SIZE, PATCH_SIZE], "TorchScript package output shape mismatch")
        result = output.squeeze(0).squeeze(0).detach().cpu().numpy().astype(np.float32, copy=False)
        _require(bool(np.isfinite(result).all()), "TorchScript package output contains non-finite values")
        _require(float(result.min()) >= 0.0 and float(result.max()) <= 1.0, "TorchScript package output outside [0,1]")
        return result

    def restore(self, image: Any) -> tuple[np.ndarray, dict[str, Any]]:
        return run_tiled_adapter(image, self.infer_patch)


def synthetic_white_small() -> np.ndarray:
    return np.full((300, 700), 255, dtype=np.uint8)


def synthetic_staff_page() -> np.ndarray:
    page = np.ones((700, 900), dtype=np.float32)
    for base in range(80, 620, 120):
        for offset in range(0, 50, 10):
            page[base + offset:base + offset + 2, 40:860] = 0.0
    for x in (120, 240, 360, 480, 600, 720):
        page[100:650, x:x + 2] = 0.0
    return page


def synthetic_direct_512() -> np.ndarray:
    return np.linspace(0.0, 1.0, PATCH_SIZE * PATCH_SIZE, dtype=np.float32).reshape(PATCH_SIZE, PATCH_SIZE)


def consumer_adapter_contract() -> dict[str, Any]:
    return {
        "contractId": CONTRACT_ID,
        "packageSha256": EXPECTED_PACKAGE_SHA256,
        "packageSizeBytes": EXPECTED_PACKAGE_SIZE_BYTES,
        "packageFormat": PACKAGE_FORMAT,
        "input": {
            "rank": 2,
            "grayscale": True,
            "acceptedDtypes": ["uint8", "float"],
            "floatRange": [0.0, 1.0],
            "uint8Range": [0, 255],
        },
        "tiling": {
            "patchSize": PATCH_SIZE,
            "overlap": OVERLAP,
            "stride": STRIDE,
            "paddingValue": 1.0,
            "overlapMerge": "arithmetic-mean",
            "outputShapePreserved": True,
        },
        "validation": {
            "syntheticInputsOnly": True,
            "direct512ParityTolerance": DIRECT_PARITY_TOLERANCE,
            "repeatTolerance": REPEAT_TOLERANCE,
            "finiteOutputRequired": True,
            "outputRange": [0.0, 1.0],
        },
        "authorization": {
            "developmentConsumerIntegrationValidationAuthorized": True,
            "productionInferenceAuthorized": False,
            "productionPromotionAuthorized": False,
            "stage12EntryAuthorized": False,
        },
    }


def validate_consumer_adapter_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == EVIDENCE_TYPE, "consumer adapter evidence type mismatch")
    _require(payload.get("schemaVersion") == EVIDENCE_SCHEMA_VERSION, "consumer adapter evidence schema mismatch")
    _require(payload.get("status") == "completed", "consumer adapter evidence must be completed")
    _require(payload.get("contractId") == CONTRACT_ID, "consumer adapter contract mismatch")
    _require(payload.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "consumer adapter package SHA mismatch")
    _require(int(payload.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "consumer adapter package size mismatch")
    _require(payload.get("sourceDataKind") == "synthetic_only", "consumer adapter validation must use synthetic-only inputs")
    _require(payload.get("heldOutAccessed") is False, "held-out access is forbidden")
    _require(payload.get("optimizerCreated") is False, "optimizer creation is forbidden")
    _require(payload.get("backpropagationExecuted") is False, "backpropagation is forbidden")
    _require(payload.get("weightsMutated") is False, "candidate weights must not mutate")

    cases = payload.get("cases")
    _require(isinstance(cases, list) and len(cases) == 3, "exact synthetic integration case set required")
    expected = {
        "white_small_u8": ([300, 700], 2),
        "synthetic_staff_float": ([700, 900], 4),
        "direct_512_float": ([512, 512], 1),
    }
    seen: set[str] = set()
    for case in cases:
        _require(isinstance(case, Mapping), "consumer adapter case must be an object")
        name = str(case.get("name") or "")
        _require(name in expected and name not in seen, f"unexpected/duplicate synthetic case: {name}")
        seen.add(name)
        shape, tile_count = expected[name]
        _require(case.get("inputShape") == shape, f"input shape mismatch: {name}")
        _require(case.get("outputShape") == shape, f"output shape mismatch: {name}")
        _require(int(case.get("tileCount", 0)) == tile_count, f"tile count mismatch: {name}")
        _require(case.get("finite") is True, f"non-finite synthetic output: {name}")
        _require(float(case.get("outputMin", -1.0)) >= 0.0, f"synthetic output below zero: {name}")
        _require(float(case.get("outputMax", 2.0)) <= 1.0, f"synthetic output above one: {name}")
    _require(seen == set(expected), "synthetic case set incomplete")
    _require(float(payload.get("direct512ParityMaxAbsDiff", 1.0)) <= DIRECT_PARITY_TOLERANCE, "direct 512 package parity failed")
    _require(float(payload.get("repeatMaxAbsDiff", 1.0)) <= REPEAT_TOLERANCE, "consumer adapter repeat determinism failed")

    authorization = payload.get("authorization") or {}
    _require(authorization.get("developmentConsumerIntegrationValidationAuthorized") is True, "development adapter validation authorization missing")
    for key in ("productionInferenceAuthorized", "productionPromotionAuthorized", "stage12EntryAuthorized"):
        _require(authorization.get(key) is False, f"authorization must remain false: {key}")

    contract = payload.get("contract") or {}
    _require(contract == consumer_adapter_contract(), "consumer adapter contract snapshot mismatch")
    return {
        "status": "pass",
        "syntheticIntegrationValidated": True,
        "packageSha256": EXPECTED_PACKAGE_SHA256,
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
    }
