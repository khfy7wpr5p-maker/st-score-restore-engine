from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage11_colab_pipeline_current_truth import load_and_validate

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "docs/live/ST_SCORE_RESTORE_STAGE11_COLAB_PIPELINE_CURRENT_TRUTH.json"


def main() -> int:
    result = load_and_validate(TRUTH)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
