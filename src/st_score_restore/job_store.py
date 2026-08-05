"""Job-store contracts, in-memory storage, and append-only audit hashing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
import secrets
from threading import RLock
from typing import Any


@dataclass(frozen=True)
class WorkClaim:
    """One bounded worker lease for a queued restoration job."""

    job_id: str
    lease_token: str
    lease_owner: str
    lease_expires_at: str


class InMemoryJobStore:
    """Non-production store used by deterministic tests and local demonstrations."""

    store_kind = "memory"

    def __init__(self) -> None:
        self.lock = RLock()
        self.jobs: dict[str, dict[str, Any]] = {}
        self.artifacts: dict[tuple[str, str], dict[str, Any]] = {}
        self.idempotency: dict[str, dict[str, str]] = {}

    def claim_next_job(
        self,
        *,
        now: datetime,
        lease_owner: str,
        lease_seconds: int,
    ) -> WorkClaim | None:
        """Claim one queued job without allowing an active lease to be stolen."""

        if not isinstance(lease_owner, str) or not lease_owner.strip():
            raise ValueError("lease_owner must be a non-empty string")
        if not 5 <= int(lease_seconds) <= 3_600:
            raise ValueError("lease_seconds must be between 5 and 3600")
        lease_owner = lease_owner.strip()
        current = _aware_utc(now)
        with self.lock:
            queued = sorted(
                (
                    job
                    for job in self.jobs.values()
                    if job["state"] in {"UPLOADED", "READY_FOR_PROCESSING"}
                ),
                key=lambda job: (job["createdAt"], job["jobId"]),
            )
            for job in queued:
                lease = job.get("processingLease")
                if lease is not None:
                    expiry = _parse_iso(lease["leaseExpiresAt"])
                    if expiry > current:
                        continue
                token = secrets.token_hex(24)
                expires = current + timedelta(seconds=int(lease_seconds))
                record = {
                    "leaseToken": token,
                    "leaseOwner": lease_owner,
                    "leaseExpiresAt": _iso(expires),
                }
                job["processingLease"] = record
                return WorkClaim(
                    job_id=job["jobId"],
                    lease_token=token,
                    lease_owner=lease_owner,
                    lease_expires_at=record["leaseExpiresAt"],
                )
        return None

    def release_claim(self, claim: WorkClaim) -> None:
        """Release a lease only when the caller still owns its token."""

        with self.lock:
            job = self.jobs.get(claim.job_id)
            if job is None:
                return
            lease = job.get("processingLease")
            if lease and secrets.compare_digest(
                lease.get("leaseToken", ""), claim.lease_token
            ):
                job.pop("processingLease", None)

    @staticmethod
    def append_event(
        job: dict[str, Any],
        *,
        event_type: str,
        occurred_at: str,
        actor: str,
        details: dict[str, Any],
        attempt_id: str | None,
    ) -> dict[str, Any]:
        """Append one hash-linked event. Existing entries are never rewritten."""

        previous_hash = job["audit"][-1]["eventHash"] if job["audit"] else None
        event = {
            "sequence": len(job["audit"]) + 1,
            "eventType": event_type,
            "occurredAt": occurred_at,
            "actor": actor,
            "attemptId": attempt_id,
            "previousEventHash": previous_hash,
            "details": details,
        }
        canonical = json.dumps(
            event,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        event["eventHash"] = hashlib.sha256(canonical).hexdigest()
        job["audit"].append(event)
        return event


def _aware_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("now must be a datetime")
    return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)


def _iso(value: datetime) -> str:
    return _aware_utc(value).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
