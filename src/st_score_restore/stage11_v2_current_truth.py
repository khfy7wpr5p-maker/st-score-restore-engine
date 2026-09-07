"""Fail-closed validator for the current Stage 11 V2/V2a symbol-preservation truth."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .stage11_v2_symbol_preservation import EXPECTED_ARCHIVE_MD5, stable_config_sha256
from .stage11_v2a_preservation import V2A_LOSS_WEIGHTS

ARTIFACT_TYPE = "stage11_v2_symbol_preservation_current_truth"
SCHEMA_VERSION = "1.1.0"
EXPECTED_STATE = "V2_DEVELOPMENT_REVIEW_REQUIRED_V2A_READY"
EXPECTED_BASE_MAIN_SHA = "1ac815df360b42634d670862e643860a474e1770"
EXPECTED_BRANCH = "stage11-v2a-symbol-preservation-finetune"
EXPECTED_V2_CONFIG_SHA256 = "9f041aad61eecba66843e4456ec05e14e9bbfb40d93a39e49033ec7d4d500a4d"
EXPECTED_V2A_CONFIG_SHA256 = "1250731992c01c238dd2376a95ced1d1c6f76dcdf87deb473ec94a0aa58f7818"
EXPECTED_V2_BEST_SHA256 = "363cb63bff2367c1119a4eea449a19d468a802160f45b4fe1f2d98ab04fb894b"


class Stage11V2CurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2CurrentTruthError(message)


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
    _require(v2.get("heldOutUsedForTraining") is False, "held-out training is forbidden")
    _require(v2.get("heldOutUsedForTuning") is False, "held-out tuning is forbidden")
    _require(abs(float(v2.get("inkRecallDelta")) - (-0.05993542307987809)) < 1e-12, "V2 ink recall evidence mismatch")
    _require(abs(float(v2.get("pixelL1ImprovementPercent")) - 57.808715708373306) < 1e-12, "V2 pixel evidence mismatch")
    _require(abs(float(v2.get("edgeL1ImprovementPercent")) - 13.596753265825802) < 1e-12, "V2 edge evidence mismatch")

    v2a = payload.get("v2aConfig") or {}
    expected_v2a = {
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
    _require(v2a == expected_v2a, "V2a config mismatch")
    _require(stable_config_sha256(v2a) == EXPECTED_V2A_CONFIG_SHA256, "V2a config hash mismatch")
    _require(payload.get("v2aConfigSha256") == EXPECTED_V2A_CONFIG_SHA256, "recorded V2a config hash mismatch")

    gates = payload.get("gates") or {}
    _require(gates.get("v2DevelopmentTrainingCompleted") is True, "V2 training must be complete")
    _require(gates.get("v2DevelopmentGatePassed") is False, "V2 dev gate must remain closed")
    _require(gates.get("v2aFineTuneAuthorized") is True, "V2a fine-tune must be authorized")
    _require(gates.get("heldOutEvaluationAuthorized") is False, "held-out evaluation must remain closed until V2a dev passes")
    _require(gates.get("stage9aEvaluationAuthorized") is False, "Stage 9A must remain closed until V2a dev passes")
    _require(gates.get("finalModelSelected") is False, "final model selection is forbidden")
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
    ):
        _require(safety.get(key) is True, f"required safety assertion missing: {key}")

    return {
        "state": EXPECTED_STATE,
        "implementationReady": True,
        "developmentTrainingCompleted": True,
        "v2DevelopmentGatePassed": False,
        "v2aFineTuneAuthorized": True,
        "heldOutEvaluationAuthorized": False,
        "stage12EntryAuthorized": False,
        "v2aConfigSha256": EXPECTED_V2A_CONFIG_SHA256,
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_stage11_v2_current_truth(payload)
