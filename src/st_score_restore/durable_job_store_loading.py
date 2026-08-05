"""Committed durable-state loading and integrity verification."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .durable_store_support import (
    DurableStoreError,
    load_object,
    parse_iso,
    validate_audit_chain,
)
from .job_store import ACTIVE_WORK_STATES


class DurableLoadingMixin:
    def _reload_committed_snapshot(self) -> None:
        self._connection.execute("BEGIN")
        try:
            self._reload_locked()
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def _reload_locked(self) -> None:
        jobs = self._load_jobs()
        artifacts = self._load_artifacts(jobs)
        idempotency = self._load_idempotency(jobs)
        self._apply_queue_leases(jobs)
        self.jobs = jobs
        self.artifacts = artifacts
        self.idempotency = idempotency

    def _load_jobs(self) -> dict[str, dict[str, Any]]:
        jobs: dict[str, dict[str, Any]] = {}
        for row in self._connection.execute(
            "SELECT job_id, payload_json FROM jobs ORDER BY job_id"
        ):
            payload = load_object(row["payload_json"], "job_payload_invalid")
            job_id = str(row["job_id"])
            if payload.get("jobId") != job_id:
                raise DurableStoreError(
                    "job_identity_mismatch",
                    "Stored job identity does not match its database key.",
                    details={"jobId": job_id},
                )
            validate_audit_chain(payload)
            jobs[job_id] = payload
        return jobs

    def _load_artifacts(
        self,
        jobs: dict[str, dict[str, Any]],
    ) -> dict[tuple[str, str], dict[str, Any]]:
        artifacts: dict[tuple[str, str], dict[str, Any]] = {}
        rows = self._connection.execute(
            """
            SELECT job_id, artifact_id, digest, byte_size, payload_json, data_present
              FROM artifacts
             ORDER BY job_id, artifact_id
            """
        )
        for row in rows:
            job_id = str(row["job_id"])
            artifact_id = str(row["artifact_id"])
            if job_id not in jobs:
                raise DurableStoreError(
                    "orphan_artifact_metadata",
                    "Artifact metadata references a missing job.",
                    details={"jobId": job_id, "artifactId": artifact_id},
                )
            payload = load_object(row["payload_json"], "artifact_payload_invalid")
            digest = str(row["digest"])
            if artifact_id != f"sha256:{digest}":
                raise DurableStoreError(
                    "artifact_identity_mismatch",
                    "Artifact identity does not match its digest.",
                    details={"artifactId": artifact_id},
                )
            if (
                payload.get("artifactId") != artifact_id
                or payload.get("jobId") != job_id
                or payload.get("digest") != digest
            ):
                raise DurableStoreError(
                    "artifact_payload_identity_mismatch",
                    "Artifact payload identity does not match its database key.",
                    details={"jobId": job_id, "artifactId": artifact_id},
                )
            stored_size = int(row["byte_size"])
            if int(payload.get("byteSize", -1)) != stored_size:
                raise DurableStoreError(
                    "artifact_size_metadata_mismatch",
                    "Artifact size metadata is internally inconsistent.",
                    details={"artifactId": artifact_id},
                )
            data = (
                self.blob_store.read(digest, stored_size)
                if int(row["data_present"])
                else None
            )
            payload["data"] = data
            artifacts[(job_id, artifact_id)] = payload
        return artifacts

    def _load_idempotency(
        self,
        jobs: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, str]]:
        records: dict[str, dict[str, str]] = {}
        for row in self._connection.execute(
            "SELECT key_digest, job_id, request_digest FROM idempotency"
        ):
            job_id = str(row["job_id"])
            if job_id not in jobs:
                raise DurableStoreError(
                    "orphan_idempotency_record",
                    "Idempotency metadata references a missing job.",
                    details={"jobId": job_id},
                )
            records[str(row["key_digest"])] = {
                "jobId": job_id,
                "requestDigest": str(row["request_digest"]),
            }
        return records

    def _apply_queue_leases(self, jobs: dict[str, dict[str, Any]]) -> None:
        queue_rows = {
            str(row["job_id"]): dict(row)
            for row in self._connection.execute("SELECT * FROM work_queue")
        }
        orphaned = sorted(set(queue_rows) - set(jobs))
        if orphaned:
            raise DurableStoreError(
                "orphan_queue_record",
                "Work-queue metadata references a missing job.",
                details={"jobIds": orphaned},
            )
        current = datetime.now(UTC)
        for job_id, job in jobs.items():
            queue = queue_rows.get(job_id)
            active_work = job.get("state") in ACTIVE_WORK_STATES
            if active_work and queue is None:
                raise DurableStoreError(
                    "queue_record_missing",
                    "An active work item is missing its durable work record.",
                    details={"jobId": job_id, "state": job.get("state")},
                )
            if not active_work and queue is not None:
                raise DurableStoreError(
                    "unexpected_queue_record",
                    "A non-active job has a durable work record.",
                    details={"jobId": job_id, "state": job.get("state")},
                )
            if queue is None:
                job["processingClaimed"] = False
                job.pop("processingLease", None)
                continue
            if str(queue.get("attempt_id")) != str(job.get("currentAttemptId")):
                raise DurableStoreError(
                    "queue_attempt_mismatch",
                    "Work-queue attempt does not match the current job attempt.",
                    details={"jobId": job_id},
                )
            lease_values = (
                queue.get("lease_owner"),
                queue.get("lease_token"),
                queue.get("lease_expires_at"),
            )
            if any(value is not None for value in lease_values) and not all(
                value is not None for value in lease_values
            ):
                raise DurableStoreError(
                    "queue_lease_incomplete",
                    "Work-queue lease metadata is incomplete.",
                    details={"jobId": job_id},
                )
            active = False
            if all(value is not None for value in lease_values):
                try:
                    active = parse_iso(str(queue["lease_expires_at"])) > current
                except (TypeError, ValueError) as error:
                    raise DurableStoreError(
                        "queue_lease_timestamp_invalid",
                        "Work-queue lease expiry is invalid.",
                        details={"jobId": job_id},
                    ) from error
            if active:
                job["processingClaimed"] = True
                job["processingLease"] = {
                    "leaseOwner": queue["lease_owner"],
                    "leaseToken": queue["lease_token"],
                    "leaseExpiresAt": queue["lease_expires_at"],
                    "attemptId": queue["attempt_id"],
                }
            else:
                job["processingClaimed"] = False
                job.pop("processingLease", None)
