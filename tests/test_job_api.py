from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np

from st_score_restore.http_api import ApiV1
from st_score_restore.job_api_types import JobApiConfig, JobApiError, UploadedPage
from st_score_restore.job_service import RestorationJobService
from st_score_restore.job_store import InMemoryJobStore

CLIENT_KEY = "client-key-0123456789abcdef"
REVIEWER_KEY = "reviewer-key-0123456789abcdef"


class FakeClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(seconds=1)
        return current


class IdFactory:
    def __init__(self) -> None:
        self.value = 0

    def __call__(self, prefix: str) -> str:
        self.value += 1
        return f"{prefix}_{self.value:04d}"


def encode_png(image: np.ndarray) -> bytes:
    ok, payload = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    assert ok
    return bytes(payload)


def synthetic_page(marker: str) -> bytes:
    image = np.full((900, 1200), 248, np.uint8)
    for base in (120, 360):
        for line in range(5):
            cv2.line(image, (80, base + line * 16), (1120, base + line * 16), 20, 1)
        for x in (220, 420, 650, 900):
            cv2.circle(image, (x, base + 32), 6, 0, -1)
            cv2.line(image, (x + 6, base + 32), (x + 6, base - 4), 0, 2)
    tab_base = 650
    for line in range(6):
        cv2.line(image, (80, tab_base + line * 18), (1120, tab_base + line * 18), 30, 1)
    cv2.putText(image, "3", (280, tab_base + 58), cv2.FONT_HERSHEY_SIMPLEX, 0.55, 0, 1, cv2.LINE_8)
    cv2.putText(image, marker, (600, tab_base + 92), cv2.FONT_HERSHEY_SIMPLEX, 0.55, 0, 1, cv2.LINE_8)
    return encode_png(image)


def make_service(retention_seconds: int = 3600):
    config = JobApiConfig(client_api_key=CLIENT_KEY, reviewer_api_key=REVIEWER_KEY, retention_seconds=retention_seconds)
    clock = FakeClock()
    service = RestorationJobService(InMemoryJobStore(), config, clock=clock, id_factory=IdFactory())
    return service, config, clock


def page_bundle() -> list[UploadedPage]:
    return [
        UploadedPage("page-1.png", "image/png", synthetic_page("10")),
        UploadedPage("page-2.png", "image/png", synthetic_page("12")),
    ]


def verify_audit_chain(events: list[dict]) -> None:
    previous = None
    for expected_sequence, event in enumerate(events, 1):
        assert event["sequence"] == expected_sequence
        assert event["previousEventHash"] == previous
        unsigned = {key: value for key, value in event.items() if key != "eventHash"}
        canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        assert hashlib.sha256(canonical).hexdigest() == event["eventHash"]
        previous = event["eventHash"]


