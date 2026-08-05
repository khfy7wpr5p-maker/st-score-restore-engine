from __future__ import annotations

import tempfile
import unittest

from st_score_restore.durable_job_store import SQLiteJobStore, StaleWorkClaimError
from st_score_restore.job_api_types import JobApiConfig, UploadedPage
from st_score_restore.job_service import RestorationJobService


class WorkerFencingGuardTests(unittest.TestCase):
    def _service(self, directory: str) -> tuple[SQLiteJobStore, RestorationJobService]:
        store = SQLiteJobStore(directory, worker_lease_seconds=30)
        config = JobApiConfig(
            client_api_key="client-key-0123456789abcdef",
            reviewer_api_key="reviewer-key-0123456789abcdef",
            retention_seconds=3_600,
        )
        return store, RestorationJobService(store, config)

    def test_direct_durable_process_job_requires_claim_context(self):
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(directory)
            created, _ = service.create_job(
                [UploadedPage("page.png", "image/png", b"opaque-uninspected-bytes")],
                idempotency_key="direct-process-guard-0001",
                actor="client",
            )
            before = service.get_audit(created["jobId"])
            with self.assertRaises(StaleWorkClaimError) as context:
                service.process_job(created["jobId"], actor="unclaimed-worker")
            self.assertEqual("stale_work_claim", context.exception.code)
            after = service.get_audit(created["jobId"])
            self.assertEqual(before, after)
            self.assertEqual("UPLOADED", service.get_job(created["jobId"])["state"])
            store.close()

    def test_claim_context_for_one_job_cannot_process_another(self):
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(directory)
            first, _ = service.create_job(
                [UploadedPage("a.png", "image/png", b"first-opaque-bytes")],
                idempotency_key="wrong-job-guard-0001",
                actor="client",
            )
            second, _ = service.create_job(
                [UploadedPage("b.png", "image/png", b"second-opaque-bytes")],
                idempotency_key="wrong-job-guard-0002",
                actor="client",
            )
            claim = store.claim_next_job(
                now=service._now(),
                lease_owner="worker-a",
                lease_seconds=30,
            )
            self.assertIsNotNone(claim)
            other_job_id = (
                second["jobId"] if claim.job_id == first["jobId"] else first["jobId"]
            )
            with store.processing_claim(claim, now_provider=service._now):
                with self.assertRaises(StaleWorkClaimError):
                    service.process_job(other_job_id, actor="worker-a")
            self.assertEqual("UPLOADED", service.get_job(other_job_id)["state"])
            store.release_claim(claim)
            store.close()
