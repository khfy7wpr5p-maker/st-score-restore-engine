# ADR 0009: Attempt-Bound Worker Fencing and In-Flight Recovery

- **Status:** Accepted for M4.2 local concurrency baseline
- **Date:** 2026-08-05
- **Decision owners:** ST Score Restore Engine maintainers
- **Related issues:** #13, #17, #22

## Context

ADR 0008 added durable SQLite work leases, but the domain service still selected work through the process-local `processingClaimed` flag. A lease protected initial queue selection, yet its token did not fence every later transaction. A worker that exceeded its lease could therefore continue attempting writes after another worker reclaimed the job. Queue rows also disappeared when a job entered `ANALYZING`, so an interrupted in-flight attempt could not be recovered through the durable claim path.

Before any multi-worker or multi-instance claim, the local baseline must prove one-owner processing, stale-worker rejection, deterministic idempotency, transactional lifecycle races, and auditable recovery.

## Decision

1. A work claim is bound to a job identifier, current attempt identifier, opaque token, owner, and expiry.
2. Durable queue rows remain present for `UPLOADED`, `ANALYZING`, `READY_FOR_PROCESSING`, `PROCESSING`, `COMPARING`, and `VALIDATING`.
3. `SQLiteJobStore.processing_claim(...)` installs a thread-local fencing context. Every outer `with store.lock` transaction validates the current job, attempt, owner, token, and expiry before mutation.
4. A valid token is renewed at the start of each outer processing transaction. Work performed outside the transaction may be discarded if the lease expires before the next mutation.
5. A stale, replaced, expired, wrong-owner, or wrong-attempt token raises the stable `stale_work_claim` error and cannot commit metadata, artifacts, audit events, or state changes.
6. An expired in-flight claim may be reclaimed. The new worker resets the current attempt to `READY_FOR_PROCESSING`, clears page pointers to partial candidate/report output, retains partial artifacts only for audit, records `WORK_LEASE_RECOVERED`, and reruns the deterministic pipeline from immutable source bytes.
7. Completion, failure, cancellation, review readiness, and expiry remove the work-queue row. Releasing an obsolete token is a no-op.
8. Each built-in `JobWorker` receives a unique local worker identifier and passes it as the lease owner.
9. The in-memory store and direct single-process service behavior remain available for deterministic tests. The public `/api/v1` contract and store schema version remain unchanged.

## Consequences

### Positive

- Two local store instances cannot actively process the same attempt.
- A worker result is accepted only while its exact fencing token remains current.
- Interrupted `ANALYZING` through `VALIDATING` work becomes recoverable after lease expiry.
- Partial output is never silently selected after recovery.
- Concurrent identical idempotency requests converge on one job; conflicting requests produce a deterministic conflict.
- SQLite transaction serialization preserves review/cancel and audit ordering under the tested local contention model.

### Negative

- Lease renewal occurs only at transaction boundaries; a single image operation longer than the lease is intentionally discarded rather than committed.
- Recovery reruns the current target pages from source and may consume additional CPU.
- Partial artifacts are retained in metadata until normal retention cleanup, increasing local storage use.
- SQLite remains a local coordination mechanism, not a distributed queue or production-scale database.

## Safety and privacy impact

The change reduces the risk of stale workers writing unreviewed or mismatched notation output. Recovery always starts from immutable source artifacts and never promotes partial candidates. Audit history records the previous state and recovery owner without storing lease tokens.

No document bytes, user filenames, lease tokens, credentials, or worker internals are added to logs by this decision. Existing local data-directory privacy requirements remain unchanged.

## Alternatives considered

### Accept the latest worker result by completion time

Rejected because wall-clock ordering cannot prove ownership and may accept a stale candidate after lease transfer.

### Delete all partial artifacts during recovery

Rejected because deletion would weaken auditability and could race with shared content-addressed references. Page selection pointers are cleared instead.

### Add an external broker now

Rejected for this slice because broker deployment, credentials, dead-letter policy, observability, and disaster recovery belong to the broader production work in Issue #13.

### Hold one SQLite transaction during image processing

Rejected because long native image operations would block unrelated API mutations and increase lock-failure risk.

## Reversal or migration path

The public service contract is unchanged. A future external queue may map its delivery token or generation number to the same attempt-bound fencing contract. Any replacement must preserve stale-worker rejection, immutable-source recovery, audit ordering, and the rule that partial artifacts are never automatically selected.
