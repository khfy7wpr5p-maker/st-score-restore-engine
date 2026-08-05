# Durable Local Persistence Baseline

**Status:** M4.1 local durability baseline  
**Store schema:** `1`  
**Metadata:** SQLite  
**Artifact bytes:** content-addressed local files

## Purpose

The default API store remains in memory for deterministic tests and short-lived demonstrations. Supplying `--data-dir` opts into a durable local store that survives process restart while preserving the existing job, review, retry, consent, artifact, and audit contracts.

This is not a production-hosting claim. The data directory is not encrypted by the application, the queue is not an external broker, and the built-in HTTP adapter still must not be exposed to an untrusted network.

## Storage layout

```text
<data-dir>/
  store.sqlite3
  store.sqlite3-wal        # created by SQLite while active
  store.sqlite3-shm        # created by SQLite while active
  blobs/
    ab/
      abcdef...            # lowercase SHA-256 digest, no user filename
```

SQLite stores job metadata, attempts, pages, idempotency digests, audit events, artifact references, deletion work, and local queue leases. Artifact bytes are never placed in SQLite.

The root and blob directories are restricted to owner access when supported. SQLite and final blob files use owner-only modes. A symbolic-link database, blob, or managed directory is rejected.

## Transaction model

The existing service mutates dictionaries inside `with store.lock`. `SQLiteJobStore` preserves that domain boundary while making the outer lock a SQLite `BEGIN IMMEDIATE` transaction:

1. reload and verify the committed snapshot,
2. allow the existing service operation to mutate it,
3. validate audit and artifact identities,
4. write and verify new immutable blobs,
5. replace the metadata snapshot transactionally,
6. commit,
7. complete pending deletion work.

An exception inside the operation rolls back metadata. New blobs created by a failed flush are deleted before the transaction lock is released. Startup also removes unreferenced hash blobs and interrupted private temporary files.

## Integrity checks

Store startup fails closed when any of the following is detected:

- unsupported store schema version,
- malformed JSON metadata,
- job, artifact, or idempotency reference mismatch,
- non-contiguous audit sequence,
- invalid audit previous-hash link,
- invalid audit event SHA-256,
- missing blob,
- blob byte-size or SHA-256 mismatch,
- symbolic-link or unexpected blob-store entry.

No corrupt blob is replaced with different bytes and no audit corruption is silently repaired.

## Durable queue leases

Queued jobs have a durable queue record. A claim contains:

- job identifier,
- opaque lease token,
- lease owner,
- UTC expiry timestamp.

SQLite `BEGIN IMMEDIATE` serializes competing claims. An active lease cannot be stolen. An unstarted claim becomes reclaimable only after expiry. The current single worker remains supported through the existing `processingClaimed` contract; the durable store maps that flag to a bounded lease.

This slice does not claim complete recovery from a process crash after the job has already transitioned into `ANALYZING`, `PROCESSING`, `COMPARING`, or `VALIDATING`. Multi-worker and mid-transition crash recovery remain tracked by Issue #17.

## Deduplication and expiry

Blob paths are derived only from SHA-256. Identical bytes across jobs share the same local blob. Artifact metadata remains scoped to each job.

Expiry sets the job's artifact references to unavailable and preserves metadata plus the hash-linked audit tombstone. A blob is deleted only when no live artifact record in any job still references its digest. Deletion work is recorded transactionally and retried on the next store startup if an operating-system deletion fails.

## Running locally

```bash
export ST_SCORE_CLIENT_API_KEY='replace-with-at-least-16-characters'
export ST_SCORE_REVIEWER_API_KEY='replace-with-a-different-16-character-key'
python tools/run_api.py \
  --host 127.0.0.1 \
  --port 8080 \
  --data-dir runtime-data/st-score-restore \
  --worker-lease-seconds 300
```

Use a dedicated data directory. It contains source and derived document bytes. Backups, encryption at rest, signed delivery, secret management, deletion attestations, disaster recovery, and legal deployment review remain outside this baseline and continue under Issue #13.

## Reversal

Stop the server, preserve or securely delete the selected data directory according to the applicable retention decision, and run the API without `--data-dir` to return to the in-memory store. The HTTP API contract does not change.
