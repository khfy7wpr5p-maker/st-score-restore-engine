# API boundary

The repository contains a non-production `/api/v1` job, immutable review-evidence, teacher-review baseline, and Stage 5 same-origin local review interface.

## Public contract

- OpenAPI 3.1: `api/openapi.v1.json`
- API version: `0.5.0`
- domain service: `st_score_restore.job_service`
- review evidence generator: `st_score_restore.review_evidence`
- evidence service contract: `st_score_restore.review_evidence_service`
- dependency-free router: `st_score_restore.http_api`
- Stage 5 local teacher-review UI: `/review`
- strict multipart and request metadata parser: `st_score_restore.http_security`
- standard-library server adapter: `st_score_restore.http_server`
- default test/demo store: `st_score_restore.job_store.InMemoryJobStore`
- optional durable local store: `st_score_restore.durable_job_store.SQLiteJobStore`
- local entry point: `tools/run_api.py`

Core API routes include job creation/status, pages, candidates, safety reports, reviewer evidence bundles, evidence-bound page review, retry attempts, cancellation, separate training consent, audit events, authenticated artifact access, and retention expiry.

## Stage 5 local review interface

`GET /review` serves a dependency-free same-origin HTML/CSS/JavaScript teacher review surface. The static UI contains no job data and does not bypass API authentication. Reviewers supply the existing local reviewer credential and actor ID; the credential is held only in page memory and is not written to `localStorage` or `sessionStorage`.

The UI provides:

- page and finding navigation;
- source/candidate evidence comparison;
- finding code, severity, and source-pixel region display;
- bounded zoom `0.25–8.0`, step `0.25`;
- `fit_width`, `fit_region`, and `actual_pixels` modes;
- evidence-bound approve, reject, and reprocess actions;
- stale-screen recovery when the evidence bundle or candidate is no longer current;
- visible focus, skip navigation, labeled controls, live status/error announcements, responsive layout, reduced-motion handling, and forced-colors handling.

The static assets are sent with no-store caching, a same-origin Content Security Policy, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, and related hardening. `/review` is a local Stage 5 capability, not a production deployment surface.

## Review evidence and stale-screen binding

`GET /api/v1/restoration-jobs/{jobId}/pages/{pageNumber}/review-bundle` is reviewer-only. It returns the current immutable bundle for the page and attempt, including:

- parent source/candidate/safety-report artifact IDs;
- source-pixel and normalized risk regions;
- paired source/candidate crop artifact IDs;
- registration/resize provenance;
- finding pagination, zoom modes, keyboard order, and mandatory screen-reader-label metadata.

Each HTTP review decision must include the current `evidenceBundleArtifactId`. Missing or stale IDs fail before mutation. Evidence artifact bytes require reviewer credentials and `purpose=review`.

The Stage 5 UI uses this existing binding directly. It does not create an alternative approval endpoint or automatic approval path.

The evidence contract visualizes validator findings but never claims semantic music recognition. It does not create automatic approval, a training label, or training consent. See `docs/review-evidence-contract.md` and ADR 0011.

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

Static keys and `X-Actor-Id` are development controls only. The durable local store is not an encrypted cloud object store and the SQLite queue is not an external broker. There is no TLS, rate limiting, durable distributed scheduler, signed object delivery, secret manager, production identity provider, backup service, disaster-recovery guarantee, or production review deployment.

Issue #13 remains open for production persistence and deployment hardening. Issue #14 tracks identity, Issue #17 broader concurrency, and Issue #18 production HTTP security review. The built-in adapter and `/review` UI must not be exposed to an untrusted network. Stage 6 remains separately governed.
