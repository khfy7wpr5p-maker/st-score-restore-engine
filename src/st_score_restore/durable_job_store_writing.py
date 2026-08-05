"""Transactional durable-state serialization and queue projection."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets
from typing import Any

from .durable_store_support import (
    DurableStoreError,
    dump_json,
    iso,
    validate_audit_chain,
)
from .job_store import ACTIVE_WORK_STATES


class DurableWritingMixin:
    def _flush_locked(self) -> None:
        self._validate_memory_state()
        previous_live_digests = {
            str(row["digest"])
            for row in self._connection.execute(
                "SELECT DISTINCT digest FROM artifacts WHERE data_present = 1"
            )
        }
        live_digests = self._write_live_blobs(previous_live_digests)
        existing_queue = {
            str(row["job_id"]): dict(row)
            for row in self._connection.execute("SELECT * FROM work_queue")
        }

        self._connection.execute("DELETE FROM work_queue")
        self._connection.execute("DELETE FROM artifacts")
        self._connection.execute("DELETE FROM idempotency")
        self._connection.execute("DELETE FROM jobs")
        self._insert_jobs()
        self._insert_artifacts()
        self._insert_idempotency()
        self._insert_queue(existing_queue)

        for digest in sorted(previous_live_digests - live_digests):
            self._connection.execute(
                "INSERT OR IGNORE INTO pending_blob_deletions(digest) VALUES(?)",
                (digest,),
            )

    def _validate_memory_state(self) -> None:
        for job_id, job in self.jobs.items():
            if job.get("jobId") != job_id:
                raise DurableStoreError(
                    "job_identity_mismatch",
                    "Job dictionary key does not match its payload identity.",
                    details={"jobId": job_id},
                )
            validate_audit_chain(job)
        for (job_id, artifact_id), artifact in self.artifacts.items():
            if job_id not in self.jobs:
                raise DurableStoreError(
                    "orphan_artifact_metadata",
                    "Artifact metadata references a missing job.",
                    details={"jobId": job_id, "artifactId": artifact_id},
                )
            digest = str(artifact.get("digest", ""))
            if artifact_id != f"sha256:{digest}":
                raise DurableStoreError(
                    "artifact_identity_mismatch",
                    "Artifact dictionary key does not match its digest.",
                    details={"artifactId": artifact_id},
                )

    def _write_live_blobs(self, previous_live_digests: set[str]) -> set[str]:
        live_digests: set[str] = set()
        for (_, artifact_id), artifact in self.artifacts.items():
            data = artifact.get("data")
            if data is None:
                continue
            if not isinstance(data, (bytes, bytearray)):
                raise DurableStoreError(
                    "invalid_artifact_bytes",
                    "Artifact data must be immutable bytes or None.",
                    details={"artifactId": artifact_id},
                )
            raw = bytes(data)
            digest = str(artifact["digest"])
            actual = hashlib.sha256(raw).hexdigest()
            if not hmac.compare_digest(actual, digest):
                raise DurableStoreError(
                    "artifact_digest_mismatch",
                    "Artifact bytes do not match the stored SHA-256 identity.",
                    details={"artifactId": artifact_id},
                )
            if int(artifact.get("byteSize", -1)) != len(raw):
                raise DurableStoreError(
                    "artifact_size_mismatch",
                    "Artifact byteSize does not match the stored bytes.",
                    details={"artifactId": artifact_id},
                )
            created = self.blob_store.write(digest, raw)
            if created or digest not in previous_live_digests:
                self._transaction_new_blobs.add(digest)
            live_digests.add(digest)
        return live_digests

    def _insert_jobs(self) -> None:
        for job_id, job in sorted(self.jobs.items()):
            self._connection.execute(
                "INSERT INTO jobs(job_id, payload_json, updated_at) VALUES(?, ?, ?)",
                (job_id, dump_json(job), str(job["updatedAt"])),
            )

    def _insert_artifacts(self) -> None:
        for (job_id, artifact_id), artifact in sorted(self.artifacts.items()):
            payload = {
                key: deepcopy(value)
                for key, value in artifact.items()
                if key != "data"
            }
            self._connection.execute(
                """
                INSERT INTO artifacts(
                    job_id, artifact_id, digest, byte_size, payload_json, data_present
                ) VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    artifact_id,
                    payload["digest"],
                    int(payload["byteSize"]),
                    dump_json(payload),
                    1 if artifact.get("data") is not None else 0,
                ),
            )

    def _insert_idempotency(self) -> None:
        for key_digest, record in sorted(self.idempotency.items()):
            self._connection.execute(
                """
                INSERT INTO idempotency(key_digest, job_id, request_digest)
                VALUES(?, ?, ?)
                """,
                (key_digest, record["jobId"], record["requestDigest"]),
            )

    def _insert_queue(self, existing_queue: dict[str, dict[str, Any]]) -> None:
        for job_id, job in sorted(self.jobs.items()):
            if job["state"] not in ACTIVE_WORK_STATES:
                continue
            attempt_id = str(job["currentAttemptId"])
            prior = existing_queue.get(job_id)
            preserve = prior is not None and str(prior.get("attempt_id")) == attempt_id
            lease_owner = prior["lease_owner"] if preserve else None
            lease_token = prior["lease_token"] if preserve else None
            lease_expires_at = prior["lease_expires_at"] if preserve else None
            if job.get("processingClaimed"):
                if not lease_token or not lease_expires_at:
                    lease_owner = "service-worker"
                    lease_token = secrets.token_hex(24)
                    lease_expires_at = iso(
                        datetime.now(UTC)
                        + timedelta(seconds=self.worker_lease_seconds)
                    )
                job["processingLease"] = {
                    "leaseOwner": lease_owner,
                    "leaseToken": lease_token,
                    "leaseExpiresAt": lease_expires_at,
                    "attemptId": attempt_id,
                }
            else:
                lease_owner = None
                lease_token = None
                lease_expires_at = None
                job.pop("processingLease", None)
            self._connection.execute(
                """
                INSERT INTO work_queue(
                    job_id, attempt_id, enqueued_at,
                    lease_owner, lease_token, lease_expires_at
                ) VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    attempt_id,
                    prior["enqueued_at"] if preserve else job["updatedAt"],
                    lease_owner,
                    lease_token,
                    lease_expires_at,
                ),
            )
