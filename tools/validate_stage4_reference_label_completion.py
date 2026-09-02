from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage4_reference_label_completion import (
    BUNDLE_CANONICAL_SHA256,
    COMPLETION_CANONICAL_SHA256,
    EXPECTED_LABEL_COUNTS,
    summarize_reference_label_completion,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/stage4/reference-labels/development-human-label-completion.v1.json"


def main() -> int:
    raw = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    summary = summarize_reference_label_completion(raw)
    print("Stage 4 completed human reference-label validation: PASS")
    print(f"- completion digest: {COMPLETION_CANONICAL_SHA256}")
    print(f"- bundle digest: {BUNDLE_CANONICAL_SHA256}")
    print(f"- record count: {summary['recordCount']}")
    print(f"- label counts: {EXPECTED_LABEL_COUNTS}")
    print("- human labels present: true")
    print("- reference bundle accepted: false")
    print("- real calibration execution: NOT AUTHORIZED")
    print("- held-out included: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
