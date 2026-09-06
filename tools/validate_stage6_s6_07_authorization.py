from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage6_s6_07_authorization import (
    AUTHORIZATION_PATH,
    EXPECTED_CANONICAL_SHA256,
    canonical_sha256,
    validate_stage6_s6_07_authorization,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    path = ROOT / AUTHORIZATION_PATH
    raw = json.loads(path.read_text(encoding="utf-8"))
    validated = validate_stage6_s6_07_authorization(raw)
    print(json.dumps({
        "authorizationId": validated["authorization_id"],
        "decision": validated["decision"],
        "canonicalSha256": canonical_sha256(validated),
        "expectedCanonicalSha256": EXPECTED_CANONICAL_SHA256,
        "nextSafeBoundary": validated["next_safe_boundary"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
