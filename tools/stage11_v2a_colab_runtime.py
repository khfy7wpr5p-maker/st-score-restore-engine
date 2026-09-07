"""Stage 11 V2a conservative symbol-preservation fine-tune/evaluation runtime.

V2a warm-starts from the completed V2 best checkpoint and uses train/development only.
Frozen held-out and Stage 9A remain gated until V2a development evidence passes.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage11_v2_symbol_preservation import (
    EXPECTED_ARCHIVE_MD5,
    build_residual_unet,
    composite_loss_torch,
    stable_config_sha256,
    validate_evaluation_provenance,
)
from st_score_restore.stage11_v2a_preservation import (
    V2A_LEARNING_RATE,
    V2A_LOSS_WEIGHTS,
    V2A_MAX_EPOCHS,
    V2A_IDEAL_INK_RECALL_DELTA,
    v2a_candidate_gate,
    v2a_candidate_rank,
)

_spec = importlib.util.spec_from_file_location("stage11_v2_base_runtime", ROOT / "tools" / "stage11_v2_colab_runtime.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("could not load Stage 11 V2 base runtime")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

V2_SOURCE_OUT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_TRAINING_OUTPUT/deepscoresv2_dense_residual_unet_v2_symbol_preservation")
V2A_TRAIN_OUT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_TRAINING_OUTPUT/deepscoresv2_dense_residual_unet_v2a_symbol_preservation")
V2A_DEV_OUT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/deepscoresv2_dense_v2a_dev")
V2A_HELD_OUT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/deepscoresv2_dense_v2a_heldout")
V2A_STAGE9A_OUT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/deepscoresv2_dense_v2a_stage9a")
STATUS_PATH = V2A_TRAIN_OUT / "run_status.v2a.json"
EXPECTED_V2_BEST_SHA256 = "363cb63bff2367c1119a4eea449a19d468a802160f45b4fe1f2d98ab04fb894b"
PARTIAL_EVERY_BATCHES = 128
BATCH = 4
TRAIN_PATCHES_PER_EPOCH = 2048
DEV_PATCHES = 512
HELDOUT_PATCHES = 704
STAGE9A_MAX_SYMBOLS = 1024

CONFIG = {
    "modelFamily": "Residual U-Net",
    "version": "V2a",
    "baseChannels": 32,
    "patchSize": 512,
    "symbolCenteredFraction": 0.5,
    "loss": V2A_LOSS_WEIGHTS.as_dict(),
    "inkThreshold": 0.75,
    "datasetMd5": EXPECTED_ARCHIVE_MD5,
    "splitSeed": "st-score-restore-stage11-deepscoresv2-dense-v1",
    "warmStart": "V2 best.pt",
    "warmStartCheckpointSha256": EXPECTED_V2_BEST_SHA256,
    "learningRate": V2A_LEARNING_RATE,
    "maxEpochs": V2A_MAX_EPOCHS,
    "checkpointSelection": "v2a-development-gate-then-ink-recall-then-pixel-edge",
    "partialCheckpointEveryTrainBatches": PARTIAL_EVERY_BATCHES,
}
CONFIG_SHA256 = stable_config_sha256(CONFIG)


def git_sha() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


def status(stage: str, **extra: Any) -> None:
    payload = {
        "schemaVersion": "stage11.v2a.run-status.v1",
        "stage": stage,
        "updatedUnix": time.time(),
        "commitSha": git_sha(),
        "configSha256": CONFIG_SHA256,
        **extra,
    }
    base.atomic_json(STATUS_PATH, payload)
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def configure_base_runtime() -> None:
    base.TRAIN_OUT = V2A_TRAIN_OUT
    base.DEV_OUT = V2A_DEV_OUT
    base.HELD_OUT = V2A_HELD_OUT
    base.STAGE9A_OUT = V2A_STAGE9A_OUT
    base.CONFIG = CONFIG
    base.CONFIG_SHA256 = CONFIG_SHA256
    base.BATCH = BATCH
    base.TRAIN_PATCHES_PER_EPOCH = TRAIN_PATCHES_PER_EPOCH
    base.DEV_PATCHES = DEV_PATCHES
    base.HELDOUT_PATCHES = HELDOUT_PATCHES
    base.STAGE9A_MAX_SYMBOLS = STAGE9A_MAX_SYMBOLS


def resolve_device(torch: Any) -> Any:
    requested = os.environ.get("ST_SCORE_RESTORE_DEVICE", "auto").strip().lower()
    if requested not in {"auto", "cpu", "cuda"}:
        raise RuntimeError(f"unsupported ST_SCORE_RESTORE_DEVICE: {requested}")
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("ST_SCORE_RESTORE_DEVICE=cuda requested but CUDA is unavailable")
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def device_label(torch: Any, device: Any) -> str:
    return torch.cuda.get_device_name(0) if device.type == "cuda" else "CPU"


def verify_v2_source() -> Path:
    best = V2_SOURCE_OUT / "best.pt"
    if not best.exists():
        raise FileNotFoundError(f"V2 source checkpoint missing: {best}")
    sha = base.file_hash(best)
    if sha != EXPECTED_V2_BEST_SHA256:
        raise RuntimeError(f"V2 source checkpoint SHA mismatch: {sha}")
    return best


def _save_checkpoint(path: Path, payload: dict[str, Any]) -> None:
    import torch
    tmp = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, tmp)
    os.replace(tmp, path)


def _checkpoint_payload(model: Any, optimizer: Any, epoch: int, *, completed_train_batches: int = 0, train_total: float = 0.0, train_batches: int = 0) -> dict[str, Any]:
    return {
        "epoch": epoch,
        "completedTrainBatches": completed_train_batches,
        "trainTotal": train_total,
        "trainBatches": train_batches,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "datasetMd5": EXPECTED_ARCHIVE_MD5,
        "configSha256": CONFIG_SHA256,
        "commitSha": git_sha(),
        "sourceV2CheckpointSha256": EXPECTED_V2_BEST_SHA256,
    }


def train_mode(data: dict[str, Any]) -> None:
    import torch
    from torch.utils.data import DataLoader

    configure_base_runtime()
    source = verify_v2_source()
    V2A_TRAIN_OUT.mkdir(parents=True, exist_ok=True)
    device = resolve_device(torch)
    label = device_label(torch, device)

    train_ds = base.make_dataset(data, "train", TRAIN_PATCHES_PER_EPOCH)
    dev_ds = base.make_dataset(data, "development", DEV_PATCHES)
    train_loader = DataLoader(train_ds, batch_size=BATCH, shuffle=False, num_workers=2, pin_memory=device.type == "cuda")
    dev_loader = DataLoader(dev_ds, batch_size=BATCH, shuffle=False, num_workers=2, pin_memory=device.type == "cuda")

    model = build_residual_unet(base_channels=32).to(device)
    source_checkpoint = torch.load(source, map_location=device)
    if source_checkpoint.get("datasetMd5") != EXPECTED_ARCHIVE_MD5:
        raise RuntimeError("V2 source dataset provenance mismatch")
    model.load_state_dict(source_checkpoint["model"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=V2A_LEARNING_RATE)

    last = V2A_TRAIN_OUT / "last.pt"
    best = V2A_TRAIN_OUT / "best.pt"
    partial = V2A_TRAIN_OUT / "partial.pt"
    history_path = V2A_TRAIN_OUT / "history.v2a.json"
    history: list[dict[str, Any]] = []
    if history_path.exists():
        existing = json.loads(history_path.read_text(encoding="utf-8"))
        if existing.get("configSha256") != CONFIG_SHA256:
            raise RuntimeError("V2a history provenance mismatch")
        history = list(existing.get("epochs") or [])

    start_epoch = 0
    resume_batch = 0
    resume_train_total = 0.0
    resume_train_batches = 0
    if last.exists():
        ckpt = torch.load(last, map_location=device)
        if ckpt.get("configSha256") != CONFIG_SHA256 or ckpt.get("datasetMd5") != EXPECTED_ARCHIVE_MD5:
            raise RuntimeError("V2a last checkpoint provenance mismatch")
        model.load_state_dict(ckpt["model"])
        optimizer.load_state_dict(ckpt["optimizer"])
        start_epoch = int(ckpt["epoch"]) + 1
    if partial.exists():
        ckpt = torch.load(partial, map_location=device)
        if ckpt.get("configSha256") != CONFIG_SHA256 or ckpt.get("datasetMd5") != EXPECTED_ARCHIVE_MD5:
            raise RuntimeError("V2a partial checkpoint provenance mismatch")
        partial_epoch = int(ckpt["epoch"])
        if partial_epoch >= start_epoch:
            model.load_state_dict(ckpt["model"])
            optimizer.load_state_dict(ckpt["optimizer"])
            start_epoch = partial_epoch
            resume_batch = int(ckpt.get("completedTrainBatches", 0))
            resume_train_total = float(ckpt.get("trainTotal", 0.0))
            resume_train_batches = int(ckpt.get("trainBatches", 0))

    best_rank: tuple[float, float, float, float] | None = None
    for row in history:
        metrics = row.get("developmentMetrics") or {}
        if metrics:
            rank = v2a_candidate_rank(metrics)
            if best_rank is None or rank > best_rank:
                best_rank = rank

    consecutive_passes = 0
    status("training_started", device=label, startEpoch=start_epoch, maxEpochs=V2A_MAX_EPOCHS, resumeBatch=resume_batch)

    for epoch in range(start_epoch, V2A_MAX_EPOCHS):
        model.train()
        train_total = resume_train_total if epoch == start_epoch else 0.0
        train_batches = resume_train_batches if epoch == start_epoch else 0
        skip_batches = resume_batch if epoch == start_epoch else 0
        for batch_index, (noisy, target, mask, _meta) in enumerate(train_loader):
            if batch_index < skip_batches:
                continue
            noisy, target, mask = noisy.to(device), target.to(device), mask.to(device)
            optimizer.zero_grad(set_to_none=True)
            pred = model(noisy)
            losses = composite_loss_torch(pred, target, mask, weights=V2A_LOSS_WEIGHTS)
            losses["total"].backward()
            optimizer.step()
            train_total += float(losses["total"].detach())
            train_batches += 1
            completed = batch_index + 1
            if completed % 32 == 0 or completed == len(train_loader):
                status(
                    "training",
                    epoch=epoch,
                    completedTrainBatches=completed,
                    totalTrainBatches=len(train_loader),
                    trainLossSoFar=train_total / max(train_batches, 1),
                )
            if completed % PARTIAL_EVERY_BATCHES == 0 and completed < len(train_loader):
                _save_checkpoint(partial, _checkpoint_payload(model, optimizer, epoch, completed_train_batches=completed, train_total=train_total, train_batches=train_batches))

        model.eval()
        dev_total = 0.0
        dev_batches = 0
        with torch.inference_mode():
            for noisy, target, mask, _meta in dev_loader:
                noisy, target, mask = noisy.to(device), target.to(device), mask.to(device)
                losses = composite_loss_torch(model(noisy), target, mask, weights=V2A_LOSS_WEIGHTS)
                dev_total += float(losses["total"])
                dev_batches += 1

        metrics = base.evaluate(model, dev_loader, device, progress_path=None)
        gate = v2a_candidate_gate(metrics)
        rank = v2a_candidate_rank(metrics)
        row = {
            "epoch": epoch,
            "trainLoss": train_total / max(train_batches, 1),
            "devLoss": dev_total / max(dev_batches, 1),
            "developmentMetrics": metrics,
            "developmentGate": gate,
            "device": label,
        }
        history = [r for r in history if int(r.get("epoch", -1)) != epoch]
        history.append(row)
        history.sort(key=lambda r: int(r["epoch"]))

        payload = _checkpoint_payload(model, optimizer, epoch)
        _save_checkpoint(last, payload)
        if partial.exists():
            partial.unlink()
        if best_rank is None or rank > best_rank:
            best_rank = rank
            _save_checkpoint(best, payload)

        base.atomic_json(history_path, {
            "schemaVersion": "stage11.v2a.training-history.v1",
            "config": CONFIG,
            "configSha256": CONFIG_SHA256,
            "commitSha": git_sha(),
            "datasetMd5": EXPECTED_ARCHIVE_MD5,
            "sourceV2CheckpointSha256": EXPECTED_V2_BEST_SHA256,
            "epochs": history,
        })
        status(
            "epoch_complete",
            epoch=epoch,
            trainLoss=row["trainLoss"],
            devLoss=row["devLoss"],
            inkRecallDelta=metrics["inkRecallDelta"],
            pixelL1ImprovementPercent=metrics["pixelL1ImprovementPercent"],
            edgeL1ImprovementPercent=metrics["edgeL1ImprovementPercent"],
            gateStatus=gate["status"],
        )

        consecutive_passes = consecutive_passes + 1 if gate["developmentGatePassed"] else 0
        if metrics["inkRecallDelta"] >= V2A_IDEAL_INK_RECALL_DELTA and gate["developmentGatePassed"]:
            status("early_stop_ideal_target_reached", epoch=epoch, inkRecallDelta=metrics["inkRecallDelta"])
            break
        if consecutive_passes >= 2:
            status("early_stop_two_consecutive_passes", epoch=epoch, inkRecallDelta=metrics["inkRecallDelta"])
            break
        resume_batch = 0
        resume_train_total = 0.0
        resume_train_batches = 0

    if not best.exists():
        raise RuntimeError("V2a best checkpoint was not created")
    evidence = {
        "artifactType": "stage11_v2a_training_evidence",
        "status": "completed",
        "commitSha": git_sha(),
        "datasetMd5": EXPECTED_ARCHIVE_MD5,
        "configSha256": CONFIG_SHA256,
        "device": label,
        "epochsCompleted": len(history),
        "bestCheckpointSha256": base.file_hash(best),
        "lastCheckpointSha256": base.file_hash(last),
        "sourceV2CheckpointSha256": EXPECTED_V2_BEST_SHA256,
        "heldOutUsedForTraining": False,
        "heldOutUsedForTuning": False,
        "historyPath": str(history_path),
    }
    base.atomic_json(V2A_TRAIN_OUT / "training_evidence.v2a.json", evidence)
    status("training_complete", epochsCompleted=len(history), bestCheckpointSha256=evidence["bestCheckpointSha256"])
    print(json.dumps(evidence, indent=2), flush=True)


def load_frozen_model(device: Any) -> tuple[Any, dict[str, Any], Path]:
    import torch
    configure_base_runtime()
    best = V2A_TRAIN_OUT / "best.pt"
    if not best.exists():
        raise FileNotFoundError(best)
    checkpoint = torch.load(best, map_location=device)
    if checkpoint.get("datasetMd5") != EXPECTED_ARCHIVE_MD5 or checkpoint.get("configSha256") != CONFIG_SHA256:
        raise RuntimeError("V2a checkpoint/config/dataset provenance mismatch")
    model = build_residual_unet(base_channels=32).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    return model, checkpoint, best


def evaluation_mode(data: dict[str, Any], mode: str) -> None:
    import torch
    from torch.utils.data import DataLoader

    configure_base_runtime()
    device = resolve_device(torch)
    model, _checkpoint, best = load_frozen_model(device)
    before = base.model_state_sha256(model)

    if mode == "dev":
        dataset = base.make_dataset(data, "development", DEV_PATCHES)
        out_root = V2A_DEV_OUT
    else:
        gate_path = V2A_DEV_OUT / "development_evidence.v2a.json"
        if not gate_path.exists():
            raise RuntimeError("V2a development evidence missing; held-out/Stage9A remain gated")
        dev_evidence = json.loads(gate_path.read_text(encoding="utf-8"))
        if not (dev_evidence.get("gate") or {}).get("eligibleForFrozenHeldOutEvaluation"):
            raise RuntimeError("V2a development gate did not pass; frozen held-out/Stage9A remain forbidden")
        if mode == "heldout":
            dataset = base.make_dataset(data, "heldOut", HELDOUT_PATCHES)
            out_root = V2A_HELD_OUT
        elif mode == "stage9a":
            dataset = base.make_dataset(data, "heldOut", STAGE9A_MAX_SYMBOLS, symbol_only=True)
            out_root = V2A_STAGE9A_OUT
        else:
            raise RuntimeError(mode)

    out_root.mkdir(parents=True, exist_ok=True)
    loader = DataLoader(dataset, batch_size=BATCH, shuffle=False, num_workers=2, pin_memory=device.type == "cuda")
    progress_path = out_root / f"{mode}_progress.v2a.json"
    label = device_label(torch, device)
    status(f"{mode}_evaluation_started", device=label)
    metrics = base.evaluate(model, loader, device, progress_path=progress_path)
    after = base.model_state_sha256(model)
    evidence_base = {
        "commitSha": git_sha(),
        "datasetMd5": EXPECTED_ARCHIVE_MD5,
        "configSha256": CONFIG_SHA256,
        "checkpointSha256": base.file_hash(best),
        "sourceV2CheckpointSha256": EXPECTED_V2_BEST_SHA256,
        "device": label,
        "weightsMutated": before != after,
        "optimizerCreated": False,
        "backpropagationExecuted": False,
        "heldOutUsedForTraining": False,
        "heldOutUsedForTuning": False,
        "modelStateSha256Before": before,
        "modelStateSha256After": after,
        "metrics": metrics,
    }
    validate_evaluation_provenance(evidence_base)

    if mode == "dev":
        gate = v2a_candidate_gate(metrics)
        evidence = {"artifactType": "stage11_v2a_development_evidence", "status": "completed", "gate": gate, **evidence_base}
        path = V2A_DEV_OUT / "development_evidence.v2a.json"
    elif mode == "heldout":
        evidence = {"artifactType": "stage11_v2a_heldout_evidence", "status": "completed", "officialHeldOutImages": 352, **evidence_base}
        path = V2A_HELD_OUT / "heldout_evidence.v2a.json"
    else:
        ink = float(metrics["inkRecallDelta"])
        stage9a_status = "pass" if ink >= -0.05 else "review_required"
        evidence = {
            "artifactType": "stage11_v2a_stage9a_symbol_region_evidence",
            "status": stage9a_status,
            "proxyOnly": True,
            "omrCorrectnessImplied": False,
            "musicalTruthImplied": False,
            **evidence_base,
        }
        path = V2A_STAGE9A_OUT / "stage9a_symbol_region_evidence.v2a.json"

    base.atomic_json(path, evidence)
    status(
        f"{mode}_evaluation_complete",
        resultStatus=(evidence.get("gate") or {}).get("status", evidence.get("status")),
        inkRecallDelta=metrics["inkRecallDelta"],
        pixelL1ImprovementPercent=metrics["pixelL1ImprovementPercent"],
        edgeL1ImprovementPercent=metrics["edgeL1ImprovementPercent"],
    )
    print(json.dumps(evidence, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("train", "dev", "heldout", "stage9a"), required=True)
    args = parser.parse_args()
    configure_base_runtime()
    data = base.load_dataset_truth()
    if args.mode == "train":
        train_mode(data)
    else:
        evaluation_mode(data, args.mode)


if __name__ == "__main__":
    main()
