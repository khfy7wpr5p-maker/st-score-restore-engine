#!/usr/bin/env python3
"""Validate the committed Stage 11 DeepScoresV2 Dense Drive registration."""

from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage11_deepscores_dense import validate_registration

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = ROOT / "evidence" / "stage11" / "training" / "deepscoresv2-dense-drive-source-registration.v1.json"


def main() -> int:
    payload = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    result = validate_registration(payload)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
