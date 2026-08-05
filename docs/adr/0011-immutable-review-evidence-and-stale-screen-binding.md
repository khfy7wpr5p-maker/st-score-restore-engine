# ADR 0011: Immutable Review Evidence and Stale-Screen Binding

- **Status:** Accepted
- **Date:** 2026-08-05
- **Decision owners:** ST Score Restore Engine maintainers
- **Related issues:** #16, #28

## Context

The M3 safety validator produces machine-readable findings, and M4 records teacher decisions, but a reviewer still needs stable visual evidence that connects a finding to exact source and candidate pixels. Serving only a mutable “current preview” creates a stale-screen risk: a retry could change the candidate or safety report while an older page remains open in a reviewer client.

The system also must not imply that visualization performs semantic music recognition or that teacher approval grants model-training consent.

## Decision

1. Generate review evidence before a job transitions from `VALIDATING` to `AWAITING_REVIEW`.
2. Store evidence as immutable SHA-256 content-addressed artifacts.
3. Create paired source/candidate grayscale PNG crops only for validator findings with explicit pixel regions.
4. Keep findings without regions in bundle metadata without inventing coordinates.
5. Express overlays in source-pixel and normalized source coordinates.
6. Record candidate resize and registration provenance and decoded pixel digests.
7. Expose the current bundle through a reviewer-only API route.
8. Restrict all evidence bundle/crop bytes to reviewer access with `purpose=review`.
9. Require every HTTP teacher decision to include the current evidence-bundle artifact ID.
10. Prevalidate all page decisions before mutation and reject stale bundles with a stable conflict.
11. Clear only the current evidence pointer during retry; preserve prior artifacts and audit history.
12. Remove evidence bytes at retention expiry while retaining audit tombstones.
13. Keep teacher approval independent from training consent.
14. Bump the API/package version from `0.4.0` to `0.5.0` because review request semantics change.

## Consequences

### Positive

- Teachers can inspect exact before/after pixels for regional safety findings.
- Decisions are cryptographically bound to the candidate/report view used during review.
- Retry cannot silently reuse an old review screen.
- Evidence artifacts are reproducible, auditable, and compatible with durable local storage.
- The later browser UI receives explicit pagination, zoom, keyboard order, and screen-reader-label requirements.

### Negative

- Validation holds the local store transaction while bounded crop artifacts are generated.
- Evidence increases retained derivative bytes.
- HTTP review clients must adopt API `0.5.0` and send an evidence bundle ID.
- Grayscale crops do not validate input color profiles or end-user display fidelity.
- This decision does not deliver a browser interface or production identity.

## Alternatives considered

### Generate crops on demand

Rejected because output could change after a retry, and access would require recomputing evidence outside the original worker/audit transaction.

### Embed crops directly in JSON

Rejected because large base64 payloads obscure artifact identity, duplicate bytes, and complicate retention/access controls.

### Allow decisions without evidence IDs

Rejected at the HTTP boundary because it cannot prevent stale-screen review. Internal service compatibility may bind an omitted ID to the current bundle, but explicitly incorrect IDs remain invalid.

### Claim full color fidelity

Rejected. This baseline records grayscale decoded pixels and explicitly reports that input color profiles and display color management are unvalidated.

## Reversal and migration path

The evidence bundle is a versioned artifact contract. A later UI or rendering adapter may add stronger display metadata while preserving parent artifact IDs and stale-screen binding. Any incompatible review request change requires a new API version. Evidence artifacts can be regenerated only as new derivatives; existing artifacts remain immutable.
