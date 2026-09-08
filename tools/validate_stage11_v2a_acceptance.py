from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage11_v2a_acceptance import load_and_validate

path = ROOT / "evidence" / "stage11" / "v2a" / "v2a-evaluation-acceptance.v1.json"
print(load_and_validate(path))
