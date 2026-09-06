from __future__ import annotations

import json
from st_score_restore.multi_engine_comparator import run_synthetic_comparator_drills


def main() -> None:
    result = run_synthetic_comparator_drills()
    print(json.dumps(result, indent=2, sort_keys=True))
    if result.get("result") != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
