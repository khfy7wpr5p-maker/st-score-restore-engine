# ADR 0008: Durable Local SQLite Metadata and Content-Addressed Blob Store

- **Status:** Accepted
- **Date:** 2026-08-05
- **Decision owners:** ST Score Restore Engine maintainers
- **Related issues:** #13, #20

## Context

ADR 0007 introduced a dependency-free, process-local job API and teacher-review workflow. Its in-memory dictionaries are appropriate for deterministic integration tests, but a process restart loses jobs, idempotency records, reviews, consent records, audit history, and artifact bytes. Issue #13 covers a much broader production-hardening program that also includes encrypted object storage, external queues, identity, TLS, backups, metrics, and deployment review.

The next implementation step needs restart durability and bounded queue claims without implying that the built-in HTTP server is production ready.

## Decision

Add an optional `SQLiteJobStore` with these boundaries:

1. SQLite stores metadata, idempotency records, complete job snapshots, audit history, artifact references, pending deletions, and local work leases.
2. Artifact bytes remain outside SQLite in an owner-private content-addressed filesystem rooted at a caller-selected data directory.
3. The lowercase SHA-256 digest is the only blob filename. Original user filenames remain metadata and never influence a storage path.
4. Every outer `with store.lock` block becomes one SQLite `BEGIN IMMEDIATE` transaction. Existing domain-service behavior and the in-memory store remain available.
5. Audit chains and blob digests are verified whenever committed state is loaded. Corruption fails closed.
6. New blob writes are atomic and verified. Blobs created by a transaction that fails before commit are removed while the SQLite write lock is still held. Startup sweeps unreferenced blobs and interrupted private temporary files.
7. Expiry uses transactional pending-deletion records. A shared digest is removed only when no live artifact reference remains.
8. Queued jobs use opaque, one-owner, time-bounded lease tokens. SQLite serializes claims and expired unstarted claims may be recovered.
9. Store schema version `1` is explicit. Unknown versions are rejected; no implicit migration is attempted.
10. `tools/run_api.py --data-dir ...` is the only opt-in. Omitting it preserves the in-memory baseline.

## Consequences

### Positive

- Jobs, idempotency, reviews, retries, consent records, artifacts, and audit history survive restart.
- SQLite provides transactional metadata updates without adding a runtime dependency.
- Content-addressed files avoid duplicate local storage for identical bytes.
- An active queue lease cannot be claimed by another local store instance.
- The public `/api/v1` contract remains unchanged.

### Negative

- The compatibility bridge reloads and rewrites the complete metadata snapshot at each outer service transaction. This favors correctness and migration safety over scale.
- Artifact bytes are loaded into memory when the snapshot is opened; large-scale streaming storage is not implemented.
- The application does not encrypt the local data directory.
- The queue is SQLite-backed rather than an external broker.
- Recovery after a crash in an already-running processing state remains incomplete and is deferred to Issue #17.

## Safety and privacy impact

The data directory contains sensitive source and derived document bytes. It must be dedicated, access restricted, excluded from Git, and managed under the applicable retention policy. Blob identity is verified before use. Missing, corrupt, or symbolic-link-backed files are rejected rather than substituted. Audit corruption blocks startup instead of being repaired automatically.

This decision does not provide encrypted cloud storage, signed URLs, production identity, key rotation, TLS, deletion attestations, backup/restore, disaster recovery, or a deployment privacy/legal review. Issue #13 remains open.

## Alternatives considered

### Store artifact bytes as SQLite BLOBs

Rejected because large document bytes would increase database write amplification, backup size, and corruption blast radius. Metadata transactions and immutable artifact storage have different operational needs.

### Add PostgreSQL and an external queue immediately

Rejected for this slice because it would add deployment infrastructure, new dependencies, secret handling, and operational claims before the local persistence contract is independently verified.

### Serialize dictionaries to one JSON file

Rejected because atomic multi-writer claims, transactional idempotency, durable deletion work, and schema evolution would be weaker.

### Replace the existing service with a new repository layer

Deferred. A full repository abstraction is a later scalability refactor. The transactional compatibility bridge minimizes behavior changes while preserving all current regression coverage.

## Reversal or migration path

The durable store is optional. Running without `--data-dir` restores the in-memory implementation. A future production store may read the explicit SQLite schema and content-addressed blob layout through a reviewed migration tool. No future backend may silently reinterpret artifact digests, audit hashes, review records, or training-consent records.
