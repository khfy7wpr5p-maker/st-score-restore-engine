from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from st_score_restore.durable_job_store import DurableStoreError, SQLiteJobStore
from st_score_restore.job_api_types import JobApiConfig, UploadedPage
from st_score_restore.job_service import RestorationJobService

CLIENT_KEY = "client-key-0123456789abcdef"
REVIEWER_KEY = "reviewer-key-0123456789abcdef"


class FakeClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        value = self.value
        self.value += timedelta(seconds=1)
        return value


def make_service(directory: str):
    store = SQLiteJobStore(directory, worker_lease_seconds=30)
    config = JobApiConfig(
        client_api_key=CLIENT_KEY,
        reviewer_api_key=REVIEWER_KEY,
        retention_seconds=3_600,
    )
    service = RestorationJobService(store, config, clock=FakeClock())
    return store, service


def create_job(service: RestorationJobService, key: str) -> dict:
    job, _ = service.create_job(
        [UploadedPage("page.png", "image/png", b"immutable-test-bytes")],
        idempotency_key=key,
        actor="client",
    )
    return job


class DurableStoreHardeningTests(unittest.TestCase):
    def test_missing_audit_history_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store, service = make_service(directory)
            job = create_job(service, "missing-audit-0001")
            store.close()
            database = sqlite3.connect(Path(directory) / "store.sqlite3")
            payload = json.loads(
                database.execute(
                    "SELECT payload_json FROM jobs WHERE job_id = ?",
                    (job["jobId"],),
                ).fetchone()[0]
            )
            payload["audit"] = []
            database.execute(
                "UPDATE jobs SET payload_json = ? WHERE job_id = ?",
                (json.dumps(payload, sort_keys=True, separators=(",", ":")), job["jobId"]),
            )
            database.commit()
            database.close()
            with self.assertRaises(DurableStoreError) as context:
                SQLiteJobStore(directory)
            self.assertEqual("audit_history_missing", context.exception.code)

    def test_artifact_payload_identity_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store, service = make_service(directory)
            job = create_job(service, "artifact-identity-0001")
            artifact_id = job["pages"][0]["sourceArtifactId"]
            store.close()
            database = sqlite3.connect(Path(directory) / "store.sqlite3")
            payload = json.loads(
                database.execute(
                    "SELECT payload_json FROM artifacts WHERE job_id = ? AND artifact_id = ?",
                    (job["jobId"], artifact_id),
                ).fetchone()[0]
            )
            payload["jobId"] = "job-tampered"
            database.execute(
                "UPDATE artifacts SET payload_json = ? WHERE job_id = ? AND artifact_id = ?",
                (
                    json.dumps(payload, sort_keys=True, separators=(",", ":")),
                    job["jobId"],
                    artifact_id,
                ),
            )
            database.commit()
            database.close()
            with self.assertRaises(DurableStoreError) as context:
                SQLiteJobStore(directory)
            self.assertEqual("artifact_payload_identity_mismatch", context.exception.code)

    def test_missing_queue_record_for_queued_job_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store, service = make_service(directory)
            job = create_job(service, "queue-missing-0001")
            store.close()
            database = sqlite3.connect(Path(directory) / "store.sqlite3")
            database.execute("DELETE FROM work_queue WHERE job_id = ?", (job["jobId"],))
            database.commit()
            database.close()
            with self.assertRaises(DurableStoreError) as context:
                SQLiteJobStore(directory)
            self.assertEqual("queue_record_missing", context.exception.code)

    def test_post_commit_blob_cleanup_failure_is_deferred_and_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            store, service = make_service(directory)
            job = create_job(service, "cleanup-deferred-0001")
            digest = job["pages"][0]["sourceArtifactId"].split(":", 1)[1]
            blob_path = Path(directory) / "blobs" / digest[:2] / digest
            with patch.object(
                store.blob_store,
                "delete",
                side_effect=DurableStoreError(
                    "blob_deletion_failed", "simulated deletion failure"
                ),
            ):
                expired = service.expire_job(job["jobId"])
            self.assertEqual("EXPIRED", expired["state"])
            self.assertIsNotNone(store.last_cleanup_error)
            self.assertEqual("blob_deletion_failed", store.last_cleanup_error.code)
            self.assertTrue(blob_path.exists())
            store.close()
            reopened = SQLiteJobStore(directory)
            self.assertFalse(blob_path.exists())
            self.assertEqual(
                0,
                reopened._connection.execute(
                    "SELECT COUNT(*) FROM pending_blob_deletions"
                ).fetchone()[0],
            )
            reopened.close()

    def test_malformed_schema_version_has_stable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteJobStore(directory)
            store.close()
            database = sqlite3.connect(Path(directory) / "store.sqlite3")
            database.execute(
                "UPDATE store_meta SET value = 'invalid' WHERE key = 'schema_version'"
            )
            database.commit()
            database.close()
            with self.assertRaises(DurableStoreError) as context:
                SQLiteJobStore(directory)
            self.assertEqual("invalid_store_schema_version", context.exception.code)


if __name__ == "__main__":
    unittest.main()
