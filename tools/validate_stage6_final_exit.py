from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage6_final_exit import (
    S6_08_CURRENT_TRUTH_GIT_BLOB_SHA1,
    git_blob_sha1,
    validate_stage6_final_exit,
)

ROOT = Path(__file__).resolve().parents[1]
CURRENT_TRUTH_PATH = ROOT / "docs/live/ST_SCORE_RESTORE_STAGE6_S6_08_CURRENT_TRUTH.json"
ACCEPTANCE_PATH = ROOT / "evidence/stage6/final-exit/stage6-final-exit-acceptance.v1.json"


def main() -> int:
    current_truth_bytes = CURRENT_TRUTH_PATH.read_bytes()
    actual_blob = git_blob_sha1(current_truth_bytes)
    if actual_blob != S6_08_CURRENT_TRUTH_GIT_BLOB_SHA1:
        raise ValueError(
            f"S6-08 current-truth Git blob changed: expected {S6_08_CURRENT_TRUTH_GIT_BLOB_SHA1}, got {actual_blob}"
        )
    current_truth = json.loads(current_truth_bytes.decode("utf-8"))
    acceptance = json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))
    summary = validate_stage6_final_exit(current_truth, acceptance)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
