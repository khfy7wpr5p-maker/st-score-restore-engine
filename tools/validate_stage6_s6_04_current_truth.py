#!/usr/bin/env python3
"""Validate production-effective Stage 6 S6-04 current truth."""

from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage6_s6_04_current_truth import summarize_stage6_s6_04_current_truth

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    summary = summarize_stage6_s6_04_current_truth(
        load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_04_CURRENT_TRUTH.json"),
        load("evidence/stage6/governance/stage6-s6-04-secrets-kms-iam-authorization.v1.json"),
        load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_03_CURRENT_TRUTH.json"),
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
