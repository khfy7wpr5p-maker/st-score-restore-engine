#!/usr/bin/env python3
"""Validate the committed Stage 6 S6-03 identity/authz authorization."""

from __future__ import annotations

from st_score_restore.stage6_s6_03_authorization import (
    Stage6S603AuthorizationError,
    load_and_validate,
)


def main() -> int:
    try:
        record = load_and_validate()
    except (OSError, ValueError, Stage6S603AuthorizationError) as error:
        print(f"Stage 6 S6-03 authorization validation failed: {error}")
        return 1
    print(
        "Stage 6 S6-03 authorization valid: "
        f"{record['authorization_id']} -> {record['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
