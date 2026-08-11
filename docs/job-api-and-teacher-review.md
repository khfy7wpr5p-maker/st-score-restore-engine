# Job API and Teacher-Review Baseline

**Status:** Milestone M4 API baseline with optional M4.1 local durability  
**API:** `/api/v1`, version `0.5.0`  
**OpenAPI:** `api/openapi.v1.json`

## Purpose

This layer exposes the existing immutable input inspector, deterministic OpenCV candidate engine, and music/TAB veto validator through a versioned service boundary. It adds job orchestration and teacher review without weakening the safety rules of the underlying engines.

The implementation uses:

- a standard-library threaded HTTP adapter,
- one in-process background worker,
- an in-memory store by default,
- an optional SQLite metadata and content-addressed local blob store,
- hash-linked append-only audit events.

It remains a local integration baseline, not a production deployment.

## Supported job input

`POST /api/v1/restoration-jobs` accepts:

- multipart form data with one or more ordered `file` fields,
- a raw PNG, JPEG, or PDF body with `X-Filename`,
- an optional multipart `restorationConfig` JSON object,
- a mandatory `Idempotency-Key`.

Repeated image files model an ordered multi-page image document so page-level review can be verified before a PDF renderer exists. Arbitrary multi-page PDF processing remains blocked by Issue #15.

## Job states

The current normal OpenCV processing path is:

```text
UPLOADED
  → ANALYZING
  → READY_FOR_PROCESSING
  → PROCESSING
  → VALIDATING
  → AWAITING_REVIEW
  → APPROVED
  → EXPORTING
  → COMPLETED
```

During `VALIDATING`, each current restoration candidate is validated against its immutable source before comparator evidence is emitted. `PAGE_VALIDATED` therefore precedes `CANDIDATES_COMPARED`; candidates with verdict `reject` are excluded from comparator eligibility evidence, and the immutable original remains recorded as selectable. This is the bounded current OpenCV selection baseline described by ADR 0015, not the Roadmap Stage 9 multi-engine comparator.

`COMPARING` remains a recognized state in the state-transition table for compatibility with existing state vocabulary, but the current normal OpenCV job path does not transition from `PROCESSING` into `COMPARING`.

Alternate or terminal states: `REJECTED`, `FAILED`, `CANCELLED`, and `EXPIRED`.

A retry or teacher-requested reprocess creates a new attempt identifier. Previous attempts, candidates, reports, and transitions remain in the audit history.

## Page review

A reviewer may decide each page independently:

- `approve`: select the current non-rejected candidate,
- `reject`: reject the candidate and select the immutable original page as fallback,
- `reprocess`: create a new attempt for that page.

A document can therefore export a mixed plan: approved candidate pages and original fallback pages. Rejecting a candidate page does not force approval of that candidate and does not discard the whole job.

When all pages are resolved, the service creates an immutable approved-export manifest. It does not yet assemble a multi-page PDF; that work is tracked separately.

## Artifact access policy

Two development roles exist: client and reviewer. Both require a credential. The baseline uses distinct static keys and `X-Actor-Id`; this does not constitute production identity. Issue #14 tracks identity-provider integration.

Access rules:

- immutable source: authenticated client or reviewer; use `purpose=original` when the same digest also represents an unapproved candidate,
- safety report and approved export manifest: authenticated client or reviewer,
- unapproved candidate: reviewer only with `purpose=review`,
- approved candidate: authenticated client or reviewer,
- expired artifact: unavailable with HTTP 410.

Every successful artifact access appends an audit event.

## Idempotency

The service stores only a SHA-256 digest of the idempotency key. The request identity covers ordered page names, media types, byte sizes, SHA-256 digests, and restoration configuration.

- same key + same request: returns the same job,
- same key + different request: HTTP 409,
- retry/reprocess: new attempt under the existing job, not an idempotency rewrite.

The in-memory implementation is single-process. The optional local durable store persists idempotency records across restart and serializes local claims through SQLite. Full multi-instance stress and external-broker behavior remain deferred to Issues #13 and #17.

## Teacher review and training consent

Teacher approval and training consent remain independent append-only records. Review records always state `trainingLabelCreated: false` and `trainingUseConsent: null`.

Training consent requires a separate call to `POST /api/v1/restoration-jobs/{jobId}/training-consent`. Consent may be `granted` or `denied`, with an explicit scope and terms version. Approval never implies consent.

## Retention and deletion

Each job has a configured expiry timestamp. Manual deletion and scheduled cleanup remove source, candidate, report, and export bytes; retain artifact metadata and SHA-256 identities; append an expiry transition and deletion event; and preserve the audit tombstone.

With the durable local store, a SHA-256 blob is deleted only after no live job reference remains. Deletion work is recorded transactionally and retried on startup. This is local durability, not a production deletion attestation or distributed scheduler guarantee.

## Running locally

Default in-memory mode:

```bash
export ST_SCORE_CLIENT_API_KEY='replace-with-at-least-16-characters'
export ST_SCORE_REVIEWER_API_KEY='replace-with-a-different-16-character-key'
python tools/run_api.py --host 127.0.0.1 --port 8080
```

Opt-in durable local mode:

```bash
python tools/run_api.py \
  --host 127.0.0.1 \
  --port 8080 \
  --data-dir runtime-data/st-score-restore \
  --worker-lease-seconds 300
```

The durable directory contains sensitive document bytes and is not encrypted by the application. This adapter has no TLS, rate limiting, production identity, signed delivery, or external queue. Do not expose it to an untrusted network.

## Deferred production work

The following open issues explicitly remain outside this baseline:

- #13 encrypted object storage, external queue, secret management, TLS, backups, deployment and privacy/legal hardening,
- #14 reviewer identity and authorization integration,
- #15 multi-page PDF rendering and PDF export assembly,
- #16 evidence crops and accessible visual review UI,
- #17 full multi-worker concurrency, processing-state crash recovery, and stress testing,
- #18 HTTP and multipart security review/fuzzing.
