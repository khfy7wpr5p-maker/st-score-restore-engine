from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage6_final_exit_current_truth import summarize_stage6_final_exit_current_truth

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    current = load("docs/live/ST_SCORE_RESTORE_STAGE6_FINAL_EXIT_CURRENT_TRUTH.json")
    acceptance = load("evidence/stage6/final-exit/stage6-final-exit-acceptance.v1.json")
    s6_08 = load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_08_CURRENT_TRUTH.json")
    summary = summarize_stage6_final_exit_current_truth(current, acceptance, s6_08)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
