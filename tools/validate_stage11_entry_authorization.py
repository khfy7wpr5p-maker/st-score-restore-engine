#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage11_entry_authorization import validate_stage11_entry_authorization

ROOT = Path(__file__).resolve().parents[1]
AUTH_PATH = ROOT / "evidence/stage11/stage11-entry-authorization.v1.json"
TRUTH_PATH = ROOT / "docs/live/ST_SCORE_RESTORE_STAGE10_FINAL_EXIT_CURRENT_TRUTH.json"


def main() -> int:
    authorization = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    stage10_truth = json.loads(TRUTH_PATH.read_text(encoding="utf-8"))
    result = validate_stage11_entry_authorization(authorization, stage10_truth)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
