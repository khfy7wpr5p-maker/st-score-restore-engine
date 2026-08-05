from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import tempfile
import threading
import unittest

import cv2
import numpy as np

from st_score_restore.durable_job_store import DurableStoreError, SQLiteJobStore
from st_score_restore.job_api_types import JobApiConfig, UploadedPage
from st_score_restore.job_service import RestorationJobService

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


def synthetic_page(marker: str = "10") -> bytes:
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
    cv2.putText(
        image,
        marker,
        (600, tab_base + 92),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        0,
        1,
        cv2.LINE_8,
    )
    return encode_png(image)


def make_config() -> JobApiConfig:
    return JobApiConfig(
        client_api_key=CLIENT_KEY,
        reviewer_api_key=REVIEWER_KEY,
        retention_seconds=3_600,
    )


def make_service(directory: str, clock: FakeClock, ids: IdFactory):
    store = SQLiteJobStore(directory, worker_lease_seconds=30)
    service = RestorationJobService(store, make_config(), clock=clock, id_factory=ids)
    return store, service


def verify_audit_chain(events: list[dict]) -> None:
    previous = None
    for expected_sequence, event in enumerate(events, 1):
        assert event["sequence"] == expected_sequence
        assert event["previousEventHash"] == previous
        unsigned = {key: value for key, value in event.items() if key != "eventHash"}
        canonical = json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        assert hashlib.sha256(canonical).hexdigest() == event["eventHash"]
        previous = event["eventHash"]


