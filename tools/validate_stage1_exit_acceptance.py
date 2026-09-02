from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_manifest import canonical_sha256, load_json_object  # noqa: E402

ACCEPTANCE = ROOT / "evidence/stage1c/corpus/stage1-exit-acceptance.v1.json"
CATALOG = ROOT / "evidence/stage1c/corpus/catalog.v2.json"
SNAPSHOT = ROOT / "evidence/stage1c/corpus/snapshot.expanded.v2.json"
REPORT = ROOT / "evidence/stage1c/corpus/coverage-bias-report.v2.json"

EXPECTED_MAIN = "8b5bdf3ff58898cfb85b8ef4d4f22c21e3b774e1"
EXPECTED_RUN_ID = 33573656067
EXPECTED_RUN_NUMBER = 199
EXPECTED_CATALOG = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"
EXPECTED_SNAPSHOT = "c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7"
EXPECTED_REPORT = "45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834"


def validate() -> list[str]:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    acceptance = load_json_object(ACCEPTANCE)
    catalog = load_json_object(CATALOG)
    snapshot = load_json_object(SNAPSHOT)
    report = load_json_object(REPORT)

    require(acceptance.get("decision") == "PASS", "Stage 1 acceptance decision is not PASS")
    require(acceptance.get("evidenceMainSha") == EXPECTED_MAIN, "accepted main SHA drifted")

    ci = acceptance.get("postMergeCi", {})
    require(ci.get("runId") == EXPECTED_RUN_ID, "post-merge CI run id drifted")
    require(ci.get("runNumber") == EXPECTED_RUN_NUMBER, "post-merge CI run number drifted")
    require(ci.get("event") == "push", "post-merge CI event must be push")
    require(ci.get("python311") == "success" and ci.get("python312") == "success", "post-merge matrix is not fully successful")

    digests = acceptance.get("evidenceDigests", {})
    require(canonical_sha256(catalog) == EXPECTED_CATALOG == digests.get("catalogV2CanonicalSha256"), "catalog v2 canonical digest mismatch")
    require(canonical_sha256(snapshot) == EXPECTED_SNAPSHOT == digests.get("snapshotV2CanonicalSha256"), "snapshot v2 canonical digest mismatch")
    require(canonical_sha256(report) == EXPECTED_REPORT == digests.get("coverageReportV2CanonicalSha256"), "coverage report v2 canonical digest mismatch")

    require(report.get("gapCodes") == [], "expanded-v2 gap codes are not empty")
    suff = report.get("sufficiency", {})
    require(suff.get("state") == "review_required", "source report must remain review_required")
    require(suff.get("requiresCorpusExpansion") is False, "source report still requires corpus expansion")
    require(suff.get("stage1ExitSupported") is False, "source report must not auto-authorize Stage 1 exit")
    require(suff.get("stage2EntrySupported") is False, "source report must not auto-authorize Stage 2")

    source_review = acceptance.get("sourceReportReview", {})
    require(source_review.get("stage1ExitSupportedByAutomaticReport") is False, "acceptance must record automatic Stage 1 denial")
    require(source_review.get("stage2EntrySupportedByAutomaticReport") is False, "acceptance must record automatic Stage 2 denial")
    require(source_review.get("requiresCorpusExpansion") is False, "acceptance source review unexpectedly requires expansion")
    require(source_review.get("gapCodes") == [], "acceptance source review gap codes are not empty")

    gates = acceptance.get("gates", {})
    require(bool(gates), "acceptance gates missing")
    require(all(str(value).startswith("pass") for value in gates.values()), f"one or more acceptance gates are not pass: {gates}")
    require(acceptance.get("blockerCodes") == [], "Stage 1 acceptance has blocker codes")
    require(acceptance.get("stage2EntryEligible") is True, "Stage 2 entry is not explicitly eligible after acceptance")
    require(acceptance.get("stage2Started") is False, "Stage 2 must not be started by the acceptance record")

    claims = acceptance.get("claims", {})
    for key in (
        "representativenessEstablished",
        "absenceOfBiasEstablished",
        "restorationEffectivenessEstablished",
        "omrImprovementEstablished",
        "musicalCorrectnessEstablished",
        "trainingAuthorized",
        "calibrationAuthorized",
    ):
        require(claims.get(key) is False, f"unsupported claim became true: {key}")

    limitations = acceptance.get("acceptedLimitations", [])
    require(any("source_selection_concentration" in item for item in limitations), "source-selection concentration limitation is not recorded")

    sensitive = acceptance.get("separateSensitivePhonePhotoPath", {})
    require(sensitive.get("requiredForAcceptedCorpus") is False, "separate sensitive phone-photo path was incorrectly made an exit dependency")
    require(str(sensitive.get("state", "")).startswith("blocked"), "separate sensitive path must remain fail-closed")

    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("Stage 1 exit acceptance validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 1 exit acceptance validation: PASS")
    print(f"- evidence main: {EXPECTED_MAIN}")
    print(f"- post-merge CI: Run #{EXPECTED_RUN_NUMBER} ({EXPECTED_RUN_ID})")
    print("- automatic coverage report remains review_required / fail-closed")
    print("- explicit governance acceptance: Stage 1 PASS")
    print("- Stage 2 entry: eligible, not started")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
