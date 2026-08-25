"""Evaluate minimum structural readiness for a Stage 1 development/held-out freeze."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_contract_common import _permission, _permission_valid_on  # noqa: E402
from st_score_restore.dataset_contract_constants import PURPOSES, DatasetManifestError  # noqa: E402
from st_score_restore.dataset_manifest import load_dataset_catalog  # noqa: E402

DEFAULT_CATALOG = ROOT / "evidence" / "stage1c" / "imslp799143" / "catalog.v1.json"
CONTRACT_PATH = ROOT / "docs" / "stage-1c-corpus-readiness.md"
EXPECTED_PURPOSE = {
    "development": "quality_evaluation",
    "held_out": "held_out_evaluation",
}
ALLOWED_STAGE1_PURPOSES = frozenset(EXPECTED_PURPOSE.values())


class CorpusReadinessError(ValueError):
    """Raised when the C13 evaluator contract or CLI input is invalid."""


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Evaluate the minimum structural corpus conditions required before a "
            "digest-bound Stage 1 development/held-out snapshot may be proposed."
        )
    )
    result.add_argument("catalog", nargs="?", type=Path, default=DEFAULT_CATALOG)
    result.add_argument("--as-of", required=True, help="evaluation date in YYYY-MM-DD")
    group = result.add_mutually_exclusive_group()
    group.add_argument("--require-ready", action="store_true")
    group.add_argument("--require-blocked", action="store_true")
    return result


def parse_date(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise CorpusReadinessError("--as-of must be a real YYYY-MM-DD date") from error
    if parsed.isoformat() != value:
        raise CorpusReadinessError("--as-of must use canonical YYYY-MM-DD form")
    return parsed


def validate_repository_contract() -> None:
    required = (DEFAULT_CATALOG, CONTRACT_PATH)
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise CorpusReadinessError(
            "missing C13 contract file(s): " + ", ".join(missing)
        )


def _current_grants(item: dict[str, Any], when: date) -> set[str]:
    current: set[str] = set()
    for purpose in PURPOSES:
        raw = item["permissions"][purpose]
        permission = _permission(raw, f"item.permissions.{purpose}")
        if raw["status"] == "granted" and _permission_valid_on(permission, when):
            current.add(purpose)
    return current


def evaluate_corpus_readiness(
    catalog: dict[str, Any], *, as_of: date
) -> dict[str, Any]:
    """Return deterministic structural readiness without creating a snapshot."""
    reasons: set[str] = set()
    counts = {"development": 0, "held_out": 0}
    families = {"development": set(), "held_out": set()}
    digests: dict[str, set[str]] = {}

    for item in catalog["items"]:
        artifact = item["artifact"]
        if artifact["state"] != "external_available":
            continue

        split = item["split"]
        if item["review"]["status"] != "approved":
            reasons.add("external_item_not_approved")
        if item["revocation"]["status"] != "not_revoked":
            reasons.add("external_item_revoked_or_deleting")

        if split == "unassigned":
            reasons.add("external_item_unassigned")
            continue
        if split not in EXPECTED_PURPOSE:
            reasons.add("out_of_scope_assigned_split")
            continue

        counts[split] += 1
        families[split].add(item["sourceFamilyId"])
        digest = artifact["sha256"]
        assert digest is not None
        digests.setdefault(digest, set()).add(split)

        expected = EXPECTED_PURPOSE[split]
        current_grants = _current_grants(item, as_of)
        if expected not in current_grants:
            reasons.add(f"{split}_purpose_not_current")
        if current_grants != {expected}:
            reasons.add("active_purpose_set_not_exact")
        if not current_grants.issubset(ALLOWED_STAGE1_PURPOSES):
            reasons.add("unauthorized_active_purpose")

    if counts["development"] == 0:
        reasons.add("missing_development_item")
    if counts["held_out"] == 0:
        reasons.add("missing_held_out_item")
    if families["development"] & families["held_out"]:
        reasons.add("source_family_split_leakage")
    if any(len(splits) > 1 for splits in digests.values()):
        reasons.add("artifact_digest_cross_split_leakage")

    state = "ready" if not reasons else "blocked"
    return {
        "state": state,
        "reasonCodes": sorted(reasons),
        "counts": counts,
        "sourceFamilyCounts": {
            "development": len(families["development"]),
            "held_out": len(families["held_out"]),
        },
    }


def main() -> None:
    args = parser().parse_args()
    try:
        validate_repository_contract()
        as_of = parse_date(args.as_of)
        catalog = load_dataset_catalog(args.catalog)
        result = evaluate_corpus_readiness(catalog, as_of=as_of)
    except (OSError, DatasetManifestError, CorpusReadinessError) as error:
        print(f"ERROR: Stage 1 corpus readiness evaluation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    if args.require_ready and result["state"] != "ready":
        raise SystemExit(2)
    if args.require_blocked and result["state"] != "blocked":
        raise SystemExit(3)


if __name__ == "__main__":
    main()
