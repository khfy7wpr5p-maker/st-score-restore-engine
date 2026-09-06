"""Fail-closed Stage 9A final-exit acceptance validation."""

from __future__ import annotations

from typing import Any, Mapping

ACCEPTANCE_ID = "stage9a.final-exit-acceptance.v1"
FINAL_STATE = "COMPLETE_PASS_PROVIDER_NEUTRAL_MSPM_EVIDENCE_AND_SAFE_ROUTING_FOUNDATION"
EXACT_HEAD_SHA = "5686d3627bd4f1ffc7e942588c2d70daa79c7b22"
CAPABILITY_MERGE_SHA = "45dfd78c6abbed1f48428fac1359bd54fb74e75a"
NEXT_BOUNDARY = "separate_stage10_entry_authorization"

EXPECTED_EXACT_HEAD_RUNS = {
    "repositoryValidation": 34058008624,
    "stage4Governance": 34058008629,
    "stage5Governance": 34058008663,
    "stage6Governance": 34058008610,
    "stage7Governance": 34058008576,
    "stage8Governance": 34058008617,
    "stage9Governance": 34058008587,
    "stage9aGovernance": 34058008665,
}
EXPECTED_POSTMERGE_RUNS = {
    "repositoryValidation": 34058100446,
    "stage4Governance": 34058100442,
    "stage5Governance": 34058100507,
    "stage6Governance": 34058100425,
    "stage7Governance": 34058100472,
    "stage8Governance": 34058100445,
    "stage9Governance": 34058100474,
    "stage9aGovernance": 34058100427,
}


class Stage9AFinalExitError(ValueError):
    """Raised when the Stage 9A final-exit artifact is inconsistent or unsafe."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage9AFinalExitError(message)


def _validate_ci(group: Any, expected: Mapping[str, int], name: str) -> None:
    _require(isinstance(group, Mapping), f"{name} CI evidence missing")
    for key, run_id in expected.items():
        item = group.get(key)
        _require(isinstance(item, Mapping), f"{name} CI item missing: {key}")
        _require(item.get("runId") == run_id, f"{name} CI run mismatch: {key}")
        _require(item.get("result") == "SUCCESS", f"{name} CI did not succeed: {key}")


def validate_stage9a_final_exit(acceptance: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(acceptance, Mapping), "final-exit acceptance must be an object")
    _require(acceptance.get("acceptanceId") == ACCEPTANCE_ID, "unexpected acceptance id")
    _require(acceptance.get("decision") == "PASS", "Stage 9A final exit must PASS")
    _require(acceptance.get("state") == FINAL_STATE, "unexpected Stage 9A final state")
    _require(acceptance.get("blockerCount") == 0, "Stage 9A blocker count must be zero")

    checkpoint = acceptance.get("capabilityCheckpoint")
    _require(isinstance(checkpoint, Mapping), "capability checkpoint missing")
    _require(checkpoint.get("pullRequest") == 184, "unexpected capability PR")
    _require(checkpoint.get("exactHeadSha") == EXACT_HEAD_SHA, "exact-head SHA mismatch")
    _require(checkpoint.get("capabilityMergeSha") == CAPABILITY_MERGE_SHA, "capability merge SHA mismatch")
    _require(checkpoint.get("pythonMatrix") == ["3.11", "3.12"], "Python matrix mismatch")
    _validate_ci(checkpoint.get("exactHeadCi"), EXPECTED_EXACT_HEAD_RUNS, "exact-head")
    _validate_ci(checkpoint.get("postmergeCi"), EXPECTED_POSTMERGE_RUNS, "postmerge")

    capabilities = acceptance.get("acceptedCapabilities")
    _require(isinstance(capabilities, Mapping), "accepted capabilities missing")
    for field in (
        "providerNeutralMspmEvidenceContractComplete",
        "extensibleMusicTabTaxonomyFoundationComplete",
        "sourceCandidateProvenanceBindingComplete",
        "materialSemanticHarmHardVetoComplete",
        "uncertainIncompleteUnavailableEvidenceFailsSafe",
        "originalFallbackRetained",
        "stage9ComparatorHandoffComplete",
        "syntheticPreservationDrillsPass",
    ):
        _require(capabilities.get(field) is True, f"accepted capability missing: {field}")
    for field in ("learnedSemanticModelComplete", "trainedMspmModelComplete", "productionInferenceComplete"):
        _require(capabilities.get(field) is False, f"unsupported Stage 9A completion claim: {field}")

    stage10 = acceptance.get("stage10")
    _require(isinstance(stage10, Mapping), "Stage 10 boundary missing")
    _require(stage10.get("entryEligible") is True, "Stage 10 should be entry eligible after Stage 9A exit")
    for field in ("entryAuthorized", "started", "selectorActivationAuthorized"):
        _require(stage10.get(field) is False, f"Stage 10 scope expanded without authorization: {field}")

    nonclaims = acceptance.get("explicitNonClaimsAndBoundaries")
    _require(isinstance(nonclaims, Mapping), "explicit non-claims missing")
    for field, value in nonclaims.items():
        _require(value is False, f"unsupported claim or authorization became true: {field}")

    safety = acceptance.get("safetyInvariants")
    _require(isinstance(safety, Mapping), "safety invariants missing")
    for field, value in safety.items():
        _require(value is True, f"Stage 9A safety invariant missing: {field}")

    _require(acceptance.get("nextSafeBoundary") == NEXT_BOUNDARY, "unexpected next safe boundary")
    return {
        "result": "PASS",
        "state": FINAL_STATE,
        "stage10EntryEligible": True,
        "stage10EntryAuthorized": False,
        "modelTrainingAuthorized": False,
        "productionInferenceAuthorized": False,
    }


__all__ = ["Stage9AFinalExitError", "validate_stage9a_final_exit"]
