from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage10_final_exit_current_truth import validate_stage10_final_exit_current_truth

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    result = validate_stage10_final_exit_current_truth(
        load("docs/live/ST_SCORE_RESTORE_STAGE10_FINAL_EXIT_CURRENT_TRUTH.json"),
        load("evidence/stage10/final-exit/stage10-final-exit-acceptance.v1.json"),
        load("evidence/stage10/stage10-entry-authorization.v1.json"),
        load("docs/live/ST_SCORE_RESTORE_STAGE9A_FINAL_EXIT_CURRENT_TRUTH.json"),
        load("api/stage10-selector-contract.v1.json"),
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
