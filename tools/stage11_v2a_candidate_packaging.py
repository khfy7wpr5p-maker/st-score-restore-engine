"""Package the frozen Stage 11 V2a checkpoint into a private TorchScript candidate.

This is a development/custody operation only. It never reads held-out data, creates an
optimizer, performs backpropagation, or authorizes production/Stage 12.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage11_v2_symbol_preservation import build_residual_unet
from st_score_restore.stage11_v2a_packaging import (
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_CONFIG_SHA256,
    EXPECTED_DATASET_MD5,
    EXPECTED_MODEL_STATE_SHA256,
    EXPECTED_SOURCE_V2_CHECKPOINT_SHA256,
    PACKAGE_CONTRACT_ID,
    PACKAGE_EVIDENCE_TYPE,
    PACKAGE_SCHEMA_VERSION,
    candidate_package_contract,
    validate_candidate_package_evidence,
)

DEFAULT_CHECKPOINT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_TRAINING_OUTPUT/deepscoresv2_dense_residual_unet_v2a_symbol_preservation/best.pt")
DEFAULT_OUT_DIR = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_PACKAGING/deepscoresv2_dense_v2a_candidate")
PACKAGE_NAME = "v2a_candidate_512.torchscript.pt"
EVIDENCE_NAME = "candidate_package_evidence.v1.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def model_state_sha256(model: Any) -> str:
    h = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        h.update(name.encode("utf-8"))
        h.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def git_sha() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


def package_candidate(checkpoint_path: Path, out_dir: Path) -> dict[str, Any]:
    import torch

    if not checkpoint_path.exists():
        raise FileNotFoundError(checkpoint_path)
    checkpoint_sha = sha256_file(checkpoint_path)
    if checkpoint_sha != EXPECTED_CHECKPOINT_SHA256:
        raise RuntimeError(f"frozen V2a checkpoint SHA mismatch: {checkpoint_sha}")

    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    if checkpoint.get("datasetMd5") != EXPECTED_DATASET_MD5:
        raise RuntimeError("checkpoint dataset provenance mismatch")
    if checkpoint.get("configSha256") != EXPECTED_CONFIG_SHA256:
        raise RuntimeError("checkpoint config provenance mismatch")
    if checkpoint.get("sourceV2CheckpointSha256") != EXPECTED_SOURCE_V2_CHECKPOINT_SHA256:
        raise RuntimeError("checkpoint source V2 provenance mismatch")

    torch.set_grad_enabled(False)
    torch.manual_seed(0)
    try:
        torch.use_deterministic_algorithms(True)
    except Exception:
        pass
    model = build_residual_unet(base_channels=32).cpu()
    model.load_state_dict(checkpoint["model"])
    model.eval()
    before = model_state_sha256(model)
    if before != EXPECTED_MODEL_STATE_SHA256:
        raise RuntimeError(f"loaded model-state SHA mismatch: {before}")

    probe = torch.linspace(0.0, 1.0, steps=512 * 512, dtype=torch.float32).reshape(1, 1, 512, 512)
    with torch.inference_mode():
        eager1 = model(probe)
        eager2 = model(probe)
    repeat_diff = float((eager1 - eager2).abs().max())
    if list(eager1.shape) != [1, 1, 512, 512]:
        raise RuntimeError(f"unexpected eager output shape: {list(eager1.shape)}")
    if not bool(torch.isfinite(eager1).all()):
        raise RuntimeError("eager output contains non-finite values")
    output_min = float(eager1.min())
    output_max = float(eager1.max())
    output_mean = float(eager1.mean())
    if output_min < 0.0 or output_max > 1.0:
        raise RuntimeError(f"eager output outside [0,1]: min={output_min} max={output_max}")
    if repeat_diff > 1e-7:
        raise RuntimeError(f"eager repeat determinism failed: {repeat_diff}")

    out_dir.mkdir(parents=True, exist_ok=True)
    package_path = out_dir / PACKAGE_NAME
    tmp_package = out_dir / (PACKAGE_NAME + ".tmp")
    traced = torch.jit.trace(model, probe, strict=True, check_trace=True)
    traced = torch.jit.freeze(traced.eval())
    torch.jit.save(traced, str(tmp_package))
    os.replace(tmp_package, package_path)

    reloaded = torch.jit.load(str(package_path), map_location="cpu").eval()
    with torch.inference_mode():
        packaged = reloaded(probe)
    reload_diff = float((eager1 - packaged).abs().max())
    if list(packaged.shape) != [1, 1, 512, 512]:
        raise RuntimeError(f"unexpected packaged output shape: {list(packaged.shape)}")
    if not bool(torch.isfinite(packaged).all()):
        raise RuntimeError("packaged output contains non-finite values")
    if reload_diff > 1e-5:
        raise RuntimeError(f"TorchScript reload parity failed: {reload_diff}")

    after = model_state_sha256(model)
    if after != before:
        raise RuntimeError("packaging mutated source model weights")

    package_sha = sha256_file(package_path)
    evidence = {
        "schemaVersion": PACKAGE_SCHEMA_VERSION,
        "artifactType": PACKAGE_EVIDENCE_TYPE,
        "status": "completed",
        "contractId": PACKAGE_CONTRACT_ID,
        "repoCommitSha": git_sha(),
        "checkpointPath": str(checkpoint_path),
        "checkpointSha256": checkpoint_sha,
        "checkpointSizeBytes": checkpoint_path.stat().st_size,
        "configSha256": EXPECTED_CONFIG_SHA256,
        "datasetMd5": EXPECTED_DATASET_MD5,
        "sourceV2CheckpointSha256": EXPECTED_SOURCE_V2_CHECKPOINT_SHA256,
        "modelStateSha256Before": before,
        "modelStateSha256After": after,
        "weightsMutated": False,
        "optimizerCreated": False,
        "backpropagationExecuted": False,
        "heldOutAccessed": False,
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "device": "CPU",
        },
        "package": {
            "path": str(package_path),
            "format": "torchscript-trace",
            "sha256": package_sha,
            "sizeBytes": package_path.stat().st_size,
        },
        "smokeTest": {
            "probe": "float32_linear_ramp_0_to_1",
            "inputShape": list(probe.shape),
            "outputShape": list(packaged.shape),
            "finite": bool(torch.isfinite(packaged).all()),
            "outputMin": output_min,
            "outputMax": output_max,
            "outputMean": output_mean,
            "repeatMaxAbsDiff": repeat_diff,
            "reloadMaxAbsDiff": reload_diff,
        },
        "authorization": {
            "candidatePackagingAuthorized": True,
            "productionInferenceAuthorized": False,
            "productionPromotionAuthorized": False,
            "stage12EntryAuthorized": False,
        },
        "contract": candidate_package_contract(),
    }
    validate_candidate_package_evidence(evidence)
    evidence_path = out_dir / EVIDENCE_NAME
    atomic_json(evidence_path, evidence)
    print(json.dumps(evidence, indent=2), flush=True)
    print(f"Evidence: {evidence_path}", flush=True)
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    package_candidate(args.checkpoint, args.out_dir)


if __name__ == "__main__":
    main()
