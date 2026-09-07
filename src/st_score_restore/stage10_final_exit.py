"""Fail-closed Stage 10 final-exit acceptance validation."""

from __future__ import annotations

from typing import Any, Mapping

from st_score_restore.stage10_entry_authorization import validate_stage10_entry_authorization
from st_score_restore.st_restore_selector import run_synthetic_selector_drills

ACCEPTANCE_ID = "stage10.final-exit-acceptance.v1"
STATE = "COMPLETE_PASS_PROVIDER_NEUTRAL_ST_RESTORE_SELECTOR_FOUNDATION"
EXACT_HEAD_SHA = "eba6219c1c9643d1ff2fd7e9137eccdd444a3d8f"
CAPABILITY_MERGE_SHA = "5e40d50f4c16cdae9267c5995511d160d95dfb24"

EXPECTED_EXACT_HEAD_CI = {
    "repositoryValidation": (34087934985, 507),
    "stage4Governance": (34087935023, 118),
    "stage5Governance": (34087935139, 110),
    "stage6Governance": (34087934967, 69),
    "stage7Governance": (34087934924, 22),
    "stage8Governance": (34087935016, 16),
    "stage9Governance": (34087934942, 9),
    "stage9aGovernance": (34087934969, 5),
    "stage10Governance": (34087935083, 1),
}
EXPECTED_POSTMERGE_CI = {
    "repositoryValidation": (34088025455, 508),
    "stage4Governance": (34088025432, 119),
    "stage5Governance": (34088025465, 111),
    "stage6Governance": (34088025434, 70),
    "stage7Governance": (34088025463, 23),
    "stage8Governance": (34088025462, 17),
    "stage9Governance": (34088025469, 10),
    "stage9aGovernance": (34088025516, 6),
    "stage10Governance": (34088025482, 2),
}
EXPECTED_BINDINGS = {
    "entryAuthorizationPath": "evidence/stage10/stage10-entry-authorization.v1.json",
    "entryAuthorizationGitBlobSha1": "a882b2a4253406a0b4365a20a091e0ae2e0485ee",
    "selectorContractPath": "api/stage10-selector-contract.v1.json",
    "selectorContractGitBlobSha1": "b642c310eb630da84184a9e6539f238ed679ed6f",
    "selectorCorePath": "src/st_score_restore/st_restore_selector.py",
    "selectorCoreGitBlobSha1": "f5b23fe1c42e0f8085d1fb5c046b070f4503fd45",
    "architectureDecisionPath": "docs/adr/0021-stage10-st-restore-selector-foundation.md",
    "architectureDecisionGitBlobSha1": "7f8691329f56f6002e43d63b924dc7a2523262a2",
}


class Stage10FinalExitError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage10FinalExitError(message)


def _validate_ci(actual: Any, expected: Mapping[str, tuple[int, int]], label: str) -> None:
    _require(isinstance(actual, Mapping), f"{label} CI evidence missing")
    _require(set(actual) == set(expected), f"{label} CI workflow set mismatch")
    for key, (run_id, run_number) in expected.items():
        item = actual.get(key)
        _require(isinstance(item, Mapping), f"{label} CI item missing: {key}")
        _require(item.get("runId") == run_id, f"{label} runId mismatch: {key}")
        _require(item.get("runNumber") == run_number, f"{label} runNumber mismatch: {key}")
        _require(item.get("result") == "SUCCESS", f"{label} CI not successful: {key}")


