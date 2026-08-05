from __future__ import annotations

import json
import sqlite3
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

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

    @staticmethod
    def _valid_page() -> bytes:
        image = np.full((500, 800), 248, np.uint8)
        for base in (80, 250):
            for line in range(5):
                cv2.line(image, (50, base + line * 12), (750, base + line * 12), 20, 1)
        for line in range(6):
            cv2.line(image, (50, 390 + line * 14), (750, 390 + line * 14), 30, 1)
        ok, payload = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        assert ok
        return bytes(payload)

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

    def test_terminal_snapshot_does_not_retain_internal_lease_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(directory)
            created, _ = service.create_job(
                [UploadedPage("page.png", "image/png", self._valid_page())],
                idempotency_key="terminal-lease-normalization-0001",
                actor="client",
            )
            job_id = created["jobId"]
            self.assertEqual(
                job_id,
                service.run_pending(actor="worker", lease_owner="worker-a"),
            )
            self.assertNotIn(service.get_job(job_id)["state"], {
                "UPLOADED", "ANALYZING", "READY_FOR_PROCESSING",
                "PROCESSING", "COMPARING", "VALIDATING",
            })
            self.assertFalse(store.jobs[job_id].get("processingClaimed", False))
            self.assertNotIn("processingLease", store.jobs[job_id])
            database = sqlite3.connect(Path(directory) / "store.sqlite3")
            payload = json.loads(
                database.execute(
                    "SELECT payload_json FROM jobs WHERE job_id = ?", (job_id,)
                ).fetchone()[0]
            )
            database.close()
            self.assertFalse(payload.get("processingClaimed", False))
            self.assertNotIn("processingLease", payload)
            store.close()
