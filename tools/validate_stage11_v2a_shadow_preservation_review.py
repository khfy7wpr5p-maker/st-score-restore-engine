#!/usr/bin/env python3
"""Validate committed Stage 11 V2a non-held-out preservation-review evidence."""
from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage11_v2a_shadow_preservation_review import (
    Stage11V2aShadowPreservationReviewError,
    validate_preservation_review_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-shadow-preservation-review-evidence.v1.json"
EXPANDED = ROOT / "evidence" / "stage11" / "v2a" / "v2a-shadow-corpus-expanded-evidence.v1.json"


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


def _bind_to_accepted_shadow_bytes(preservation: dict, expanded: dict) -> None:
    expected = _accepted_shadow_page_identities(expanded)
    actual_pages = preservation.get("pages") or []
    if len(expected) != 5 or len(actual_pages) != 5:
        raise Stage11V2aShadowPreservationReviewError("exact five-page accepted shadow set required")
    seen: set[tuple[str, int]] = set()
    for page in actual_pages:
        key = (str(page.get("datasetItemId") or ""), int(page.get("pageIndex", -1)))
        if key in seen or key not in expected:
            raise Stage11V2aShadowPreservationReviewError(f"unexpected/duplicate preservation page: {key}")
        seen.add(key)
        expected_source, expected_shadow = expected[key]
        if page.get("sourceSha256") != expected_source:
            raise Stage11V2aShadowPreservationReviewError(f"preservation source SHA drift: {key}")
        if page.get("shadowCandidateSha256") != expected_shadow:
            raise Stage11V2aShadowPreservationReviewError(f"preservation shadow SHA drift: {key}")
    if seen != set(expected):
        raise Stage11V2aShadowPreservationReviewError("preservation review does not cover the full accepted shadow set")


def main() -> int:
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    expanded = json.loads(EXPANDED.read_text(encoding="utf-8"))
    result = validate_preservation_review_evidence(payload)
    _bind_to_accepted_shadow_bytes(payload, expanded)
    result["acceptedShadowByteIdentityBound"] = True
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
