import hashlib
import json
import unittest
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

from st_score_restore.job_api_types import JobApiConfig, JobApiError, UploadedPage
from st_score_restore.job_store import InMemoryJobStore
from st_score_restore.stage11_v2a_shadow_handoff import (
    SHADOW_CANDIDATE_ROLE,
    SHADOW_EVIDENCE_ROLE,
    Stage11V2aShadowHandoffError,
    Stage11V2aShadowObserver,
    validate_shadow_job_evidence,
)
from st_score_restore.stage11_v2a_shadow_job_service import (
    Stage11V2aShadowRestorationJobService,
)
from st_score_restore.stage11_v2a_staging_api import (
    EXPECTED_PACKAGE_SHA256,
    decode_grayscale_png,
    encode_grayscale_png,
)
from st_score_restore.stage11_v2a_shadow_current_truth import (
    Stage11V2aShadowCurrentTruthError,
    validate_stage11_v2a_shadow_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-shadow-job-handoff-evidence.v1.json"
TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_SHADOW_CURRENT_TRUTH.json"


class _Clock:
    def __call__(self):
        return datetime(2026, 9, 8, 12, 0, tzinfo=UTC)


class _Ids:
    def __init__(self):
        self.value = 0

    def __call__(self, prefix: str) -> str:
        self.value += 1
        return f"{prefix}_shadow_{self.value:04d}"


def _synthetic_png(height: int = 180, width: int = 260) -> bytes:
    page = np.full((height, width), 255, dtype=np.uint8)
    for base in (35, 95):
        for offset in range(0, 25, 6):
            page[base + offset : base + offset + 1, 15 : width - 15] = 0
    cv2.circle(page, (80, 58), 5, 0, -1)
    cv2.line(page, (85, 58), (85, 37), 0, 1)
    cv2.circle(page, (145, 118), 5, 0, -1)
    cv2.line(page, (150, 118), (150, 96), 0, 1)
    ok, encoded = cv2.imencode(".png", page, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    assert ok
    return encoded.tobytes()


def _identity_handle(body, metadata):
    source = decode_grayscale_png(body)
    response = encode_grayscale_png(source.astype(np.float32) / 255.0)
    return response, {
        "requestId": metadata["requestId"],
        "sourceDataKind": metadata["sourceDataKind"],
        "packageSha256": EXPECTED_PACKAGE_SHA256,
        "tileCount": 1,
        "requestSha256": hashlib.sha256(body).hexdigest(),
        "responseSha256": hashlib.sha256(response).hexdigest(),
        "networkRouteRegistered": False,
        "existingHttpApiModified": False,
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
    }


def _service():
    config = JobApiConfig(
        client_api_key="client-key-shadow-0123456789",
        reviewer_api_key="review-key-shadow-0123456789",
        retention_seconds=3600,
    )
    return Stage11V2aShadowRestorationJobService(
        InMemoryJobStore(),
        config,
        clock=_Clock(),
        id_factory=_Ids(),
    )


def _create_job(service):
    created, reused = service.create_job(
        [UploadedPage("synthetic-shadow.png", "image/png", _synthetic_png())],
        idempotency_key="shadow-job-0001",
        actor="synthetic-test",
        restoration_config={
            "orientation_enabled": False,
            "deskew_enabled": False,
            "perspective_enabled": False,
            "crop_enabled": False,
            "illumination_enabled": False,
            "denoise_enabled": False,
            "contrast_enabled": False,
            "binarization_profile": "none",
        },
    )
    assert not reused
    return created["jobId"]


class Stage11V2aShadowHandoffTests(unittest.TestCase):
    def test_observer_rejects_real_user_kind(self):
        source = _synthetic_png(40, 60)
        observer = Stage11V2aShadowObserver(_identity_handle)
        with self.assertRaises(Stage11V2aShadowHandoffError):
            observer.observe(
                source,
                source,
                request_id="shadow:reject-real-user",
                source_data_kind="real_user",
            )

    def test_observer_is_observational_only(self):
        source = _synthetic_png(40, 60)
        observer = Stage11V2aShadowObserver(_identity_handle)
        response, evidence = observer.observe(
            source,
            source,
            request_id="shadow:synthetic-observer",
            source_data_kind="synthetic_only",
        )
        self.assertEqual(decode_grayscale_png(response).shape, [40, 60])
        self.assertEqual(0.0, evidence["comparison"]["meanAbsDiff"])
        self.assertFalse(evidence["comparison"]["qualityDecisionMade"])
        self.assertFalse(evidence["safety"]["shadowSelectable"])
        self.assertFalse(evidence["authorization"]["productionInferenceAuthorized"])

    def test_shadow_requires_primary_job_to_finish_first(self):
        service = _service()
        job_id = _create_job(service)
        with self.assertRaises(JobApiError) as caught:
            service.run_stage11_v2a_shadow_job(
                job_id,
                source_data_kind="synthetic_only",
                observer=Stage11V2aShadowObserver(_identity_handle),
            )
        self.assertEqual("stage11_shadow_job_not_observable", caught.exception.code)

    def test_shadow_job_does_not_replace_primary_state(self):
        service = _service()
        job_id = _create_job(service)
        service.run_pending(actor="primary-worker")
        self.assertEqual("AWAITING_REVIEW", service.get_job(job_id)["state"])
        with service.store.lock:
            page = service.store.jobs[job_id]["pages"][0]
            before = {
                "candidate": page["currentCandidateArtifactId"],
                "safety": page["currentSafetyReportArtifactId"],
                "review": page["reviewDecision"],
                "selected": page["selectedArtifactId"],
            }

        result = service.run_stage11_v2a_shadow_job(
            job_id,
            source_data_kind="synthetic_only",
            observer=Stage11V2aShadowObserver(_identity_handle),
        )
        self.assertFalse(result["shadowSelectable"])
        self.assertFalse(result["qualityDecisionMade"])
        self.assertFalse(result["productionInferenceAuthorized"])
        self.assertEqual(1, result["pageCount"])

        with service.store.lock:
            page = service.store.jobs[job_id]["pages"][0]
            after = {
                "candidate": page["currentCandidateArtifactId"],
                "safety": page["currentSafetyReportArtifactId"],
                "review": page["reviewDecision"],
                "selected": page["selectedArtifactId"],
            }
            self.assertEqual(before, after)
            roles = {
                reference["role"]
                for artifact in service.store.artifacts.values()
                for reference in artifact["references"]
            }
            self.assertIn(SHADOW_CANDIDATE_ROLE, roles)
            self.assertIn(SHADOW_EVIDENCE_ROLE, roles)
            events = [
                event
                for event in service.store.jobs[job_id]["audit"]
                if event["eventType"] == "STAGE11_V2A_SHADOW_JOB_OBSERVED"
            ]
            self.assertEqual(1, len(events))

    def test_shadow_job_is_idempotent_for_same_primary_attempt(self):
        service = _service()
        job_id = _create_job(service)
        service.run_pending(actor="primary-worker")
        observer = Stage11V2aShadowObserver(_identity_handle)
        first = service.run_stage11_v2a_shadow_job(
            job_id, source_data_kind="synthetic_only", observer=observer
        )
        second = service.run_stage11_v2a_shadow_job(
            job_id, source_data_kind="synthetic_only", observer=observer
        )
        self.assertFalse(first["reused"])
        self.assertTrue(second["reused"])
        with service.store.lock:
            events = [
                event
                for event in service.store.jobs[job_id]["audit"]
                if event["eventType"] == "STAGE11_V2A_SHADOW_JOB_OBSERVED"
            ]
            self.assertEqual(1, len(events))

    def test_committed_exact_package_evidence_passes(self):
        payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        result = validate_shadow_job_evidence(payload)
        self.assertTrue(result["shadowJobHandoffValidated"])
        self.assertFalse(result["productionInferenceAuthorized"])

    def test_shadow_current_truth_passes_and_stage12_stays_closed(self):
        payload = json.loads(TRUTH.read_text(encoding="utf-8"))
        result = validate_stage11_v2a_shadow_current_truth(payload)
        self.assertTrue(result["shadowJobHandoffValidated"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_truth_cannot_enable_real_user_rollout(self):
        payload = json.loads(TRUTH.read_text(encoding="utf-8"))
        payload["authorization"]["realUserRolloutAuthorized"] = True
        with self.assertRaises(Stage11V2aShadowCurrentTruthError):
            validate_stage11_v2a_shadow_current_truth(payload)


if __name__ == "__main__":
    unittest.main()
