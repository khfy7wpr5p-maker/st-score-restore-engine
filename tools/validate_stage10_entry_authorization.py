from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage10_entry_authorization import validate_stage10_entry_authorization

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "evidence/stage10/stage10-entry-authorization.v1.json"
TRUTH = ROOT / "docs/live/ST_SCORE_RESTORE_STAGE9A_FINAL_EXIT_CURRENT_TRUTH.json"


def main() -> int:
    authorization = json.loads(AUTH.read_text(encoding="utf-8"))
    truth = json.loads(TRUTH.read_text(encoding="utf-8"))
    result = validate_stage10_entry_authorization(authorization, truth)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
