#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage11_foundation_current_truth import validate_stage11_foundation_current_truth

ROOT = Path(__file__).resolve().parents[1]
TRUTH_PATH = ROOT / "docs/live/ST_SCORE_RESTORE_STAGE11_FOUNDATION_CURRENT_TRUTH.json"


def main() -> int:
    truth = json.loads(TRUTH_PATH.read_text(encoding="utf-8"))
    result = validate_stage11_foundation_current_truth(truth)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
