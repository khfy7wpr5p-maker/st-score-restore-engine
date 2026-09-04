from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_stage5_final_exit(
    qa_evidence: dict[str, Any],
    acceptance: dict[str, Any],
    stage4_final: dict[str, Any],
    stage5_entry: dict[str, Any],
    stage5_start: dict[str, Any],
) -> dict[str, Any]:
    if stage4_final.get("stage4ExitPass") is not True:
        raise ValueError("Stage 4 final PASS is required")
    if stage5_entry.get("decision") != "AUTHORIZE_STAGE5_ENTRY":
        raise ValueError("Stage 5 entry authorization is required")
    if stage5_start.get("decision") != "AUTHORIZE_STAGE5_FRAMEWORK_START_AND_LOCAL_IMPLEMENTATION_EXECUTION":
        raise ValueError("Stage 5 framework/start authorization is required")
    scope = stage5_start.get("scope") or {}
    if scope.get("localAccessibilityVerificationAuthorized") is not True or scope.get("localDisplayQaAuthorized") is not True:
        raise ValueError("Stage 5 local accessibility/display QA authorization is required")

    if qa_evidence.get("evidenceId") != "stage5.accessibility-display-qa.v1":
        raise ValueError("unexpected Stage 5 QA evidence ID")
    production = qa_evidence.get("productionReviewUiCheckpoint") or {}
    if production.get("mainSha") != "ad3dc11cec311b345fac600316a44d05d444f21b" or production.get("mergePr") != 153:
        raise ValueError("Stage 5 production review UI checkpoint mismatch")
    screen_reader = qa_evidence.get("screenReaderExecution") or {}
    if screen_reader.get("temporaryProbePr") != 154 or screen_reader.get("temporaryProbeMerged") is not False:
        raise ValueError("screen-reader probe must remain explicitly temporary/unmerged")
    if screen_reader.get("exactHeadSha") != "214b31c67b4ca3af5cb3d28ef312162a22af3420":
        raise ValueError("screen-reader exact head mismatch")
    if screen_reader.get("workflowRunId") != 33843450746 or screen_reader.get("jobId") != 100930256714:
        raise ValueError("screen-reader execution checkpoint mismatch")
    if screen_reader.get("result") != "PASS":
        raise ValueError("screen-reader execution must PASS")
    assertions = screen_reader.get("assertions") or {}
    required_screen_reader = {
        "connectionControlNamesAndRolesObserved",
        "reviewWorkspaceNamesAndRolesObserved",
        "sourceAndCandidateEvidenceNamesObserved",
        "reviewNotesObserved",
        "approveRejectReprocessObserved",
        "realSpeechOutputObserved",
        "keyboardOnlyTraversalExecuted",
    }
    if any(assertions.get(key) is not True for key in required_screen_reader):
        raise ValueError("screen-reader assertions incomplete")

    display = qa_evidence.get("boundedDisplayQa") or {}
    if display.get("pullRequest") != 155 or display.get("exactHeadSha") != "b8dd7c9aa73d5b6e11acefd8be07575f0a7ec16e":
        raise ValueError("bounded display QA exact checkpoint mismatch")
    if display.get("result") != "PASS":
        raise ValueError("bounded display QA must PASS")
    contract = display.get("contract") or {}
    expected_contract = {
        "cropEncoding": "png_grayscale_8bit",
        "inputColorProfiles": "not_inspected",
        "colorManagementValidated": False,
        "grayscaleBrowserDecodeVerified": True,
        "actualPixelsAtOneXVerified": True,
        "colorFidelityNotClaimed": True,
    }
    if contract != expected_contract:
        raise ValueError("bounded display-integrity contract mismatch")

    safety = qa_evidence.get("safetyBoundaries") or {}
    for key in (
        "realOrDerivativeBytesInOrdinaryGit",
        "rawPrivateMetricsInOrdinaryGit",
        "productionDeploymentAuthorized",
        "stage6EntryAuthorized",
        "productionThresholdChangesAuthorized",
        "productionResourceLimitChangesAuthorized",
        "modelTrainingAuthorized",
    ):
        if safety.get(key) is not False:
            raise ValueError(f"unsafe Stage 5 QA boundary: {key}")

    if acceptance.get("acceptanceId") != "stage5.final-exit-acceptance.v1" or acceptance.get("decision") != "PASS":
        raise ValueError("Stage 5 final acceptance must PASS")
    if acceptance.get("acceptedOn") != "2026-09-04":
        raise ValueError("unexpected Stage 5 final acceptance date")
    if acceptance.get("decisionAuthorityReference") != "authority:project-governance-owner-20260904-01":
        raise ValueError("unexpected Stage 5 final acceptance authority")
    if acceptance.get("acceptanceSourceCode") != "explicit_user_authorization":
        raise ValueError("Stage 5 final acceptance must come from explicit user authorization")
    digest = acceptance.get("stage5QaEvidenceDigest") or {}
    if digest != {"algorithm": "sha256", "value": canonical_sha256(qa_evidence)}:
        raise ValueError("Stage 5 QA evidence digest mismatch")

    readiness = acceptance.get("acceptedReadinessState") or {}
    if readiness.get("decision") != "STAGE5_COMPLETE_PASS" or readiness.get("readinessPrerequisitesSatisfied") is not True:
        raise ValueError("Stage 5 readiness state is not complete/pass")
    if readiness.get("blockerCount") != 0 or readiness.get("blockerCodes") != []:
        raise ValueError("Stage 5 final acceptance cannot retain blockers")
    for key in (
        "accessibleTeacherReviewInterfaceImplemented",
        "realBrowserQaPassed",
        "screenReaderQaPassed",
        "boundedDisplayIntegrityQaPassed",
        "staleScreenFailClosedVerified",
        "evidenceBoundReviewDecisionVerified",
    ):
        if readiness.get(key) is not True:
            raise ValueError(f"Stage 5 readiness assertion missing: {key}")
    if readiness.get("colorManagementValidated") is not False or readiness.get("colorFidelityClaimed") is not False:
        raise ValueError("Stage 5 must not claim color-management validation or color fidelity")

    if acceptance.get("stage5ExitPass") is not True or acceptance.get("stage6EntryEligible") is not True:
        raise ValueError("Stage 5 PASS must make Stage 6 entry eligible")
    if acceptance.get("stage6EntryAuthorized") is not False or acceptance.get("stage6Started") is not False:
        raise ValueError("Stage 6 must remain separately unauthorized/not started")
    claims = acceptance.get("claims") or {}
    forbidden_true = (
        "productionDeploymentAuthorized",
        "identityNetworkInfrastructureAuthorized",
        "previewReleaseAuthorized",
        "productionThresholdChangesAuthorized",
        "productionResourceLimitChangesAuthorized",
        "heldOutRetuningAuthorized",
        "modelTrainingAuthorized",
        "publicationAuthorized",
        "colorManagementValidated",
        "colorFidelityCertified",
        "representativenessEstablished",
        "absenceOfBiasEstablished",
        "omrCorrectnessEstablished",
        "restorationEffectivenessEstablished",
    )
    if any(claims.get(key) is not False for key in forbidden_true):
        raise ValueError("Stage 5 final acceptance contains an unauthorized claim")

    return {
        "stage5State": "COMPLETE_PASS",
        "stage5ExitPass": True,
        "stage6EntryEligible": True,
        "stage6EntryAuthorized": False,
        "stage6Started": False,
        "qaEvidenceDigest": canonical_sha256(qa_evidence),
        "acceptanceDigest": canonical_sha256(acceptance),
        "colorManagementValidated": False,
        "colorFidelityCertified": False,
    }


__all__ = ["canonical_sha256", "validate_stage5_final_exit"]
