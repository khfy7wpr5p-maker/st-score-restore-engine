#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage6_s6_08_authorization import (
    AUTHORIZATION_PATH,
    EXPECTED_CANONICAL_SHA256,
    validate_stage6_s6_08_authorization,
)


def main() -> int:
    record = json.loads(Path(AUTHORIZATION_PATH).read_text(encoding="utf-8"))
    validate_stage6_s6_08_authorization(record)
    print(json.dumps({
        "status": "pass",
        "authorizationId": record["authorization_id"],
        "canonicalSha256": EXPECTED_CANONICAL_SHA256,
        "nextSafeBoundary": record["next_safe_boundary"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
