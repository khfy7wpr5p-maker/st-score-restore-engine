from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage6_s6_05_authorization import (
    AUTHORIZATION_PATH,
    EXPECTED_CANONICAL_SHA256,
    canonical_sha256,
    validate_stage6_s6_05_authorization,
)


def main() -> int:
    record = json.loads(Path(AUTHORIZATION_PATH).read_text(encoding="utf-8"))
    validated = validate_stage6_s6_05_authorization(record)
    digest = canonical_sha256(validated)
    if digest != EXPECTED_CANONICAL_SHA256:
        raise SystemExit("S6-05 authorization digest mismatch")
    print(f"S6-05 production-network authorization valid: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
