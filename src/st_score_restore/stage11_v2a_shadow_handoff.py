"""Development-only shadow handoff from the non-production job service to frozen V2a.

The handoff is observational only. It never replaces the OpenCV candidate, never changes
its safety report or a review decision, and is not registered as a network route. Only
synthetic or explicitly non-held-out test inputs are permitted.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from .job_api_types import JobApiError
from .job_service_support import _artifact_id, _canonical_json_bytes
from .stage11_v2a_staging_api import (
    EXPECTED_PACKAGE_SHA256,
    EXPECTED_PACKAGE_SIZE_BYTES,
    TorchScriptStagingService,
    decode_grayscale_png,
)

CONTRACT_ID = "stage11.v2a.shadow-job-handoff.synthetic-nonheldout.v1"
OBSERVATION_TYPE = "stage11_v2a_shadow_observation"
OBSERVATION_SCHEMA_VERSION = "stage11.v2a.shadow-observation.v1"
JOB_EVIDENCE_TYPE = "stage11_v2a_shadow_job_handoff_evidence"
JOB_EVIDENCE_SCHEMA_VERSION = "stage11.v2a.shadow-job-handoff-evidence.v1"
ALLOWED_SOURCE_DATA_KINDS = frozenset({"synthetic_only", "nonheldout_test_only"})
SHADOW_CANDIDATE_ROLE = "stage11_v2a_shadow_candidate"
SHADOW_EVIDENCE_ROLE = "stage11_v2a_shadow_evidence"
OBSERVABLE_JOB_STATE = "AWAITING_REVIEW"


class Stage11V2aShadowHandoffError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11V2aShadowHandoffError(message)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _source_kind(value: str) -> str:
    normalized = str(value or "").strip()
    _require(normalized in ALLOWED_SOURCE_DATA_KINDS, "shadow handoff sourceDataKind is not permitted")
    return normalized


def shadow_job_handoff_contract() -> dict[str, Any]:
    return {
        "contractId": CONTRACT_ID,
        "candidate": {
            "packageSha256": EXPECTED_PACKAGE_SHA256,
            "packageSizeBytes": EXPECTED_PACKAGE_SIZE_BYTES,
            "frozen": True,
        },
        "jobService": {
            "integrationMode": "explicit-in-process-shadow-call",
            "requiredJobState": OBSERVABLE_JOB_STATE,
            "sourceDataKinds": sorted(ALLOWED_SOURCE_DATA_KINDS),
            "sourceMediaType": "image/png",
            "nativeGrayscalePngRequired": True,
            "allCurrentAttemptPagesObservedAtomically": True,
            "networkRouteRegistered": False,
            "existingHttpApiModified": False,
            "openApiModified": False,
        },
        "artifacts": {
            "shadowCandidateRole": SHADOW_CANDIDATE_ROLE,
            "shadowEvidenceRole": SHADOW_EVIDENCE_ROLE,
            "shadowSelectable": False,
            "shadowCanReplaceCurrentCandidate": False,
            "shadowCanReplaceSafetyReport": False,
        },
        "comparison": {
            "purpose": "observational_only",
            "metrics": ["meanAbsDiff", "maxAbsDiff", "changedPixelFraction"],
            "qualityDecisionAllowed": False,
            "automaticPromotionAllowed": False,
        },
        "authorization": {
            "shadowIntegrationValidationAuthorized": True,
            "productionInferenceAuthorized": False,
            "productionPromotionAuthorized": False,
            "realUserRolloutAuthorized": False,
            "finalProductionModelSelectionAuthorized": False,
            "stage12EntryAuthorized": False,
        },
    }


class Stage11V2aShadowObserver:
    """Compare staging output with the current primary candidate without selection."""

    def __init__(
        self,
        handle: Callable[[bytes, Mapping[str, Any]], tuple[bytes, Mapping[str, Any]]],
    ) -> None:
        if not callable(handle):
            raise TypeError("shadow staging handle must be callable")
        self._handle = handle

    @classmethod
    def from_package(cls, package_path: Path) -> "Stage11V2aShadowObserver":
        service = TorchScriptStagingService(Path(package_path))
        return cls(service.handle)

    def observe(
        self,
        source_png: bytes,
        primary_candidate_png: bytes,
        *,
        request_id: str,
        source_data_kind: str,
    ) -> tuple[bytes, dict[str, Any]]:
        kind = _source_kind(source_data_kind)
        _require(isinstance(source_png, bytes) and bool(source_png), "shadow source bytes required")
        _require(isinstance(primary_candidate_png, bytes) and bool(primary_candidate_png), "primary candidate bytes required")
        source = decode_grayscale_png(source_png)
        primary = decode_grayscale_png(primary_candidate_png)
        _require(source.shape == primary.shape, "primary candidate shape must match immutable source")

        response_body, raw_meta = self._handle(
            source_png,
            {"requestId": request_id, "sourceDataKind": kind},
        )
        meta = dict(raw_meta)
        _require(meta.get("requestId") == request_id, "shadow staging requestId mismatch")
        _require(meta.get("sourceDataKind") == kind, "shadow staging sourceDataKind mismatch")
        _require(meta.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "shadow staging package SHA mismatch")
        _require(meta.get("networkRouteRegistered") is False, "shadow staging cannot register a network route")
        _require(meta.get("existingHttpApiModified") is False, "shadow staging cannot modify existing HTTP API")
        _require(meta.get("productionInferenceAuthorized") is False, "shadow staging cannot authorize production inference")
        _require(meta.get("stage12EntryAuthorized") is False, "shadow staging cannot authorize Stage 12")

        shadow = decode_grayscale_png(response_body)
        _require(shadow.shape == source.shape, "shadow output shape must match immutable source")
        diff = np.abs(primary.astype(np.float32) / 255.0 - shadow.astype(np.float32) / 255.0)
        observation = {
            "artifactType": OBSERVATION_TYPE,
            "schemaVersion": OBSERVATION_SCHEMA_VERSION,
            "status": "completed",
            "contractId": CONTRACT_ID,
            "requestId": request_id,
            "sourceDataKind": kind,
            "packageSha256": EXPECTED_PACKAGE_SHA256,
            "source": {
                "sha256": _sha256_bytes(source_png),
                "byteSize": len(source_png),
                "shape": list(source.shape),
            },
            "primaryCandidate": {
                "sha256": _sha256_bytes(primary_candidate_png),
                "byteSize": len(primary_candidate_png),
                "shape": list(primary.shape),
            },
            "shadowCandidate": {
                "sha256": _sha256_bytes(response_body),
                "byteSize": len(response_body),
                "shape": list(shadow.shape),
                "packageSha256": EXPECTED_PACKAGE_SHA256,
            },
            "comparison": {
                "purpose": "observational_only",
                "meanAbsDiff": float(diff.mean()),
                "maxAbsDiff": float(diff.max()),
                "changedPixelFraction": float((diff > (0.5 / 255.0)).mean()),
                "qualityDecisionMade": False,
                "automaticPromotionPerformed": False,
            },
            "transport": {
                "tileCount": int(meta.get("tileCount", 0)),
                "requestSha256": meta.get("requestSha256"),
                "responseSha256": meta.get("responseSha256"),
                "networkRouteRegistered": False,
                "existingHttpApiModified": False,
            },
            "safety": {
                "heldOutAccessed": False,
                "optimizerCreated": False,
                "backpropagationExecuted": False,
                "weightsMutated": False,
                "realUserDataUsed": False,
                "shadowSelectable": False,
                "primaryCandidateReplacementAllowed": False,
                "safetyReportReplacementAllowed": False,
            },
            "authorization": shadow_job_handoff_contract()["authorization"],
        }
        validate_shadow_observation(observation)
        return bytes(response_body), observation


def validate_shadow_observation(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == OBSERVATION_TYPE, "shadow observation type mismatch")
    _require(payload.get("schemaVersion") == OBSERVATION_SCHEMA_VERSION, "shadow observation schema mismatch")
    _require(payload.get("status") == "completed", "shadow observation must be completed")
    _require(payload.get("contractId") == CONTRACT_ID, "shadow contract mismatch")
    _require(payload.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "shadow package SHA mismatch")
    _source_kind(str(payload.get("sourceDataKind") or ""))
    for section in ("source", "primaryCandidate", "shadowCandidate"):
        item = payload.get(section) or {}
        digest = str(item.get("sha256") or "")
        _require(len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest), f"invalid {section} SHA")
        _require(int(item.get("byteSize", 0)) > 0, f"missing {section} byte size")
        shape = item.get("shape")
        _require(isinstance(shape, list) and len(shape) == 2 and all(int(v) > 0 for v in shape), f"invalid {section} shape")
    _require(payload["source"]["shape"] == payload["primaryCandidate"]["shape"] == payload["shadowCandidate"]["shape"], "shadow observation shapes differ")
    _require((payload.get("shadowCandidate") or {}).get("packageSha256") == EXPECTED_PACKAGE_SHA256, "shadow candidate package mismatch")
    comparison = payload.get("comparison") or {}
    _require(comparison.get("purpose") == "observational_only", "shadow comparison purpose mismatch")
    _require(float(comparison.get("meanAbsDiff", -1.0)) >= 0.0, "shadow meanAbsDiff missing")
    _require(float(comparison.get("maxAbsDiff", -1.0)) >= 0.0, "shadow maxAbsDiff missing")
    changed = float(comparison.get("changedPixelFraction", -1.0))
    _require(0.0 <= changed <= 1.0, "shadow changedPixelFraction invalid")
    _require(comparison.get("qualityDecisionMade") is False, "shadow comparison cannot make a quality decision")
    _require(comparison.get("automaticPromotionPerformed") is False, "shadow comparison cannot promote")
    safety = payload.get("safety") or {}
    for key in (
        "heldOutAccessed", "optimizerCreated", "backpropagationExecuted", "weightsMutated",
        "realUserDataUsed", "shadowSelectable", "primaryCandidateReplacementAllowed",
        "safetyReportReplacementAllowed",
    ):
        _require(safety.get(key) is False, f"shadow safety flag must be false: {key}")
    transport = payload.get("transport") or {}
    _require(transport.get("networkRouteRegistered") is False, "shadow transport route must remain closed")
    _require(transport.get("existingHttpApiModified") is False, "shadow transport cannot modify HTTP API")
    authorization = payload.get("authorization") or {}
    _require(authorization.get("shadowIntegrationValidationAuthorized") is True, "shadow validation authorization missing")
    for key in (
        "productionInferenceAuthorized", "productionPromotionAuthorized", "realUserRolloutAuthorized",
        "finalProductionModelSelectionAuthorized", "stage12EntryAuthorized",
    ):
        _require(authorization.get(key) is False, f"shadow authorization must remain false: {key}")
    return {
        "status": "pass",
        "shadowObservationValid": True,
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
    }


class Stage11V2aShadowJobMixin:
    """Explicit in-process shadow observation method for ``RestorationJobService``."""

    def run_stage11_v2a_shadow_job(
        self,
        job_id: str,
        *,
        source_data_kind: str,
        observer: Stage11V2aShadowObserver,
        actor: str = "stage11-v2a-shadow",
    ) -> dict[str, Any]:
        kind = _source_kind(source_data_kind)
        if not isinstance(observer, Stage11V2aShadowObserver):
            raise TypeError("observer must be Stage11V2aShadowObserver")

        with self.store.lock:
            job = self._job(job_id)
            if job["state"] != OBSERVABLE_JOB_STATE:
                raise JobApiError(
                    "stage11_shadow_job_not_observable",
                    "Stage 11 shadow handoff requires an AWAITING_REVIEW job.",
                    http_status=409,
                    details={"state": job["state"]},
                )
            attempt = self._current_attempt(job)
            attempt_id = job["currentAttemptId"]
            captures: list[dict[str, Any]] = []
            candidate_ids: list[str] = []
            for raw_page_number in attempt["targetPages"]:
                page_number = int(raw_page_number)
                page = self._page(job, page_number)
                if page["contentType"] != "image/png":
                    raise JobApiError(
                        "stage11_shadow_source_media_type_not_supported",
                        "Stage 11 shadow handoff currently accepts PNG source pages only.",
                        http_status=409,
                        details={"pageNumber": page_number, "contentType": page["contentType"]},
                    )
                if page.get("reviewDecision") is not None or page.get("selectedArtifactId") is not None:
                    raise JobApiError(
                        "stage11_shadow_review_already_started",
                        "Stage 11 shadow observation must run before any review selection.",
                        http_status=409,
                        details={"pageNumber": page_number},
                    )
                candidate_id = page.get("currentCandidateArtifactId")
                report_id = page.get("currentSafetyReportArtifactId")
                if not candidate_id or not report_id:
                    raise JobApiError(
                        "stage11_shadow_primary_not_ready",
                        "Primary candidate and safety report must exist before shadow observation.",
                        http_status=409,
                        details={"pageNumber": page_number},
                    )
                source_id = page["sourceArtifactId"]
                captures.append({
                    "pageNumber": page_number,
                    "sourceArtifactId": source_id,
                    "sourceBytes": self._artifact_bytes(self._artifact(job_id, source_id)),
                    "primaryCandidateArtifactId": candidate_id,
                    "primaryCandidateBytes": self._artifact_bytes(self._artifact(job_id, candidate_id)),
                    "safetyReportArtifactId": report_id,
                })
                candidate_ids.append(candidate_id)
            run_key = hashlib.sha256(
                "|".join([job_id, attempt_id, kind, EXPECTED_PACKAGE_SHA256, *candidate_ids]).encode("utf-8")
            ).hexdigest()
            for event in job.get("audit", []):
                if event.get("eventType") == "STAGE11_V2A_SHADOW_JOB_OBSERVED" and (event.get("details") or {}).get("shadowRunKey") == run_key:
                    reused = dict(event["details"])
                    reused["reused"] = True
                    return reused

        staged: list[dict[str, Any]] = []
        for captured in captures:
            request_id = f"shadow:{job_id}:{attempt_id}:{captured['pageNumber']}"
            _require(len(request_id) <= 128, "derived shadow requestId exceeds staging limit")
            shadow_bytes, observation = observer.observe(
                captured["sourceBytes"],
                captured["primaryCandidateBytes"],
                request_id=request_id,
                source_data_kind=kind,
            )
            observation.update({
                "jobId": job_id,
                "attemptId": attempt_id,
                "pageNumber": captured["pageNumber"],
                "sourceArtifactId": captured["sourceArtifactId"],
                "primaryCandidateArtifactId": captured["primaryCandidateArtifactId"],
                "primarySafetyReportArtifactId": captured["safetyReportArtifactId"],
            })
            evidence_bytes = _canonical_json_bytes(observation)
            staged.append({
                **captured,
                "shadowBytes": shadow_bytes,
                "shadowArtifactId": _artifact_id(shadow_bytes),
                "observation": observation,
                "evidenceBytes": evidence_bytes,
                "evidenceArtifactId": _artifact_id(evidence_bytes),
            })

        with self.store.lock:
            job = self._job(job_id)
            if job["state"] != OBSERVABLE_JOB_STATE or job["currentAttemptId"] != attempt_id:
                raise JobApiError(
                    "stage11_shadow_job_became_stale",
                    "The job changed while Stage 11 shadow observation was running.",
                    http_status=409,
                )
            for item in staged:
                page = self._page(job, item["pageNumber"])
                unchanged = (
                    page["sourceArtifactId"] == item["sourceArtifactId"]
                    and page.get("currentCandidateArtifactId") == item["primaryCandidateArtifactId"]
                    and page.get("currentSafetyReportArtifactId") == item["safetyReportArtifactId"]
                    and page.get("reviewDecision") is None
                    and page.get("selectedArtifactId") is None
                )
                if not unchanged:
                    raise JobApiError(
                        "stage11_shadow_page_became_stale",
                        "A page changed while Stage 11 shadow observation was running.",
                        http_status=409,
                        details={"pageNumber": item["pageNumber"]},
                    )

            event_pages: list[dict[str, Any]] = []
            for item in staged:
                self._store_artifact(
                    job,
                    artifact_id=item["shadowArtifactId"],
                    attempt_id=attempt_id,
                    page_number=item["pageNumber"],
                    role=SHADOW_CANDIDATE_ROLE,
                    name=f"page-{item['pageNumber']}.v2a-shadow.png",
                    media_type="image/png",
                    data=item["shadowBytes"],
                )
                self._store_artifact(
                    job,
                    artifact_id=item["evidenceArtifactId"],
                    attempt_id=attempt_id,
                    page_number=item["pageNumber"],
                    role=SHADOW_EVIDENCE_ROLE,
                    name=f"page-{item['pageNumber']}.v2a-shadow-evidence.json",
                    media_type="application/json",
                    data=item["evidenceBytes"],
                )
                event_pages.append({
                    "pageNumber": item["pageNumber"],
                    "sourceArtifactId": item["sourceArtifactId"],
                    "primaryCandidateArtifactId": item["primaryCandidateArtifactId"],
                    "primarySafetyReportArtifactId": item["safetyReportArtifactId"],
                    "shadowCandidateArtifactId": item["shadowArtifactId"],
                    "shadowEvidenceArtifactId": item["evidenceArtifactId"],
                    "meanAbsDiff": item["observation"]["comparison"]["meanAbsDiff"],
                    "maxAbsDiff": item["observation"]["comparison"]["maxAbsDiff"],
                    "changedPixelFraction": item["observation"]["comparison"]["changedPixelFraction"],
                })
            details = {
                "shadowRunKey": run_key,
                "sourceDataKind": kind,
                "packageSha256": EXPECTED_PACKAGE_SHA256,
                "attemptId": attempt_id,
                "pageCount": len(event_pages),
                "pages": event_pages,
                "primaryCandidateUnchanged": True,
                "primarySafetyReportsUnchanged": True,
                "reviewDecisionsUnchanged": True,
                "selectedArtifactsUnchanged": True,
                "shadowSelectable": False,
                "qualityDecisionMade": False,
                "networkRouteRegistered": False,
                "productionInferenceAuthorized": False,
                "stage12EntryAuthorized": False,
                "reused": False,
            }
            self._append_event(job, "STAGE11_V2A_SHADOW_JOB_OBSERVED", actor, details, attempt_id)
            return dict(details)


def validate_shadow_job_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == JOB_EVIDENCE_TYPE, "shadow job evidence type mismatch")
    _require(payload.get("schemaVersion") == JOB_EVIDENCE_SCHEMA_VERSION, "shadow job evidence schema mismatch")
    _require(payload.get("status") == "completed", "shadow job evidence must be completed")
    _require(payload.get("contractId") == CONTRACT_ID, "shadow job evidence contract mismatch")
    _require(payload.get("packageSha256") == EXPECTED_PACKAGE_SHA256, "shadow job evidence package mismatch")
    _require(int(payload.get("packageSizeBytes", 0)) == EXPECTED_PACKAGE_SIZE_BYTES, "shadow job evidence package size mismatch")
    _require(payload.get("sourceDataKind") == "synthetic_only", "acceptance evidence must be synthetic-only")
    _require(payload.get("exactFrozenPackageExecuted") is True, "exact frozen package execution missing")
    _require(payload.get("existingJobServiceIntegrationCoveredByTests") is True, "job-service integration test coverage missing")
    _require(payload.get("networkRouteRegistered") is False, "shadow job evidence cannot register a route")
    _require(payload.get("existingHttpApiModified") is False, "shadow job evidence cannot modify HTTP API")
    _require(payload.get("realUserDataUsed") is False, "real-user data is forbidden")
    validate_shadow_observation(payload.get("observation") or {})
    invariants = payload.get("selectionInvariants") or {}
    for key in (
        "primaryCandidateUnchanged", "primarySafetyReportUnchanged",
        "reviewDecisionUnchanged", "selectedArtifactUnchanged",
    ):
        _require(invariants.get(key) is True, f"shadow selection invariant missing: {key}")
    _require(invariants.get("shadowSelectable") is False, "shadow artifact cannot be selectable")
    _require(payload.get("authorization") == shadow_job_handoff_contract()["authorization"], "shadow job evidence authorization mismatch")
    _require(payload.get("contract") == shadow_job_handoff_contract(), "shadow job evidence contract snapshot mismatch")
    return {
        "status": "pass",
        "shadowJobHandoffValidated": True,
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
    }
