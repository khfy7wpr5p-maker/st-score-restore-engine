# Stage 6 S6-07 — Synthetic Operational Safety / Recovery Drills

Status: AUTHORIZED AND IMPLEMENTED FOR SYNTHETIC-ONLY VALIDATION

This slice validates the provider-neutral Stage 6 storage/deployment safety contracts under deterministic, bounded, in-memory failure scenarios. It does not provision or contact a production provider and does not authorize a production deployment.

## Authorized drill inventory

1. Queue redelivery and stale-worker fencing
   - a valid monotonic fencing token is accepted;
   - reuse of the current fencing token is rejected;
   - a redelivery with a newer token is accepted.

2. Crash recovery and idempotent replay
   - atomic metadata commit, artifact integrity, commit-before-ack, replay idempotency and stale-worker fencing are required;
   - missing partial-write cleanup evidence fails closed.

3. Two-stage deletion and restore anti-resurrection
   - deletion intent/completion and tombstone propagation are required;
   - restore publication is rejected when deleted-data resurrection protection is absent.

4. Audit dependency failure
   - a sensitive storage/deletion operation is blocked when durable audit acceptance is unavailable.

5. Deployment candidate and rollback gate
   - a signed immutable candidate may be evaluated without production activation;
   - production activation remains rejected without separate authorization;
   - missing rollback validation fails closed.

6. Bounded synthetic concurrency and idempotency stress
   - a small in-memory concurrent workload exercises monotonic fencing and duplicate idempotency commits;
   - this is not a production load/soak test and does not establish production concurrency targets or failure budgets.

## Safety boundary

- synthetic/in-memory only;
- no real corpus or derivative document bytes;
- no provider API calls;
- no live database, object store, queue, backup, audit or deployment resources;
- no production-state mutation;
- no production deployment;
- provider selection remains UNSELECTED;
- local SQLite remains a non-production baseline;
- no threshold or production resource-limit changes;
- no held-out retuning, model training or publication;
- historical evidence remains immutable.

## Evidence rule

The executable drill runner is `tools/run_stage6_s6_07_synthetic_operational_drills.py`. Stage 6 CI runs it on Python 3.11 and 3.12. A later S6-07 current-truth overlay may mark synthetic drills complete only after exact-head and post-merge Repository, Stage 4, Stage 5 and Stage 6 workflows succeed.

## Not completed by S6-07

Provider-specific security certification, independent production security sign-off, live distributed stress/load/soak testing, production concurrency targets/failure budgets, production deployment and Stage 7 remain outside this authorization.

Next safe boundary: `separate_explicit_s6_08_integration_security_regression_authorization`.