def validate_stage10_final_exit(
    acceptance: Mapping[str, Any],
    authorization: Mapping[str, Any],
    stage9a_truth: Mapping[str, Any],
    selector_contract: Mapping[str, Any],
) -> dict[str, Any]:
    _require(isinstance(acceptance, Mapping), "acceptance must be an object")
    validate_stage10_entry_authorization(authorization, stage9a_truth)

    _require(acceptance.get("acceptanceId") == ACCEPTANCE_ID, "unexpected acceptance id")
    _require(acceptance.get("decision") == "PASS", "Stage 10 final decision must PASS")
    _require(acceptance.get("state") == STATE, "unexpected Stage 10 final state")
    _require(acceptance.get("blockerCount") == 0, "Stage 10 blockers remain")

    checkpoint = acceptance.get("capabilityCheckpoint")
    _require(isinstance(checkpoint, Mapping), "capability checkpoint missing")
    _require(checkpoint.get("mergePr") == 186, "capability PR mismatch")
    _require(checkpoint.get("exactHeadSha") == EXACT_HEAD_SHA, "exact-head SHA mismatch")
    _require(checkpoint.get("capabilityMergeSha") == CAPABILITY_MERGE_SHA, "capability merge SHA mismatch")
    _validate_ci(checkpoint.get("exactHeadCi"), EXPECTED_EXACT_HEAD_CI, "exact-head")
    _validate_ci(checkpoint.get("postmergeCi"), EXPECTED_POSTMERGE_CI, "postmerge")
    _require(checkpoint.get("pythonMatrix") == ["3.11", "3.12"], "Python matrix mismatch")

    bindings = acceptance.get("artifactBindings")
    _require(isinstance(bindings, Mapping), "artifact bindings missing")
    for key, value in EXPECTED_BINDINGS.items():
        _require(bindings.get(key) == value, f"artifact binding mismatch: {key}")

    _require(selector_contract.get("contractVersion") == "stage10.st-restore-selector.v1", "selector contract mismatch")
    _require(selector_contract.get("liveSelectorActivationAuthorized") is False, "live selector scope expansion")
    _require(selector_contract.get("automaticFinalSelectionAuthorized") is False, "automatic final-selection scope expansion")
    _require(selector_contract.get("productionDeploymentAuthorized") is False, "production scope expansion")

    capabilities = acceptance.get("acceptedCapabilities")
    _require(isinstance(capabilities, Mapping), "accepted capabilities missing")
    for field in (
        "providerNeutralSelectorContractComplete",
        "engineEligibilityPlanningComplete",
        "originalAlwaysIncluded",
        "stage9RecommendationConsumptionComplete",
        "stage9aEvidenceEnforcementComplete",
        "originalAwareControlledSelectionComplete",
        "failSafeReviewOriginalFallbackComplete",
        "explainableReasonCodesComplete",
        "syntheticSelectorDrillsPass",
    ):
        _require(capabilities.get(field) is True, f"Stage 10 capability incomplete: {field}")
    for field in ("liveSelectorActivationComplete", "automaticFinalUserFacingSelectionComplete"):
        _require(capabilities.get(field) is False, f"unsupported completion claim: {field}")

    drills = run_synthetic_selector_drills()
    _require(drills.get("result") == "PASS", "Stage 10 synthetic selector drills failed")
    _require(drills.get("liveSelectorActivated") is False, "synthetic drills activated selector")
    _require(drills.get("productionDeploymentPerformed") is False, "synthetic drills performed production deployment")
    _require(drills.get("modelTrainingPerformed") is False, "synthetic drills performed model training")

    stage11 = acceptance.get("stage11")
    _require(isinstance(stage11, Mapping), "Stage 11 boundary missing")
    _require(stage11.get("entryEligible") is True, "Stage 11 must be entry eligible")
    for field in ("entryAuthorized", "started", "imageModelTrainingAuthorized"):
        _require(stage11.get(field) is False, f"Stage 11 scope expansion: {field}")

    boundaries = acceptance.get("boundaries")
    _require(isinstance(boundaries, Mapping), "Stage 10 boundaries missing")
    for field, value in boundaries.items():
        _require(value is False, f"unsupported boundary claim: {field}")

    _require(acceptance.get("nextSafeBoundary") == "separate_stage11_entry_authorization", "unexpected next boundary")

    return {
        "result": "PASS",
        "acceptanceId": ACCEPTANCE_ID,
        "state": STATE,
        "capabilityMergeSha": CAPABILITY_MERGE_SHA,
        "stage10ExitPass": True,
        "stage11EntryEligible": True,
        "stage11EntryAuthorized": False,
        "liveSelectorActivationAuthorized": False,
        "automaticFinalSelectionAuthorized": False,
        "productionDeploymentAuthorized": False,
        "nextSafeBoundary": "separate_stage11_entry_authorization",
    }


__all__ = ["ACCEPTANCE_ID", "STATE", "Stage10FinalExitError", "validate_stage10_final_exit"]
