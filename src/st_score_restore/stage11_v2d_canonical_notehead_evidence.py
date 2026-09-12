"""Bind and validate completed Stage 11 V2d canonical notehead evidence.

The canonical result remains a Drive artifact.  This module verifies its exact bytes,
recomputes every page metric and aggregate, and emits a reviewable repository binding.
It can accept notehead evidence only; it cannot authorize overall Stage 11, production,
or Stage 12.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .stage11_v2c_semantic_preservation import Stage11V2cSemanticPreservationError

RESULT_SCHEMA = "stage11.v2d.canonical-cpu-restore-gpu-notehead-semantic-rerun.v1"
BINDING_SCHEMA = "stage11.v2d.canonical-notehead-result-binding.v1"
CONTRACT_ID = "stage11.v2c.semantic-preservation.nonheldout.v1"
RESULT_DRIVE_FILE_ID = "15ZspsDK3jAAtfqmmebBebopEpo3a1Xpn"
RESULT_DRIVE_PATH = "/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/V2D_RESULTS/v2d_canonical_cpu_restore_gpu_notehead_semantic_rerun_result.json"
RESULT_BYTE_SIZE = 23228
RESULT_SHA256 = "ab6197bcf0dd58407ffd4401d61aefc195e5c8dd63cb68e5a05deee261dd2e54"
EXPECTED_PAGE_COUNT = 18
RECALL_MARKER = 0.80
FORBIDDEN_OVERALL_CLAIMS = (
    "semanticPreservationEstablished",
    "overallStage11PassAuthorized",
    "productionReady",
    "productionPromotionAuthorized",
    "stage12EntryAuthorized",
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2cSemanticPreservationError(message)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _close(left: Any, right: Any, *, tolerance: float = 1e-12) -> bool:
    try:
        return abs(float(left) - float(right)) <= tolerance
    except (TypeError, ValueError):
        return False


def _validate_claim_boundary(boundary: Mapping[str, Any]) -> None:
    _require(boundary.get("noteheadCanonicalCpuSemanticRerunCompleted") is True, "canonical notehead completion marker required")
    _require(boundary.get("gpuDetectorAdmittedOnlyAfterCpuCanaryEquivalence") is True, "CPU/GPU canary admission marker required")
    for key in FORBIDDEN_OVERALL_CLAIMS:
        _require(boundary.get(key) is False, f"overall claim must remain false: {key}")


def _summarize_pages(pages: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    _require(isinstance(pages, list) and len(pages) == EXPECTED_PAGE_COUNT, "exactly 18 canonical notehead pages required")
    summaries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in pages:
        _require(isinstance(page, Mapping), "canonical page must be an object")
        page_id = str(page.get("pageId") or "")
        _require(page_id and page_id not in seen, "canonical pageId missing or duplicate")
        seen.add(page_id)
        _require(page.get("teacherState") == "present", f"teacher-present page required: {page_id}")
        metric = page.get("metric") or {}
        _require(metric.get("classId") == "notehead", f"notehead metric required: {page_id}")
        source = metric.get("sourceCount")
        candidate = metric.get("candidateCount")
        matched = metric.get("matchedCount")
        candidate_only = metric.get("candidateOnlyCount")
        _require(all(type(value) is int for value in (source, candidate, matched, candidate_only)), f"integer counts required: {page_id}")
        _require(source > 0 and 0 <= matched <= source and 0 <= matched <= candidate, f"invalid counts: {page_id}")
        _require(candidate_only == candidate - matched, f"candidate-only arithmetic mismatch: {page_id}")
        recall = matched / source
        _require(_close(metric.get("sourceRecall"), recall), f"source recall arithmetic mismatch: {page_id}")
        _require(metric.get("recallAtLeast0_80") is (recall >= RECALL_MARKER), f"recall marker mismatch: {page_id}")
        for key in ("canonicalRestoredFileSha256", "canonicalRestoredPixelSha256"):
            digest = str(page.get(key) or "")
            _require(len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest), f"invalid {key}: {page_id}")
        summaries.append({
            "pageId": page_id,
            "teacherState": "present",
            "canonicalRestoredFileSha256": page["canonicalRestoredFileSha256"],
            "canonicalRestoredPixelSha256": page["canonicalRestoredPixelSha256"],
            "metric": dict(metric),
        })
    recalls = [float(page["metric"]["sourceRecall"]) for page in summaries]
    aggregate = {
        "evaluatedPageCount": len(summaries),
        "pagesAtRecallGte0_80": sum(value >= RECALL_MARKER for value in recalls),
        "rateAtRecallGte0_80": sum(value >= RECALL_MARKER for value in recalls) / len(recalls),
        "meanSourceRecall": sum(recalls) / len(recalls),
        "minimumSourceRecall": min(recalls),
        "maximumSourceRecall": max(recalls),
        "sourceCountTotal": sum(page["metric"]["sourceCount"] for page in summaries),
        "matchedCountTotal": sum(page["metric"]["matchedCount"] for page in summaries),
        "candidateCountTotal": sum(page["metric"]["candidateCount"] for page in summaries),
        "candidateOnlyCountTotal": sum(page["metric"]["candidateOnlyCount"] for page in summaries),
    }
    return summaries, aggregate


def _validate_reported_aggregate(reported: Mapping[str, Any], recomputed: Mapping[str, Any]) -> None:
    for key in ("evaluatedPageCount", "pagesAtRecallGte0_80"):
        _require(reported.get(key) == recomputed[key], f"reported aggregate mismatch: {key}")
    _require(reported.get("allTeacherPresentPagesEvaluated") is True, "all teacher-present pages must be evaluated")
    for key in ("rateAtRecallGte0_80", "meanSourceRecall", "minimumSourceRecall", "maximumSourceRecall"):
        _require(_close(reported.get(key), recomputed[key]), f"reported aggregate mismatch: {key}")


def bind_canonical_notehead_result(result_path: Path) -> dict[str, Any]:
    raw = result_path.read_bytes()
    _require(len(raw) == RESULT_BYTE_SIZE, "canonical result byte-size mismatch")
    _require(_sha256(raw) == RESULT_SHA256, "canonical result SHA-256 mismatch")
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise Stage11V2cSemanticPreservationError("canonical result is not valid JSON") from exc
    _require(isinstance(result, Mapping), "canonical result JSON object required")
    _require(result.get("schemaVersion") == RESULT_SCHEMA, "canonical result schema mismatch")
    _require(result.get("contractId") == CONTRACT_ID, "canonical result contract mismatch")
    _require(result.get("status") == "COMPLETE", "canonical result must be COMPLETE")
    scope = result.get("scope") or {}
    _require(scope.get("developmentOnly") is True, "canonical result must remain development-only")
    _require(scope.get("selectedSemanticClass") == "notehead", "canonical result must be notehead-only")
    _require(scope.get("selectedTeacherPresentPageCount") == EXPECTED_PAGE_COUNT, "selected page count mismatch")
    for key in ("detectorOutputUsedAsGroundTruth", "trainingPerformed", "fineTuningPerformed", "heldOutAccessed"):
        _require(scope.get(key) is False, f"forbidden scope flag: {key}")
    runtime = result.get("runtime") or {}
    _require(runtime.get("python") == "3.13.5" and runtime.get("torch") == "2.10.0+cpu", "canonical Restore runtime mismatch")
    _require(runtime.get("restoreDevice") == "CPU", "Restore must remain CPU")
    _require(runtime.get("detectorProvider") == "CUDAExecutionProvider", "detector CUDA provider mismatch")
    _require(runtime.get("wholeSessionFallbackDisabled") is True, "whole-session fallback must be disabled")
    restore = result.get("restore") or {}
    _require(restore.get("device") == "CPU" and restore.get("actualCpuOutputsPersistedAndHashBound") is True, "canonical CPU Restore provenance mismatch")
    detector = result.get("detector") or {}
    _require(detector.get("segNetOnly") is True and detector.get("fullOemerPipelineExecuted") is False and detector.get("unetBigExecuted") is False, "notehead detector scope mismatch")
    _require(detector.get("gpuAdmittedAfterExactCpuCanaryBoxEquivalence") is True, "GPU detector equivalence missing")
    _require(detector.get("wholeSessionFallbackDisabled") is True, "detector fallback guard missing")
    summaries, aggregate = _summarize_pages(result.get("pages"))
    _validate_reported_aggregate(result.get("noteheadEvidence") or {}, aggregate)
    _validate_claim_boundary(result.get("claimBoundary") or {})
    return {
        "schemaVersion": BINDING_SCHEMA,
        "contractId": CONTRACT_ID,
        "generatedOn": "2026-09-09",
        "sourceResult": {
            "driveFileId": RESULT_DRIVE_FILE_ID,
            "drivePath": RESULT_DRIVE_PATH,
            "byteSize": RESULT_BYTE_SIZE,
            "sha256": RESULT_SHA256,
            "schemaVersion": RESULT_SCHEMA,
            "status": "COMPLETE",
        },
        "runtimeEvidence": {"restore": dict(restore), "detector": dict(detector), "runtime": dict(runtime)},
        "recomputedAggregate": aggregate,
        "reportedAggregateMatchesRecomputed": True,
        "pages": summaries,
        "classOutcome": {
            "classId": "notehead",
            "decision": "PASS_CANONICAL_CLASS_EVIDENCE",
            "basis": "18/18 teacher-present pages evaluated; every page source recall is at least 0.80 on hash-bound canonical CPU Restore outputs",
        },
        "claimBoundary": dict(result["claimBoundary"]),
    }


def validate_notehead_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    _require(binding.get("schemaVersion") == BINDING_SCHEMA, "binding schema mismatch")
    _require(binding.get("contractId") == CONTRACT_ID, "binding contract mismatch")
    source = binding.get("sourceResult") or {}
    _require(source.get("driveFileId") == RESULT_DRIVE_FILE_ID, "binding Drive file mismatch")
    _require(source.get("drivePath") == RESULT_DRIVE_PATH, "binding Drive path mismatch")
    _require(source.get("byteSize") == RESULT_BYTE_SIZE, "binding byte-size mismatch")
    _require(source.get("sha256") == RESULT_SHA256, "binding SHA-256 mismatch")
    _require(source.get("schemaVersion") == RESULT_SCHEMA and source.get("status") == "COMPLETE", "binding source result identity mismatch")
    runtime_evidence = binding.get("runtimeEvidence") or {}
    runtime = runtime_evidence.get("runtime") or {}
    restore = runtime_evidence.get("restore") or {}
    detector = runtime_evidence.get("detector") or {}
    _require(runtime.get("python") == "3.13.5" and runtime.get("torch") == "2.10.0+cpu", "binding Restore runtime mismatch")
    _require(runtime.get("restoreDevice") == "CPU" and runtime.get("detectorProvider") == "CUDAExecutionProvider", "binding device provenance mismatch")
    _require(runtime.get("wholeSessionFallbackDisabled") is True, "binding runtime fallback guard missing")
    _require(restore.get("device") == "CPU" and restore.get("actualCpuOutputsPersistedAndHashBound") is True, "binding Restore provenance mismatch")
    _require(detector.get("segNetOnly") is True and detector.get("fullOemerPipelineExecuted") is False and detector.get("unetBigExecuted") is False, "binding detector scope mismatch")
    _require(detector.get("gpuAdmittedAfterExactCpuCanaryBoxEquivalence") is True and detector.get("wholeSessionFallbackDisabled") is True, "binding detector admission guard missing")
    summaries, aggregate = _summarize_pages(binding.get("pages"))
    reported = binding.get("recomputedAggregate") or {}
    for key, value in aggregate.items():
        if isinstance(value, float):
            _require(_close(reported.get(key), value), f"binding aggregate mismatch: {key}")
        else:
            _require(reported.get(key) == value, f"binding aggregate mismatch: {key}")
    outcome = binding.get("classOutcome") or {}
    _require(outcome.get("classId") == "notehead" and outcome.get("decision") == "PASS_CANONICAL_CLASS_EVIDENCE", "notehead class outcome mismatch")
    _require(binding.get("reportedAggregateMatchesRecomputed") is True, "reported aggregate review marker required")
    _validate_claim_boundary(binding.get("claimBoundary") or {})
    return {"status": "pass", "pageCount": len(summaries), "meanSourceRecall": aggregate["meanSourceRecall"], "overallStage11PassAuthorized": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    binding = bind_canonical_notehead_result(args.result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validate_notehead_binding(binding)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
