# API boundary

The repository contains a non-production `/api/v1` job and teacher-review baseline.

## Public contract

- OpenAPI 3.1: `api/openapi.v1.json`
- API version: `0.4.0`
- domain service: `st_score_restore.job_service`
- dependency-free router: `st_score_restore.http_api`
- standard-library server adapter: `st_score_restore.http_server`
- default test/demo store: `st_score_restore.job_store.InMemoryJobStore`
- optional durable local store: `st_score_restore.durable_job_store.SQLiteJobStore`
- local entry point: `tools/run_api.py`

Core routes include job creation/status, pages, candidates, safety reports, page review, retry attempts, cancellation, separate training consent, audit events, authenticated artifact access, and retention expiry.

## Existing engine boundaries

- immutable source inspection: `st_score_restore.input_inspection`
- deterministic candidate engine: `st_score_restore.safe_restoration`
- music-score/TAB veto validator: `st_score_restore.music_safety_validator`

## Local persistence option

The API defaults to process-local memory. `tools/run_api.py --data-dir <path>` opts into SQLite metadata, verified content-addressed local blobs, restart persistence, and bounded local queue leases. This option does not change the HTTP contract.

## Non-production warning

Static keys and `X-Actor-Id` are development controls only. The durable local store is not an encrypted cloud object store and the SQLite queue is not an external broker. There is no TLS, rate limiting, durable distributed scheduler, signed object delivery, secret manager, production identity provider, backup service, or disaster-recovery guarantee.

Issue #13 remains open for production persistence and deployment hardening. Issues #14–#18 track identity, PDF, UI, concurrency, and HTTP security work. The built-in adapter must not be exposed to an untrusted network.
