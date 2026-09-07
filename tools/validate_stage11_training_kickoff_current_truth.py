#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage11_training_kickoff_current_truth import validate_stage11_training_kickoff_current_truth

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    truth = json.loads((ROOT / "docs/live/ST_SCORE_RESTORE_STAGE11_TRAINING_KICKOFF_CURRENT_TRUTH.json").read_text(encoding="utf-8"))
    print(json.dumps(validate_stage11_training_kickoff_current_truth(truth), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
