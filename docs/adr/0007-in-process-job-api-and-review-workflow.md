# ADR 0007: In-Process Job API and Teacher-Review Workflow

- **Status:** Accepted for M4 baseline
- **Date:** 2026-08-05
- **Decision owners:** Project owner and ST Score Restore maintainers

## Context

The immutable inspector, deterministic OpenCV candidate engine, and music/TAB safety validator existed only as transport-neutral Python and CLI boundaries. Future music applications need a versioned service workflow, but introducing a database, queue, identity provider, or web framework before the domain contract is stable would enlarge the security and dependency surface.

## Decision

1. Introduce `/api/v1` version `0.4.0` with a checked-in OpenAPI 3.1 contract.
2. Implement the first transport adapter with the Python standard library and no new runtime dependency.
3. Use an in-memory store and one worker only; mark both as non-production.
4. Accept ordered image-page bundles so page-level teacher review can be tested before a PDF renderer is approved.
5. Preserve the canonical append-only state machine and create a new attempt for retry or reprocess.
6. Make upload idempotent by a key digest plus canonical request digest; conflicting reuse fails.
7. Require authenticated client or reviewer roles for all document operations.
8. Allow unapproved candidate bytes only as authenticated reviewer preview; final candidate access requires page approval.
9. Record page-level `approve`, `reject`, and `reprocess`. Reject selects the immutable original as fallback.
10. Keep teacher review and training consent in separate endpoints and audit events.
11. Hash-link every audit event. Retention removes bytes but leaves an expired audit tombstone.
12. Do not claim production authentication, persistence, deletion assurance, arbitrary multi-page PDF support, or multi-worker correctness.

## Consequences

The repository gains a complete, testable image-bundle workflow from upload through export-manifest creation. Future clients can design against a stable contract without importing restoration code.

The implementation loses all active jobs on process restart and cannot safely scale to multiple instances. Static development keys and self-declared actor IDs are not production identity. The built-in HTTP/multipart surface requires dedicated security review before exposure.

## Safety impact

- source bytes remain immutable,
- validator rejection cannot be teacher-approved,
- unresolved or rejected candidates are not final-download eligible,
- original fallback remains available until retention expiry,
- approval does not create training consent,
- retry and deletion cannot erase audit history.

## Migration path

Production adapters must implement the same domain and OpenAPI contracts behind transactional storage, durable queues, approved authentication, encrypted artifacts, and tested deletion workflows. Contract-breaking changes require a new API version or an explicit compatibility period.
