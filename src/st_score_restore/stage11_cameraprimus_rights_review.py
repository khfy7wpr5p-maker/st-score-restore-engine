"""Fail-closed validator for the Stage 11 Camera-PrIMuS rights review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPECTED_DECISION = "COMPLETE_NOT_ADMITTED_FOR_COMMERCIAL_MODEL_TRAINING"


class Stage11CameraPrIMuSRightsReviewError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11CameraPrIMuSRightsReviewError(message)


def validate_stage11_cameraprimus_rights_review(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == "stage11_cameraprimus_rights_review", "artifact type mismatch")
    _require(payload.get("dataset") == "CameraPrIMuS", "dataset mismatch")
    _require(payload.get("decision") == EXPECTED_DECISION, "unexpected rights decision")
    _require(payload.get("commercialTrainingAdmissionAllowed") is False, "commercial training must remain unadmitted")

    evidence = payload.get("evidence") or []
    _require(len(evidence) >= 4, "rights review must preserve all primary evidence classes")
    sources = {item.get("source") for item in evidence if isinstance(item, dict)}
    for required_source in (
        "official_camera_primus_dataset_page",
        "camera_primus_ismir_2018_paper",
        "towards_universal_omr_ismir_2024",
        "rism_data_services",
    ):
        _require(required_source in sources, f"missing evidence source {required_source}")
    for item in evidence:
        _require(item.get("sufficientForCommercialTrainingAdmission") is False, "no reviewed source may silently authorize commercial training")

    reasoning = payload.get("reasoning") or {}
    for key in (
        "publicAvailabilityIsNotCommercialLicense",
        "paperLicenseDoesNotAutomaticallyLicenseDatasetPackage",
        "underlyingSourceLicenseDoesNotAutomaticallyLicenseDerivedPackage",
        "failClosedForCommercialRoadmap",
    ):
        _require(reasoning.get(key) is True, f"reasoning assertion {key} must be true")

    assertions = payload.get("assertions") or {}
    for key in (
        "cameraPrIMuSDriveBytesMayRemainStoredButNotAdmittedForCommercialTraining",
        "noCameraPrIMuSTrainingRunMayBeClaimedUnderThisDecision",
        "privateUserStudentDataRemainsUnauthorized",
        "productionInferenceRemainsUnauthorized",
        "stage12RemainsUnauthorized",
    ):
        _require(assertions.get(key) is True, f"assertion {key} must be true")

    alternatives = payload.get("safeAlternatives") or []
    _require(len(alternatives) >= 3, "safe alternatives must be recorded")
    return {
        "decision": EXPECTED_DECISION,
        "commercialTrainingAdmissionAllowed": False,
        "reviewComplete": True,
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_stage11_cameraprimus_rights_review(payload)
