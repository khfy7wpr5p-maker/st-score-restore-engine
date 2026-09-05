from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage6_s6_05_current_truth import (
    summarize_stage6_s6_05_current_truth,
    validate_stage6_s6_05_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    current = read("docs/live/ST_SCORE_RESTORE_STAGE6_S6_05_CURRENT_TRUTH.json")
    authorization = read("evidence/stage6/governance/stage6-s6-05-production-network-authorization.v1.json")
    previous = read("docs/live/ST_SCORE_RESTORE_STAGE6_S6_04_CURRENT_TRUTH.json")
    validate_stage6_s6_05_current_truth(current, authorization, previous)
    summary = summarize_stage6_s6_05_current_truth(current, authorization, previous)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
