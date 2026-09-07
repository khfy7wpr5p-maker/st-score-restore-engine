"""Autonomous Stage 11 V2a pipeline: train -> dev -> gated held-out -> Stage 9A.

The pipeline never bypasses the development gate. It is safe to restart: training and
evaluation runtimes persist resumable checkpoints/progress in Google Drive.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tools" / "stage11_v2a_colab_runtime.py"
TRAIN_OUT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_TRAINING_OUTPUT/deepscoresv2_dense_residual_unet_v2a_symbol_preservation")
DEV_EVIDENCE = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/deepscoresv2_dense_v2a_dev/development_evidence.v2a.json")
HELD_EVIDENCE = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/deepscoresv2_dense_v2a_heldout/heldout_evidence.v2a.json")
STAGE9A_EVIDENCE = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/deepscoresv2_dense_v2a_stage9a/stage9a_symbol_region_evidence.v2a.json")
PIPELINE_STATUS = TRAIN_OUT / "pipeline_status.v2a.json"


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def write_status(stage: str, **extra) -> None:
    payload = {"schemaVersion": "stage11.v2a.pipeline-status.v1", "stage": stage, "updatedUnix": time.time(), **extra}
    atomic_json(PIPELINE_STATUS, payload)
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def run(mode: str) -> None:
    write_status(f"{mode}_starting")
    subprocess.run([sys.executable, "-u", str(RUNTIME), "--mode", mode], check=True)
    write_status(f"{mode}_finished")


def main() -> None:
    try:
        run("train")
        run("dev")
        if not DEV_EVIDENCE.exists():
            raise RuntimeError("V2a development evidence was not created")
        dev = json.loads(DEV_EVIDENCE.read_text(encoding="utf-8"))
        gate = dev.get("gate") or {}
        if not gate.get("eligibleForFrozenHeldOutEvaluation"):
            write_status(
                "complete_review_required",
                developmentGate=gate,
                inkRecallDelta=(dev.get("metrics") or {}).get("inkRecallDelta"),
                heldOutExecuted=False,
                stage9aExecuted=False,
            )
            return
        run("heldout")
        run("stage9a")
        held = json.loads(HELD_EVIDENCE.read_text(encoding="utf-8")) if HELD_EVIDENCE.exists() else {}
        stage9a = json.loads(STAGE9A_EVIDENCE.read_text(encoding="utf-8")) if STAGE9A_EVIDENCE.exists() else {}
        write_status(
            "complete",
            developmentGate=gate,
            heldOutStatus=held.get("status"),
            stage9aStatus=stage9a.get("status"),
            heldOutExecuted=True,
            stage9aExecuted=True,
            productionPromotionAuthorized=False,
            stage12EntryAuthorized=False,
        )
    except Exception as exc:
        write_status("failed", errorType=type(exc).__name__, error=str(exc))
        raise


if __name__ == "__main__":
    main()
