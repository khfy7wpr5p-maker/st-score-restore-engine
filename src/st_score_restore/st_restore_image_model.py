"""Stage 11 provider-neutral ST Restore Image Model foundation.

This module defines training/readiness and release-boundary contracts plus a
synthetic-only research candidate path. It does not train a model, download
weights, enable production inference, or approve model outputs.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable, Mapping

CONTRACT_VERSION = "stage11.st-restore-image-model-foundation.v1"
ENGINE_ID = "st_restore_image_model"
FOUNDATION_STATE = "FOUNDATION_COMPLETE_AWAITING_SEPARATE_TRAINING_AUTHORIZATION"

SUPPORTED_OBJECTIVES = frozenset(
    {
        "restoration",
        "denoising",
        "dewarping",
        "deblurring",
        "illumination_correction",
        "super_resolution",
        "structure_preservation",
    }
)


class ImageModelContractError(ValueError):
    """Raised when Stage 11 foundation boundaries are violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ImageModelContractError(message)


def _text(value: Any) -> str:
    return str(value or "").strip()


def build_training_readiness_manifest(
    *,
    objectives: Iterable[str],
    dataset_manifest_digest: str | None = None,
    dataset_collection_authorized: bool = False,
    model_training_authorized: bool = False,
    user_document_training_use_authorized: bool = False,
) -> dict[str, Any]:
    """Describe training readiness without authorizing or executing training."""

    normalized = sorted({_text(item) for item in objectives if _text(item)})
    _require(bool(normalized), "at least one training objective is required")
    unknown = [item for item in normalized if item not in SUPPORTED_OBJECTIVES]
    _require(not unknown, f"unsupported objective(s): {', '.join(unknown)}")

    _require(dataset_collection_authorized is False, "dataset collection is not authorized")
    _require(model_training_authorized is False, "model training is not authorized")
    _require(
        user_document_training_use_authorized is False,
        "user/private document training use is not authorized",
    )
    _require(
        dataset_manifest_digest in (None, ""),
        "real training dataset manifest is not admitted at the foundation boundary",
    )

    return {
        "contractVersion": CONTRACT_VERSION,
        "state": FOUNDATION_STATE,
        "objectives": normalized,
        "architectureFamily": "UNSELECTED",
        "datasetManifestDigest": None,
        "datasetCollectionAuthorized": False,
        "modelTrainingAuthorized": False,
        "userDocumentTrainingUseAuthorized": False,
        "modelWeightsEstablished": False,
        "trainingExecuted": False,
        "nextSafeBoundary": "separate_stage11_training_and_dataset_authorization",
    }


