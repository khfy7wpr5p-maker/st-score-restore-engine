# Local Multi-Worker Concurrency and Recovery Baseline

**Status:** M4.2 local proof and hardening  
**Public API:** unchanged at `/api/v1` version `0.4.0`  
**Store schema:** unchanged at `1`

## Purpose

This baseline connects the durable SQLite lease to the actual processing workflow. It allows bounded local concurrency tests and safe recovery from an expired in-flight worker without claiming that SQLite is a production queue or that the built-in HTTP server is ready for public exposure.

## Claim and fencing contract

A claim contains:

- `job_id`,
- `attempt_id`,
- opaque `lease_token`,
- `lease_owner`,
- UTC expiry.

The token is not an audit field or public API value. While a durable worker processes a job, every outer metadata transaction verifies all claim fields and confirms that the expiry is still in the future. A successful verification renews the same token. A stale token fails with `stale_work_claim` before the transaction can mutate state.

The work-queue row remains durable through:

```text
UPLOADED
  → ANALYZING
  → READY_FOR_PROCESSING
  → PROCESSING
  → COMPARING
  → VALIDATING
```

It is removed when the job reaches review readiness or another non-processing state.

## In-flight recovery

After a lease expires, another worker may claim the same attempt. When the stored state is already in flight:

1. the new token is validated,
2. current page pointers to candidate and safety-report output are cleared,
3. any partial artifact records remain only as audit evidence,
4. the attempt returns to `READY_FOR_PROCESSING`,
5. `WORK_LEASE_RECOVERED` is appended,
6. processing restarts from immutable source bytes.

The old worker cannot write after transfer because its token no longer matches. A partial candidate is never selected or approved automatically.

## Concurrent mutation behavior

SQLite `BEGIN IMMEDIATE` serializes each outer domain mutation. The bounded stress suite covers:

- identical concurrent idempotency requests converging on one job,
- conflicting use of one idempotency key producing one winner and one conflict,
- active claim protection and expired-claim transfer,
- stale-token transaction rejection,
- recovery after a partial candidate write,
- three local workers processing multiple jobs without duplicate completion,
- teacher review racing with cancellation,
- audit hash-chain validation after contention.

These tests prove the checked-in local implementation on supported CI platforms; they are not a throughput benchmark or distributed-systems proof.

## Operational rule

Set the lease longer than the expected worst-case duration of one individual inspection, restoration, or validation operation. The lease is renewed at transaction boundaries. When an operation exceeds the lease, its next write is rejected and a later worker may safely rerun the attempt.

## Explicit limitations

- no external broker or dead-letter queue,
- no distributed database,
- no cross-host clock-synchronization guarantee,
- no automatic horizontal scaling,
- no production metrics or alerting,
- no public deployment approval,
- no change to static development credentials,
- no claim that every possible race has been exhaustively proven.

Issues #13, #14, #17, and #18 remain the controlling production-hardening work.
