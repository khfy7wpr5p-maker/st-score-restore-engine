from __future__ import annotations

import json
from pathlib import Path
import re
import sys

from st_score_restore.dataset_manifest import canonical_sha256
from st_score_restore.dataset_catalog_validation import validate_dataset_catalog

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "evidence" / "stage2" / "corpus" / "execution-evidence.v1.json"
CATALOG_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"
EXPECTED_MAIN = "6ab6e603550559ef701bfba9b2a200c2e5f794b9"
EXPECTED_RUN = 217
EXPECTED_RUN_ID = 33604394945
EXPECTED_CATALOG = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"
EXPECTED_EVIDENCE = "78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d"
SHA = re.compile(r"^[0-9a-f]{64}$")
OPAQUE_EVIDENCE = re.compile(r"^evidence:opq_[0-9a-f]{32}$")
REAL_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
PURPOSE_BY_SPLIT = {"development": "quality_evaluation", "held_out": "held_out_evaluation"}
EXPECTED_RESULTS = {
    "dataset.item.imslp799143-beethoven-op48-no3.v1": (
        "deferred_stage3_renderer", None, "8ba95676ec30dbca3548cacc55cbda43de9d34a177b3b6766dcddc5a76ea88c3"
    ),
    "dataset.item.wikimedia-guitar-technical-exercise-no1.v1": (
        "analyzed", "e8e466ee8f4d0a3ff3ea10ec6c626f2316d8cedf9feec28d3c7b03a8be5453f6", "086d266afe0fc0f31161a2cda9b598695b8e086056d4605306ed3394dc41d532"
    ),
    "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1": (
        "not_applicable_vector_pdf", "0ec6f6d0bed4589e14f70cb954ecaa3c92ecd2b877e75fd106e8afced13f044b", "1a110095e63f59b366331532bb5146617255316a2db46acfa3112cc55b3ae7ca"
    ),
    "dataset.item.imslp82860-chopin-op69.v2": (
        "deferred_stage3_renderer", None, "4031f38278249e61992009eaba08b24ac209aad4b3d01563f39d6f8c72dc9d49"
    ),
    "dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1": (
        "analyzed", "fa04245f53719e9704b49b7a37d0820b7998d4414bcf3a962476dbf9ca38ff57", "06ad5c71192b918b49b589e09acf025aec282e44cdd28498f5b5110946a71f66"
    ),
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    evidence = _load(EVIDENCE_PATH)
    catalog = validate_dataset_catalog(_load(CATALOG_PATH))
    by_id = {item["datasetItemId"]: item for item in catalog["items"]}

    digest_payload = dict(evidence)
    claimed_digest = digest_payload.pop("evidenceDigest", {})
    require(claimed_digest.get("algorithm") == "sha256", "execution evidence digest algorithm drifted")
    require(claimed_digest.get("value") == EXPECTED_EVIDENCE, "execution evidence frozen digest drifted")
    require(canonical_sha256(digest_payload) == EXPECTED_EVIDENCE, "execution evidence content does not match its frozen digest")

    require(evidence.get("repositoryMainSha") == EXPECTED_MAIN, "execution evidence main binding drifted")
    validation = evidence.get("postMergeValidation", {})
    require(validation.get("runNumber") == EXPECTED_RUN, "execution evidence Run number drifted")
    require(validation.get("runId") == EXPECTED_RUN_ID, "execution evidence Run id drifted")
    require(validation.get("python311") == "success", "execution evidence lacks Python 3.11 success")
    require(validation.get("python312") == "success", "execution evidence lacks Python 3.12 success")
    require(evidence.get("catalogCanonicalSha256") == EXPECTED_CATALOG, "execution evidence catalog binding drifted")
    require(canonical_sha256(catalog) == EXPECTED_CATALOG, "expanded-v2 catalog canonical digest drifted")
    require(evidence.get("contractVersion") == "0.1.0", "custody execution contract version drifted")
    require(evidence.get("analyzerVersion") == "0.1.1", "quality analyzer version drifted")
    require(evidence.get("calibrationState") == "uncalibrated_engineering_defaults", "Stage 2 calibration boundary drifted")

    items = evidence.get("items", [])
    require(len(items) == 5, "execution evidence must contain exactly five accepted items")
    evidence_by_id = {item.get("datasetItemId"): item for item in items}
    require(set(evidence_by_id) == set(EXPECTED_RESULTS), "execution evidence item set drifted")
    require(set(by_id) == set(EXPECTED_RESULTS), "expanded-v2 accepted item set drifted")

    for item_id, (expected_status, expected_report, expected_receipt) in EXPECTED_RESULTS.items():
        observed = evidence_by_id.get(item_id, {})
        catalog_item = by_id.get(item_id, {})
        require(observed.get("sourceSha256") == catalog_item.get("artifact", {}).get("sha256"), f"{item_id} exact SHA-256 binding drifted")
        require(observed.get("byteSize") == catalog_item.get("artifact", {}).get("byteSize"), f"{item_id} byte-size binding drifted")
        split = catalog_item.get("split")
        require(observed.get("split") == split, f"{item_id} split drifted")
        require(observed.get("purpose") == PURPOSE_BY_SPLIT.get(split), f"{item_id} Stage 2 purpose drifted")
        require(observed.get("storageClass") == catalog_item.get("retention", {}).get("storageClass"), f"{item_id} storage class drifted")
        require(observed.get("status") == expected_status, f"{item_id} execution status drifted")
        require(observed.get("reportSha256") == expected_report, f"{item_id} detailed report digest drifted")
        require(observed.get("publicReceiptSha256") == expected_receipt, f"{item_id} public receipt digest drifted")
        require(SHA.fullmatch(observed.get("sourceSha256", "")) is not None, f"{item_id} invalid source digest")
        require(SHA.fullmatch(observed.get("publicReceiptSha256", "")) is not None, f"{item_id} invalid receipt digest")
        if expected_report is None:
            require(observed.get("detailedEvidenceReference") is None, f"{item_id} deferred item unexpectedly claims detailed evidence")
            require(observed.get("analysisErrorCode") == "pdf_renderer_not_available", f"{item_id} deferred renderer reason drifted")
        else:
            require(OPAQUE_EVIDENCE.fullmatch(observed.get("detailedEvidenceReference", "")) is not None, f"{item_id} detailed evidence reference is not opaque")
            require(observed.get("analysisErrorCode") is None, f"{item_id} analyzed/vector item unexpectedly records analysis error")

    c17d = evidence_by_id.get("dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1", {})
    require(c17d.get("externalExportState") == "explicitly_blocked", "C17D external_export=false boundary drifted")
    for item_id, item in evidence_by_id.items():
        if item_id != "dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1":
            require(item.get("externalExportState") == "not_authorized_by_stage2_execution", f"{item_id} Stage 2 export state drifted")

    assertions = evidence.get("assertions", {})
    for name in (
        "heldOutThresholdTuningUsed", "sourceBytesModified", "realArtifactBytesInGit",
        "trainingAuthorized", "calibrationAuthorized", "publicationAuthorized",
        "detailedMetricsInPublicEvidence", "stage2ExitPass", "stage3EntryAuthorized",
    ):
        require(assertions.get(name) is False, f"unsafe/unsupported Stage 2 evidence assertion: {name}")

    keys = set(_walk_keys(evidence))
    require("metrics" not in keys and "findings" not in keys, "public execution evidence contains detailed metrics/findings")
    serialized = json.dumps(evidence, sort_keys=True).lower()
    for forbidden in ("drive.google", "google drive", "/mnt/data", "folderid", "fileid"):
        require(forbidden not in serialized, f"public execution evidence leaks provider/local custody locator: {forbidden}")

    summary = evidence.get("summary", {})
    expected_summary = {
        "itemCount": 5, "analyzedCount": 2, "vectorNotApplicableCount": 1,
        "stage3DeferredCount": 2, "developmentCount": 3, "heldOutCount": 2,
        "restrictedNoExportCount": 1,
    }
    require(summary == expected_summary, "Stage 2 execution summary drifted")

    binary_paths = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "evidence" / "stage2").rglob("*")
        if path.is_file() and path.suffix.lower() in REAL_SUFFIXES
    ]
    require(not binary_paths, f"real corpus artifact bytes found under evidence/stage2: {binary_paths}")

    if failures:
        print("Stage 2 corpus execution evidence validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 2 corpus execution evidence validation: PASS")
    print(f"- frozen evidence digest: {EXPECTED_EVIDENCE}")
    print("- accepted corpus: 5/5 exact source identities bound")
    print("- results: 2 analyzed / 1 vector not-applicable / 2 Stage-3-deferred")
    print("- held-out tuning: false")
    print("- C17D detailed export: blocked")
    print("- public evidence metrics/findings: absent")
    print("- Stage 2 exit: not decided")
    print("- Stage 3 entry: blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
