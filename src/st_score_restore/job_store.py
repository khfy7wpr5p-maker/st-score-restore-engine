"""In-process storage and append-only audit hashing for the M4 API baseline."""

from __future__ import annotations

import hashlib
import json
from threading import RLock
from typing import Any


class InMemoryJobStore:
    """Non-production store. Raw document bytes disappear on expiry; metadata remains."""

    def __init__(self) -> None:
        self.lock = RLock()
        self.jobs: dict[str, dict[str, Any]] = {}
        self.artifacts: dict[tuple[str, str], dict[str, Any]] = {}
        self.idempotency: dict[str, dict[str, str]] = {}

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
