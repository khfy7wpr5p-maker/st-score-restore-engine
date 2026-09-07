#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage11_training_authorization import validate_stage11_training_authorization

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    result = validate_stage11_training_authorization(
        load("evidence/stage11/training/stage11-training-dataset-authorization.v1.json"),
        load("docs/live/ST_SCORE_RESTORE_STAGE11_FOUNDATION_CURRENT_TRUTH.json"),
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
