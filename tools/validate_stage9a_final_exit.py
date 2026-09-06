from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage9a_final_exit import (  # noqa: E402
    Stage9AFinalExitError,
    validate_stage9a_final_exit,
)


def main() -> int:
    path = ROOT / "evidence/stage9a/final-exit/stage9a-final-exit-acceptance.v1.json"
    try:
        result = validate_stage9a_final_exit(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, Stage9AFinalExitError) as exc:
        print(json.dumps({"result": "BLOCKED", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
