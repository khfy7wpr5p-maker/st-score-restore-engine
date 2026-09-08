#!/usr/bin/env python3
"""Validate the Stage 11 V2a two-family non-held-out shadow observation package."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from st_score_restore.stage11_v2a_shadow_corpus_expansion import (  # noqa: E402
    EXPANDED_PAGE_COUNT,
    EXPANDED_SOURCE_FAMILY_COUNT,
    SECOND_DATASET_ITEM_ID,
    SECOND_SOURCE_FAMILY_ID,
    SECOND_SOURCE_SHA256,
    validate_shadow_corpus_expansion_evidence,
)
from st_score_restore.stage11_v2a_staging_api import (  # noqa: E402
    EXPECTED_PACKAGE_SHA256,
    EXPECTED_PACKAGE_SIZE_BYTES,
)

EVIDENCE = ROOT / "evidence/stage11/v2a/v2a-shadow-corpus-expanded-evidence.v1.json"
TRUTH = ROOT / "docs/live/ST_SCORE_RESTORE_STAGE11_V2A_SHADOW_CORPUS_EXPANDED_CURRENT_TRUTH.json"
EXPECTED_BASE_MAIN_SHA = "cef3c93c3e9f10bb0322bcfc038853f04e5289e2"
EXPECTED_BRANCH = "stage11-v2a-shadow-corpus-source-family-expansion"
EXPECTED_STATE = "NONHELDOUT_SHADOW_CORPUS_SOURCE_FAMILIES_EXPANDED"
EXPECTED_NEXT_BOUNDARY = "nonheldout-shadow-preservation-review-package"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    result = validate_shadow_corpus_expansion_evidence(evidence)
    require(result["status"] == "pass", "expanded evidence validation did not pass")
    require(result["pageObservationCount"] == EXPANDED_PAGE_COUNT, "expanded page count result mismatch")
    require(result["sourceFamilyCount"] == EXPANDED_SOURCE_FAMILY_COUNT, "expanded source family result mismatch")

    truth = json.loads(TRUTH.read_text(encoding="utf-8"))
    require(truth.get("artifactType") == "stage11_v2a_shadow_corpus_expanded_current_truth", "expanded current-truth type mismatch")
    require(truth.get("schemaVersion") == "1.0.0", "expanded current-truth schema mismatch")
    require(truth.get("baseMainSha") == EXPECTED_BASE_MAIN_SHA, "expanded current-truth base main mismatch")
    require(truth.get("implementationBranch") == EXPECTED_BRANCH, "expanded current-truth branch mismatch")
    require(truth.get("state") == EXPECTED_STATE, "expanded current-truth state mismatch")
    require(truth.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "expanded current-truth package SHA mismatch")
    require(int(truth.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "expanded current-truth package size mismatch")
    require(truth.get("evidenceRepoPath") == "evidence/stage11/v2a/v2a-shadow-corpus-expanded-evidence.v1.json", "expanded current-truth evidence path mismatch")
    require(truth.get("nextSafeBoundary") == EXPECTED_NEXT_BOUNDARY, "expanded current-truth next boundary mismatch")

    execution = truth.get("execution") or {}
    require(execution.get("completed") is True, "expanded current-truth execution incomplete")
    require(execution.get("sourceDataKind") == "nonheldout_test_only", "expanded current-truth source kind mismatch")
    require(int(execution.get("pageObservationCount", 0)) == EXPANDED_PAGE_COUNT, "expanded current-truth page count mismatch")
    require(int(execution.get("sourceFamilyCount", 0)) == EXPANDED_SOURCE_FAMILY_COUNT, "expanded current-truth family count mismatch")
    require(execution.get("independentSourceFamiliesVerified") is True, "expanded source-family independence missing")

    families = execution.get("sourceFamilies") or []
    require(isinstance(families, list) and len(families) == 2, "expanded current-truth source family list mismatch")
    second = families[1]
    require(second.get("datasetItemId") == SECOND_DATASET_ITEM_ID, "expanded second dataset item mismatch")
    require(second.get("sourceFamilyId") == SECOND_SOURCE_FAMILY_ID, "expanded second source family mismatch")
    require(second.get("sourceSha256") == SECOND_SOURCE_SHA256, "expanded second source SHA mismatch")

    truth_aggregate = execution.get("aggregate") or {}
    evidence_aggregate = evidence.get("aggregate") or {}
    for key in (
        "meanOfPageMeanAbsDiff",
        "maxPageMeanAbsDiff",
        "minPageMeanAbsDiff",
        "meanChangedPixelFraction",
        "maxChangedPixelFraction",
        "minChangedPixelFraction",
    ):
        require(abs(float(truth_aggregate.get(key, -1.0)) - float(evidence_aggregate.get(key, -2.0))) <= 1e-12, f"expanded current-truth aggregate mismatch: {key}")
    require(truth_aggregate.get("qualityDecisionMade") is False, "expanded current-truth cannot decide quality")
    require(truth_aggregate.get("automaticPromotionPerformed") is False, "expanded current-truth cannot promote")

    authorization = truth.get("authorization") or {}
    require(authorization.get("shadowCorpusObservationAuthorized") is True, "expanded current-truth observation authorization missing")
    for key in (
        "trainingAuthorized",
        "tuningAuthorized",
        "productionInferenceAuthorized",
        "productionPromotionAuthorized",
        "realUserRolloutAuthorized",
        "finalProductionModelSelectionAuthorized",
        "stage12EntryAuthorized",
    ):
        require(authorization.get(key) is False, f"expanded current-truth authorization must remain false: {key}")

    interpretation = truth.get("interpretation") or {}
    require(interpretation.get("metricsAreObservationalOnly") is True, "expanded metrics must remain observational")
    require(interpretation.get("metricsAreQualityGate") is False, "expanded metrics cannot become a quality gate")
    require(interpretation.get("metricsMayTuneModel") is False, "expanded metrics cannot tune the frozen model")
    require(interpretation.get("sourceFamilyExpansionEstablishesProductionReadiness") is False, "expanded observations cannot establish production readiness")

    print(json.dumps({
        "state": truth["state"],
        "pageObservationCount": EXPANDED_PAGE_COUNT,
        "sourceFamilyCount": EXPANDED_SOURCE_FAMILY_COUNT,
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
        "nextSafeBoundary": truth["nextSafeBoundary"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
