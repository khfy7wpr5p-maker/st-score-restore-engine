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
        current = datetime.now(UTC)
        for job_id, job in jobs.items():
            queue = queue_rows.get(job_id)
            active = bool(
                queue
                and queue.get("lease_token")
                and queue.get("lease_expires_at")
                and parse_iso(str(queue["lease_expires_at"])) > current
            )
            if active:
                job["processingClaimed"] = True
                job["processingLease"] = {
                    "leaseOwner": queue["lease_owner"],
                    "leaseToken": queue["lease_token"],
                    "leaseExpiresAt": queue["lease_expires_at"],
                }
            else:
                job["processingClaimed"] = False
                job.pop("processingLease", None)
