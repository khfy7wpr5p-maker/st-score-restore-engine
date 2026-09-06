#!/usr/bin/env python3
from __future__ import annotations

import json

from st_score_restore.stage6_integration_security_regression import run_integration_security_regression


def main() -> int:
    report = run_integration_security_regression()
    print(json.dumps(report.to_dict(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
