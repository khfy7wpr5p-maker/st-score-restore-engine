from __future__ import annotations

import json
from pathlib import Path
import re
import sys

from st_score_restore.dataset_manifest import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_PATH = ROOT / "evidence" / "stage2" / "corpus" / "stage2-exit-acceptance.v1.json"
EXECUTION_PATH = ROOT / "evidence" / "stage2" / "corpus" / "execution-evidence.v1.json"
STAGE1_ACCEPTANCE_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "stage1-exit-acceptance.v1.json"
EXPECTED_MAIN = "ffea7f5aa618187f3cabcfb49801804e3f6658bf"
EXPECTED_PR_HEAD = "7d6c812dd09a1ce42ae91d224f9d08992884b77a"
EXPECTED_PR_RUN = 220
EXPECTED_PR_RUN_ID = 33606224352
EXPECTED_MAIN_RUN = 221
EXPECTED_MAIN_RUN_ID = 33607016064
EXPECTED_EXECUTION = "78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d"
EXPECTED_CATALOG = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"
REAL_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    acceptance = _load(ACCEPTANCE_PATH)
    execution = _load(EXECUTION_PATH)
    stage1 = _load(STAGE1_ACCEPTANCE_PATH)

    require(acceptance.get("decisionId") == "stage2.exit.acceptance.v1", "Stage 2 decision id drifted")
    require(acceptance.get("decision") == "PASS", "Stage 2 exit acceptance is not PASS")
    require(acceptance.get("evidenceMainSha") == EXPECTED_MAIN, "Stage 2 acceptance main binding drifted")
    require(acceptance.get("acceptanceAuthority") == "issue-83-autonomous-objective-gates", "Stage 2 acceptance authority drifted")

    pr = acceptance.get("exactHeadPrVerification", {})
    require(pr.get("prNumber") == 87, "Stage 2 acceptance PR binding drifted")
    require(pr.get("headSha") == EXPECTED_PR_HEAD, "Stage 2 acceptance exact-head binding drifted")
    require(pr.get("runNumber") == EXPECTED_PR_RUN and pr.get("runId") == EXPECTED_PR_RUN_ID, "Stage 2 exact-head CI binding drifted")
    require(pr.get("python311") == "success" and pr.get("python312") == "success", "Stage 2 exact-head CI is not green on both Python versions")

    post = acceptance.get("postMergeCi", {})
    require(post.get("runNumber") == EXPECTED_MAIN_RUN and post.get("runId") == EXPECTED_MAIN_RUN_ID, "Stage 2 post-merge CI binding drifted")
    require(post.get("event") == "push", "Stage 2 post-merge validation is not a main push run")
    require(post.get("python311") == "success" and post.get("python312") == "success", "Stage 2 post-merge CI is not green on both Python versions")

    digests = acceptance.get("evidenceDigests", {})
    require(digests.get("corpusExecutionEvidenceCanonicalSha256") == EXPECTED_EXECUTION, "Stage 2 execution evidence digest binding drifted")
    require(digests.get("catalogV2CanonicalSha256") == EXPECTED_CATALOG, "Stage 2 catalog digest binding drifted")

    execution_payload = dict(execution)
    claimed = execution_payload.pop("evidenceDigest", {})
    require(claimed.get("value") == EXPECTED_EXECUTION, "frozen corpus execution evidence digest drifted")
    require(canonical_sha256(execution_payload) == EXPECTED_EXECUTION, "corpus execution evidence content no longer matches frozen digest")
    require(execution.get("repositoryMainSha") == "6ab6e603550559ef701bfba9b2a200c2e5f794b9", "historical execution evidence main binding was rewritten")
    execution_assertions = execution.get("assertions", {})
    require(execution_assertions.get("stage2ExitPass") is False, "historical execution evidence was retroactively changed to Stage 2 PASS")
    require(execution_assertions.get("stage3EntryAuthorized") is False, "historical execution evidence was retroactively changed to authorize Stage 3")
    require(execution_assertions.get("heldOutThresholdTuningUsed") is False, "historical execution evidence no longer preserves held-out non-tuning")
    require(execution_assertions.get("realArtifactBytesInGit") is False, "historical execution evidence claims real artifact bytes in Git")

    summary = acceptance.get("executionSummary", {})
    require(summary == {
        "itemCount": 5,
        "analyzedCount": 2,
        "vectorNotApplicableCount": 1,
        "stage3DeferredCount": 2,
        "developmentCount": 3,
        "heldOutCount": 2,
        "restrictedNoExportCount": 1,
        "exactSha256Matches": 5,
        "exactByteSizeMatches": 5,
    }, "Stage 2 acceptance execution summary drifted")

    gates = acceptance.get("gates", {})
    require(bool(gates), "Stage 2 acceptance gates are missing")
    for name, state in gates.items():
        require(isinstance(state, str) and state.startswith("pass"), f"Stage 2 acceptance gate is not PASS: {name}")

    require(acceptance.get("stage2ExitPass") is True, "Stage 2 acceptance does not explicitly pass exit")
    require(acceptance.get("stage3EntryEligible") is True, "Stage 2 acceptance does not make Stage 3 entry eligible")
    require(acceptance.get("stage3Started") is False, "Stage 3 must remain not started in the Stage 2 acceptance slice")
    require(acceptance.get("blockerCodes") == [], "Stage 2 acceptance contains blocker codes")

    claims = acceptance.get("claims", {})
    for name in (
        "thresholdsCalibrated",
        "representativenessEstablished",
        "absenceOfBiasEstablished",
        "restorationEffectivenessEstablished",
        "omrImprovementEstablished",
        "musicalCorrectnessEstablished",
        "trainingAuthorized",
        "calibrationAuthorized",
        "publicationAuthorized",
    ):
        require(claims.get(name) is False, f"unsupported Stage 2 acceptance claim: {name}")

    limitations = "\n".join(acceptance.get("acceptedLimitations", [])).lower()
    for required in (
        "stage 3 renderer",
        "vector-preserved",
        "uncalibrated engineering defaults",
        "custody-only",
        "external_export=false",
        "representativeness is not established",
        "absence of bias is not established",
    ):
        require(required in limitations, f"Stage 2 accepted limitations lost required boundary: {required}")

    require(stage1.get("decision") == "PASS", "Stage 1 accepted exit no longer remains PASS")
    require(stage1.get("stage2EntryEligible") is True, "Stage 1 acceptance no longer supports Stage 2 entry")

    serialized = json.dumps(acceptance, sort_keys=True).lower()
    for forbidden in ("drive.google", "google drive", "/mnt/data", "folderid", "fileid"):
        require(forbidden not in serialized, f"Stage 2 acceptance leaks provider/local custody locator: {forbidden}")

    binary_paths = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "evidence" / "stage2").rglob("*")
        if path.is_file() and path.suffix.lower() in REAL_SUFFIXES
    ]
    require(not binary_paths, f"real corpus artifact bytes found under evidence/stage2: {binary_paths}")

    if failures:
        print("Stage 2 final exit acceptance validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 2 final exit acceptance validation: PASS")
    print(f"- evidence main: {EXPECTED_MAIN}")
    print(f"- exact-head verification: Run #{EXPECTED_PR_RUN}")
    print(f"- post-merge main verification: Run #{EXPECTED_MAIN_RUN}")
    print(f"- corpus execution evidence: {EXPECTED_EXECUTION}")
    print("- accepted corpus identities: 5/5")
    print("- held-out threshold tuning: false")
    print("- Stage 2 exit: PASS")
    print("- Stage 3 entry: eligible / not started")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
