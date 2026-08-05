"""SQLite metadata and content-addressed local artifact persistence.

This is a durable local baseline, not a production deployment claim. The
existing mutable service contract remains in memory while every outer
``with store.lock`` block is committed as one SQLite transaction.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import secrets
import sqlite3
from threading import RLock
from typing import Any

from .durable_blob_store import ContentAddressedBlobStore
from .durable_job_store_loading import DurableLoadingMixin
from .durable_job_store_maintenance import DurableMaintenanceMixin
from .durable_job_store_writing import DurableWritingMixin
from .durable_store_support import (
    DurableStoreError,
    STORE_SCHEMA_VERSION,
    aware_utc,
    iso,
)
from .job_store import InMemoryJobStore, WorkClaim


class _TransactionalLock:
    """Re-entrant transaction boundary compatible with ``with store.lock``."""

    def __init__(self, store: "SQLiteJobStore", mutex: RLock) -> None:
        self.store = store
        self._mutex = mutex
        self._depth = 0

    def __enter__(self) -> "_TransactionalLock":
        self._mutex.acquire()
        try:
            if self._depth == 0:
                self.store._begin_outer_transaction()
            self._depth += 1
            return self
        except Exception:
            self._mutex.release()
            raise

    def __exit__(self, exc_type, exc, traceback) -> bool:
        self._depth -= 1
        try:
            if self._depth == 0:
                self.store._finish_outer_transaction(exc)
        finally:
            self._mutex.release()
        return False


class SQLiteJobStore(
    DurableLoadingMixin,
    DurableWritingMixin,
    DurableMaintenanceMixin,
    InMemoryJobStore,
):
    """Durable local store using SQLite metadata and verified blob files."""

    store_kind = "sqlite-local"

    def __init__(
        self,
        data_directory: str | Path,
        *,
        busy_timeout_ms: int = 5_000,
        worker_lease_seconds: int = 300,
    ) -> None:
        if not 5 <= int(worker_lease_seconds) <= 3_600:
            raise DurableStoreError(
                "invalid_worker_lease",
                "worker_lease_seconds must be between 5 and 3600.",
            )
        self.worker_lease_seconds = int(worker_lease_seconds)
        self.root = Path(data_directory)
        ContentAddressedBlobStore.prepare_directory(self.root)
        self.blob_store = ContentAddressedBlobStore(self.root / "blobs")
        self.blob_root = self.blob_store.root
        self.database_path = self.root / "store.sqlite3"
        if self.database_path.exists() and self.database_path.is_symlink():
            raise DurableStoreError(
                "symlink_database_path_forbidden",
                "The SQLite database path must not be a symbolic link.",
            )
        self._mutex = RLock()
        self.jobs: dict[str, dict[str, Any]] = {}
        self.artifacts: dict[tuple[str, str], dict[str, Any]] = {}
        self.idempotency: dict[str, dict[str, str]] = {}
        self._transaction_new_blobs: set[str] = set()
        self._connection = sqlite3.connect(
            self.database_path,
            timeout=max(1.0, busy_timeout_ms / 1000),
            isolation_level=None,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA synchronous = FULL")
        self._connection.execute("PRAGMA temp_store = MEMORY")
        ContentAddressedBlobStore.set_private_file_mode(self.database_path)
        try:
            self._initialize_schema()
            self._drain_pending_deletions()
            self._sweep_orphan_blobs()
            self.lock = _TransactionalLock(self, self._mutex)
            self._reload_committed_snapshot()
        except Exception:
            self._connection.close()
            raise

    def close(self) -> None:
        with self._mutex:
            self._connection.close()

    def claim_next_job(
        self,
        *,
        now: datetime,
        lease_owner: str,
        lease_seconds: int,
    ) -> WorkClaim | None:
        """Atomically claim one queued job across store instances."""

        if not isinstance(lease_owner, str) or not lease_owner.strip():
            raise DurableStoreError(
                "invalid_lease_owner",
                "A non-empty worker lease owner is required.",
            )
        if not 5 <= int(lease_seconds) <= 3_600:
            raise DurableStoreError(
                "invalid_worker_lease",
                "lease_seconds must be between 5 and 3600.",
            )
        current = aware_utc(now)
        expires = current + timedelta(seconds=int(lease_seconds))
        token = secrets.token_hex(24)
        lease_owner = lease_owner.strip()
        with self._mutex:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._connection.execute(
                    """
                    UPDATE work_queue
                       SET lease_owner = NULL,
                           lease_token = NULL,
                           lease_expires_at = NULL
                     WHERE lease_expires_at IS NOT NULL
                       AND lease_expires_at <= ?
                    """,
                    (iso(current),),
                )
                row = self._connection.execute(
                    """
                    SELECT job_id
                      FROM work_queue
                     WHERE lease_token IS NULL
                     ORDER BY enqueued_at, job_id
                     LIMIT 1
                    """
                ).fetchone()
                if row is None:
                    self._connection.commit()
                    return None
                job_id = str(row["job_id"])
                updated = self._connection.execute(
                    """
                    UPDATE work_queue
                       SET lease_owner = ?,
                           lease_token = ?,
                           lease_expires_at = ?
                     WHERE job_id = ?
                       AND lease_token IS NULL
                    """,
                    (lease_owner, token, iso(expires), job_id),
                ).rowcount
                if updated != 1:
                    self._connection.rollback()
                    return None
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise
        return WorkClaim(
            job_id=job_id,
            lease_token=token,
            lease_owner=lease_owner,
            lease_expires_at=iso(expires),
        )

    def release_claim(self, claim: WorkClaim) -> None:
        """Release a queue lease only when its token still matches."""

        with self._mutex:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._connection.execute(
                    """
                    UPDATE work_queue
                       SET lease_owner = NULL,
                           lease_token = NULL,
                           lease_expires_at = NULL
                     WHERE job_id = ? AND lease_token = ?
                    """,
                    (claim.job_id, claim.lease_token),
                )
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

    def _begin_outer_transaction(self) -> None:
        self._transaction_new_blobs = set()
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            self._reload_locked()
        except Exception:
            self._connection.rollback()
            raise

    def _finish_outer_transaction(self, error: BaseException | None) -> None:
        if error is not None:
            cleanup_error = self._discard_uncommitted_blobs()
            self._connection.rollback()
            self._reload_committed_snapshot()
            if cleanup_error is not None:
                raise cleanup_error from error
            return
        try:
            self._flush_locked()
            self._connection.commit()
        except Exception as flush_error:
            cleanup_error = None
            if self._connection.in_transaction:
                cleanup_error = self._discard_uncommitted_blobs()
                self._connection.rollback()
            else:
                self._transaction_new_blobs.clear()
            self._reload_committed_snapshot()
            if cleanup_error is not None:
                raise cleanup_error from flush_error
            raise
        self._transaction_new_blobs.clear()
        self._drain_pending_deletions()


__all__ = [
    "DurableStoreError",
    "SQLiteJobStore",
    "STORE_SCHEMA_VERSION",
]
