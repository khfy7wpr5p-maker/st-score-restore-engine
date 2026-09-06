#!/usr/bin/env python3
"""Validate the bounded Stage 8 entry authorization against Stage 7 final truth."""

from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage8_entry_authorization import summarize_stage8_entry_authorization

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    authorization = load("evidence/stage8/stage8-entry-authorization.v1.json")
    stage7_truth = load("docs/live/ST_SCORE_RESTORE_STAGE7_FINAL_EXIT_CURRENT_TRUTH.json")
    summary = summarize_stage8_entry_authorization(authorization, stage7_truth)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
