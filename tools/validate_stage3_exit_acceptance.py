from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.dataset_contract_common import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
EXECUTION = ROOT / "evidence" / "stage3" / "corpus" / "execution-evidence.v1.json"
LIMITATIONS = ROOT / "evidence" / "stage3" / "corpus" / "limitations-review.v1.json"
ACCEPTANCE = ROOT / "evidence" / "stage3" / "corpus" / "stage3-exit-acceptance.v1.json"

EXECUTION_DIGEST = "a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6"
LIMITATIONS_DIGEST = "5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d"
PURPOSE_DIGEST = "3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8"
CATALOG_DIGEST = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"
EVIDENCE_MAIN = "b15d91ff3fbf21b47a0e484b5a337c4611a17355"
EVIDENCE_PR_HEAD = "88737a8dec70e8c84075e141dd9364794b3605bf"
BINARY_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest_without(value: dict, field: str) -> str:
    payload = dict(value)
    payload.pop(field, None)
    return canonical_sha256(payload)


def main() -> int:
    failures: list[str] = []
    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    execution = load(EXECUTION)
    limitations = load(LIMITATIONS)
    acceptance = load(ACCEPTANCE)

    require(digest_without(execution, "evidenceDigest") == EXECUTION_DIGEST, "execution evidence digest mismatch")
    require(execution.get("evidenceDigest", {}).get("value") == EXECUTION_DIGEST, "execution evidence digest field drifted")
    require(digest_without(limitations, "reviewDigest") == LIMITATIONS_DIGEST, "limitations review digest mismatch")
    require(limitations.get("reviewDigest", {}).get("value") == LIMITATIONS_DIGEST, "limitations review digest field drifted")
    require(limitations.get("executionEvidenceCanonicalSha256") == EXECUTION_DIGEST, "limitations review execution binding drifted")

    require(acceptance.get("schemaVersion") == "1.0.0", "acceptance schema drifted")
    require(acceptance.get("decisionId") == "stage3.exit.acceptance.v1", "acceptance decision id drifted")
    require(acceptance.get("decision") == "PASS", "Stage 3 decision is not PASS")
    require(acceptance.get("acceptanceAuthority") == "issue-90-autonomous-objective-gates", "acceptance authority drifted")
    require(acceptance.get("evidenceMainSha") == EVIDENCE_MAIN, "evidence production main binding drifted")
    require(acceptance.get("exactHeadPrVerification") == {
        "prNumber": 101,
        "headSha": EVIDENCE_PR_HEAD,
        "runId": 33645447424,
        "runNumber": 250,
        "python311": "success",
        "python312": "success",
    }, "evidence exact-head verification binding drifted")
    require(acceptance.get("postMergeCi") == {
        "runId": 33645607053,
        "runNumber": 251,
        "event": "push",
        "python311": "success",
        "python312": "success",
    }, "evidence post-merge CI binding drifted")
    require(acceptance.get("evidenceDigests") == {
        "realCorpusExecutionEvidenceCanonicalSha256": EXECUTION_DIGEST,
        "limitationsReviewCanonicalSha256": LIMITATIONS_DIGEST,
        "purposeGrantCanonicalSha256": PURPOSE_DIGEST,
        "catalogV2CanonicalSha256": CATALOG_DIGEST,
    }, "acceptance evidence digest set drifted")
    require(acceptance.get("executionSummary") == {
        "itemCount": 3,
        "pageCount": 14,
        "renderedPageCount": 12,
        "preservedVectorPageCount": 2,
        "reviewRequiredCount": 0,
        "developmentCount": 2,
        "heldOutCount": 1,
    }, "acceptance execution summary drifted")

    summary = execution.get("summary", {})
    require(summary.get("itemCount") == 3 and summary.get("pageCount") == 14, "execution summary item/page counts drifted")
    require(summary.get("renderedPageCount") == 12, "execution rendered count drifted")
    require(summary.get("statusCounts", {}).get("preserved_vector_page") == 2, "preserved vector count drifted")
    require(summary.get("reviewRequiredCount") == 0, "unexpected review-required pages")
    require(summary.get("allPageOrderPreserved") is True, "page order not preserved")
    require(summary.get("anyVectorPagesRasterized") is False, "vector rasterization occurred")

    assertions = execution.get("assertions", {})
    require(assertions.get("heldOutThresholdTuningUsed") is False, "held-out tuning occurred")
    require(assertions.get("realCorpusBytesInGit") is False, "real corpus bytes entered Git")
    require(assertions.get("stage3ExitPass") is False, "historical execution evidence was rewritten to accept exit")
    require(assertions.get("stage4EntryAuthorized") is False, "historical execution evidence was rewritten to authorize Stage 4")
    require(limitations.get("claims", {}).get("stage3ExitPass") is False, "limitations review was rewritten to accept exit")
    require(limitations.get("claims", {}).get("stage4EntryAuthorized") is False, "limitations review was rewritten to authorize Stage 4")

    require(acceptance.get("acceptedLimitations") == limitations.get("acceptedLimitations"), "accepted limitations do not exactly match review")
    require(acceptance.get("acceptedPurpose") == "stage4-safety-calibration-entry", "accepted purpose drifted")
    require(acceptance.get("stage3ExitPass") is True, "Stage 3 exit PASS flag missing")
    require(acceptance.get("stage4EntryEligible") is True, "Stage 4 entry eligibility missing")
    require(acceptance.get("stage4Started") is False, "Stage 4 started prematurely")
    require(acceptance.get("blockerCodes") == [], "Stage 3 acceptance has blockers")
    for claim, value in acceptance.get("claims", {}).items():
        require(value is False, f"unsupported positive acceptance claim: {claim}")

    stage3_root = ROOT / "evidence" / "stage3"
    binaries = [str(p.relative_to(ROOT)) for p in stage3_root.rglob("*") if p.is_file() and p.suffix.lower() in BINARY_SUFFIXES]
    require(not binaries, f"real artifact/derivative bytes found under evidence/stage3: {binaries}")

    if failures:
        print("Stage 3 final exit acceptance validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 3 final exit acceptance validation: PASS")
    print(f"- evidence main: {EVIDENCE_MAIN}")
    print(f"- execution evidence: {EXECUTION_DIGEST}")
    print(f"- limitations review: {LIMITATIONS_DIGEST}")
    print("- Stage 3 acceptance candidate: PASS")
    print("- Stage 4 entry: eligible only after this acceptance is production-effective")
    print("- Stage 4 started: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
