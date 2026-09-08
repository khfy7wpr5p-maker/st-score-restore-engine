"""Current-truth validation for the Stage 11 V2a shadow preservation-review blocker."""
from __future__ import annotations

from typing import Any, Mapping

EXPECTED_BASE_MAIN_SHA = "af23595d423dbc513029040cf5b66b906dc8ce12"
EXPECTED_BRANCH = "stage11-v2a-shadow-preservation-review"
EXPECTED_STATE = "NONHELDOUT_SHADOW_PRESERVATION_REVIEW_BLOCKED"
EXPECTED_EVIDENCE_PATH = "evidence/stage11/v2a/v2a-shadow-preservation-review-evidence.v1.json"
EXPECTED_PACKAGE_SHA256 = "7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234"
EXPECTED_NEXT_BOUNDARY = "diagnose-shadow-output-byte-drift-and-structural-veto-root-causes-with-nonheldout-data-only"


class Stage11V2aShadowPreservationCurrentTruthError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aShadowPreservationCurrentTruthError(message)


def validate_current_truth(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == "stage11_v2a_shadow_preservation_review_current_truth", "current truth type mismatch")
    _require(payload.get("schemaVersion") == "1.0.0", "current truth schema mismatch")
    _require(payload.get("baseMainSha") == EXPECTED_BASE_MAIN_SHA, "current truth base main mismatch")
    _require(payload.get("implementationBranch") == EXPECTED_BRANCH, "current truth branch mismatch")
    _require(payload.get("state") == EXPECTED_STATE, "current truth state mismatch")
    _require(payload.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "current truth package SHA mismatch")
    _require(payload.get("evidenceRepoPath") == EXPECTED_EVIDENCE_PATH, "current truth evidence path mismatch")
    execution = payload.get("execution") or {}
    _require(execution.get("completed") is True, "preservation review must be completed")
    _require(int(execution.get("pageCount", 0)) == 5, "current truth page count mismatch")
    _require(int(execution.get("sourceFamilyCount", 0)) == 2, "current truth source-family count mismatch")
    _require(execution.get("verdictCounts") == {"pass": 0, "review_required": 0, "reject": 5}, "current truth verdict counts mismatch")
    _require(execution.get("preservationDisposition") == "blocked", "current truth disposition must be blocked")
    _require(execution.get("automaticPromotionPerformed") is False, "current truth cannot auto-promote")
    cross_run = payload.get("crossRunIdentity") or {}
    _require(cross_run.get("acceptedSourceNormalizedHashesPreserved") is True, "source identity binding missing")
    _require(cross_run.get("priorShadowOutputByteIdentityStable") is False, "cross-run byte drift must remain recorded")
    _require(int(cross_run.get("priorShadowByteMatchCount", -1)) == 1, "cross-run shadow match count mismatch")
    _require(int(cross_run.get("priorShadowByteMatchTotal", 0)) == 5, "cross-run shadow match total mismatch")
    _require(cross_run.get("rootCauseResolved") is False, "cross-run root cause must remain unresolved")
    interpretation = payload.get("interpretation") or {}
    _require(interpretation.get("semanticPerClassIdentityClaimed") is False, "semantic class identity may not be claimed")
    _require(interpretation.get("newMusicalSymbolCreationProven") is False, "new musical symbol creation is not proven")
    _require(interpretation.get("consumedHeldoutMayNotBeUsedForRetuning") is True, "held-out freeze must remain explicit")
    authorization = payload.get("authorization") or {}
    _require(authorization.get("preservationReviewAuthorized") is True, "preservation review authorization missing")
    for key in (
        "trainingAuthorized", "tuningAuthorized", "productionInferenceAuthorized", "productionPromotionAuthorized",
        "realUserRolloutAuthorized", "finalProductionModelSelectionAuthorized", "stage12EntryAuthorized",
    ):
        _require(authorization.get(key) is False, f"authorization must remain false: {key}")
    _require(payload.get("nextSafeBoundary") == EXPECTED_NEXT_BOUNDARY, "current truth next boundary mismatch")
    return {
        "status": "pass",
        "state": EXPECTED_STATE,
        "preservationDisposition": "blocked",
        "priorShadowByteMatchCount": 1,
        "priorShadowByteMatchTotal": 5,
        "productionPromotionAuthorized": False,
        "stage12EntryAuthorized": False,
    }


__all__ = [
    "EXPECTED_BASE_MAIN_SHA",
    "EXPECTED_BRANCH",
    "EXPECTED_STATE",
    "Stage11V2aShadowPreservationCurrentTruthError",
    "validate_current_truth",
]
