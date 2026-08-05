# API boundary

The repository contains a non-production `/api/v1` job and teacher-review baseline.

## Public contract

- OpenAPI 3.1: `api/openapi.v1.json`
- API version: `0.4.0`
- domain service: `st_score_restore.job_service`
- dependency-free router: `st_score_restore.http_api`
- strict multipart and request metadata parser: `st_score_restore.http_security`
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

The API defaults to process-local memory. `tools/run_api.py --data-dir <path>` opts into SQLite metadata, verified content-addressed local blobs, restart persistence, and bounded local queue leases. This option does not change the HTTP resource contract.

## Local HTTP security boundary

The built-in adapter rejects ambiguous `Content-Length`, all `Transfer-Encoding`, protocol upgrades, trailers, expectations, folded headers, unsafe targets, oversized headers/JSON/multipart metadata, and incomplete or inactive body reads. It parses multipart with strict CRLF and boundary rules, preserves file bytes exactly, and closes every connection after one response.

See `docs/http-transport-and-multipart-security.md` and ADR 0010 for the exact limits and unsupported HTTP/MIME features.

## Non-production warning

Static keys and `X-Actor-Id` are development controls only. The durable local store is not an encrypted cloud object store and the SQLite queue is not an external broker. There is no TLS, rate limiting, durable distributed scheduler, signed object delivery, secret manager, production identity provider, backup service, or disaster-recovery guarantee.

Issue #13 remains open for production persistence and deployment hardening. Issue #14 tracks identity, Issue #15 PDF, Issue #16 UI evidence, Issue #17 broader concurrency, and Issue #18 production HTTP security review. The built-in adapter must not be exposed to an untrusted network.
