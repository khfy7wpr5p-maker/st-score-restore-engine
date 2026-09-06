#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage6_s6_08_current_truth import summarize_stage6_s6_08_current_truth


def _load(path: str) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    current = _load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_08_CURRENT_TRUTH.json")
    authorization = _load("evidence/stage6/governance/stage6-s6-08-integration-security-regression-authorization.v1.json")
    previous = _load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_07_CURRENT_TRUTH.json")
    print(json.dumps(summarize_stage6_s6_08_current_truth(current, authorization, previous), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
