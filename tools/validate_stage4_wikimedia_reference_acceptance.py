from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage4_wikimedia_reference_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    summarize_wikimedia_reference_acceptance,
    validate_wikimedia_reference_acceptance,
)

ROOT = Path(__file__).resolve().parents[1]
WORK_PACKAGE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"
COMPLETION = ROOT / "evidence/stage4/corpus-expansion/wikimedia/human-label-completion.v1.json"
ACCEPTANCE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-bundle-acceptance.v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    acceptance = validate_wikimedia_reference_acceptance(
        _load(ACCEPTANCE), _load(COMPLETION), _load(WORK_PACKAGE)
    )
    summary = summarize_wikimedia_reference_acceptance(
        acceptance, _load(COMPLETION), _load(WORK_PACKAGE)
    )

    if summary["acceptanceDigest"]["value"] != ACCEPTANCE_CANONICAL_SHA256:
        raise SystemExit("Wikimedia acceptance digest drifted")
    if not summary["referenceBundleAccepted"] or not summary["candidateDerivationEligible"]:
        raise SystemExit("Wikimedia accepted reference bundle is not derivation-eligible")
    if summary["realDataCalibrationExecutionAuthorized"]:
        raise SystemExit("Wikimedia reference acceptance improperly authorized calibration execution")
    if summary["heldOutIncluded"] or summary["stage4ExitPass"] or summary["stage5EntryAuthorized"]:
        raise SystemExit("Wikimedia reference acceptance improperly opened a later gate")

    print("Stage 4 Wikimedia reference-bundle acceptance validation: PASS")
    print("- 7/7 human expert labels remain bound to the immutable completion evidence")
    print("- reference bundle accepted: true")
    print("- candidate derivation eligible: true")
    print("- calibration execution authorized: false")
    print("- held-out included: false")
    print("- Stage 4 PASS: false")
    print("- Stage 5 entry: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
