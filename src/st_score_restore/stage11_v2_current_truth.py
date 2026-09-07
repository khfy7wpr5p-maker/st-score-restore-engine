"""Fail-closed validator for Stage 11 V2 symbol-preservation development truth."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .stage11_v2_symbol_preservation import EXPECTED_ARCHIVE_MD5, LossWeights, Stage11V2SymbolPreservationError, stable_config_sha256

ARTIFACT_TYPE = "stage11_v2_symbol_preservation_current_truth"
SCHEMA_VERSION = "1.0.0"
EXPECTED_STATE = "IMPLEMENTATION_READY_DEVELOPMENT_TRAINING_PENDING"
EXPECTED_BASE_MAIN_SHA = "3aa92c551cf9fc91ad6ebb4758cb842e04f4022c"
EXPECTED_BRANCH = "stage11-v2-symbol-preservation-residual-unet"
EXPECTED_CONFIG_SHA256 = "9f041aad61eecba66843e4456ec05e14e9bbfb40d93a39e49033ec7d4d500a4d"


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
    _require(payload.get("state") == EXPECTED_STATE, "unexpected V2 state")

    source = payload.get("trainingSource") or {}
    _require(source.get("datasetId") == "deepscoresv2.dense.v2", "dataset id mismatch")
    _require(source.get("archiveMd5Expected") == EXPECTED_ARCHIVE_MD5, "dataset MD5 mismatch")
    _require(source.get("rightsClearedForCommercialTraining") is True, "training rights must be cleared")
    _require(source.get("privateStudentUserDataAuthorized") is False, "private/student/user training data must remain forbidden")

    v1 = payload.get("v1Reference") or {}
    _require(v1.get("stage9aStatus") == "review_required", "V1 Stage 9A reference must record review_required")
    _require(float(v1.get("inkRecallDelta")) == -0.166, "V1 ink recall reference mismatch")
    _require(v1.get("repositoryEvidenceImported") is False, "operator-reported V1 evidence must not be presented as repository-imported evidence")

    config = payload.get("v2Config") or {}
    expected_loss = LossWeights().as_dict()
    _require(config.get("loss") == expected_loss, "V2 loss weights mismatch")
    _require(config.get("patchSize") == 512, "V2 patch size mismatch")
    _require(float(config.get("symbolCenteredFraction")) == 0.5, "V2 symbol sampling fraction mismatch")
    _require(config.get("modelFamily") == "Residual U-Net", "V2 model family mismatch")
    _require(config.get("version") == "V2", "V2 version mismatch")
    _require(config.get("datasetMd5") == EXPECTED_ARCHIVE_MD5, "V2 config dataset MD5 mismatch")
    _require(stable_config_sha256(config) == EXPECTED_CONFIG_SHA256, "V2 config hash mismatch")
    _require(payload.get("v2ConfigSha256") == EXPECTED_CONFIG_SHA256, "recorded V2 config hash mismatch")

    gates = payload.get("gates") or {}
    _require(gates.get("developmentTrainingCompleted") is False, "development training is not yet evidenced")
    _require(gates.get("developmentGatePassed") is False, "development gate cannot pass before evidence")
    _require(gates.get("heldOutEvaluationAuthorized") is False, "held-out evaluation must remain closed")
    _require(gates.get("stage9aV2EvaluationAuthorized") is False, "V2 Stage 9A must remain closed before development gate")
    _require(gates.get("finalModelSelected") is False, "final model selection is forbidden")
    _require(gates.get("stage12EntryAuthorized") is False, "Stage 12 entry is forbidden")
    _require(gates.get("productionInferenceAuthorized") is False, "production inference is forbidden")

    implementation = payload.get("implementation") or {}
    for key in ("symbolAwareParserReady", "symbolMasksReady", "hardExampleSamplingReady", "compositeLossReady", "splitLeakageGuardReused", "trainingNotebookReady", "developmentEvalNotebookReady", "heldOutEvalNotebookReady", "stage9aEvalNotebookReady", "ciValidationReady"):
        _require(implementation.get(key) is True, f"implementation flag must be true: {key}")

    required_paths = set(payload.get("notebooks") or [])
    for path in (
        "notebooks/stage11_deepscoresv2_dense_residual_unet_v2_symbol_preservation_colab.ipynb",
        "notebooks/stage11_deepscoresv2_dense_v2_dev_eval_colab.ipynb",
        "notebooks/stage11_deepscoresv2_dense_v2_heldout_eval_colab.ipynb",
        "notebooks/stage11_deepscoresv2_dense_v2_stage9a_symbol_region_eval_colab.ipynb",
    ):
        _require(path in required_paths, f"missing notebook declaration: {path}")

    safety = payload.get("safety") or {}
    for key in ("historicalEvidenceImmutable", "sourceFamilyLeakageForbidden", "heldOutNeverTrainOrTune", "weightsMustNotMutateDuringEvaluation", "omrCorrectnessNotImplied", "musicalTruthNotImplied", "automaticProductionPromotionForbidden"):
        _require(safety.get(key) is True, f"required safety assertion missing: {key}")

    return {
        "state": EXPECTED_STATE,
        "implementationReady": True,
        "developmentTrainingCompleted": False,
        "heldOutEvaluationAuthorized": False,
        "stage12EntryAuthorized": False,
        "configSha256": EXPECTED_CONFIG_SHA256,
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return validate_stage11_v2_current_truth(payload)
    except Stage11V2SymbolPreservationError as exc:
        raise Stage11V2CurrentTruthError(str(exc)) from exc
