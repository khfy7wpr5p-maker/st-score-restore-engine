"""Fail-closed validator for the current Stage 11 V2/V2a symbol-preservation truth."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .stage11_v2_symbol_preservation import EXPECTED_ARCHIVE_MD5, stable_config_sha256
from .stage11_v2a_preservation import V2A_LOSS_WEIGHTS
from .stage11_v2a_acceptance import (
    EXPECTED_CHECKPOINT_SHA256 as EXPECTED_V2A_BEST_SHA256,
    EXPECTED_CONFIG_SHA256 as EXPECTED_V2A_CONFIG_SHA256,
    EXPECTED_MODEL_STATE_SHA256 as EXPECTED_V2A_MODEL_STATE_SHA256,
    EXPECTED_SOURCE_RUN_COMMIT as EXPECTED_V2A_SOURCE_RUN_COMMIT,
)

ARTIFACT_TYPE = "stage11_v2_symbol_preservation_current_truth"
SCHEMA_VERSION = "1.2.0"
EXPECTED_STATE = "V2A_HELDOUT_AND_STAGE9A_PASS_CANDIDATE_FROZEN"
EXPECTED_BASE_MAIN_SHA = "4b4bc6d6c2fac185dea598963866f14075452fb0"
EXPECTED_BRANCH = "stage11-v2a-evidence-acceptance-freeze"
EXPECTED_V2_CONFIG_SHA256 = "9f041aad61eecba66843e4456ec05e14e9bbfb40d93a39e49033ec7d4d500a4d"
EXPECTED_V2_BEST_SHA256 = "363cb63bff2367c1119a4eea449a19d468a802160f45b4fe1f2d98ab04fb894b"


class Stage11V2CurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2CurrentTruthError(message)


def _require_close(actual: Any, expected: float, label: str) -> None:
    _require(abs(float(actual) - expected) < 1e-12, f"{label} mismatch")


def validate_stage11_v2_current_truth(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == ARTIFACT_TYPE, "artifact type mismatch")
    _require(payload.get("schemaVersion") == SCHEMA_VERSION, "schema version mismatch")
    _require(payload.get("baseMainSha") == EXPECTED_BASE_MAIN_SHA, "base main SHA mismatch")
    _require(payload.get("implementationBranch") == EXPECTED_BRANCH, "implementation branch mismatch")
    _require(payload.get("state") == EXPECTED_STATE, "unexpected Stage 11 V2/V2a state")

    source = payload.get("trainingSource") or {}
    _require(source.get("datasetId") == "deepscoresv2.dense.v2", "dataset id mismatch")
    _require(source.get("archiveMd5Expected") == EXPECTED_ARCHIVE_MD5, "dataset MD5 mismatch")
    _require(source.get("rightsClearedForCommercialTraining") is True, "training rights must be cleared")
    _require(source.get("privateStudentUserDataAuthorized") is False, "private/student/user training data must remain forbidden")

    v2 = payload.get("v2Result") or {}
    _require(v2.get("trainingCompleted") is True, "V2 training completion missing")
    _require(int(v2.get("epochsCompleted", -1)) == 20, "V2 epoch count mismatch")
    _require(v2.get("bestCheckpointSha256") == EXPECTED_V2_BEST_SHA256, "V2 best checkpoint mismatch")
    _require(v2.get("configSha256") == EXPECTED_V2_CONFIG_SHA256, "V2 config hash mismatch")
    _require(v2.get("developmentStatus") == "review_required", "V2 development status must remain review_required")
    _require(v2.get("developmentGatePassed") is False, "V2 development gate must remain closed")
    _require(v2.get("heldOutUsedForTraining") is False, "V2 held-out training is forbidden")
    _require(v2.get("heldOutUsedForTuning") is False, "V2 held-out tuning is forbidden")
    _require_close(v2.get("inkRecallDelta"), -0.05993542307987809, "V2 ink recall")
    _require_close(v2.get("pixelL1ImprovementPercent"), 57.808715708373306, "V2 pixel L1")
    _require_close(v2.get("edgeL1ImprovementPercent"), 13.596753265825802, "V2 edge L1")

    v2a_config = payload.get("v2aConfig") or {}
    expected_v2a_config = {
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
        "learningRate": 5e-5,
        "maxEpochs": 8,
        "checkpointSelection": "v2a-development-gate-then-ink-recall-then-pixel-edge",
        "partialCheckpointEveryTrainBatches": 128,
    }
    _require(v2a_config == expected_v2a_config, "V2a config mismatch")
    _require(stable_config_sha256(v2a_config) == EXPECTED_V2A_CONFIG_SHA256, "V2a config hash mismatch")
    _require(payload.get("v2aConfigSha256") == EXPECTED_V2A_CONFIG_SHA256, "recorded V2a config hash mismatch")

    v2a = payload.get("v2aResult") or {}
    _require(v2a.get("trainingCompleted") is True, "V2a training completion missing")
    _require(v2a.get("developmentStatus") == "pass", "V2a development status must pass")
    _require(v2a.get("developmentGatePassed") is True, "V2a development gate pass missing")
    _require(v2a.get("developmentNumericMetricsCommitted") is False, "uncaptured V2a development numbers must not be invented")
    _require(v2a.get("developmentPassBasis") == "gated_pipeline_progression", "V2a development pass basis mismatch")
    _require(v2a.get("heldoutEvaluationStatus") == "completed", "V2a held-out evaluation must be completed")
    _require(int(v2a.get("officialHeldOutImages", 0)) == 352, "V2a held-out image count mismatch")
    _require(v2a.get("heldoutPreservationGatePassed") is True, "V2a held-out preservation gate missing")
    _require_close(v2a.get("heldoutInkRecallDelta"), -0.037029366940259933, "V2a held-out ink recall")
    _require_close(v2a.get("heldoutPixelL1ImprovementPercent"), 53.772181502991145, "V2a held-out pixel L1")
    _require_close(v2a.get("heldoutEdgeL1ImprovementPercent"), 7.465588872979961, "V2a held-out edge L1")
    _require_close(v2a.get("heldoutFalseInkRateDelta"), -0.09465780964290552, "V2a held-out false ink")
    _require_close(v2a.get("heldoutMseImprovementPercent"), -12.064218277766777, "V2a held-out MSE")
    _require(v2a.get("stage9aStatus") == "pass", "V2a Stage 9A must pass")
    _require(v2a.get("stage9aProxyOnly") is True, "V2a Stage 9A must remain proxy-only")
    _require_close(v2a.get("stage9aInkRecallDelta"), -0.030930931214243174, "V2a Stage 9A ink recall")
    _require_close(v2a.get("stage9aPixelL1ImprovementPercent"), 47.90019887277439, "V2a Stage 9A pixel L1")
    _require_close(v2a.get("stage9aEdgeL1ImprovementPercent"), 5.336352757154033, "V2a Stage 9A edge L1")
    _require_close(v2a.get("stage9aFalseInkRateDelta"), -0.07233098943834193, "V2a Stage 9A false ink")
    _require_close(v2a.get("stage9aMseImprovementPercent"), -19.59240047175054, "V2a Stage 9A MSE")
    _require(v2a.get("idealInkRecallTargetReached") is False, "ideal target must not be overstated")
    _require(v2a.get("mseRegressionObserved") is True, "MSE regression must remain explicit")
    _require(v2a.get("bestCheckpointSha256") == EXPECTED_V2A_BEST_SHA256, "V2a best checkpoint mismatch")
    _require(v2a.get("modelStateSha256") == EXPECTED_V2A_MODEL_STATE_SHA256, "V2a model state hash mismatch")
    _require(v2a.get("sourceRunCommitSha") == EXPECTED_V2A_SOURCE_RUN_COMMIT, "V2a source run commit mismatch")
    _require(v2a.get("device") == "Tesla T4", "V2a evaluation device mismatch")
    _require(v2a.get("weightsMutatedDuringEvaluation") is False, "V2a evaluation weights must remain immutable")
    _require(v2a.get("heldOutUsedForTraining") is False, "V2a held-out training is forbidden")
    _require(v2a.get("heldOutUsedForTuning") is False, "V2a held-out tuning is forbidden")
    _require(v2a.get("acceptanceEvidence") == "evidence/stage11/v2a/v2a-evaluation-acceptance.v1.json", "V2a acceptance evidence path mismatch")

    gates = payload.get("gates") or {}
    expected_true_gates = (
        "v2DevelopmentTrainingCompleted",
        "v2aFineTuneCompleted",
        "v2aDevelopmentGatePassed",
        "heldOutEvaluationAuthorized",
        "heldOutEvaluationCompleted",
        "stage9aEvaluationAuthorized",
        "stage9aEvaluationCompleted",
        "candidateCheckpointFrozen",
        "furtherTuningAgainstConsumedHeldoutForbidden",
    )
    for key in expected_true_gates:
        _require(gates.get(key) is True, f"gate must be true: {key}")
    _require(gates.get("v2DevelopmentGatePassed") is False, "historical V2 development gate must remain closed")
    _require(gates.get("finalModelSelected") is False, "final production model selection remains separate")
    _require(gates.get("stage12EntryAuthorized") is False, "Stage 12 entry is forbidden")
    _require(gates.get("productionInferenceAuthorized") is False, "production inference is forbidden")

    implementation = payload.get("implementation") or {}
    for key in (
        "v2EvidenceImported",
        "v2aPolicyReady",
        "v2aRuntimeReady",
        "v2aAutonomousPipelineReady",
        "v2aBackgroundNotebookReady",
        "partialCheckpointResumeReady",
        "driveStatusMonitoringReady",
        "developmentGateEnforced",
        "v2aAcceptanceEvidenceImported",
        "candidateCheckpointFreezeRecorded",
        "consumedHeldoutRetuningGuardRecorded",
    ):
        _require(implementation.get(key) is True, f"implementation flag must be true: {key}")

    safety = payload.get("safety") or {}
    for key in (
        "historicalEvidenceImmutable",
        "sourceFamilyLeakageForbidden",
        "heldOutNeverTrainOrTune",
        "weightsMustNotMutateDuringEvaluation",
        "omrCorrectnessNotImplied",
        "musicalTruthNotImplied",
        "automaticProductionPromotionForbidden",
        "consumedHeldoutCannotBeReusedForAdaptiveTuning",
    ):
        _require(safety.get(key) is True, f"required safety assertion missing: {key}")

    return {
        "state": EXPECTED_STATE,
        "implementationReady": True,
        "v2DevelopmentGatePassed": False,
        "v2aDevelopmentGatePassed": True,
        "heldOutEvaluationCompleted": True,
        "stage9aEvaluationCompleted": True,
        "candidateCheckpointFrozen": True,
        "finalModelSelected": False,
        "stage12EntryAuthorized": False,
        "productionInferenceAuthorized": False,
        "v2aConfigSha256": EXPECTED_V2A_CONFIG_SHA256,
        "v2aCheckpointSha256": EXPECTED_V2A_BEST_SHA256,
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_stage11_v2_current_truth(payload)
