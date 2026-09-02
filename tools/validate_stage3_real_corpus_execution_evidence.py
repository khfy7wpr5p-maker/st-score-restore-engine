from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.dataset_contract_common import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
EXECUTION_PATH = ROOT / "evidence" / "stage3" / "corpus" / "execution-evidence.v1.json"
LIMITATIONS_PATH = ROOT / "evidence" / "stage3" / "corpus" / "limitations-review.v1.json"

EXECUTION_DIGEST = "a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6"
LIMITATIONS_DIGEST = "5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d"
CATALOG_DIGEST = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"
RUNTIME_MAIN = "5e682f1933a7167fc142689306352fe53b4b1833"
RUNTIME_RUN = 246
RUNTIME_RUN_ID = 33641537118

EXPECTED = {
    "dataset.item.imslp799143-beethoven-op48-no3.v1": {
        "sha256": "c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c",
        "byteSize": 1182561,
        "split": "development",
        "purpose": "pdf_pipeline_evaluation",
        "classification": {"raster_only": 4},
        "pageCount": 4,
        "renderedPageCount": 4,
        "statusCounts": {"rendered_raster_page": 4},
        "externalExportState": "explicitly_blocked",
    },
    "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1": {
        "sha256": "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e",
        "byteSize": 84689,
        "split": "development",
        "purpose": "pdf_pipeline_evaluation",
        "classification": {"vector_only": 2},
        "pageCount": 2,
        "renderedPageCount": 0,
        "statusCounts": {"preserved_vector_page": 2},
        "externalExportState": "explicitly_blocked",
    },
    "dataset.item.imslp82860-chopin-op69.v2": {
        "sha256": "b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3",
        "byteSize": 1114479,
        "split": "held_out",
        "purpose": "held_out_evaluation",
        "classification": {"raster_only": 8},
        "pageCount": 8,
        "renderedPageCount": 8,
        "statusCounts": {"rendered_raster_page": 8},
        "externalExportState": "not_authorized_by_stage3_execution",
    },
}


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

    execution = load(EXECUTION_PATH)
    review = load(LIMITATIONS_PATH)

    require(execution.get("schemaVersion") == "1.0.0", "execution evidence schema drifted")
    require(execution.get("status") == "executed", "execution evidence status is not executed")
    require(execution.get("runnerVersion") == "0.1.0", "runner version drifted")
    require(execution.get("rendererBindingVersion") == "5.13.0", "renderer binding is not exact 5.13.0")
    require(execution.get("catalogCanonicalSha256") == CATALOG_DIGEST, "catalog digest drifted")
    require(execution.get("repositoryMainSha") == RUNTIME_MAIN, "runtime production main binding drifted")
    require(execution.get("postMergeValidation") == {"runId": RUNTIME_RUN_ID, "runNumber": RUNTIME_RUN}, "runtime post-merge CI binding drifted")
    require(execution.get("executionDate") == "2026-09-02", "execution date drifted")
    require(execution.get("evidenceDigest") == {"algorithm": "sha256", "value": EXECUTION_DIGEST}, "execution evidence digest field drifted")
    require(digest_without(execution, "evidenceDigest") == EXECUTION_DIGEST, "execution evidence canonical digest mismatch")

    expected_order = list(EXPECTED)
    require(execution.get("itemIds") == expected_order, "execution item order/set drifted")
    receipts = execution.get("receipts")
    require(isinstance(receipts, list) and len(receipts) == 3, "execution must contain exactly three public receipts")
    receipt_map = {
        item.get("datasetItemId"): item
        for item in receipts or []
        if isinstance(item, dict) and isinstance(item.get("datasetItemId"), str)
    }
    require(set(receipt_map) == set(EXPECTED), "public receipt item set drifted")

    for item_id, wanted in EXPECTED.items():
        receipt = receipt_map.get(item_id, {})
        require(receipt.get("status") == "completed", f"receipt not completed: {item_id}")
        require(receipt.get("byteSize") == wanted["byteSize"], f"byte size drifted: {item_id}")
        require(receipt.get("sourceDigest") == {"algorithm": "sha256", "value": wanted["sha256"]}, f"source digest drifted: {item_id}")
        require(receipt.get("split") == wanted["split"], f"split drifted: {item_id}")
        require(receipt.get("purpose") == wanted["purpose"], f"purpose drifted: {item_id}")
        require(receipt.get("environment") == "stage1_offline", f"environment drifted: {item_id}")
        require(receipt.get("storageClass") == "managed_standard", f"storage class drifted: {item_id}")
        require(receipt.get("renderer") == {"binding": "pypdfium2", "bindingVersion": "5.13.0", "name": "pdfium"}, f"renderer drifted: {item_id}")
        summary = receipt.get("pageSummary", {})
        require(summary.get("pageCount") == wanted["pageCount"], f"page count drifted: {item_id}")
        require(summary.get("renderedPageCount") == wanted["renderedPageCount"], f"rendered page count drifted: {item_id}")
        require(summary.get("reviewRequiredCount") == 0, f"unexpected review-required page: {item_id}")
        require(summary.get("classificationCounts") == wanted["classification"], f"classification counts drifted: {item_id}")
        require(summary.get("statusCounts") == wanted["statusCounts"], f"status counts drifted: {item_id}")
        require(summary.get("pageOrderPreserved") is True, f"page order not preserved: {item_id}")
        require(summary.get("vectorPagesRasterized") is False, f"vector rasterization occurred: {item_id}")
        assertions = receipt.get("assertions", {})
        for key in (
            "exactByteSizeMatched",
            "exactDigestMatched",
            "environmentRestrictionSatisfied",
            "purposePermissionValid",
            "retentionRestrictionSatisfied",
            "splitRestrictionSatisfied",
            "storageRestrictionSatisfied",
        ):
            require(assertions.get(key) is True, f"receipt gate failed {key}: {item_id}")
        for key in (
            "heldOutThresholdTuningUsed",
            "sourceBytesModified",
            "realArtifactBytesInGit",
            "omrPerformed",
            "musicalCorrectnessEstablished",
            "trainingAuthorized",
            "calibrationAuthorized",
            "publicationAuthorized",
        ):
            require(assertions.get(key) is False, f"unsafe/unsupported receipt assertion {key}: {item_id}")
        handling = receipt.get("reportHandling", {})
        require(handling.get("custodyOnly") is True, f"report handling not custody-only: {item_id}")
        require(handling.get("detailedManifestPublic") is False, f"detailed manifest public: {item_id}")
        require(handling.get("detailedManifestExported") is False, f"detailed manifest exported: {item_id}")
        require(handling.get("derivativeBytesExported") is False, f"derivative bytes exported: {item_id}")
        require(handling.get("externalExportState") == wanted["externalExportState"], f"external-export state drifted: {item_id}")

    require(execution.get("summary") == {
        "allPageOrderPreserved": True,
        "anyVectorPagesRasterized": False,
        "classificationCounts": {"raster_only": 12, "vector_only": 2},
        "developmentCount": 2,
        "heldOutCount": 1,
        "itemCount": 3,
        "pageCount": 14,
        "renderedPageCount": 12,
        "reviewRequiredCount": 0,
        "statusCounts": {"preserved_vector_page": 2, "rendered_raster_page": 12},
    }, "aggregate execution summary drifted")

    top_assertions = execution.get("assertions", {})
    for key in (
        "calibrationAuthorized",
        "detailedManifestsPublic",
        "heldOutThresholdTuningUsed",
        "publicationAuthorized",
        "realCorpusBytesInGit",
        "renderedDerivativesPublic",
        "sourceBytesModified",
        "stage3ExitPass",
        "stage4EntryAuthorized",
        "trainingAuthorized",
    ):
        require(top_assertions.get(key) is False, f"unsafe/unsupported top-level assertion: {key}")

    public_text = EXECUTION_PATH.read_text(encoding="utf-8")
    for forbidden in ("/mnt/data/", "sediment://", "drive.google.com", "webViewLink", "download_url", "manifestFileName"):
        require(forbidden not in public_text, f"public execution evidence leaks custody/provider detail: {forbidden}")

    require(review.get("schemaVersion") == "1.0.0", "limitations review schema drifted")
    require(review.get("reviewId") == "stage3.real-corpus.limitations-review.v1", "limitations review id drifted")
    require(review.get("decision") == "PASS_WITH_ACCEPTED_LIMITATIONS", "limitations review decision drifted")
    require(review.get("executionEvidenceCanonicalSha256") == EXECUTION_DIGEST, "limitations review lost execution-evidence binding")
    require(review.get("reviewDigest") == {"algorithm": "sha256", "value": LIMITATIONS_DIGEST}, "limitations review digest field drifted")
    require(digest_without(review, "reviewDigest") == LIMITATIONS_DIGEST, "limitations review canonical digest mismatch")
    require(review.get("observedCoverage") == {
        "developmentCount": 2,
        "heldOutCount": 1,
        "hybridPageCount": 0,
        "itemCount": 3,
        "pageCount": 14,
        "preservedVectorPageCount": 2,
        "rasterOnlyPageCount": 12,
        "renderedPageCount": 12,
        "reviewRequiredCount": 0,
        "vectorOnlyPageCount": 2,
    }, "limitations observed coverage drifted")
    invariants = review.get("verifiedInvariants", {})
    for key in ("exactSourceIdentity", "pageOrderPreserved"):
        require(invariants.get(key) is True, f"limitations review invariant failed: {key}")
    for key in (
        "vectorPagesRasterized",
        "heldOutThresholdTuningUsed",
        "sourceBytesModified",
        "realCorpusBytesInGit",
        "detailedManifestsPublic",
        "renderedDerivativesPublic",
        "trainingAuthorized",
        "calibrationAuthorized",
        "publicationAuthorized",
    ):
        require(invariants.get(key) is False, f"limitations review unsafe invariant: {key}")
    require(len(review.get("acceptedLimitations", [])) >= 6, "limitations review is incomplete")
    require(any("no real hybrid page" in item for item in review.get("acceptedLimitations", [])), "real hybrid coverage limitation is not explicit")
    for claim, value in review.get("claims", {}).items():
        require(value is False, f"limitations review contains unsupported positive claim: {claim}")

    if failures:
        print("Stage 3 real-corpus execution evidence validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 3 real-corpus execution evidence validation: PASS")
    print(f"- execution canonical SHA-256: {EXECUTION_DIGEST}")
    print(f"- limitations canonical SHA-256: {LIMITATIONS_DIGEST}")
    print("- exact runtime: main 5e682f1933a7167fc142689306352fe53b4b1833 / Run #246 / pypdfium2 5.13.0")
    print("- real batch: 3 items / 14 pages / 12 raster rendered / 2 vector preserved")
    print("- held-out tuning: false")
    print("- Stage 3 exit: not accepted by this evidence slice")
    print("- Stage 4: not authorized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
