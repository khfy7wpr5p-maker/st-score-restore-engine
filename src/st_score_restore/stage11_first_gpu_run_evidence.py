"""Fail-closed validation for the first verified Stage 11 DeepScoresV2 GPU run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED_DATASET = "deepscoresv2.dense.v2"
EXPECTED_MD5 = "7237318e381e6e0848ec30eb82decb83"
EXPECTED_CONFIG = "deff0f1270009839e234608dd9967038e1228a6b2b034e26059ac2f8cbfd0f80"
EXPECTED_BEST_SHA256 = "08b279161a9e8c4bd37376da221ecb4e07130724254ccf7d9591c8d32f368683"
EXPECTED_LAST_SHA256 = "29eea696a4b73fee16457a5d377fc51516a9aed8c84335d54f5c16625786a09f"


class Stage11FirstGpuRunEvidenceError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11FirstGpuRunEvidenceError(message)


def validate_first_gpu_run_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == "stage11_deepscoresv2_dense_first_gpu_run_evidence", "artifact type mismatch")
    run = payload.get("runEvidence") or {}
    _require(run.get("artifactType") == "stage11_first_gpu_run_evidence", "run evidence type mismatch")
    _require(run.get("datasetId") == EXPECTED_DATASET, "dataset id mismatch")
    _require(run.get("archiveMd5") == EXPECTED_MD5, "archive MD5 mismatch")
    _require(run.get("archiveChecksumVerified") is True, "archive checksum must be verified")
    _require(run.get("gpu") == "Tesla T4", "unexpected GPU evidence")
    _require(run.get("epochsCompleted") == 20, "expected 20 completed epochs")
    _require(run.get("bestCheckpointExists") is True, "best checkpoint missing")
    _require(run.get("lastCheckpointExists") is True, "last checkpoint missing")
    _require(run.get("configSha256") == EXPECTED_CONFIG, "training config hash mismatch")
    _require(run.get("heldOutUsedForTuning") is False, "held-out tuning is forbidden")
    _require(run.get("productionInferenceAuthorized") is False, "production inference must remain closed")
    _require(run.get("modelPublicationAuthorized") is False, "model publication must remain closed")
    _require(run.get("stage12EntryAuthorized") is False, "Stage 12 must remain closed")

    checkpoint = payload.get("verifiedCheckpoint") or {}
    _require(checkpoint.get("bestEpoch") == 19, "unexpected best epoch")
    _require(checkpoint.get("checkpointEpoch") == 19, "checkpoint epoch mismatch")
    _require(checkpoint.get("checkpointHistoryLength") == 20, "checkpoint history length mismatch")
    _require(checkpoint.get("checkpointArchiveMd5") == EXPECTED_MD5, "checkpoint dataset identity mismatch")
    _require(checkpoint.get("checkpointConfigSha256") == EXPECTED_CONFIG, "checkpoint config identity mismatch")
    _require(abs(float(checkpoint.get("bestDevelopmentLoss", -1)) - float(run["bestDevelopmentLoss"])) < 1e-12, "best loss mismatch")

    metrics = payload.get("metrics") or {}
    e0 = ((metrics.get("epoch0") or {}).get("development") or {})
    e19 = ((metrics.get("epoch19") or {}).get("development") or {})
    _require(float(e19.get("loss", 9)) < float(e0.get("loss", -1)), "development loss did not improve")
    _require(float(e19.get("pixel", 9)) < float(e0.get("pixel", -1)), "pixel L1 did not improve")
    _require(float(e19.get("edge", 9)) < float(e0.get("edge", -1)), "edge loss did not improve")
    _require(float(e19.get("psnr", -1)) > float(e0.get("psnr", 9)), "development PSNR did not improve")

    drive = payload.get("driveArtifacts") or {}
    _require((drive.get("bestCheckpoint") or {}).get("sha256") == EXPECTED_BEST_SHA256, "best checkpoint SHA256 mismatch")
    _require((drive.get("lastCheckpoint") or {}).get("sha256") == EXPECTED_LAST_SHA256, "last checkpoint SHA256 mismatch")
    _require((drive.get("bestCheckpoint") or {}).get("sizeBytes") == 23449829, "best checkpoint size mismatch")
    _require((drive.get("lastCheckpoint") or {}).get("sizeBytes") == 23449829, "last checkpoint size mismatch")

    decision = payload.get("decision") or {}
    _require(decision.get("firstGpuTrainingRunPass") is True, "first GPU run must pass")
    _require(decision.get("candidateModelEstablished") is True, "candidate model must be established")
    _require(decision.get("finalStage11Pass") is False, "final Stage 11 pass is premature")
    _require(decision.get("heldOutEvaluationCompleted") is False, "held-out evaluation must still be pending")
    _require(decision.get("stage9aPreservationEvaluationCompleted") is False, "Stage 9A preservation evaluation must still be pending")

    assertions = payload.get("assertions") or {}
    _require(assertions.get("heldOutUsedForTuning") is False, "held-out tuning assertion mismatch")
    _require(assertions.get("productionInferenceAuthorized") is False, "production assertion mismatch")
    _require(assertions.get("modelPublicationAuthorized") is False, "publication assertion mismatch")
    _require(assertions.get("stage12EntryAuthorized") is False, "Stage 12 assertion mismatch")
    _require(assertions.get("ordinaryGitContainsModelWeights") is False, "model weights must remain outside ordinary Git")

    return {
        "valid": True,
        "datasetId": run["datasetId"],
        "epochsCompleted": run["epochsCompleted"],
        "bestEpoch": checkpoint["bestEpoch"],
        "bestDevelopmentLoss": run["bestDevelopmentLoss"],
        "firstGpuTrainingRunPass": True,
        "finalStage11Pass": False,
        "nextSafeBoundary": "held_out_final_evaluation_then_stage9a_preservation_evaluation",
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    return validate_first_gpu_run_evidence(json.loads(Path(path).read_text(encoding="utf-8")))