class JobServiceIntegrationTests(unittest.TestCase):
    def test_full_multi_page_review_export_retry_consent_and_cleanup(self):
        service, _, clock = make_service()
        pages = page_bundle()
        created, replay = service.create_job(pages, idempotency_key="upload-0001", actor="client-app")
        self.assertFalse(replay)
        job_id = created["jobId"]
        repeated, replay = service.create_job(pages, idempotency_key="upload-0001", actor="client-app")
        self.assertTrue(replay)
        self.assertEqual(job_id, repeated["jobId"])
        with self.assertRaises(JobApiError) as conflict:
            service.create_job([UploadedPage("changed.png", "image/png", synthetic_page("13"))], idempotency_key="upload-0001", actor="client-app")
        self.assertEqual("idempotency_conflict", conflict.exception.code)
        self.assertEqual(job_id, service.run_pending())
        awaiting = service.get_job(job_id)
        self.assertEqual("AWAITING_REVIEW", awaiting["state"])
        self.assertEqual(2, len(awaiting["pages"]))
        for page in awaiting["pages"]:
            self.assertIsNotNone(page["currentCandidateArtifactId"])
            self.assertIsNotNone(page["currentEvidenceBundleArtifactId"])
            self.assertIn(page["safetyReport"]["verdict"], {"pass", "review_required"})
        candidate_one = awaiting["pages"][0]["currentCandidateArtifactId"]
        candidate_two = awaiting["pages"][1]["currentCandidateArtifactId"]
        with self.assertRaises(JobApiError) as blocked:
            service.get_artifact(job_id, candidate_one, role="client", purpose=None, actor="client-app")
        self.assertEqual("artifact_access_forbidden", blocked.exception.code)
        _, preview = service.get_artifact(job_id, candidate_one, role="reviewer", purpose="review", actor="teacher-1")
        self.assertTrue(preview.startswith(b"\x89PNG"))
        completed = service.review_job(job_id, [
            {"pageNumber": 1, "action": "approve", "candidateArtifactId": candidate_one},
            {"pageNumber": 2, "action": "reject", "candidateArtifactId": candidate_two, "notes": "Use original page two."},
        ], reviewer_id="teacher-1")
        self.assertEqual("COMPLETED", completed["state"])
        self.assertEqual(candidate_one, completed["pages"][0]["selectedArtifactId"])
        self.assertEqual(completed["pages"][1]["sourceArtifactId"], completed["pages"][1]["selectedArtifactId"])
        self.assertIsNone(completed["trainingConsent"])
        _, approved_bytes = service.get_artifact(job_id, candidate_one, role="client", purpose=None, actor="client-app")
        self.assertTrue(approved_bytes.startswith(b"\x89PNG"))
        with self.assertRaises(JobApiError):
            service.get_artifact(job_id, candidate_two, role="client", purpose=None, actor="client-app")
        consented = service.record_training_consent(job_id, consent="granted", reviewer_id="teacher-1", scope="approved_derivatives", terms_version="2026-08")
        self.assertEqual("granted", consented["trainingConsent"]["consent"])
        self.assertFalse(consented["pages"][0]["reviewDecision"]["trainingLabelCreated"])
        event_count = len(service.get_audit(job_id)["events"])
        retry = service.create_attempt(job_id, target_pages=[2], actor="teacher-1", reason="stronger-lighting-profile")
        self.assertEqual("READY_FOR_PROCESSING", retry["state"])
        self.assertEqual(2, len(retry["attempts"]))
        self.assertIsNotNone(retry["pages"][0]["reviewDecision"])
        self.assertIsNone(retry["pages"][1]["reviewDecision"])
        self.assertIsNone(retry["pages"][1]["currentEvidenceBundleArtifactId"])
        service.run_pending()
        after_retry = service.get_job(job_id)
        self.assertEqual("AWAITING_REVIEW", after_retry["state"])
        self.assertGreater(len(service.get_audit(job_id)["events"]), event_count)
        service.review_job(job_id, [{"pageNumber": 2, "action": "reject"}], reviewer_id="teacher-1")
        audit = service.get_audit(job_id)
        verify_audit_chain(audit["events"])
        source_id = service.get_job(job_id)["pages"][0]["sourceArtifactId"]
        clock.value += timedelta(days=2)
        self.assertEqual([job_id], service.cleanup_expired())
        self.assertEqual("EXPIRED", service.get_job(job_id)["state"])
        with self.assertRaises(JobApiError) as expired:
            service.get_artifact(job_id, source_id, role="client", purpose=None, actor="client-app")
        self.assertEqual("artifact_expired", expired.exception.code)
        verify_audit_chain(service.get_audit(job_id)["events"])

    def test_identical_source_bytes_are_isolated_across_jobs(self):
        service, _, _ = make_service()
        page = page_bundle()[0]
        first, _ = service.create_job([page], idempotency_key="isolate-0001", actor="client-a")
        second, _ = service.create_job([page], idempotency_key="isolate-0002", actor="client-b")
        self.assertNotEqual(first["jobId"], second["jobId"])
        self.assertEqual(first["pages"][0]["sourceArtifactId"], second["pages"][0]["sourceArtifactId"])
        service.run_pending(); service.run_pending()
        self.assertEqual("AWAITING_REVIEW", service.get_job(first["jobId"])["state"])
        self.assertEqual("AWAITING_REVIEW", service.get_job(second["jobId"])["state"])

    def test_identical_candidate_bytes_require_explicit_original_purpose_before_approval(self):
        service, _, _ = make_service()
        page = page_bundle()[0]
        digest = hashlib.sha256(page.data).hexdigest()
        manifest = {"status": "candidate_ready", "sourceDigest": {"algorithm": "sha256", "value": digest}, "candidate": {"digest": {"algorithm": "sha256", "value": digest}, "teacherApproved": False}}
        with patch("st_score_restore.job_service_processing.restore_bytes", return_value=SimpleNamespace(output_bytes=page.data, manifest=manifest)):
            created, _ = service.create_job([page], idempotency_key="same-bytes-0001", actor="client")
            service.run_pending()
        current = service.get_job(created["jobId"])
        artifact_id = current["pages"][0]["currentCandidateArtifactId"]
        self.assertEqual(current["pages"][0]["sourceArtifactId"], artifact_id)
        with self.assertRaises(JobApiError):
            service.get_artifact(current["jobId"], artifact_id, role="client", purpose=None, actor="client")
        _, original = service.get_artifact(current["jobId"], artifact_id, role="client", purpose="original", actor="client")
        self.assertEqual(page.data, original)

    def test_cancel_and_retry_preserve_attempt_history(self):
        service, _, _ = make_service()
        created, _ = service.create_job([page_bundle()[0]], idempotency_key="cancel-0001", actor="client-app")
        job_id = created["jobId"]
        self.assertEqual("CANCELLED", service.cancel_job(job_id, actor="client-app")["state"])
        retried = service.create_attempt(job_id, target_pages=None, actor="teacher-1")
        self.assertEqual("READY_FOR_PROCESSING", retried["state"])
        self.assertEqual(2, len(retried["attempts"]))
        service.run_pending()
        self.assertEqual("AWAITING_REVIEW", service.get_job(job_id)["state"])

    def test_invalid_image_fails_without_losing_original(self):
        service, _, _ = make_service()
        created, _ = service.create_job([UploadedPage("bad.png", "image/png", b"not-a-real-png")], idempotency_key="broken-0001", actor="client-app")
        service.run_pending()
        failed = service.get_job(created["jobId"])
        self.assertEqual("FAILED", failed["state"])
        source_id = failed["pages"][0]["sourceArtifactId"]
        _, original = service.get_artifact(failed["jobId"], source_id, role="client", purpose=None, actor="client-app")
        self.assertEqual(b"not-a-real-png", original)


