#!/usr/bin/env python3
"""Run Stage 8 synthetic DocRes optional-candidate safety drills."""

from __future__ import annotations

import json

from st_score_restore.docres_optional_candidate import run_synthetic_docres_candidate_drills


def main() -> int:
    report = run_synthetic_docres_candidate_drills()
    print(json.dumps(report, sort_keys=True))
    return 0 if report.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
