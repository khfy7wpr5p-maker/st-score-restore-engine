from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "evidence/stage9/stage9-entry-authorization.v1.json"
TRUTH = ROOT / "docs/live/ST_SCORE_RESTORE_STAGE8_FINAL_EXIT_CURRENT_TRUTH.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"BLOCKED: {message}")


def main() -> None:
    auth = json.loads(AUTH.read_text(encoding="utf-8"))
    truth = json.loads(TRUTH.read_text(encoding="utf-8"))
    require(auth.get("decision") == "AUTHORIZE_STAGE9_ENTRY_AND_MULTI_ENGINE_COMPARATOR_FOUNDATION", "decision drifted")
    require(auth.get("authorizationSourceCode") == "explicit_user_authorization", "authorization source drifted")
    binding = auth.get("stage8FinalExitBinding", {})
    require(binding.get("currentTruthGitBlobSha") == "65d688e0525ffe9c0c6ef32c6a1c812d09f6e9ed", "Stage 8 truth binding drifted")
    require(binding.get("stage8FinalMainSha") == "878ce22e3189ef5eeb96da1db5ca0d5297655f3f", "Stage 8 main binding drifted")
    require(truth.get("stage8", {}).get("exit_pass") is True, "Stage 8 exit is not PASS")
    require(truth.get("stage9", {}).get("entry_eligible") is True, "Stage 9 not entry eligible")
    scope = auth.get("scope", {})
    require(scope.get("stage9EntryAuthorized") is True and scope.get("stage9Started") is True, "Stage 9 entry/start missing")
    for key in (
        "automaticFinalSelectionAuthorized",
        "teacherApprovalAutomationAuthorized",
        "stage9aEntryAuthorized",
        "stage9aTrainingAuthorized",
        "stage10EntryAuthorized",
        "stage10SelectorActivationAuthorized",
        "docresRuntimeDependencyApproved",
        "modelArtifactDownloadAuthorized",
        "networkFetchAuthorized",
        "providerSpecificActivationAuthorized",
        "liveResourceCreationAuthorized",
        "productionDeploymentAuthorized",
        "thresholdChangesAuthorized",
        "resourceLimitChangesAuthorized",
        "heldOutRetuningAuthorized",
        "modelTrainingAuthorized",
        "modelPublicationAuthorized",
    ):
        require(scope.get(key) is False, f"unauthorized scope widened: {key}")
    safety = auth.get("safetyBoundaries", {})
    for key in (
        "sourceArtifactImmutable",
        "derivedArtifactsRequireProvenance",
        "safetyValidationPrecedesComparatorEligibility",
        "hardDeterministicVetoCannotBeOverridden",
        "hardSemanticVetoCannotBeOverriddenWhenPresent",
        "originalAlwaysSelectable",
        "reviewRequiredCannotBecomeAutomaticWinner",
        "unknownEvidenceFailsSafe",
        "noOpaqueUniversalQualityScore",
    ):
        require(safety.get(key) is True, f"safety boundary missing: {key}")
    print("PASS: Stage 9 entry authorization is fail-closed and bound to Stage 8 final truth")


if __name__ == "__main__":
    main()
