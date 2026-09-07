"""Validate the immutable Stage 11 DeepScoresV2 Dense held-out evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED_CHECKPOINT = "08b279161a9e8c4bd37376da221ecb4e07130724254ccf7d9591c8d32f368683"
EXPECTED_CONFIG = "deff0f1270009839e234608dd9967038e1228a6b2b034e26059ac2f8cbfd0f80"
EXPECTED_ARCHIVE_MD5 = "7237318e381e6e0848ec30eb82decb83"
EXPECTED_WEBARCHIVE_SHA256 = "d2ddafb3980a6ab7a1df1ba5e709d5e2520d2766e4c896c50ddab5199cc953f7"


class Stage11HeldOutEvidenceError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11HeldOutEvidenceError(message)


def validate_heldout_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == "stage11_deepscoresv2_dense_heldout_final_evidence", "artifact type mismatch")
    _require(payload.get("schemaVersion") == "1.0.0", "schema version mismatch")

    source = payload.get("sourceEvidence") or {}
    _require(source.get("kind") == "user_provided_colab_webarchive", "source evidence kind mismatch")
    _require(source.get("sha256") == EXPECTED_WEBARCHIVE_SHA256, "source evidence sha mismatch")
    _require(source.get("sizeBytes") == 970792, "source evidence size mismatch")

    dataset = payload.get("dataset") or {}
    _require(dataset.get("datasetId") == "deepscoresv2.dense.v2", "dataset id mismatch")
    _require(dataset.get("archiveMd5") == EXPECTED_ARCHIVE_MD5, "archive md5 mismatch")
    _require(dataset.get("archiveChecksumVerified") is True, "archive checksum must be verified")
    _require(dataset.get("officialHeldOutImages") == 352, "held-out image count mismatch")
    _require(dataset.get("heldOutVariants") == 2, "held-out variant count mismatch")
    _require(dataset.get("evaluatedPairs") == 704, "evaluated pair count mismatch")

    checkpoint = payload.get("checkpoint") or {}
    _require(checkpoint.get("sha256") == EXPECTED_CHECKPOINT, "checkpoint sha mismatch")
    _require(checkpoint.get("configSha256") == EXPECTED_CONFIG, "config sha mismatch")
    _require(checkpoint.get("epoch") == 19, "checkpoint epoch mismatch")
    _require(checkpoint.get("weightsMutated") is False, "held-out evaluation mutated model weights")
    _require(checkpoint.get("weightsBeforeSha256") == checkpoint.get("weightsAfterSha256"), "weight state hashes differ")

    execution = payload.get("execution") or {}
    _require(execution.get("optimizerCreated") is False, "optimizer forbidden during held-out evaluation")
    _require(execution.get("backpropagationExecuted") is False, "backpropagation forbidden during held-out evaluation")
    _require(execution.get("heldOutUsedForTraining") is False, "held-out training use forbidden")
    _require(execution.get("heldOutUsedForTuning") is False, "held-out tuning use forbidden")

    metrics = payload.get("metrics") or {}
    baseline = metrics.get("baseline") or {}
    restored = metrics.get("restored") or {}
    for key in ("loss", "pixelL1", "edgeLoss", "mse"):
        _require(float(restored.get(key, 1e9)) < float(baseline.get(key, -1)), f"{key} did not improve")
    _require(float(restored.get("psnrDb", -1e9)) > float(baseline.get("psnrDb", 1e9)), "PSNR did not improve")

    decision = payload.get("decision") or {}
    _require(decision.get("qualityImproved") is True, "quality improvement decision must be true")
    _require(decision.get("heldOutPass") is True, "held-out pass must be true")
    _require(decision.get("stage9aPreservationEvaluationRequired") is True, "Stage 9A gate must remain required")
    _require(decision.get("finalStage11Pass") is False, "final Stage 11 pass is premature")
    _require(decision.get("productionInferenceAuthorized") is False, "production inference must remain unauthorized")
    _require(decision.get("modelPublicationAuthorized") is False, "model publication must remain unauthorized")
    _require(decision.get("stage12EntryAuthorized") is False, "Stage 12 must remain unauthorized")

    return {
        "valid": True,
        "heldOutPass": True,
        "evaluatedPairs": 704,
        "weightsMutated": False,
        "finalStage11Pass": False,
        "nextSafeBoundary": "stage9a_symbol_region_preservation_evaluation",
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    return validate_heldout_evidence(json.loads(Path(path).read_text(encoding="utf-8")))
