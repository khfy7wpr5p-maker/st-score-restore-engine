# API boundary

The repository now contains a non-production `/api/v1` job and teacher-review baseline.

## Public contract

- OpenAPI 3.1: `api/openapi.v1.json`
- API version: `0.4.0`
- domain service: `st_score_restore.job_service`
- dependency-free router: `st_score_restore.http_api`
- standard-library server adapter: `st_score_restore.http_server`
- local entry point: `tools/run_api.py`

Core routes include job creation/status, pages, candidates, safety reports, page review, retry attempts, cancellation, separate training consent, audit events, authenticated artifact access, and retention expiry.

## Existing engine boundaries

- immutable source inspection: `st_score_restore.input_inspection`
- deterministic candidate engine: `st_score_restore.safe_restoration`
- music-score/TAB veto validator: `st_score_restore.music_safety_validator`

## Non-production warning

The current store and worker are process-local. Static keys and `X-Actor-Id` are development controls only. There is no TLS, database, external queue, rate limiting, durable cleanup scheduler, signed object delivery, or production identity provider.

Issues #13–#18 track required hardening and deferred PDF/UI work. The built-in adapter must not be exposed to an untrusted network.
