"""Stage 11 V2 symbol-aware supervision for the DeepScoresV2 Dense Residual U-Net.

The module intentionally keeps PyTorch optional. Repository/CI validation can exercise
annotation parsing, masks, sampling, loss math, provenance, and development gating with
NumPy only; Colab training uses the lazy torch helpers.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import random
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

DATASET_ID = "deepscoresv2.dense.v2"
EXPECTED_ARCHIVE_MD5 = "7237318e381e6e0848ec30eb82decb83"
V2_POLICY_ID = "stage11.v2.symbol-preservation.residual-unet.v1"
DEFAULT_PATCH_SIZE = 512
DEFAULT_SYMBOL_FRACTION = 0.50
INK_TARGET_THRESHOLD = 0.75

V1_STAGE9A_REFERENCE = {
    "falseInkRateDelta": -0.196,
    "inkRecallDelta": -0.166,
    "selectedSymbolRegions": 861,
    "officialHeldOutImages": 352,
}

HARD_EXAMPLE_TOKENS = (
    "notehead", "stem", "beam", "accidental", "staff", "rest", "articulation",
    "flag", "dot", "tie", "slur", "barline", "clef",
)


class Stage11V2SymbolPreservationError(ValueError):
    """Raised when V2 supervision/provenance violates the Stage 11 contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2SymbolPreservationError(message)


@dataclass(frozen=True)
class LossWeights:
    pixel_l1: float = 0.40
    edge_l1: float = 0.20
    symbol_region_l1: float = 0.25
    ink_recall_penalty: float = 0.15

    def validated(self) -> "LossWeights":
        values = asdict(self)
        _require(all(float(v) >= 0 for v in values.values()), "loss weights must be non-negative")
        _require(abs(sum(float(v) for v in values.values()) - 1.0) <= 1e-9, "loss weights must sum to 1.0")
        _require(self.symbol_region_l1 > 0, "symbol-region supervision must be active")
        _require(self.ink_recall_penalty > 0, "ink-removal penalty must be active")
        return self

    def as_dict(self) -> dict[str, float]:
        self.validated()
        return {k: float(v) for k, v in asdict(self).items()}


def stable_config_sha256(config: Mapping[str, Any]) -> str:
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _image_name(row: Mapping[str, Any]) -> str:
    return str(row.get("filename") or row.get("file_name") or row.get("img_name") or row.get("name") or "").strip()


def _image_id(row: Mapping[str, Any], fallback_index: int) -> str:
    for key in ("id", "img_id", "image_id"):
        if row.get(key) is not None:
            return str(row[key])
    name = _image_name(row)
    return name or f"row:{fallback_index}"


def _category_ids(annotation: Mapping[str, Any]) -> list[str]:
    raw = annotation.get("cat_id")
    if raw is None:
        raw = annotation.get("category_id")
    if raw is None:
        raw = annotation.get("categoryId")
    if isinstance(raw, (list, tuple)):
        return [str(value) for value in raw if value is not None]
    return [] if raw is None else [str(raw)]


def _category_name(categories: Mapping[str, Any], category_id: str) -> str:
    row = categories.get(str(category_id), categories.get(category_id))
    if isinstance(row, Mapping):
        return str(row.get("name") or row.get("label") or category_id)
    return str(row) if row is not None else str(category_id)


def native_bbox_xywh(annotation: Mapping[str, Any]) -> tuple[float, float, float, float] | None:
    """Parse the corrected DeepScores schema.

    Native ``a_bbox`` is [left, top, right, bottom]. A COCO-style ``bbox`` fallback
    is accepted for defensive compatibility but is not allowed to reinterpret a_bbox.
    """
    native = annotation.get("a_bbox")
    if isinstance(native, (list, tuple)) and len(native) >= 4:
        left, top, right, bottom = (float(v) for v in native[:4])
        if right > left and bottom > top:
            return left, top, right - left, bottom - top
        return None
    bbox = annotation.get("bbox")
    if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
        x, y, width, height = (float(v) for v in bbox[:4])
        if width > 0 and height > 0:
            return x, y, width, height
    return None


