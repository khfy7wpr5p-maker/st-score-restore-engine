#!/usr/bin/env python3
"""Validate committed Stage 11 V2a shadow handoff evidence and current truth."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from st_score_restore.stage11_v2a_shadow_current_truth import (  # noqa: E402
    validate_truth_with_evidence,
)
from st_score_restore.stage11_v2a_shadow_handoff import (  # noqa: E402
    validate_shadow_job_evidence,
)

EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-shadow-job-handoff-evidence.v1.json"
TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_SHADOW_CURRENT_TRUTH.json"


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    validate_shadow_job_evidence(evidence)
    result = validate_truth_with_evidence(TRUTH, EVIDENCE)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
