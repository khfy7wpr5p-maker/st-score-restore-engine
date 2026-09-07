#!/usr/bin/env python3
"""Validate the Stage 11 Camera-PrIMuS rights review evidence."""

from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage11_cameraprimus_rights_review import load_and_validate


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "evidence/stage11/training/cameraprimus-rights-review.v1.json"


if __name__ == "__main__":
    result = load_and_validate(PATH)
    print(json.dumps(result, sort_keys=True))
