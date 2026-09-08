#!/usr/bin/env python3
"""Validate committed Stage 11 V2a non-held-out preservation-review evidence."""
from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage11_v2a_shadow_preservation_review import validate_preservation_review_evidence

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-shadow-preservation-review-evidence.v1.json"


def main() -> int:
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    result = validate_preservation_review_evidence(payload)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
