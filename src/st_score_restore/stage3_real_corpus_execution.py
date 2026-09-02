"""Offline Stage 3 real-corpus execution orchestration with strict output separation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .dataset_catalog_validation import validate_dataset_catalog
from .dataset_contract_common import canonical_sha256
from .pdf_pipeline import RENDERER_BINDING_VERSION
from .stage3_custody_execution import run_authorized_pdf_pipeline_execution
from .stage3_purpose_grants import run_purpose_granted_pdf_pipeline_execution

SCHEMA_VERSION = "1.0.0"
RUNNER_VERSION = "0.1.0"
REQUIRED_RENDERER_BINDING_VERSION = "5.13.0"
ACCEPTED_CATALOG_CANONICAL_SHA256 = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"

BEETHOVEN_ID = "dataset.item.imslp799143-beethoven-op48-no3.v1"
BARLEY_ID = "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1"
CHOPIN_ID = "dataset.item.imslp82860-chopin-op69.v2"
EXPECTED_ITEM_IDS = (BEETHOVEN_ID, BARLEY_ID, CHOPIN_ID)


class Stage3RealCorpusExecutionError(ValueError):
    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})


@dataclass(frozen=True)
class Stage3RealCorpusBatchResult:
    public_evidence: Mapping[str, Any]
    custody_output_dir: str

    def to_public_dict(self) -> dict[str, Any]:
        return deepcopy(dict(self.public_evidence))


def _canonical_digest(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_custody_result(
    *,
    result: Any,
    dataset_item_id: str,
    custody_dir: Path,
) -> dict[str, Any]:
    safe_name = dataset_item_id.replace("dataset.item.", "").replace("/", "_")
    manifest = result.restricted_manifest_for_custody()
    if manifest is None:
        raise Stage3RealCorpusExecutionError(
            "custody_manifest_missing",
            "Authorized Stage 3 execution did not return a custody manifest.",
            details={"datasetItemId": dataset_item_id},
        )
    manifest_path = custody_dir / f"{safe_name}.manifest.json"
    _write_json(manifest_path, manifest)

    derivative_records: list[dict[str, Any]] = []
    for page in manifest.get("pages", []):
        if not isinstance(page, Mapping):
            continue
        index = page.get("pageIndex")
        if not isinstance(index, int):
            continue
        payload = result.restricted_page_bytes_for_custody(index)
        if payload is None:
            continue
        derivative_path = custody_dir / f"{safe_name}.page-{index:04d}.png"
        derivative_path.write_bytes(payload)
        derivative_records.append(
            {
                "pageIndex": index,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "byteSize": len(payload),
            }
        )

    return {
        "manifestSha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "manifestFileName": manifest_path.name,
        "renderedDerivativeCount": len(derivative_records),
        "renderedDerivatives": derivative_records,
    }


def _aggregate_page_summary(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    classification_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    for receipt in receipts:
        page_summary = receipt.get("pageSummary", {})
        for key, count in page_summary.get("classificationCounts", {}).items():
            classification_counts[str(key)] = classification_counts.get(str(key), 0) + int(count)
        for key, count in page_summary.get("statusCounts", {}).items():
            status_counts[str(key)] = status_counts.get(str(key), 0) + int(count)
    return {
        "pageCount": sum(int(item.get("pageSummary", {}).get("pageCount", 0)) for item in receipts),
        "renderedPageCount": sum(int(item.get("pageSummary", {}).get("renderedPageCount", 0)) for item in receipts),
        "reviewRequiredCount": sum(int(item.get("pageSummary", {}).get("reviewRequiredCount", 0)) for item in receipts),
        "classificationCounts": dict(sorted(classification_counts.items())),
        "statusCounts": dict(sorted(status_counts.items())),
        "allPageOrderPreserved": all(item.get("pageSummary", {}).get("pageOrderPreserved") is True for item in receipts),
        "anyVectorPagesRasterized": any(item.get("pageSummary", {}).get("vectorPagesRasterized") is True for item in receipts),
    }


def execute_stage3_real_corpus_batch(
    catalog: Mapping[str, Any],
    purpose_grants: Mapping[str, Any],
    *,
    source_paths: Mapping[str, str | Path],
    custody_output_dir: str | Path,
    repository_root: str | Path,
    execution_date: date | str,
    repository_main_sha: str,
    post_merge_ci_run_number: int,
    post_merge_ci_run_id: int,
) -> Stage3RealCorpusBatchResult:
    """Execute exactly Beethoven, Barley and Chopin in an approved offline custody workspace."""

    if RENDERER_BINDING_VERSION != REQUIRED_RENDERER_BINDING_VERSION:
        raise Stage3RealCorpusExecutionError(
            "renderer_version_mismatch",
            "Real Stage 3 corpus evidence requires the exact production PDFium binding version.",
            details={
                "required": REQUIRED_RENDERER_BINDING_VERSION,
                "actual": RENDERER_BINDING_VERSION,
            },
        )

    validated_catalog = validate_dataset_catalog(deepcopy(dict(catalog)))
    if canonical_sha256(validated_catalog) != ACCEPTED_CATALOG_CANONICAL_SHA256:
        raise Stage3RealCorpusExecutionError(
            "catalog_digest_mismatch",
            "Real Stage 3 corpus execution requires the accepted expanded-v2 catalog.",
        )

    if set(source_paths) != set(EXPECTED_ITEM_IDS):
        raise Stage3RealCorpusExecutionError(
            "source_item_set_mismatch",
            "Real Stage 3 execution requires exactly Beethoven, Barley and Chopin source paths.",
        )

    repo_root = Path(repository_root).resolve()
    custody_dir = Path(custody_output_dir).resolve()
    if _inside(custody_dir, repo_root):
        raise Stage3RealCorpusExecutionError(
            "custody_output_inside_repository",
            "Detailed Stage 3 output must remain outside the ordinary Git working tree.",
        )
    custody_dir.mkdir(parents=True, exist_ok=True)

    for item_id in EXPECTED_ITEM_IDS:
        path = Path(source_paths[item_id]).resolve()
        if _inside(path, repo_root):
            raise Stage3RealCorpusExecutionError(
                "real_source_inside_repository",
                "Real corpus source bytes must remain outside the ordinary Git working tree.",
                details={"datasetItemId": item_id},
            )
        if not path.is_file():
            raise Stage3RealCorpusExecutionError(
                "real_source_missing",
                "Required real corpus source is not available in approved custody.",
                details={"datasetItemId": item_id},
            )

    receipts: list[dict[str, Any]] = []
    private_summaries: dict[str, Any] = {}
    for item_id in EXPECTED_ITEM_IDS:
        path = Path(source_paths[item_id]).resolve()
        data = path.read_bytes()
        if item_id in {BEETHOVEN_ID, BARLEY_ID}:
            result = run_purpose_granted_pdf_pipeline_execution(
                validated_catalog,
                purpose_grants,
                dataset_item_id=item_id,
                data=data,
                purpose="pdf_pipeline_evaluation",
                execution_date=execution_date,
            )
        else:
            result = run_authorized_pdf_pipeline_execution(
                validated_catalog,
                dataset_item_id=item_id,
                data=data,
                purpose="held_out_evaluation",
                execution_date=execution_date,
            )
        receipt = result.to_public_dict()
        receipts.append(receipt)
        private_summaries[item_id] = _write_custody_result(
            result=result,
            dataset_item_id=item_id,
            custody_dir=custody_dir,
        )

    summary = {
        "itemCount": len(receipts),
        "developmentCount": sum(1 for item in receipts if item.get("split") == "development"),
        "heldOutCount": sum(1 for item in receipts if item.get("split") == "held_out"),
        **_aggregate_page_summary(receipts),
    }
    public_evidence: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "runnerVersion": RUNNER_VERSION,
        "status": "executed",
        "executionDate": execution_date.isoformat() if isinstance(execution_date, date) else execution_date,
        "repositoryMainSha": repository_main_sha,
        "postMergeValidation": {
            "runNumber": post_merge_ci_run_number,
            "runId": post_merge_ci_run_id,
        },
        "catalogCanonicalSha256": ACCEPTED_CATALOG_CANONICAL_SHA256,
        "rendererBindingVersion": RENDERER_BINDING_VERSION,
        "itemIds": list(EXPECTED_ITEM_IDS),
        "receipts": receipts,
        "summary": summary,
        "assertions": {
            "sourceBytesModified": False,
            "realCorpusBytesInGit": False,
            "detailedManifestsPublic": False,
            "renderedDerivativesPublic": False,
            "heldOutThresholdTuningUsed": False,
            "trainingAuthorized": False,
            "calibrationAuthorized": False,
            "publicationAuthorized": False,
            "stage3ExitPass": False,
            "stage4EntryAuthorized": False,
        },
        "limitations": [
            "This execution evidence does not by itself accept Stage 3 exit.",
            "Detailed manifests, quality evidence and rendered derivatives remain custody-only.",
            "Held-out execution is evaluation-only and must not tune thresholds or resource limits.",
        ],
    }
    public_evidence["evidenceDigest"] = {
        "algorithm": "sha256",
        "value": _canonical_digest(public_evidence),
    }
    _write_json(custody_dir / "private-execution-index.json", {
        "schemaVersion": SCHEMA_VERSION,
        "datasetItems": private_summaries,
        "publicEvidenceSha256": public_evidence["evidenceDigest"]["value"],
    })
    return Stage3RealCorpusBatchResult(
        public_evidence=public_evidence,
        custody_output_dir=str(custody_dir),
    )


__all__ = [
    "ACCEPTED_CATALOG_CANONICAL_SHA256",
    "BARLEY_ID",
    "BEETHOVEN_ID",
    "CHOPIN_ID",
    "EXPECTED_ITEM_IDS",
    "REQUIRED_RENDERER_BINDING_VERSION",
    "RUNNER_VERSION",
    "SCHEMA_VERSION",
    "Stage3RealCorpusBatchResult",
    "Stage3RealCorpusExecutionError",
    "execute_stage3_real_corpus_batch",
]
