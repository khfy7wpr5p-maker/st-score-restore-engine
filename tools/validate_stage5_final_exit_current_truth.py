from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage5_final_exit_current_truth import validate_stage5_final_exit_current_truth


ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    summary = validate_stage5_final_exit_current_truth(
        load("docs/live/ST_SCORE_RESTORE_STAGE5_FINAL_EXIT_CURRENT_TRUTH.json"),
        load("evidence/stage5/qa/stage5-accessibility-display-qa.v1.json"),
        load("evidence/stage5/final-exit/stage5-final-exit-acceptance.v1.json"),
        load("docs/live/ST_SCORE_RESTORE_STAGE5_ENTRY_AUTHORIZATION_CURRENT_TRUTH.json"),
    )
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