class DurableJobStoreTests(unittest.TestCase):
    def test_service_restart_preserves_workflow_idempotency_review_consent_and_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = FakeClock()
            ids = IdFactory()
            page = UploadedPage("page.png", "image/png", synthetic_page())

            first_store, first_service = make_service(directory, clock, ids)
            created, replayed = first_service.create_job(
                [page], idempotency_key="durable-0001", actor="client"
            )
            self.assertFalse(replayed)
            job_id = created["jobId"]
            first_store.close()

            second_store, second_service = make_service(directory, clock, ids)
            replay, replayed = second_service.create_job(
                [page], idempotency_key="durable-0001", actor="client"
            )
            self.assertTrue(replayed)
            self.assertEqual(job_id, replay["jobId"])
            self.assertEqual(job_id, second_service.run_pending(actor="worker-a"))
            awaiting = second_service.get_job(job_id)
            self.assertEqual("AWAITING_REVIEW", awaiting["state"])
            second_service.review_job(
                job_id,
                [{"pageNumber": 1, "action": "reject"}],
                reviewer_id="teacher-1",
            )
            second_service.record_training_consent(
                job_id,
                consent="granted",
                reviewer_id="teacher-1",
                scope="source",
                terms_version="2026-08",
            )
            retry = second_service.create_attempt(
                job_id,
                target_pages=[1],
                actor="teacher-1",
                reason="restart-regression",
            )
            self.assertEqual("READY_FOR_PROCESSING", retry["state"])
            second_store.close()

            third_store, third_service = make_service(directory, clock, ids)
            restored = third_service.get_job(job_id)
            self.assertEqual(2, len(restored["attempts"]))
            self.assertEqual("granted", restored["trainingConsent"]["consent"])
            self.assertEqual(job_id, third_service.run_pending(actor="worker-b"))
            self.assertEqual("AWAITING_REVIEW", third_service.get_job(job_id)["state"])
            verify_audit_chain(third_service.get_audit(job_id)["events"])
            third_store.close()

    def test_transaction_exception_rolls_back_all_mutations(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = FakeClock()
            ids = IdFactory()
            store, service = make_service(directory, clock, ids)
            created, _ = service.create_job(
                [UploadedPage("page.png", "image/png", synthetic_page())],
                idempotency_key="rollback-0001",
                actor="client",
            )
            job_id = created["jobId"]
            with self.assertRaises(RuntimeError):
                with store.lock:
                    store.jobs[job_id]["state"] = "FAILED"
                    store.idempotency.clear()
                    raise RuntimeError("abort")
            self.assertEqual("UPLOADED", store.jobs[job_id]["state"])
            self.assertTrue(store.idempotency)
            store.close()
            reopened = SQLiteJobStore(directory)
            self.assertEqual("UPLOADED", reopened.jobs[job_id]["state"])
            self.assertTrue(reopened.idempotency)
            reopened.close()

    def test_active_lease_cannot_be_stolen_and_expired_lease_is_reclaimed(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = FakeClock()
            ids = IdFactory()
            first, service = make_service(directory, clock, ids)
            created, _ = service.create_job(
                [UploadedPage("page.png", "image/png", synthetic_page())],
                idempotency_key="lease-0001",
                actor="client",
            )
            second = SQLiteJobStore(directory, worker_lease_seconds=30)
            now = datetime.now(UTC)
            claim = first.claim_next_job(
                now=now, lease_owner="worker-a", lease_seconds=30
            )
            self.assertIsNotNone(claim)
            self.assertEqual(created["jobId"], claim.job_id)
            self.assertIsNone(
                second.claim_next_job(
                    now=now + timedelta(seconds=10),
                    lease_owner="worker-b",
                    lease_seconds=30,
                )
            )
            recovered = second.claim_next_job(
                now=now + timedelta(seconds=31),
                lease_owner="worker-b",
                lease_seconds=30,
            )
            self.assertIsNotNone(recovered)
            self.assertEqual(created["jobId"], recovered.job_id)
            self.assertNotEqual(claim.lease_token, recovered.lease_token)
            first.close()
            second.close()

    def test_two_store_instances_cannot_claim_the_same_active_job(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = FakeClock()
            ids = IdFactory()
            seed, service = make_service(directory, clock, ids)
            service.create_job(
                [UploadedPage("page.png", "image/png", synthetic_page())],
                idempotency_key="claim-race-0001",
                actor="client",
            )
            seed.close()
            stores = [SQLiteJobStore(directory), SQLiteJobStore(directory)]
            results = []
            barrier = threading.Barrier(2)

            def claim(store, owner):
                barrier.wait()
                results.append(
                    store.claim_next_job(
                        now=datetime.now(UTC),
                        lease_owner=owner,
                        lease_seconds=60,
                    )
                )

            threads = [
                threading.Thread(target=claim, args=(stores[0], "worker-a")),
                threading.Thread(target=claim, args=(stores[1], "worker-b")),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(1, sum(result is not None for result in results))
            for store in stores:
                store.close()

    def test_corrupt_blob_fails_closed_on_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = FakeClock()
            ids = IdFactory()
            store, service = make_service(directory, clock, ids)
            created, _ = service.create_job(
                [UploadedPage("page.png", "image/png", synthetic_page())],
                idempotency_key="blob-corrupt-0001",
                actor="client",
            )
            artifact_id = created["pages"][0]["sourceArtifactId"]
            digest = artifact_id.split(":", 1)[1]
            blob_path = Path(directory) / "blobs" / digest[:2] / digest
            store.close()
            blob_path.write_bytes(b"tampered")
            with self.assertRaises(DurableStoreError) as context:
                SQLiteJobStore(directory)
            self.assertEqual("artifact_blob_corrupt", context.exception.code)

    def test_corrupt_audit_hash_fails_closed_on_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = FakeClock()
            ids = IdFactory()
            store, service = make_service(directory, clock, ids)
            created, _ = service.create_job(
                [UploadedPage("page.png", "image/png", synthetic_page())],
                idempotency_key="audit-corrupt-0001",
                actor="client",
            )
            store.close()
            database = sqlite3.connect(Path(directory) / "store.sqlite3")
            payload = json.loads(
                database.execute(
                    "SELECT payload_json FROM jobs WHERE job_id = ?",
                    (created["jobId"],),
                ).fetchone()[0]
            )
            payload["audit"][0]["details"]["tampered"] = True
            database.execute(
                "UPDATE jobs SET payload_json = ? WHERE job_id = ?",
                (
                    json.dumps(payload, sort_keys=True, separators=(",", ":")),
                    created["jobId"],
                ),
            )
            database.commit()
            database.close()
            with self.assertRaises(DurableStoreError) as context:
                SQLiteJobStore(directory)
            self.assertEqual("audit_hash_corrupt", context.exception.code)

    def test_expiry_removes_only_unreferenced_shared_blob(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = FakeClock()
            ids = IdFactory()
            store, service = make_service(directory, clock, ids)
            page = UploadedPage("page.png", "image/png", synthetic_page())
            first, _ = service.create_job(
                [page], idempotency_key="shared-blob-0001", actor="client"
            )
            second, _ = service.create_job(
                [page], idempotency_key="shared-blob-0002", actor="client"
            )
            first_id = first["pages"][0]["sourceArtifactId"]
            second_id = second["pages"][0]["sourceArtifactId"]
            self.assertEqual(first_id, second_id)
            digest = first_id.split(":", 1)[1]
            blob_path = Path(directory) / "blobs" / digest[:2] / digest
            self.assertTrue(blob_path.exists())
            service.expire_job(first["jobId"])
            self.assertTrue(blob_path.exists())
            _, remaining = service.get_artifact(
                second["jobId"],
                second_id,
                role="client",
                purpose="original",
                actor="client",
            )
            self.assertEqual(page.data, remaining)
            service.expire_job(second["jobId"])
            self.assertFalse(blob_path.exists())
            self.assertEqual("EXPIRED", service.get_job(first["jobId"])["state"])
            self.assertTrue(service.get_audit(first["jobId"])["events"])
            store.close()

    def test_failed_new_artifact_transaction_removes_uncommitted_blob(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteJobStore(directory)
            data = b"uncommitted"
            digest = hashlib.sha256(data).hexdigest()
            artifact_id = f"sha256:{digest}"
            blob_path = Path(directory) / "blobs" / digest[:2] / digest
            with self.assertRaises(sqlite3.IntegrityError):
                with store.lock:
                    job = {
                        "jobId": "job-new",
                        "state": "UPLOADED",
                        "createdAt": "2026-08-05T12:00:00Z",
                        "updatedAt": "2026-08-05T12:00:00Z",
                        "currentAttemptId": "attempt-new",
                        "audit": [],
                    }
                    store.append_event(
                        job,
                        event_type="JOB_CREATED",
                        occurred_at="2026-08-05T12:00:00Z",
                        actor="test",
                        details={},
                        attempt_id="attempt-new",
                    )
                    store.jobs["job-new"] = job
                    store.artifacts[("job-new", artifact_id)] = {
                        "artifactId": artifact_id,
                        "jobId": "job-new",
                        "byteSize": len(data),
                        "digest": digest,
                        "createdAt": "2026-08-05T12:00:00Z",
                        "deletedAt": None,
                        "references": [],
                        "data": data,
                    }
                    store.idempotency["bad-key"] = {
                        "jobId": "missing-job",
                        "requestDigest": "0" * 64,
                    }
            self.assertFalse(blob_path.exists())
            self.assertNotIn("job-new", store.jobs)
            store.close()

    def test_legacy_worker_claim_is_visible_across_store_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = FakeClock()
            ids = IdFactory()
            first, service = make_service(directory, clock, ids)
            created, _ = service.create_job(
                [UploadedPage("page.png", "image/png", synthetic_page())],
                idempotency_key="legacy-claim-0001",
                actor="client",
            )
            job_id = created["jobId"]
            with first.lock:
                first.jobs[job_id]["processingClaimed"] = True
            second = SQLiteJobStore(directory, worker_lease_seconds=30)
            self.assertTrue(second.jobs[job_id]["processingClaimed"])
            self.assertIsNone(
                second.claim_next_job(
                    now=datetime.now(UTC),
                    lease_owner="worker-b",
                    lease_seconds=30,
                )
            )
            second.close()
            first.close()

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits required")
    def test_local_database_blob_and_directories_use_private_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = FakeClock()
            ids = IdFactory()
            store, service = make_service(directory, clock, ids)
            created, _ = service.create_job(
                [UploadedPage("page.png", "image/png", synthetic_page())],
                idempotency_key="permissions-0001",
                actor="client",
            )
            digest = created["pages"][0]["sourceArtifactId"].split(":", 1)[1]
            blob_path = Path(directory) / "blobs" / digest[:2] / digest
            self.assertEqual(0o700, stat.S_IMODE(Path(directory).stat().st_mode))
            self.assertEqual(
                0o700,
                stat.S_IMODE((Path(directory) / "blobs").stat().st_mode),
            )
            self.assertEqual(0o600, stat.S_IMODE(store.database_path.stat().st_mode))
            self.assertEqual(0o600, stat.S_IMODE(blob_path.stat().st_mode))
            store.close()

    def test_unknown_store_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteJobStore(directory)
            store.close()
            database = sqlite3.connect(Path(directory) / "store.sqlite3")
            database.execute(
                "UPDATE store_meta SET value = '99' WHERE key = 'schema_version'"
            )
            database.commit()
            database.close()
            with self.assertRaises(DurableStoreError) as context:
                SQLiteJobStore(directory)
            self.assertEqual("unsupported_store_schema", context.exception.code)


if __name__ == "__main__":
    unittest.main()
