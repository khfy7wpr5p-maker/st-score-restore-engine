"""Validation for the verified Stage 11 DeepScoresV2 Dense held-out run."""

from __future__ import annotations

from typing import Any

EXPECTED_DATASET = "deepscoresv2.dense.v2"
EXPECTED_ARCHIVE_MD5 = "7237318e381e6e0848ec30eb82decb83"
EXPECTED_CHECKPOINT_SHA256 = "08b279161a9e8c4bd37376da221ecb4e07130724254ccf7d9591c8d32f368683"
EXPECTED_CONFIG_SHA256 = "deff0f1270009839e234608dd9967038e1228a6b2b034e26059ac2f8cbfd0f80"


class Stage11HeldOutEvidenceError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11HeldOutEvidenceError(message)


def validate_stage11_heldout_final_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == "stage11_deepscoresv2_dense_heldout_final_acceptance", "artifact type mismatch")
    _require(payload.get("datasetId") == EXPECTED_DATASET, "dataset mismatch")

    dataset = payload.get("datasetIdentity") or {}
    _require(dataset.get("archiveMd5") == EXPECTED_ARCHIVE_MD5, "archive MD5 mismatch")
    _require(dataset.get("archiveChecksumVerified") is True, "archive checksum not verified")
    _require(dataset.get("officialHeldOutImages") == 352, "held-out image count mismatch")
    _require(dataset.get("heldOutVariants") == 2, "held-out variant count mismatch")
    _require(dataset.get("evaluatedPairs") == 704, "evaluated pair count mismatch")

    checkpoint = payload.get("checkpointIdentity") or {}
    _require(checkpoint.get("file") == "best.pt", "checkpoint file mismatch")
    _require(checkpoint.get("epoch") == 19, "checkpoint epoch mismatch")
    _require(checkpoint.get("sha256") == EXPECTED_CHECKPOINT_SHA256, "checkpoint SHA256 mismatch")
    _require(checkpoint.get("configSha256") == EXPECTED_CONFIG_SHA256, "config SHA256 mismatch")

    execution = payload.get("execution") or {}
    _require(execution.get("optimizerCreated") is False, "optimizer must not exist in held-out evaluation")
    _require(execution.get("backpropagationExecuted") is False, "backpropagation is forbidden")
    _require(execution.get("heldOutUsedForTraining") is False, "held-out training is forbidden")
    _require(execution.get("heldOutUsedForTuning") is False, "held-out tuning is forbidden")
    _require(execution.get("weightsMutated") is False, "weights mutated during held-out evaluation")
    _require(execution.get("weightsBeforeSha256") == execution.get("weightsAfterSha256"), "weight state identity changed")

    baseline = payload.get("baseline") or {}
    restored = payload.get("restored") or {}
    _require(restored.get("loss") < baseline.get("loss"), "held-out loss did not improve")
    _require(restored.get("pixelL1") < baseline.get("pixelL1"), "held-out pixel L1 did not improve")
    _require(restored.get("edgeLoss") < baseline.get("edgeLoss"), "held-out edge loss did not improve")
    _require(restored.get("mse") < baseline.get("mse"), "held-out MSE did not improve")
    _require(restored.get("psnrDb") > baseline.get("psnrDb"), "held-out PSNR did not improve")

    decision = payload.get("decision") or {}
    _require(decision.get("qualityImproved") is True, "qualityImproved must be true")
    _require(decision.get("heldOutPass") is True, "heldOutPass must be true")
    _require(decision.get("finalStage11Pass") is False, "final Stage 11 PASS is premature")
    _require(decision.get("stage9aPreservationEvaluationRequired") is True, "Stage 9A preservation must remain required")
    _require(decision.get("productionInferenceAuthorized") is False, "production inference must remain closed")
    _require(decision.get("modelPublicationAuthorized") is False, "model publication must remain closed")
    _require(decision.get("stage12EntryAuthorized") is False, "Stage 12 must remain closed")

    return {
        "valid": True,
        "heldOutPass": True,
        "evaluatedPairs": 704,
        "qualityImproved": True,
        "finalStage11Pass": False,
        "nextSafeBoundary": decision.get("nextSafeBoundary"),
    }
