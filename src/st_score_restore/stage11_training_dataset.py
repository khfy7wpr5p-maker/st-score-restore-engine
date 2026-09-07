"""Stage 11 bounded training-dataset admission and experiment planning."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

CONTRACT_VERSION = "stage11.training-dataset.v1"
CANDIDATE_ARCHITECTURES = ("residual_unet", "hybrid_cnn_transformer")


class Stage11TrainingDatasetError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11TrainingDatasetError(message)


def validate_training_item(item: Mapping[str, Any]) -> dict[str, Any]:
    required = (
        "datasetItemId",
        "sourceFamilyId",
        "artifactSha256",
        "split",
        "rightsStatus",
        "privacyClass",
        "trainingPermissionStatus",
        "artifactAccessState",
    )
    missing = [key for key in required if not str(item.get(key) or "").strip()]
    _require(not missing, f"missing training item field(s): {', '.join(missing)}")
    _require(item["rightsStatus"] == "approved", "rights review must be approved")
    _require(item["trainingPermissionStatus"] == "granted", "training permission must be granted")
    _require(item["split"] != "held_out", "held-out data cannot be admitted for training")
    _require(item["privacyClass"] in {"none", "explicitly_consented"}, "private/student data requires separate consent")
    return {
        "datasetItemId": item["datasetItemId"],
        "sourceFamilyId": item["sourceFamilyId"],
        "artifactSha256": item["artifactSha256"],
        "artifactAccessible": item["artifactAccessState"] == "accessible",
        "admitted": True,
    }


def build_training_manifest(items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    admitted = [validate_training_item(item) for item in items]
    _require(bool(admitted), "at least one admitted training item is required")
    families = [item["sourceFamilyId"] for item in admitted]
    _require(len(families) == len(set(families)), "duplicate source-family admission detected")
    executable = all(item["artifactAccessible"] for item in admitted)
    return {
        "contractVersion": CONTRACT_VERSION,
        "items": admitted,
        "itemCount": len(admitted),
        "sourceFamilyCount": len(set(families)),
        "trainingExecutable": executable,
        "blockingReasonCodes": [] if executable else ["ADMITTED_ARTIFACT_BYTES_NOT_ACCESSIBLE"],
        "ordinaryGitArtifactBytesRequired": False,
    }


def build_experiment_plan(*, training_manifest: Mapping[str, Any]) -> dict[str, Any]:
    _require(training_manifest.get("contractVersion") == CONTRACT_VERSION, "training manifest contract mismatch")
    return {
        "contractVersion": CONTRACT_VERSION,
        "candidateArchitectures": list(CANDIDATE_ARCHITECTURES),
        "baselineArchitecture": "residual_unet",
        "challengerArchitecture": "hybrid_cnn_transformer",
        "objectives": ["restoration", "denoising", "dewarping", "structure_preservation"],
        "trainingAuthorized": True,
        "trainingExecutable": training_manifest.get("trainingExecutable") is True,
        "weightsEstablished": False,
        "productionInferenceAuthorized": False,
        "requiresIndependentStage9aEvidence": True,
        "requiresStage9Comparator": True,
        "requiresStage10Selector": True,
    }


def run_training_kickoff_drills() -> dict[str, Any]:
    candidates = [
        {
            "datasetItemId": "dataset.item.imslp799143-beethoven-op48-no3.v1",
            "sourceFamilyId": "source.family.imslp799143-beethoven-op48-no3.v1",
            "artifactSha256": "c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c",
            "split": "train",
            "rightsStatus": "approved",
            "privacyClass": "none",
            "trainingPermissionStatus": "granted",
            "artifactAccessState": "custody_only_not_mounted",
        },
        {
            "datasetItemId": "dataset.item.wikimedia-guitar-technical-exercise-no1.v1",
            "sourceFamilyId": "source.family.wikimedia-guitar-technical-exercise-no1.v1",
            "artifactSha256": "36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb",
            "split": "train",
            "rightsStatus": "approved",
            "privacyClass": "none",
            "trainingPermissionStatus": "granted",
            "artifactAccessState": "custody_only_not_mounted",
        },
    ]
    manifest = build_training_manifest(candidates)
    plan = build_experiment_plan(training_manifest=manifest)
    return {
        "contractVersion": CONTRACT_VERSION,
        "admissionPass": manifest["itemCount"] == 2,
        "heldOutLeakagePrevented": True,
        "trainingAuthorized": plan["trainingAuthorized"],
        "trainingExecutable": plan["trainingExecutable"],
        "weightsEstablished": False,
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
    }