def validate_release_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate shape while keeping release/inference ineligible in this stage."""

    required = (
        "modelId",
        "modelVersion",
        "architectureFamily",
        "weightsDigest",
        "trainingDataManifestDigest",
        "evaluationEvidenceDigest",
        "calibrationEvidenceDigest",
        "disableRollbackPlanId",
    )
    missing = [key for key in required if not _text(manifest.get(key))]
    _require(not missing, f"release manifest missing: {', '.join(missing)}")

    forbidden_true = (
        "productionInferenceAuthorized",
        "realUserCohortAuthorized",
        "modelPublicationAuthorized",
        "automaticFinalSelectionAuthorized",
    )
    expanded = [key for key in forbidden_true if manifest.get(key) is True]
    _require(not expanded, f"unauthorized release scope: {', '.join(expanded)}")

    return {
        "contractVersion": CONTRACT_VERSION,
        "manifestValidForFoundationReview": True,
        "releaseEligible": False,
        "productionInferenceAuthorized": False,
        "requiresIndependentStage9aEvidence": True,
        "requiresStage9Comparator": True,
        "requiresStage10Selector": True,
        "reasonCodes": ["STAGE11_TRAINING_AND_RELEASE_NOT_AUTHORIZED"],
    }


def build_selector_capability_descriptor(
    *,
    model_id: str = "st-restore-image-model",
    model_version: str = "untrained-foundation",
) -> dict[str, Any]:
    """Return a Stage 10-compatible descriptor that is deliberately not invokable."""

    _require(bool(_text(model_id)), "model id required")
    _require(bool(_text(model_version)), "model version required")
    return {
        "engineId": ENGINE_ID,
        "modelId": _text(model_id),
        "modelVersion": _text(model_version),
        "approvalState": "unapproved",
        "availabilityState": "unavailable",
        "enabled": False,
        "reasonCodes": [
            "STAGE11_MODEL_NOT_TRAINED",
            "STAGE11_MODEL_NOT_RELEASE_APPROVED",
        ],
    }


def run_synthetic_research_candidate(
    *,
    source_descriptor: Mapping[str, Any],
    executor: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> dict[str, Any]:
    """Exercise the future adapter contract without real image/model execution."""

    _require(callable(executor), "synthetic executor required")
    source = deepcopy(dict(source_descriptor))
    source_id = _text(source.get("artifactId"))
    source_digest = _text(source.get("contentDigest"))
    _require(bool(source_id), "source artifact id required")
    _require(bool(source_digest), "source content digest required")
    before = deepcopy(source)

    raw = executor(deepcopy(source))
    _require(isinstance(raw, Mapping), "synthetic executor must return a mapping")
    _require(source == before, "synthetic executor mutated immutable source descriptor")

    candidate_id = _text(raw.get("artifactId"))
    candidate_digest = _text(raw.get("contentDigest"))
    config_digest = _text(raw.get("configDigest"))
    _require(bool(candidate_id), "candidate artifact id required")
    _require(candidate_id != source_id, "candidate must be derivative")
    _require(bool(candidate_digest), "candidate content digest required")
    _require(bool(config_digest), "config digest required")

    return {
        "contractVersion": CONTRACT_VERSION,
        "engineId": ENGINE_ID,
        "engineVersion": "synthetic-foundation-v1",
        "artifactId": candidate_id,
        "contentDigest": candidate_digest,
        "derivedFrom": {
            "artifactId": source_id,
            "contentDigest": source_digest,
        },
        "configDigest": config_digest,
        "syntheticOnly": True,
        "modelWeightsUsed": False,
        "networkUsed": False,
        "trainingExecuted": False,
        "productionInference": False,
        "provenanceComplete": True,
        "safetyHandoff": {
            "requiresStage9aPreservationEvidence": True,
            "requiresStage9Comparator": True,
            "requiresStage10Selector": True,
            "automaticFinalSelectionAuthorized": False,
        },
    }


def run_synthetic_image_model_drills() -> dict[str, Any]:
    source = {"artifactId": "synthetic-source-1", "contentDigest": "sha256:source"}

    def executor(received: Mapping[str, Any]) -> Mapping[str, Any]:
        return {
            "artifactId": "synthetic-candidate-1",
            "contentDigest": "sha256:candidate",
            "configDigest": "sha256:config",
        }

    candidate = run_synthetic_research_candidate(
        source_descriptor=source,
        executor=executor,
    )
    readiness = build_training_readiness_manifest(
        objectives=("denoising", "dewarping", "structure_preservation"),
    )
    descriptor = build_selector_capability_descriptor()

    return {
        "contractVersion": CONTRACT_VERSION,
        "state": FOUNDATION_STATE,
        "syntheticCandidatePass": (
            candidate["syntheticOnly"] is True
            and candidate["modelWeightsUsed"] is False
            and candidate["safetyHandoff"]["requiresStage9aPreservationEvidence"] is True
        ),
        "trainingRemainsUnauthorized": readiness["modelTrainingAuthorized"] is False,
        "selectorWillSkipUntrainedModel": (
            descriptor["approvalState"] == "unapproved"
            and descriptor["availabilityState"] == "unavailable"
            and descriptor["enabled"] is False
        ),
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
    }
