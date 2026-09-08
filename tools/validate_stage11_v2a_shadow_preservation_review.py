#!/usr/bin/env python3
"""Validate committed Stage 11 V2a non-held-out preservation-review evidence."""
from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage11_v2a_shadow_preservation_review import (
    Stage11V2aShadowPreservationReviewError,
    validate_preservation_review_evidence,
)
from st_score_restore.stage11_v2a_shadow_preservation_review_current_truth import (
    validate_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-shadow-preservation-review-evidence.v1.json"
EXPANDED = ROOT / "evidence" / "stage11" / "v2a" / "v2a-shadow-corpus-expanded-evidence.v1.json"
CURRENT_TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_SHADOW_PRESERVATION_REVIEW_CURRENT_TRUTH.json"


def _accepted_shadow_page_identities(payload: dict) -> dict[tuple[str, int], tuple[str, str]]:
    result: dict[tuple[str, int], tuple[str, str]] = {}
    for item in payload.get("corpus") or []:
        item_id = str(item.get("datasetItemId") or "")
        for page in item.get("pages") or []:
            key = (item_id, int(page.get("pageIndex", -1)))
            result[key] = (
                str(page.get("normalizedGrayscaleSha256") or ""),
                str(page.get("shadowCandidateSha256") or ""),
            )
    return result


def _compare_with_accepted_shadow_run(preservation: dict, expanded: dict) -> dict[str, object]:
    expected = _accepted_shadow_page_identities(expanded)
    actual_pages = preservation.get("pages") or []
    if len(expected) != 5 or len(actual_pages) != 5:
        raise Stage11V2aShadowPreservationReviewError("exact five-page accepted shadow set required")
    seen: set[tuple[str, int]] = set()
    shadow_matches = 0
    drifted: list[str] = []
    for page in actual_pages:
        key = (str(page.get("datasetItemId") or ""), int(page.get("pageIndex", -1)))
        if key in seen or key not in expected:
            raise Stage11V2aShadowPreservationReviewError(f"unexpected/duplicate preservation page: {key}")
        seen.add(key)
        expected_source, expected_shadow = expected[key]
        if page.get("sourceSha256") != expected_source:
            raise Stage11V2aShadowPreservationReviewError(f"preservation source SHA drift: {key}")
        actual_shadow = str(page.get("shadowCandidateSha256") or "")
        if len(actual_shadow) != 64 or any(ch not in "0123456789abcdef" for ch in actual_shadow):
            raise Stage11V2aShadowPreservationReviewError(f"invalid preservation shadow SHA: {key}")
        if actual_shadow == expected_shadow:
            shadow_matches += 1
        else:
            drifted.append(f"{key[0]}:page-{key[1]}")
    if seen != set(expected):
        raise Stage11V2aShadowPreservationReviewError("preservation review does not cover the full accepted shadow set")
    return {
        "acceptedSourceByteIdentityBound": True,
        "priorShadowByteMatchCount": shadow_matches,
        "priorShadowByteMatchTotal": len(expected),
        "crossRunShadowByteIdentityStable": shadow_matches == len(expected),
        "crossRunShadowByteDriftedPages": drifted,
    }


def _bind_current_truth(current_truth: dict, cross_run: dict[str, object]) -> None:
    identity = current_truth.get("crossRunIdentity") or {}
    if identity.get("acceptedSourceNormalizedHashesPreserved") is not cross_run["acceptedSourceByteIdentityBound"]:
        raise Stage11V2aShadowPreservationReviewError("current truth source-identity statement mismatch")
    if int(identity.get("priorShadowByteMatchCount", -1)) != int(cross_run["priorShadowByteMatchCount"]):
        raise Stage11V2aShadowPreservationReviewError("current truth prior shadow match count mismatch")
    if int(identity.get("priorShadowByteMatchTotal", -1)) != int(cross_run["priorShadowByteMatchTotal"]):
        raise Stage11V2aShadowPreservationReviewError("current truth prior shadow match total mismatch")
    if bool(identity.get("priorShadowOutputByteIdentityStable")) != bool(cross_run["crossRunShadowByteIdentityStable"]):
        raise Stage11V2aShadowPreservationReviewError("current truth cross-run stability statement mismatch")


def main() -> int:
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    expanded = json.loads(EXPANDED.read_text(encoding="utf-8"))
    current_truth = json.loads(CURRENT_TRUTH.read_text(encoding="utf-8"))
    result = validate_preservation_review_evidence(payload)
    current_truth_result = validate_current_truth(current_truth)
    cross_run = _compare_with_accepted_shadow_run(payload, expanded)
    _bind_current_truth(current_truth, cross_run)
    result.update(cross_run)
    result["currentTruthValidated"] = current_truth_result["status"] == "pass"
    result["currentTruthState"] = current_truth_result["state"]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
