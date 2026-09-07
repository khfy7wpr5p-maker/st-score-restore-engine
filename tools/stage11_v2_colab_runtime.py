"""Colab-only Stage 11 V2 Residual U-Net train/evaluate runtime.

Modes are deliberately separated. `train` can only use the official train family split;
`dev` can assess/tune the development split; `heldout` and `stage9a` require a passing
frozen development gate and never create an optimizer or run backpropagation.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import tarfile
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage11_deepscores_dense import split_source_families
from st_score_restore.stage11_v2_symbol_preservation import (
    EXPECTED_ARCHIVE_MD5,
    LossWeights,
    build_residual_unet,
    centered_crop_box,
    composite_loss_torch,
    development_gate,
    hard_example_priority,
    parse_deepscores_native_annotations,
    rasterize_symbol_mask,
    stable_config_sha256,
    validate_evaluation_provenance,
)

DATA_ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_TRAINING_DATA/DeepScoresV2/dense")
LEGACY_ARCHIVE = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_TRAINING_DATA/ds2_dense.tar.gz")
TRAIN_OUT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_TRAINING_OUTPUT/deepscoresv2_dense_residual_unet_v2_symbol_preservation")
DEV_OUT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/deepscoresv2_dense_v2_dev")
HELD_OUT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/deepscoresv2_dense_v2_heldout")
STAGE9A_OUT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/deepscoresv2_dense_v2_stage9a")
EXTRACT_ROOT = Path("/content/st_score_restore_deepscoresv2_dense_v2")
SEED = 20260907
PATCH = 512
BATCH = 4
EPOCHS = 20
TRAIN_PATCHES_PER_EPOCH = 2048
DEV_PATCHES = 512
HELDOUT_PATCHES = 704
STAGE9A_MAX_SYMBOLS = 1024

CONFIG = {
    "modelFamily": "Residual U-Net",
    "version": "V2",
    "baseChannels": 32,
    "patchSize": PATCH,
    "symbolCenteredFraction": 0.5,
    "loss": LossWeights().as_dict(),
    "inkThreshold": 0.75,
    "datasetMd5": EXPECTED_ARCHIVE_MD5,
    "splitSeed": "st-score-restore-stage11-deepscoresv2-dense-v1",
}
CONFIG_SHA256 = stable_config_sha256(CONFIG)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def file_hash(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        while block := f.read(8 << 20):
            h.update(block)
    return h.hexdigest()


def git_sha() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


def model_state_sha256(model: Any) -> str:
    h = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        h.update(name.encode("utf-8")); h.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def find_archive() -> Path:
    candidates = [DATA_ROOT / "ds2_dense.tar.gz", LEGACY_ARCHIVE]
    candidates.extend(DATA_ROOT.rglob("ds2_dense.tar.gz") if DATA_ROOT.exists() else [])
    present = []
    for candidate in candidates:
        if candidate.exists() and candidate not in present:
            present.append(candidate)
    if not present:
        raise FileNotFoundError("ds2_dense.tar.gz not found under admitted Stage 11 Drive roots")
    archive = present[0]
    md5 = file_hash(archive, "md5")
    if md5 != EXPECTED_ARCHIVE_MD5:
        raise RuntimeError(f"DeepScoresV2 Dense MD5 mismatch: {md5}")
    return archive


def safe_extract(archive: Path) -> None:
    marker = EXTRACT_ROOT / ".md5-ok"
    if marker.exists() and marker.read_text().strip() == EXPECTED_ARCHIVE_MD5:
        return
    EXTRACT_ROOT.mkdir(parents=True, exist_ok=True)
    base = EXTRACT_ROOT.resolve()
    with tarfile.open(archive, "r:gz") as tf:
        for member in tf.getmembers():
            name = member.name.replace("\\", "/")
            if not name or name.startswith("/") or ".." in Path(name).parts or member.issym() or member.islnk() or member.isdev():
                raise RuntimeError(f"unsafe tar member: {member.name}")
            destination = (EXTRACT_ROOT / name).resolve()
            if destination != base and base not in destination.parents:
                raise RuntimeError(f"tar escape: {member.name}")
        tf.extractall(EXTRACT_ROOT)
    marker.write_text(EXPECTED_ARCHIVE_MD5, encoding="utf-8")


def load_dataset_truth() -> dict[str, Any]:
    archive = find_archive(); safe_extract(archive)
    train_jsons = list(EXTRACT_ROOT.rglob("deepscores_train.json"))
    test_jsons = list(EXTRACT_ROOT.rglob("deepscores_test.json"))
    if len(train_jsons) != 1 or len(test_jsons) != 1:
        raise RuntimeError(f"expected one train/test annotation JSON, got train={len(train_jsons)} test={len(test_jsons)}")
    train_json, test_json = train_jsons[0], test_jsons[0]
    train_payload = json.loads(train_json.read_text(encoding="utf-8")); test_payload = json.loads(test_json.read_text(encoding="utf-8"))
    train_ann = parse_deepscores_native_annotations(train_payload); test_ann = parse_deepscores_native_annotations(test_payload)

    def names(payload: dict[str, Any]) -> list[str]:
        result = []
        for row in payload["images"]:
            name = row.get("filename") or row.get("file_name") or row.get("img_name") or row.get("name")
            if name: result.append(str(name))
        return result

    split = split_source_families(names(train_payload), names(test_payload), development_percent=10)
    if split["counts"]["heldOut"] != 352:
        raise RuntimeError(f"official held-out count changed: {split['counts']['heldOut']}")
    return {
        "archive": archive, "trainJson": train_json, "testJson": test_json,
        "trainPayload": train_payload, "testPayload": test_payload,
        "trainAnnotations": train_ann, "testAnnotations": test_ann, "split": split,
    }


def resolve_image(annotation_json: Path, name: str) -> Path:
    roots = [annotation_json.parent / "images", annotation_json.parent]
    for root in roots:
        candidate = root / name
        if candidate.exists(): return candidate
    matches = list(annotation_json.parent.rglob(Path(name).name))
    if len(matches) == 1: return matches[0]
    raise FileNotFoundError(name)


def crop_and_pad(image: Any, crop: tuple[int, int, int, int], *, fill: int) -> Any:
    from PIL import ImageOps
    left, top, width, height = crop
    out = image.crop((left, top, left + width, top + height))
    pad_right, pad_bottom = PATCH - out.width, PATCH - out.height
    if pad_right < 0 or pad_bottom < 0: raise RuntimeError("crop exceeds patch size")
    if pad_right or pad_bottom:
        out = ImageOps.expand(out, border=(0, 0, pad_right, pad_bottom), fill=fill)
    return out


def mask_for_crop(records: list[dict[str, Any]], crop: tuple[int, int, int, int]) -> Any:
    from PIL import Image
    import numpy as np
    left, top, width, height = crop
    local = []
    for record in records:
        x, y, w, h = (float(v) for v in record["bbox"])
        if x + w <= left or y + h <= top or x >= left + width or y >= top + height: continue
        local.append({"bbox": [x - left, y - top, w, h]})
    mask = rasterize_symbol_mask(width, height, local, pad_px=1)
    if width != PATCH or height != PATCH:
        padded = np.zeros((PATCH, PATCH), dtype="float32"); padded[:height, :width] = mask; mask = padded
    return Image.fromarray((mask * 255).astype("uint8"), mode="L")


def degrade(clean: Any, rng: random.Random) -> Any:
    """Realistic camera degradation constrained not to destroy symbols beyond recognition."""
    import cv2
    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter
    image = ImageEnhance.Brightness(clean).enhance(rng.uniform(0.82, 1.18))
    image = ImageEnhance.Contrast(image).enhance(rng.uniform(0.85, 1.15))
    image = image.filter(ImageFilter.GaussianBlur(rng.uniform(0.15, 1.35)))
    array = np.asarray(image, dtype=np.float32) / 255.0
    h, w = array.shape
    p = rng.uniform(0.0, 0.012) * min(h, w)
    src = np.float32([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]])
    dst = src + np.float32([[rng.uniform(-p,p), rng.uniform(-p,p)] for _ in range(4)])
    matrix = cv2.getPerspectiveTransform(src, dst)
    array = cv2.warpPerspective(array, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    yy, xx = np.mgrid[:h, :w]; cx, cy = rng.uniform(0,w), rng.uniform(0,h)
    radius = np.sqrt((xx-cx)**2 + (yy-cy)**2); radius /= max(float(radius.max()), 1.0)
    array *= 1.0 - rng.uniform(0.0, 0.16) * (1.0 - radius)
    if rng.random() < 0.30:
        k = rng.choice((3, 5)); kernel = np.zeros((k,k), np.float32); kernel[k//2, :] = 1.0/k
        array = cv2.filter2D(array, -1, kernel)
    if rng.random() < 0.45:
        scale = rng.uniform(0.65, 0.9); small = cv2.resize(array, (max(16,int(w*scale)), max(16,int(h*scale))), interpolation=cv2.INTER_AREA)
        array = cv2.resize(small, (w,h), interpolation=cv2.INTER_CUBIC)
    sigma = rng.uniform(0.002, 0.022)
    array += np.random.default_rng(rng.randrange(2**32)).normal(0.0, sigma, array.shape)
    array = np.clip(array, 0.0, 1.0)
    encoded_ok, encoded = cv2.imencode(".jpg", (array*255).astype("uint8"), [int(cv2.IMWRITE_JPEG_QUALITY), rng.randint(60, 95)])
    if not encoded_ok: raise RuntimeError("JPEG degradation encode failed")
    decoded = cv2.imdecode(encoded, cv2.IMREAD_GRAYSCALE)
    return Image.fromarray(decoded, mode="L")


def make_dataset(data: dict[str, Any], split_name: str, patch_count: int, *, symbol_only: bool = False) -> Any:
    import numpy as np
    import torch
    from PIL import Image
    from torch.utils.data import Dataset
    if split_name == "heldOut":
        names = list(data["split"]["heldOut"]); ann = data["testAnnotations"]; annotation_json = data["testJson"]
    else:
        names = list(data["split"][split_name]); ann = data["trainAnnotations"]; annotation_json = data["trainJson"]
    by_image = ann["byImage"]
    symbol_records = [record for name in names for record in by_image.get(name, [])]
    if not symbol_records: raise RuntimeError(f"no symbol records in {split_name}")
    symbol_weights = [hard_example_priority(record) for record in symbol_records]

    class PatchDataset(Dataset):
        def __len__(self): return patch_count
        def __getitem__(self, index: int):
            rng = random.Random(SEED * 1000003 + index + {"train":0,"development":10_000_000,"heldOut":20_000_000}[split_name])
            symbol_mode = symbol_only or index % 2 == 1
            if symbol_mode:
                record = rng.choices(symbol_records, weights=symbol_weights, k=1)[0]; name = record["imageName"]
            else:
                name = rng.choice(names); record = None
            path = resolve_image(annotation_json, name)
            with Image.open(path) as source: clean_page = source.convert("L")
            if record is not None:
                crop = centered_crop_box(clean_page.width, clean_page.height, record["bbox"], patch_size=PATCH)
            else:
                cw, ch = min(PATCH, clean_page.width), min(PATCH, clean_page.height)
                left = 0 if clean_page.width == cw else rng.randint(0, clean_page.width-cw); top = 0 if clean_page.height == ch else rng.randint(0, clean_page.height-ch)
                crop = (left, top, cw, ch)
            clean = crop_and_pad(clean_page, crop, fill=255)
            mask = mask_for_crop(by_image.get(name, []), crop)
            noisy = degrade(clean, rng)
            def tensor(im): return torch.from_numpy(np.asarray(im, dtype=np.float32)/255.0).unsqueeze(0)
            return tensor(noisy), tensor(clean), tensor(mask), {"imageName": name, "mode": "symbol" if symbol_mode else "random"}
    return PatchDataset()


def evaluate(model: Any, loader: Any, device: Any, *, progress_path: Path | None = None) -> dict[str, float]:
    import torch
    import torch.nn.functional as F
    keys = ("baselinePixelL1","restoredPixelL1","baselineEdgeL1","restoredEdgeL1","baselineMse","restoredMse","baselineInkRecall","restoredInkRecall","baselineFalseInkRate","restoredFalseInkRate")
    totals = {k: 0.0 for k in keys}; count = 0; completed_batches = 0
    if progress_path is not None and progress_path.exists():
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        if progress.get("configSha256") != CONFIG_SHA256 or progress.get("checkpointSha256") != file_hash(TRAIN_OUT / "best.pt"):
            raise RuntimeError("evaluation progress provenance mismatch")
        completed_batches = int(progress.get("completedBatches", 0)); count = int(progress.get("count", 0))
        stored = progress.get("totals") or {}
        totals = {k: float(stored.get(k, 0.0)) for k in keys}
    def edge(x):
        dx = torch.diff(x, dim=-1, append=x[..., -1:]); dy = torch.diff(x, dim=-2, append=x[..., -1:, :]); return 0.5*(dx.abs()+dy.abs())
    with torch.inference_mode():
        for batch_index, (noisy, target, mask, _meta) in enumerate(loader):
            if batch_index < completed_batches: continue
            noisy, target, mask = noisy.to(device), target.to(device), mask.to(device)
            restored = model(noisy)
            symbol = mask > 0.5; ink = (target < 0.75) & symbol; white = (target > 0.95) & symbol
            def metrics(pred):
                return (
                    F.l1_loss(pred,target).item(), F.l1_loss(edge(pred),edge(target)).item(), F.mse_loss(pred,target).item(),
                    (((pred<0.85)&ink).float().sum()/ink.float().sum().clamp_min(1)).item(),
                    (((pred<0.80)&white).float().sum()/white.float().sum().clamp_min(1)).item(),
                )
            b = metrics(noisy); r = metrics(restored)
            for key, value in zip(("baselinePixelL1","baselineEdgeL1","baselineMse","baselineInkRecall","baselineFalseInkRate"), b): totals[key] += value
            for key, value in zip(("restoredPixelL1","restoredEdgeL1","restoredMse","restoredInkRecall","restoredFalseInkRate"), r): totals[key] += value
            count += 1; completed_batches = batch_index + 1
            if progress_path is not None and (completed_batches % 8 == 0 or completed_batches == len(loader)):
                atomic_json(progress_path,{"schemaVersion":"stage11.v2.eval-progress.v1","configSha256":CONFIG_SHA256,"checkpointSha256":file_hash(TRAIN_OUT / "best.pt"),"completedBatches":completed_batches,"count":count,"totals":totals,"weightsMutated":False,"optimizerCreated":False,"backpropagationExecuted":False})
    if count == 0: raise RuntimeError("evaluation produced no batches")
    avg = {k:v/count for k,v in totals.items()}
    avg.update({
        "pixelL1ImprovementPercent": 100.0*(avg["baselinePixelL1"]-avg["restoredPixelL1"])/max(avg["baselinePixelL1"],1e-12),
        "edgeL1ImprovementPercent": 100.0*(avg["baselineEdgeL1"]-avg["restoredEdgeL1"])/max(avg["baselineEdgeL1"],1e-12),
        "mseImprovementPercent": 100.0*(avg["baselineMse"]-avg["restoredMse"])/max(avg["baselineMse"],1e-12),
        "inkRecallDelta": avg["restoredInkRecall"]-avg["baselineInkRecall"],
        "falseInkRateDelta": avg["restoredFalseInkRate"]-avg["baselineFalseInkRate"],
    })
    return avg


def load_frozen_model(device: Any) -> tuple[Any, dict[str, Any], Path]:
    import torch
    best = TRAIN_OUT / "best.pt"
    if not best.exists(): raise FileNotFoundError(best)
    checkpoint = torch.load(best, map_location=device)
    if checkpoint.get("datasetMd5") != EXPECTED_ARCHIVE_MD5 or checkpoint.get("configSha256") != CONFIG_SHA256:
        raise RuntimeError("checkpoint/config/dataset provenance mismatch")
    model = build_residual_unet(base_channels=32).to(device); model.load_state_dict(checkpoint["model"]); model.eval()
    return model, checkpoint, best


def train_mode(data: dict[str, Any]) -> None:
    import torch
    from torch.utils.data import DataLoader
    TRAIN_OUT.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda": raise RuntimeError("V2 training requires a Colab GPU; evaluation notebooks support CPU fallback")
    train_ds = make_dataset(data, "train", TRAIN_PATCHES_PER_EPOCH); dev_ds = make_dataset(data, "development", DEV_PATCHES)
    train_loader = DataLoader(train_ds, batch_size=BATCH, shuffle=False, num_workers=2, pin_memory=True)
    dev_loader = DataLoader(dev_ds, batch_size=BATCH, shuffle=False, num_workers=2, pin_memory=True)
    model = build_residual_unet(base_channels=32).to(device); optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4)
    start_epoch = 0; history = []
    last = TRAIN_OUT / "last.pt"; best = TRAIN_OUT / "best.pt"; history_path = TRAIN_OUT / "history.v2.json"
    if last.exists():
        checkpoint = torch.load(last, map_location=device)
        if checkpoint.get("datasetMd5") != EXPECTED_ARCHIVE_MD5 or checkpoint.get("configSha256") != CONFIG_SHA256: raise RuntimeError("resume checkpoint provenance mismatch")
        model.load_state_dict(checkpoint["model"]); optimizer.load_state_dict(checkpoint["optimizer"]); start_epoch = int(checkpoint["epoch"]) + 1
        if history_path.exists(): history = json.loads(history_path.read_text(encoding="utf-8")).get("epochs", [])
    best_loss = min([float(row["devLoss"]) for row in history], default=float("inf"))
    for epoch in range(start_epoch, EPOCHS):
        model.train(); train_total = 0.0; train_batches = 0
        for noisy, target, mask, _meta in train_loader:
            noisy, target, mask = noisy.to(device), target.to(device), mask.to(device); optimizer.zero_grad(set_to_none=True)
            pred = model(noisy); losses = composite_loss_torch(pred,target,mask); losses["total"].backward(); optimizer.step()
            train_total += float(losses["total"].detach()); train_batches += 1
        model.eval(); dev_total = 0.0; dev_batches = 0
        with torch.inference_mode():
            for noisy,target,mask,_meta in dev_loader:
                noisy,target,mask = noisy.to(device),target.to(device),mask.to(device); losses = composite_loss_torch(model(noisy),target,mask)
                dev_total += float(losses["total"]); dev_batches += 1
        row = {"epoch":epoch,"trainLoss":train_total/max(train_batches,1),"devLoss":dev_total/max(dev_batches,1),"device":torch.cuda.get_device_name(0)}; history.append(row)
        payload = {"epoch":epoch,"model":model.state_dict(),"optimizer":optimizer.state_dict(),"datasetMd5":EXPECTED_ARCHIVE_MD5,"configSha256":CONFIG_SHA256,"commitSha":git_sha()}
        tmp = TRAIN_OUT / "last.pt.tmp"; torch.save(payload,tmp); os.replace(tmp,last)
        if row["devLoss"] < best_loss:
            best_loss = row["devLoss"]; tmp_best = TRAIN_OUT / "best.pt.tmp"; torch.save(payload,tmp_best); os.replace(tmp_best,best)
        atomic_json(history_path,{"schemaVersion":"stage11.v2.training-history.v1","config":CONFIG,"configSha256":CONFIG_SHA256,"commitSha":git_sha(),"datasetMd5":EXPECTED_ARCHIVE_MD5,"epochs":history})
        print(row)
    evidence = {"artifactType":"stage11_v2_training_evidence","status":"completed","commitSha":git_sha(),"datasetMd5":EXPECTED_ARCHIVE_MD5,"configSha256":CONFIG_SHA256,"device":torch.cuda.get_device_name(0),"epochsCompleted":len(history),"bestCheckpointSha256":file_hash(best),"lastCheckpointSha256":file_hash(last),"heldOutUsedForTraining":False,"heldOutUsedForTuning":False,"historyPath":str(history_path)}
    atomic_json(TRAIN_OUT/"training_evidence.v2.json",evidence); print(json.dumps(evidence,indent=2))


def evaluation_mode(data: dict[str, Any], mode: str) -> None:
    import torch
    from torch.utils.data import DataLoader
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, checkpoint, best = load_frozen_model(device); before = model_state_sha256(model)
    if mode == "dev":
        dataset = make_dataset(data,"development",DEV_PATCHES); out_root = DEV_OUT
    else:
        gate_path = DEV_OUT / "development_evidence.v2.json"
        if not gate_path.exists(): raise RuntimeError("development evidence missing; held-out/Stage9A remain gated")
        dev_evidence = json.loads(gate_path.read_text(encoding="utf-8"))
        if not (dev_evidence.get("gate") or {}).get("eligibleForFrozenHeldOutEvaluation"): raise RuntimeError("development gate did not pass; frozen held-out/Stage9A remain forbidden")
        if mode == "heldout": dataset = make_dataset(data,"heldOut",HELDOUT_PATCHES); out_root = HELD_OUT
        elif mode == "stage9a": dataset = make_dataset(data,"heldOut",STAGE9A_MAX_SYMBOLS,symbol_only=True); out_root = STAGE9A_OUT
        else: raise RuntimeError(mode)
    loader = DataLoader(dataset,batch_size=BATCH,shuffle=False,num_workers=2,pin_memory=device.type=="cuda")
    progress_path = out_root / f"{mode}_progress.v2.json"
    metrics = evaluate(model,loader,device,progress_path=progress_path); after = model_state_sha256(model)
    base = {"commitSha":git_sha(),"datasetMd5":EXPECTED_ARCHIVE_MD5,"configSha256":CONFIG_SHA256,"checkpointSha256":file_hash(best),"device":torch.cuda.get_device_name(0) if device.type=="cuda" else "CPU","weightsMutated":before!=after,"optimizerCreated":False,"backpropagationExecuted":False,"heldOutUsedForTraining":False,"heldOutUsedForTuning":False,"modelStateSha256Before":before,"modelStateSha256After":after,"metrics":metrics}
    validate_evaluation_provenance(base)
    if mode == "dev":
        gate = development_gate(metrics); evidence = {"artifactType":"stage11_v2_development_evidence","status":"completed","gate":gate,**base}; path=DEV_OUT/"development_evidence.v2.json"
    elif mode == "heldout":
        evidence = {"artifactType":"stage11_v2_heldout_evidence","status":"completed","officialHeldOutImages":352,**base}; path=HELD_OUT/"heldout_evidence.v2.json"
    else:
        ink = float(metrics["inkRecallDelta"]); status = "pass" if ink >= -0.05 else "review_required"
        evidence = {"artifactType":"stage11_v2_stage9a_symbol_region_evidence","status":status,"proxyOnly":True,"omrCorrectnessImplied":False,"musicalTruthImplied":False,**base}; path=STAGE9A_OUT/"stage9a_symbol_region_evidence.v2.json"
    atomic_json(path,evidence); print(json.dumps(evidence,indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--mode",choices=("train","dev","heldout","stage9a"),required=True); args=parser.parse_args()
    data=load_dataset_truth()
    if args.mode=="train": train_mode(data)
    else: evaluation_mode(data,args.mode)


if __name__ == "__main__": main()
