from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.music_symbol_preservation import run_synthetic_mspm_drills  # noqa: E402


def main() -> int:
    result = run_synthetic_mspm_drills()
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
