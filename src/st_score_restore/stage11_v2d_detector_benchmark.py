"""Stage 11 V2d detector benchmark contract.

This module defines a development-only, inference-only benchmark boundary for
external semantic detector candidates. It intentionally cannot train, tune,
access held-out data, authorize production, or authorize Stage 12.

GPU execution is exploratory only. Any detector candidate selected here must be
re-run against the frozen V2a candidate under the canonical CPU evidence path
before semantic-preservation claims can be upgraded.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from .stage11_v2c_semantic_preservation import (
    CONTRACT_ID,
    SEMANTIC_CLASSES,
    Stage11V2cSemanticPreservationError,
    validate_expected_class_manifest,
)

REGISTRY_SCHEMA_VERSION = "stage11.v2d.detector-candidate-registry.v1"
RESULT_SCHEMA_VERSION = "stage11.v2d.detector-benchmark-result.v1"

ALLOWED_CODE_LICENSES = frozenset({"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause"})
ALLOWED_WEIGHT_LICENSE_STATUSES = frozenset(
    {"explicit_permissive", "repo_scoped_not_separately_declared", "unknown_review_required"}
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2cSemanticPreservationError(message)


def validate_detector_candidate_registry(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("schemaVersion") == REGISTRY_SCHEMA_VERSION, "V2d registry schema mismatch")
    _require(payload.get("contractId") == CONTRACT_ID, "V2d registry contract mismatch")
    candidates = payload.get("candidates")
    _require(isinstance(candidates, list) and candidates, "V2d registry candidates required")
    seen: set[str] = set()
    production_admitted = 0
    for candidate in candidates:
        _require(isinstance(candidate, Mapping), "V2d candidate must be object")
        cid = str(candidate.get("candidateId") or "")
        _require(cid and cid not in seen, "V2d candidateId missing/duplicate")
        seen.add(cid)
        _require(bool(candidate.get("upstreamRepository")), f"upstream repository required: {cid}")
        commit = str(candidate.get("upstreamCommit") or "")
        _require(len(commit) == 40 and all(ch in "0123456789abcdef" for ch in commit), f"pinned upstream commit required: {cid}")
        code_license = str(candidate.get("codeLicense") or "")
        _require(code_license in ALLOWED_CODE_LICENSES, f"non-permissive code license forbidden: {cid}")
        weight_status = str(candidate.get("weightLicenseStatus") or "")
        _require(weight_status in ALLOWED_WEIGHT_LICENSE_STATUSES, f"invalid weight license status: {cid}")
        classes = candidate.get("semanticClasses")
        _require(isinstance(classes, list) and classes, f"semantic classes required: {cid}")
        _require(set(classes) <= set(SEMANTIC_CLASSES), f"unknown semantic class in candidate: {cid}")
        scope = candidate.get("scope") or {}
        _require(scope.get("trainingAllowed") is False, f"training must remain forbidden: {cid}")
        _require(scope.get("heldOutAccessAllowed") is False, f"held-out access must remain forbidden: {cid}")
        _require(scope.get("detectorOutputMayBecomeGroundTruth") is False, f"detector cannot become ground truth: {cid}")
        _require(scope.get("stage12EntryAuthorized") is False, f"Stage 12 must remain closed: {cid}")
        if scope.get("productionAdmissionAuthorized") is True:
            _require(weight_status == "explicit_permissive", f"production admission requires explicit permissive weight license: {cid}")
            production_admitted += 1
    return {
        "status": "pass",
        "candidateCount": len(candidates),
        "productionAdmittedCandidateCount": production_admitted,
        "allTrainingForbidden": True,
        "allHeldOutAccessForbidden": True,
    }


def teacher_present_class_pairs(manifest: Mapping[str, Any]) -> set[tuple[str, str]]:
    validate_expected_class_manifest(manifest)
    pairs: set[tuple[str, str]] = set()
    for page in manifest.get("pages") or []:
        page_id = str(page["pageId"])
        for class_id, record in page["classes"].items():
            if record["state"] == "present":
                pairs.add((page_id, class_id))
    return pairs


def benchmark_coverage_from_present_pairs(
    manifest: Mapping[str, Any],
    confidently_evaluated_pairs: Iterable[tuple[str, str]],
) -> dict[str, Any]:
    eligible = teacher_present_class_pairs(manifest)
    evaluated = set(confidently_evaluated_pairs)
    _require(evaluated <= eligible, "V2d evaluated pair not teacher-confirmed present")
    by_class: dict[str, dict[str, Any]] = {}
    for class_id in SEMANTIC_CLASSES:
        e = {pair for pair in eligible if pair[1] == class_id}
        c = {pair for pair in evaluated if pair[1] == class_id}
        by_class[class_id] = {
            "eligiblePresentClassPageCount": len(e),
            "confidentlyEvaluatedClassPageCount": len(c),
            "coverage": len(c) / max(1, len(e)),
        }
    return {
        "eligibleExpectedPresentClassPageCount": len(eligible),
        "confidentlyEvaluatedExpectedPresentClassPageCount": len(evaluated),
        "applicableClassDetectorCoverage": len(evaluated) / max(1, len(eligible)),
        "classCoverage": by_class,
    }


def validate_detector_benchmark_result(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("schemaVersion") == RESULT_SCHEMA_VERSION, "V2d result schema mismatch")
    _require(payload.get("contractId") == CONTRACT_ID, "V2d result contract mismatch")
    boundary = payload.get("boundary") or {}
    _require(boundary.get("developmentOnly") is True, "V2d benchmark must be development-only")
    _require(boundary.get("teacherGroundTruthFrozen") is True, "teacher ground truth must be frozen")
    _require(boundary.get("detectorOutputUsedAsGroundTruth") is False, "detector output cannot be ground truth")
    _require(boundary.get("trainingPerformed") is False, "training forbidden")
    _require(boundary.get("fineTuningPerformed") is False, "fine-tuning forbidden")
    _require(boundary.get("heldOutAccessed") is False, "held-out access forbidden")
    _require(boundary.get("productionPromotionAuthorized") is False, "production promotion forbidden")
    _require(boundary.get("stage12EntryAuthorized") is False, "Stage 12 must remain closed")

    runtime = payload.get("runtime") or {}
    _require(runtime.get("purpose") == "exploratory_detector_benchmark", "V2d GPU runtime is exploratory only")
    _require(runtime.get("finalCanonicalCpuRerunRequired") is True, "canonical CPU rerun must be required")

    coverage = payload.get("coverage") or {}
    eligible = int(coverage.get("eligibleExpectedPresentClassPageCount", -1))
    evaluated = int(coverage.get("confidentlyEvaluatedExpectedPresentClassPageCount", -1))
    reported = float(coverage.get("applicableClassDetectorCoverage", -1.0))
    _require(eligible > 0, "positive V2d coverage denominator required")
    _require(0 <= evaluated <= eligible, "invalid V2d evaluated count")
    _require(abs(reported - evaluated / eligible) < 1e-12, "V2d coverage arithmetic mismatch")

    claims = payload.get("claimBoundary") or {}
    _require(claims.get("semanticPreservationEstablished") is False, "GPU exploration cannot establish semantic preservation")
    _require(claims.get("productionReady") is False, "GPU exploration cannot establish production readiness")
    return {
        "status": "pass",
        "eligibleExpectedPresentClassPageCount": eligible,
        "confidentlyEvaluatedExpectedPresentClassPageCount": evaluated,
        "applicableClassDetectorCoverage": reported,
        "finalCanonicalCpuRerunRequired": True,
    }
