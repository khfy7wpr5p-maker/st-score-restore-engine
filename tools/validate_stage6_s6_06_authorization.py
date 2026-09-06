#!/usr/bin/env python3
from __future__ import annotations

from st_score_restore.stage6_s6_06_authorization import (
    EXPECTED_CANONICAL_SHA256,
    load_and_validate,
)


def main() -> int:
    record = load_and_validate()
    print(
        "Stage 6 S6-06 authorization valid:",
        record["authorization_id"],
        EXPECTED_CANONICAL_SHA256,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
