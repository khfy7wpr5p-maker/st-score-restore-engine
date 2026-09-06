from __future__ import annotations

import json

from st_score_restore.stage6_operational_drills import run_synthetic_operational_drills


def main() -> int:
    report = run_synthetic_operational_drills()
    print(json.dumps(report.to_dict(), sort_keys=True))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
