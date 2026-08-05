"""SQLite schema, rollback cleanup, and durable blob deletion work."""

from __future__ import annotations

from .durable_store_support import DurableStoreError, STORE_SCHEMA_VERSION


class DurableMaintenanceMixin:
    def _initialize_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS store_meta(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS jobs(
                job_id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS artifacts(
                job_id TEXT NOT NULL,
                artifact_id TEXT NOT NULL,
                digest TEXT NOT NULL,
                byte_size INTEGER NOT NULL CHECK(byte_size >= 0),
                payload_json TEXT NOT NULL,
                data_present INTEGER NOT NULL CHECK(data_present IN (0, 1)),
                PRIMARY KEY(job_id, artifact_id),
                FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS artifacts_digest_idx
                ON artifacts(digest, data_present);
            CREATE TABLE IF NOT EXISTS idempotency(
                key_digest TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                request_digest TEXT NOT NULL,
                FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS work_queue(
                job_id TEXT PRIMARY KEY,
                attempt_id TEXT NOT NULL,
                enqueued_at TEXT NOT NULL,
                lease_owner TEXT,
                lease_token TEXT,
                lease_expires_at TEXT,
                FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS work_queue_claim_idx
                ON work_queue(lease_expires_at, enqueued_at, job_id);
            CREATE TABLE IF NOT EXISTS pending_blob_deletions(
                digest TEXT PRIMARY KEY
            );
            """
        )
        row = self._connection.execute(
            "SELECT value FROM store_meta WHERE key = 'schema_version'"
        ).fetchone()
        if row is None:
            self._connection.execute(
                "INSERT INTO store_meta(key, value) VALUES('schema_version', ?)",
                (str(STORE_SCHEMA_VERSION),),
            )
        elif int(row["value"]) != STORE_SCHEMA_VERSION:
            raise DurableStoreError(
                "unsupported_store_schema",
                "The durable store schema version is not supported.",
                details={
                    "found": int(row["value"]),
                    "supported": STORE_SCHEMA_VERSION,
                },
            )

    def _discard_uncommitted_blobs(self) -> DurableStoreError | None:
        first_error: DurableStoreError | None = None
        for digest in sorted(self._transaction_new_blobs):
            try:
                self.blob_store.delete(digest)
            except DurableStoreError as error:
                first_error = first_error or error
        self._transaction_new_blobs.clear()
        return first_error

    def _sweep_orphan_blobs(self) -> None:
        with self._mutex:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                live_digests = {
                    str(row["digest"])
                    for row in self._connection.execute(
                        "SELECT DISTINCT digest FROM artifacts WHERE data_present = 1"
                    )
                }
                self.blob_store.sweep_orphans(live_digests)
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

    def _drain_pending_deletions(self) -> None:
        while True:
            with self._mutex:
                self._connection.execute("BEGIN IMMEDIATE")
                try:
                    row = self._connection.execute(
                        "SELECT digest FROM pending_blob_deletions ORDER BY digest LIMIT 1"
                    ).fetchone()
                    if row is None:
                        self._connection.commit()
                        return
                    digest = str(row["digest"])
                    live = self._connection.execute(
                        """
                        SELECT 1 FROM artifacts
                         WHERE digest = ? AND data_present = 1
                         LIMIT 1
                        """,
                        (digest,),
                    ).fetchone()
                    if live is None:
                        self.blob_store.delete(digest)
                    self._connection.execute(
                        "DELETE FROM pending_blob_deletions WHERE digest = ?",
                        (digest,),
                    )
                    self._connection.commit()
                except Exception:
                    self._connection.rollback()
                    raise