def parse_deepscores_native_annotations(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return image-linked symbol records from DeepScoresV2 Dense native annotations."""
    _require(isinstance(payload, Mapping), "DeepScores payload must be an object")
    images = payload.get("images")
    annotations = payload.get("annotations")
    categories = payload.get("categories")
    _require(isinstance(images, list), "DeepScores images must be a list")
    _require(isinstance(annotations, Mapping), "DeepScores annotations must be an ID-keyed object")
    _require(isinstance(categories, Mapping), "DeepScores categories must be an ID-keyed object")

    records: list[dict[str, Any]] = []
    image_rows: dict[str, dict[str, Any]] = {}
    missing_annotation_ids: list[str] = []
    for index, raw_row in enumerate(images):
        _require(isinstance(raw_row, Mapping), f"image row {index} must be an object")
        row = dict(raw_row)
        name = _image_name(row)
        _require(bool(name), f"image row {index} has no filename")
        iid = _image_id(row, index)
        ann_ids = row.get("ann_ids") or []
        _require(isinstance(ann_ids, (list, tuple)), f"ann_ids must be a list for {name}")
        image_rows[iid] = row
        for ann_id in ann_ids:
            annotation = annotations.get(str(ann_id), annotations.get(ann_id))
            if not isinstance(annotation, Mapping):
                missing_annotation_ids.append(str(ann_id))
                continue
            bbox = native_bbox_xywh(annotation)
            if bbox is None:
                continue
            category_ids = _category_ids(annotation)
            if not category_ids:
                continue
            x, y, w, h = bbox
            if x < 0 or y < 0 or w < 1 or h < 1:
                continue
            for category_id in category_ids:
                records.append({
                    "imageId": iid,
                    "imageName": name,
                    "annotationId": str(ann_id),
                    "categoryId": category_id,
                    "categoryName": _category_name(categories, category_id),
                    "bbox": [x, y, w, h],
                })

    _require(bool(image_rows), "DeepScores image table is empty")
    _require(bool(records), "no usable DeepScores symbol annotations found")
    by_image: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_image.setdefault(record["imageName"], []).append(record)
    return {
        "images": image_rows,
        "records": records,
        "byImage": by_image,
        "missingAnnotationIds": sorted(set(missing_annotation_ids)),
        "schema": "deepscores-native-images-list-annotations-dict-ann_ids-a_bbox-ltrb",
    }


def rasterize_symbol_mask(
    width: int,
    height: int,
    records: Iterable[Mapping[str, Any]],
    *,
    pad_px: int = 1,
) -> np.ndarray:
    _require(width > 0 and height > 0, "mask dimensions must be positive")
    _require(pad_px >= 0, "mask padding must be non-negative")
    mask = np.zeros((height, width), dtype=np.float32)
    for record in records:
        bbox = record.get("bbox")
        if not isinstance(bbox, Sequence) or len(bbox) < 4:
            continue
        x, y, w, h = (float(v) for v in bbox[:4])
        left = max(0, int(math.floor(x)) - pad_px)
        top = max(0, int(math.floor(y)) - pad_px)
        right = min(width, int(math.ceil(x + w)) + pad_px)
        bottom = min(height, int(math.ceil(y + h)) + pad_px)
        if right > left and bottom > top:
            mask[top:bottom, left:right] = 1.0
    return mask


def hard_example_priority(record: Mapping[str, Any]) -> float:
    name = str(record.get("categoryName") or "").lower()
    bbox = record.get("bbox") or [0, 0, 0, 0]
    try:
        _, _, width, height = (float(v) for v in bbox[:4])
    except (TypeError, ValueError):
        width = height = 0.0
    score = 1.0
    if any(token in name for token in HARD_EXAMPLE_TOKENS):
        score += 3.0
    if 0 < min(width, height) <= 8:
        score += 2.0
    if 0 < width * height <= 256:
        score += 1.0
    return score


def centered_crop_box(
    image_width: int,
    image_height: int,
    bbox: Sequence[float],
    *,
    patch_size: int = DEFAULT_PATCH_SIZE,
) -> tuple[int, int, int, int]:
    _require(image_width > 0 and image_height > 0, "image dimensions must be positive")
    _require(patch_size > 0, "patch size must be positive")
    _require(len(bbox) >= 4, "bbox must contain x,y,w,h")
    x, y, w, h = (float(v) for v in bbox[:4])
    cx, cy = x + w / 2.0, y + h / 2.0
    crop_w = min(patch_size, image_width)
    crop_h = min(patch_size, image_height)
    left = int(round(cx - crop_w / 2.0))
    top = int(round(cy - crop_h / 2.0))
    left = min(max(0, left), max(0, image_width - crop_w))
    top = min(max(0, top), max(0, image_height - crop_h))
    return left, top, crop_w, crop_h


def _random_crop_box(rng: random.Random, image_width: int, image_height: int, patch_size: int) -> tuple[int, int, int, int]:
    crop_w, crop_h = min(patch_size, image_width), min(patch_size, image_height)
    left = 0 if image_width == crop_w else rng.randint(0, image_width - crop_w)
    top = 0 if image_height == crop_h else rng.randint(0, image_height - crop_h)
    return left, top, crop_w, crop_h


def build_patch_plan(
    image_sizes: Mapping[str, Sequence[int]],
    records_by_image: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    patch_count: int,
    symbol_fraction: float = DEFAULT_SYMBOL_FRACTION,
    patch_size: int = DEFAULT_PATCH_SIZE,
    seed: str = "stage11-v2-symbol-preservation",
) -> list[dict[str, Any]]:
    """Create a deterministic exact-mix patch plan with hard-example-weighted symbol crops."""
    _require(patch_count > 0, "patch_count must be positive")
    _require(0.0 <= symbol_fraction <= 1.0, "symbol_fraction must be in [0,1]")
    _require(bool(image_sizes), "image size catalog is empty")
    rng = random.Random(int.from_bytes(hashlib.sha256(seed.encode()).digest()[:8], "big"))
    image_names = sorted(image_sizes)
    symbol_records = [
        record for name in image_names for record in records_by_image.get(name, [])
        if name in image_sizes
    ]
    symbol_count = int(round(patch_count * symbol_fraction))
    symbol_count = min(symbol_count, patch_count)
    if symbol_count:
        _require(bool(symbol_records), "symbol-centered sampling requested but no symbol records exist")

    modes = ["symbol" for _ in range(symbol_count)] + ["random" for _ in range(patch_count - symbol_count)]
    rng.shuffle(modes)
    weights = [hard_example_priority(record) for record in symbol_records]
    plan: list[dict[str, Any]] = []
    for index, mode in enumerate(modes):
        if mode == "symbol":
            record = rng.choices(symbol_records, weights=weights, k=1)[0]
            name = str(record["imageName"])
            width, height = (int(v) for v in image_sizes[name][:2])
            crop = centered_crop_box(width, height, record["bbox"], patch_size=patch_size)
            plan.append({
                "index": index,
                "mode": mode,
                "imageName": name,
                "cropXYWH": list(crop),
                "annotationId": str(record.get("annotationId") or ""),
                "categoryName": str(record.get("categoryName") or ""),
                "hardExamplePriority": hard_example_priority(record),
            })
        else:
            name = rng.choice(image_names)
            width, height = (int(v) for v in image_sizes[name][:2])
            crop = _random_crop_box(rng, width, height, patch_size)
            plan.append({"index": index, "mode": mode, "imageName": name, "cropXYWH": list(crop)})
    return plan


def sampling_mix(plan: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(plan)
    _require(total > 0, "patch plan is empty")
    symbol = sum(1 for item in plan if item.get("mode") == "symbol")
    random_count = sum(1 for item in plan if item.get("mode") == "random")
    _require(symbol + random_count == total, "patch plan contains unsupported sampling mode")
    return {
        "total": total,
        "symbolCentered": symbol,
        "random": random_count,
        "symbolFraction": symbol / total,
        "randomFraction": random_count / total,
    }


def _as_gray_float(array: Any) -> np.ndarray:
    value = np.asarray(array, dtype=np.float32)
    _require(value.ndim in {2, 3, 4}, "loss arrays must be grayscale image tensors")
    _require(np.all(np.isfinite(value)), "loss arrays contain non-finite values")
    return value


def _edge_components(value: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    dx = np.diff(value, axis=-1, append=value[..., -1:])
    dy = np.diff(value, axis=-2, append=value[..., -1:, :])
    return dx, dy


def composite_loss_numpy(
    prediction: Any,
    target: Any,
    symbol_mask: Any,
    *,
    weights: LossWeights = LossWeights(),
    ink_threshold: float = INK_TARGET_THRESHOLD,
) -> dict[str, float]:
    """Reference V2 objective. White=1, ink=0; erasure means prediction > target."""
    weights.validated()
    pred = _as_gray_float(prediction)
    truth = _as_gray_float(target)
    mask = _as_gray_float(symbol_mask)
    _require(pred.shape == truth.shape, "prediction/target shape mismatch")
    while mask.ndim < truth.ndim:
        mask = np.expand_dims(mask, axis=0)
    try:
        mask = np.broadcast_to(mask, truth.shape).astype(np.float32, copy=False)
    except ValueError as exc:
        raise Stage11V2SymbolPreservationError("symbol mask shape mismatch") from exc
    mask = (mask > 0.5).astype(np.float32)

    pixel_l1 = float(np.mean(np.abs(pred - truth)))
    pdx, pdy = _edge_components(pred)
    tdx, tdy = _edge_components(truth)
    edge_l1 = float(0.5 * (np.mean(np.abs(pdx - tdx)) + np.mean(np.abs(pdy - tdy))))
    symbol_den = max(float(mask.sum()), 1.0)
    symbol_region_l1 = float((np.abs(pred - truth) * mask).sum() / symbol_den)
    target_ink = ((truth < ink_threshold).astype(np.float32) * mask)
    ink_den = max(float(target_ink.sum()), 1.0)
    ink_recall_penalty = float((np.maximum(pred - truth, 0.0) * target_ink).sum() / ink_den)
    components = {
        "pixel_l1": pixel_l1,
        "edge_l1": edge_l1,
        "symbol_region_l1": symbol_region_l1,
        "ink_recall_penalty": ink_recall_penalty,
    }
    weight_map = weights.as_dict()
    total = float(sum(weight_map[key] * components[key] for key in components))
    return {"total": total, **components}


def composite_loss_torch(prediction: Any, target: Any, symbol_mask: Any, *, weights: LossWeights = LossWeights(), ink_threshold: float = INK_TARGET_THRESHOLD) -> dict[str, Any]:
    """Differentiable torch equivalent, imported lazily for Colab only."""
    weights.validated()
    try:
        import torch
        import torch.nn.functional as F
    except ImportError as exc:  # pragma: no cover - production/CI need not ship torch
        raise RuntimeError("PyTorch is required only for Stage 11 V2 Colab training") from exc
    if prediction.shape != target.shape:
        raise Stage11V2SymbolPreservationError("prediction/target shape mismatch")
    mask = symbol_mask.float()
    while mask.ndim < target.ndim:
        mask = mask.unsqueeze(0)
    mask = torch.broadcast_to(mask, target.shape)
    pixel = F.l1_loss(prediction, target)
    pdx = torch.diff(prediction, dim=-1, append=prediction[..., -1:])
    pdy = torch.diff(prediction, dim=-2, append=prediction[..., -1:, :])
    tdx = torch.diff(target, dim=-1, append=target[..., -1:])
    tdy = torch.diff(target, dim=-2, append=target[..., -1:, :])
    edge = 0.5 * (F.l1_loss(pdx, tdx) + F.l1_loss(pdy, tdy))
    symbol_den = mask.sum().clamp_min(1.0)
    symbol = (torch.abs(prediction - target) * mask).sum() / symbol_den
    target_ink = (target < ink_threshold).float() * mask
    ink = (torch.relu(prediction - target) * target_ink).sum() / target_ink.sum().clamp_min(1.0)
    wm = weights.as_dict()
    total = wm["pixel_l1"] * pixel + wm["edge_l1"] * edge + wm["symbol_region_l1"] * symbol + wm["ink_recall_penalty"] * ink
    return {"total": total, "pixel_l1": pixel, "edge_l1": edge, "symbol_region_l1": symbol, "ink_recall_penalty": ink}


def build_residual_unet(*, base_channels: int = 32) -> Any:
    """Return the V1-compatible residual U-Net architecture without making torch a runtime dependency."""
    _require(base_channels >= 8 and base_channels % 8 == 0, "base_channels must be >=8 and divisible by 8")
    try:
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("PyTorch is required only for Stage 11 V2 Colab training") from exc

    class ConvBlock(nn.Module):
        def __init__(self, in_ch: int, out_ch: int):
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, 3, padding=1), nn.GroupNorm(8, out_ch), nn.SiLU(),
                nn.Conv2d(out_ch, out_ch, 3, padding=1), nn.GroupNorm(8, out_ch), nn.SiLU(),
            )
        def forward(self, x: Any) -> Any:
            return self.net(x)

    class ResidualUNet(nn.Module):
        def __init__(self):
            super().__init__()
            b = base_channels
            self.e1 = ConvBlock(1, b); self.e2 = ConvBlock(b, 2*b); self.e3 = ConvBlock(2*b, 4*b)
            self.mid = ConvBlock(4*b, 8*b); self.d3 = ConvBlock(12*b, 4*b); self.d2 = ConvBlock(6*b, 2*b); self.d1 = ConvBlock(3*b, b)
            self.out = nn.Conv2d(b, 1, 1)
        def forward(self, x: Any) -> Any:
            a = self.e1(x); b = self.e2(F.max_pool2d(a, 2)); c = self.e3(F.max_pool2d(b, 2)); d = self.mid(F.max_pool2d(c, 2))
            d = self.d3(torch.cat([F.interpolate(d, size=c.shape[-2:], mode="bilinear", align_corners=False), c], 1))
            d = self.d2(torch.cat([F.interpolate(d, size=b.shape[-2:], mode="bilinear", align_corners=False), b], 1))
            d = self.d1(torch.cat([F.interpolate(d, size=a.shape[-2:], mode="bilinear", align_corners=False), a], 1))
            return torch.clamp(x + torch.tanh(self.out(d)) * 0.5, 0.0, 1.0)

    return ResidualUNet()


def development_gate(metrics: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed: preservation is primary, restoration usefulness must remain positive."""
    required = ("inkRecallDelta", "pixelL1ImprovementPercent", "edgeL1ImprovementPercent")
    for key in required:
        _require(key in metrics, f"development metric missing: {key}")
    ink_delta = float(metrics["inkRecallDelta"])
    pixel_improvement = float(metrics["pixelL1ImprovementPercent"])
    edge_improvement = float(metrics["edgeL1ImprovementPercent"])
    psnr_delta = float(metrics.get("psnrDeltaDb", 0.0))
    reasons: list[str] = []
    if ink_delta < -0.05:
        reasons.append("ink_recall_delta_below_v2_target")
    if pixel_improvement <= 0.0:
        reasons.append("pixel_restoration_not_meaningfully_better_than_noisy_baseline")
    if edge_improvement < -5.0:
        reasons.append("edge_restoration_materially_regressed")
    if psnr_delta < -0.5:
        reasons.append("psnr_materially_regressed")
    passed = not reasons
    return {
        "status": "pass" if passed else "review_required",
        "developmentGatePassed": passed,
        "eligibleForFrozenHeldOutEvaluation": passed,
        "inkRecallDeltaTarget": -0.05,
        "idealInkRecallDelta": -0.02,
        "reasonCodes": reasons,
    }


def validate_evaluation_provenance(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Reject held-out/Stage9A evidence if identity or no-mutation claims are incomplete."""
    for key in ("commitSha", "datasetMd5", "configSha256", "checkpointSha256", "device"):
        _require(bool(str(evidence.get(key) or "").strip()), f"evaluation provenance missing {key}")
    _require(evidence.get("datasetMd5") == EXPECTED_ARCHIVE_MD5, "dataset MD5 mismatch")
    _require(evidence.get("weightsMutated") is False, "evaluation mutated model weights")
    _require(evidence.get("optimizerCreated") is False, "evaluation optimizer is forbidden")
    _require(evidence.get("backpropagationExecuted") is False, "evaluation backpropagation is forbidden")
    _require(evidence.get("heldOutUsedForTraining") is False, "held-out training is forbidden")
    _require(evidence.get("heldOutUsedForTuning") is False, "held-out tuning is forbidden")
    before = str(evidence.get("modelStateSha256Before") or "")
    after = str(evidence.get("modelStateSha256After") or "")
    _require(bool(before) and before == after, "model state hash changed during evaluation")
    return {"provenanceValid": True, "weightsMutated": False, "heldOutTuning": False}