class HttpApiTests(unittest.TestCase):
    def setUp(self):
        self.service, self.config, _ = make_service()
        self.api = ApiV1(self.service, self.config)

    def test_authenticated_multipart_flow_and_access_policy(self):
        body, content_type = multipart_body([("page-1.png", "image/png", synthetic_page("10")), ("page-2.png", "image/png", synthetic_page("12"))])
        headers = {"Authorization": f"Bearer {CLIENT_KEY}", "Content-Type": content_type, "Idempotency-Key": "http-0001", "X-Actor-Id": "client-app"}
        created = self.api.handle("POST", "/api/v1/restoration-jobs", headers, body)
        self.assertEqual(202, created.status)
        job_id = json.loads(created.body)["jobId"]
        self.service.run_pending()
        status = self.api.handle("GET", f"/api/v1/restoration-jobs/{job_id}/status", {"X-Api-Key": CLIENT_KEY})
        self.assertEqual("AWAITING_REVIEW", json.loads(status.body)["state"])
        current = self.service.get_job(job_id)
        candidate_one = current["pages"][0]["currentCandidateArtifactId"]
        candidate_two = current["pages"][1]["currentCandidateArtifactId"]
        evidence_one = current["pages"][0]["currentEvidenceBundleArtifactId"]
        evidence_two = current["pages"][1]["currentEvidenceBundleArtifactId"]
        blocked_review = self.api.handle("POST", f"/api/v1/restoration-jobs/{job_id}/review", {"X-Api-Key": CLIENT_KEY, "Content-Type": "application/json"}, json.dumps({"decisions": []}).encode())
        self.assertEqual(403, blocked_review.status)
        preview = self.api.handle("GET", f"/api/v1/restoration-jobs/{job_id}/artifacts/{candidate_one}?purpose=review", {"X-Api-Key": REVIEWER_KEY, "X-Actor-Id": "teacher-1"})
        self.assertEqual(200, preview.status)
        final_before_review = self.api.handle("GET", f"/api/v1/restoration-jobs/{job_id}/artifacts/{candidate_one}", {"X-Api-Key": CLIENT_KEY})
        self.assertEqual(403, final_before_review.status)
        review = self.api.handle("POST", f"/api/v1/restoration-jobs/{job_id}/review", {"X-Api-Key": REVIEWER_KEY, "X-Actor-Id": "teacher-1", "Content-Type": "application/json"}, json.dumps({"decisions": [{"pageNumber": 1, "action": "approve", "candidateArtifactId": candidate_one, "evidenceBundleArtifactId": evidence_one}, {"pageNumber": 2, "action": "reject", "candidateArtifactId": candidate_two, "evidenceBundleArtifactId": evidence_two}]}).encode())
        self.assertEqual(200, review.status)
        self.assertEqual("COMPLETED", json.loads(review.body)["state"])
        self.assertEqual(200, self.api.handle("GET", f"/api/v1/restoration-jobs/{job_id}/artifacts/{candidate_one}", {"X-Api-Key": CLIENT_KEY}).status)
        replay = self.api.handle("POST", "/api/v1/restoration-jobs", headers, body)
        self.assertEqual(200, replay.status)
        self.assertEqual("true", replay.headers["Idempotency-Replayed"])
        conflicting_body, conflicting_type = multipart_body([("changed.png", "image/png", synthetic_page("13"))])
        conflict = self.api.handle("POST", "/api/v1/restoration-jobs", {**headers, "Content-Type": conflicting_type}, conflicting_body)
        self.assertEqual(409, conflict.status)

    def test_reviewer_identity_cannot_differ_from_authenticated_actor(self):
        response = self.api.handle("POST", "/api/v1/restoration-jobs/missing/review", {"X-Api-Key": REVIEWER_KEY, "X-Actor-Id": "teacher-1"}, json.dumps({"reviewerId": "teacher-2", "decisions": []}).encode())
        self.assertEqual(403, response.status)
        self.assertEqual("reviewer_identity_mismatch", json.loads(response.body)["error"]["code"])

    def test_malformed_request_shapes_fail_as_structured_errors(self):
        bad_review = self.api.handle("POST", "/api/v1/restoration-jobs/missing/review", {"X-Api-Key": REVIEWER_KEY, "X-Actor-Id": "teacher-1"}, json.dumps({"decisions": "not-an-array"}).encode())
        self.assertEqual(400, bad_review.status)
        self.assertEqual("invalid_review_decisions", json.loads(bad_review.body)["error"]["code"])
        bad_attempt = self.api.handle("POST", "/api/v1/restoration-jobs/missing/attempts", {"X-Api-Key": REVIEWER_KEY}, json.dumps({"targetPages": "1"}).encode())
        self.assertEqual(400, bad_attempt.status)
        self.assertEqual("invalid_target_pages", json.loads(bad_attempt.body)["error"]["code"])

    def test_authentication_is_required(self):
        self.assertEqual(401, self.api.handle("GET", "/api/v1/restoration-jobs/missing", {}).status)


def multipart_body(files: list[tuple[str, str, bytes]]) -> tuple[bytes, str]:
    boundary = "st-score-boundary-001"
    chunks: list[bytes] = []
    for filename, content_type, data in files:
        chunks.extend([f"--{boundary}\r\n".encode(), ('Content-Disposition: form-data; name="file"; ' f'filename="{filename}"\r\n').encode(), f"Content-Type: {content_type}\r\n\r\n".encode(), data, b"\r\n"])
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


if __name__ == "__main__":
    unittest.main()
