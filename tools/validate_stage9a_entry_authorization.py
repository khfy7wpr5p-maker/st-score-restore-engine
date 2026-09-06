from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage9a_entry_authorization import (  # noqa: E402
    Stage9AEntryAuthorizationError,
    validate_stage9a_entry_authorization,
)


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    try:
        result = validate_stage9a_entry_authorization(
            load("evidence/stage9a/stage9a-entry-authorization.v1.json"),
            load("docs/live/ST_SCORE_RESTORE_STAGE9_FINAL_EXIT_CURRENT_TRUTH.json"),
        )
    except (OSError, json.JSONDecodeError, Stage9AEntryAuthorizationError) as exc:
        print(json.dumps({"result": "BLOCKED", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
