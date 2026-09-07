from __future__ import annotations

import json

from st_score_restore.st_restore_selector import run_synthetic_selector_drills


def main() -> int:
    result = run_synthetic_selector_drills()
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
