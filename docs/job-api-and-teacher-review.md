# Job API and Teacher-Review Baseline

**Status:** Milestone M4 in-process baseline  
**API:** `/api/v1`, version `0.4.0`  
**OpenAPI:** `api/openapi.v1.json`

## Purpose

This layer exposes the existing immutable input inspector, deterministic OpenCV candidate engine, and music/TAB veto validator through a versioned service boundary. It adds job orchestration and teacher review without changing the safety rules of the underlying engines.

The implementation is intentionally dependency-free beyond the existing locked runtime. It uses:

- a standard-library threaded HTTP adapter,
- one in-process background worker,
- an in-memory job and artifact store,
- hash-linked append-only audit events.

It is a testable integration baseline, not a production deployment.

## Supported job input

`POST /api/v1/restoration-jobs` accepts:

- multipart form data with one or more ordered `file` fields,
- a raw PNG, JPEG, or PDF body with `X-Filename`,
- an optional multipart `restorationConfig` JSON object,
- a mandatory `Idempotency-Key`.

Repeated image files model an ordered multi-page image document so page-level review can be verified before a PDF renderer exists. Arbitrary multi-page PDF processing remains blocked by Issue #15.

## Job states

```text
UPLOADED
  → ANALYZING
  → READY_FOR_PROCESSING
  → PROCESSING
  → COMPARING
  → VALIDATING
  → AWAITING_REVIEW
  → APPROVED
  → EXPORTING
  → COMPLETED
```

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

The in-memory implementation is single-instance only. Multi-instance behavior remains deferred to Issues #13 and #17.

## Teacher review and training consent

Teacher approval and training consent remain independent append-only records. Review records always state `trainingLabelCreated: false` and `trainingUseConsent: null`.

Training consent requires a separate call to `POST /api/v1/restoration-jobs/{jobId}/training-consent`. Consent may be `granted` or `denied`, with an explicit scope and terms version. Approval never implies consent.

## Retention and deletion

Each job has a configured expiry timestamp. Manual deletion and scheduled cleanup remove source, candidate, report, and export bytes; retain artifact metadata and SHA-256 identities; append an expiry transition and deletion event; and preserve the audit tombstone.

Cleanup is idempotent. The in-memory timer is not durable and must not be represented as production deletion assurance.

## Running locally

```bash
export ST_SCORE_CLIENT_API_KEY='replace-with-at-least-16-characters'
export ST_SCORE_REVIEWER_API_KEY='replace-with-a-different-16-character-key'
python tools/run_api.py --host 127.0.0.1 --port 8080
```

This adapter has no TLS, durable storage, external queue, rate limiting, or identity provider. Do not expose it to an untrusted network.

## Deferred production work

The following open issues explicitly remain outside this baseline:

- #13 production persistence, queue, encryption, and deployment hardening,
- #14 reviewer identity and authorization integration,
- #15 multi-page PDF rendering and PDF export assembly,
- #16 evidence crops and accessible visual review UI,
- #17 multi-worker concurrency and idempotency stress testing,
- #18 HTTP and multipart security review/fuzzing.
