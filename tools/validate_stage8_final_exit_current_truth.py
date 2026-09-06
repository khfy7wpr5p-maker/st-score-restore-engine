#!/usr/bin/env python3
"""Validate the Stage 8 final-exit current-truth overlay."""

from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage8_final_exit_current_truth import validate_stage8_final_exit_current_truth

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    result = validate_stage8_final_exit_current_truth(
        load("evidence/stage8/stage8-entry-authorization.v1.json"),
        load("docs/live/ST_SCORE_RESTORE_STAGE7_FINAL_EXIT_CURRENT_TRUTH.json"),
        load("api/stage8-docres-candidate-contract.v1.json"),
        load("evidence/stage8/final-exit/stage8-final-exit-acceptance.v1.json"),
        load("docs/live/ST_SCORE_RESTORE_STAGE8_FINAL_EXIT_CURRENT_TRUTH.json"),
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
