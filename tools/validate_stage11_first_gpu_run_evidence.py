from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage11_first_gpu_run_evidence import load_and_validate

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/stage11/training/deepscoresv2-dense-first-gpu-run.v1.json"


def main() -> int:
    print(json.dumps(load_and_validate(EVIDENCE), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
