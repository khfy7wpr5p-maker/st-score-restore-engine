from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage11_v2a_packaging_current_truth import load_and_validate

path = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_PACKAGING_CURRENT_TRUTH.json"
print(load_and_validate(path))
