#!/usr/bin/env python3
"""Validate committed Stage 11 V2a approved non-held-out shadow-corpus evidence."""
from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage11_v2a_shadow_corpus_current_truth import validate_truth_with_evidence

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-shadow-corpus-evidence.v1.json"
TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_SHADOW_CORPUS_CURRENT_TRUTH.json"


def main() -> int:
    result = validate_truth_with_evidence(TRUTH, EVIDENCE)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
