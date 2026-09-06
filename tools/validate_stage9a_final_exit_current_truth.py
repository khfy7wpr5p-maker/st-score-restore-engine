from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage9a_final_exit import Stage9AFinalExitError  # noqa: E402
from st_score_restore.stage9a_final_exit_current_truth import (  # noqa: E402
    Stage9AFinalTruthError,
    validate_stage9a_final_exit_current_truth,
)


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    try:
        result = validate_stage9a_final_exit_current_truth(
            load("docs/live/ST_SCORE_RESTORE_STAGE9A_FINAL_EXIT_CURRENT_TRUTH.json"),
            load("evidence/stage9a/final-exit/stage9a-final-exit-acceptance.v1.json"),
        )
    except (OSError, json.JSONDecodeError, Stage9AFinalExitError, Stage9AFinalTruthError) as exc:
        print(json.dumps({"result": "BLOCKED", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
