"""Fail-closed validator for accepted Stage 11 V2a evaluation evidence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

ARTIFACT_TYPE = "stage11_v2a_evaluation_acceptance"
SCHEMA_VERSION = "stage11.v2a.acceptance.v1"
EXPECTED_SOURCE_RUN_COMMIT = "4b4bc6d6c2fac185dea598963866f14075452fb0"
EXPECTED_DATASET_MD5 = "7237318e381e6e0848ec30eb82decb83"
EXPECTED_CONFIG_SHA256 = "1250731992c01c238dd2376a95ced1d1c6f76dcdf87deb473ec94a0aa58f7818"
EXPECTED_CHECKPOINT_SHA256 = "15afc73233c91a80a7ef1285cb631d5d3acd681e9cfed9a93b35642bf39fff4c"
EXPECTED_SOURCE_V2_SHA256 = "363cb63bff2367c1119a4eea449a19d468a802160f45b4fe1f2d98ab04fb894b"
EXPECTED_MODEL_STATE_SHA256 = "1d8becbebfb2b86beb21b4f757c6dacb01354c981bc7216b6e988fc74fd2d32b"

INK_RECALL_MINIMUM = -0.05
INK_RECALL_IDEAL = -0.02
PIXEL_L1_FLOOR = 45.0
EDGE_L1_FLOOR = 5.0


class Stage11V2aAcceptanceError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aAcceptanceError(message)


def _require_close(actual: Any, expected: float, label: str) -> None:
    _require(abs(float(actual) - expected) < 1e-12, f"{label} mismatch")


def validate_stage11_v2a_acceptance(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == ARTIFACT_TYPE, "artifact type mismatch")
    _require(payload.get("schemaVersion") == SCHEMA_VERSION, "schema version mismatch")
    _require(payload.get("sourceRunCommitSha") == EXPECTED_SOURCE_RUN_COMMIT, "source run commit mismatch")
    _require(payload.get("datasetMd5") == EXPECTED_DATASET_MD5, "dataset MD5 mismatch")
    _require(payload.get("configSha256") == EXPECTED_CONFIG_SHA256, "config SHA mismatch")
    _require(payload.get("checkpointSha256") == EXPECTED_CHECKPOINT_SHA256, "checkpoint SHA mismatch")
    _require(payload.get("sourceV2CheckpointSha256") == EXPECTED_SOURCE_V2_SHA256, "source V2 checkpoint mismatch")
    _require(payload.get("modelStateSha256") == EXPECTED_MODEL_STATE_SHA256, "model state SHA mismatch")
    _require(payload.get("device") == "Tesla T4", "device mismatch")

    capture = payload.get("evidenceCapture") or {}
    _require(capture.get("operatorProvidedColabArchive") is True, "operator archive evidence missing")
    _require(capture.get("developmentNumericArtifactFullyCaptured") is False, "uncaptured development metrics must not be claimed")
    _require(capture.get("heldoutMetricSegmentCaptured") is True, "held-out metric capture missing")
    _require(capture.get("stage9aArtifactFullyCaptured") is True, "Stage 9A full artifact capture missing")
    _require(capture.get("developmentGatePassEstablishedByGatedPipelineProgression") is True, "development gate basis missing")

    development = payload.get("development") or {}
    _require(development.get("status") == "pass", "V2a development gate must pass")
    _require(development.get("developmentGatePassed") is True, "development gate pass missing")
    _require(development.get("eligibleForFrozenHeldOutEvaluation") is True, "held-out eligibility missing")
    _require(development.get("numericMetricsCommitted") is False, "uncaptured development metrics must remain absent")
    _require(development.get("basis") == "gated_pipeline_progression", "development evidence basis mismatch")

    heldout = payload.get("heldout") or {}
    _require(heldout.get("status") == "completed", "held-out evaluation must be completed")
    _require(int(heldout.get("officialHeldOutImages", 0)) == 352, "held-out image count mismatch")
    heldout_metrics = heldout.get("metrics") or {}
    _require_close(heldout_metrics.get("pixelL1ImprovementPercent"), 53.772181502991145, "held-out pixel L1")
    _require_close(heldout_metrics.get("edgeL1ImprovementPercent"), 7.465588872979961, "held-out edge L1")
    _require_close(heldout_metrics.get("falseInkRateDelta"), -0.09465780964290552, "held-out false ink delta")
    _require_close(heldout_metrics.get("inkRecallDelta"), -0.037029366940259933, "held-out ink recall delta")
    _require_close(heldout_metrics.get("mseImprovementPercent"), -12.064218277766777, "held-out MSE")
    _require(float(heldout_metrics["inkRecallDelta"]) >= INK_RECALL_MINIMUM, "held-out preservation gate failed")
    _require(float(heldout_metrics["pixelL1ImprovementPercent"]) >= PIXEL_L1_FLOOR, "held-out pixel cleanup floor failed")
    _require(float(heldout_metrics["edgeL1ImprovementPercent"]) >= EDGE_L1_FLOOR, "held-out edge cleanup floor failed")
    for key in ("weightsMutated", "optimizerCreated", "backpropagationExecuted", "heldOutUsedForTraining", "heldOutUsedForTuning"):
        _require(heldout.get(key) is False, f"held-out safety assertion violated: {key}")

    stage9a = payload.get("stage9a") or {}
    _require(stage9a.get("status") == "pass", "Stage 9A must pass")
    _require(stage9a.get("proxyOnly") is True, "Stage 9A must remain explicitly proxy-only")
    stage9a_metrics = stage9a.get("metrics") or {}
    _require_close(stage9a_metrics.get("pixelL1ImprovementPercent"), 47.90019887277439, "Stage 9A pixel L1")
    _require_close(stage9a_metrics.get("edgeL1ImprovementPercent"), 5.336352757154033, "Stage 9A edge L1")
    _require_close(stage9a_metrics.get("falseInkRateDelta"), -0.07233098943834193, "Stage 9A false ink delta")
    _require_close(stage9a_metrics.get("inkRecallDelta"), -0.030930931214243174, "Stage 9A ink recall delta")
    _require_close(stage9a_metrics.get("mseImprovementPercent"), -19.59240047175054, "Stage 9A MSE")
    _require(float(stage9a_metrics["inkRecallDelta"]) >= INK_RECALL_MINIMUM, "Stage 9A preservation gate failed")
    _require(float(stage9a_metrics["pixelL1ImprovementPercent"]) >= PIXEL_L1_FLOOR, "Stage 9A pixel cleanup floor failed")
    _require(float(stage9a_metrics["edgeL1ImprovementPercent"]) >= EDGE_L1_FLOOR, "Stage 9A edge cleanup floor failed")
    for key in ("weightsMutated", "optimizerCreated", "backpropagationExecuted", "heldOutUsedForTraining", "heldOutUsedForTuning"):
        _require(stage9a.get(key) is False, f"Stage 9A safety assertion violated: {key}")
    _require(stage9a.get("omrCorrectnessImplied") is False, "OMR correctness must not be implied")
    _require(stage9a.get("musicalTruthImplied") is False, "musical truth must not be implied")

    decision = payload.get("decision") or {}
    _require(decision.get("preservationGatePassed") is True, "preservation acceptance missing")
    _require(decision.get("heldoutCleanupFloorsPassed") is True, "held-out cleanup acceptance missing")
    _require(decision.get("stage9aCleanupFloorsPassed") is True, "Stage 9A cleanup acceptance missing")
    _require(decision.get("idealInkRecallTargetReached") is False, "ideal target must not be overstated")
    _require(float(stage9a_metrics["inkRecallDelta"]) < INK_RECALL_IDEAL, "ideal target flag inconsistent")
    _require(decision.get("mseRegressionObserved") is True, "MSE regression must remain explicit")
    _require(float(heldout_metrics["mseImprovementPercent"]) < 0.0, "held-out MSE regression missing")
    _require(float(stage9a_metrics["mseImprovementPercent"]) < 0.0, "Stage 9A MSE regression missing")
    _require(decision.get("candidateCheckpointFrozen") is True, "candidate checkpoint must be frozen")
    _require(decision.get("furtherTuningAgainstConsumedHeldoutForbidden") is True, "consumed held-out must not become a tuning set")
    _require(decision.get("productionPromotionAuthorized") is False, "production promotion is forbidden")
    _require(decision.get("stage12EntryAuthorized") is False, "Stage 12 entry is forbidden")
    _require(decision.get("productionInferenceAuthorized") is False, "production inference is forbidden")

    return {
        "status": "pass",
        "checkpointSha256": EXPECTED_CHECKPOINT_SHA256,
        "developmentGatePassed": True,
        "heldoutPassed": True,
        "stage9aPassed": True,
        "candidateCheckpointFrozen": True,
        "idealInkRecallTargetReached": False,
        "mseRegressionObserved": True,
        "productionPromotionAuthorized": False,
        "stage12EntryAuthorized": False,
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_stage11_v2a_acceptance(payload)
