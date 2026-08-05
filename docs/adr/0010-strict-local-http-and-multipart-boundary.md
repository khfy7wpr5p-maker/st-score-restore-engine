# ADR 0010: Strict Local HTTP and Multipart Boundary

- **Status:** Accepted
- **Date:** 2026-08-05
- **Decision owners:** ST Score Restore Engine maintainers
- **Related issues:** #13, #18, #24

## Context

ADR 0007 introduced a dependency-free `/api/v1` adapter using Python's standard-library HTTP server and MIME parser. That baseline was sufficient for deterministic local orchestration but intentionally deferred malformed framing, slow-client, request-smuggling, and multipart fuzz review. The API now has durable local storage and attempt-bound worker fencing, so transport ambiguity is the next unsafe boundary before identity, PDF, or UI integrations expand the reachable surface.

## Decision

1. Keep the built-in adapter dependency-free and explicitly non-production.
2. Add bounded HTTP metadata limits to `JobApiConfig`.
3. Reject ambiguous framing: duplicate `Content-Length`, all `Transfer-Encoding`, upgrades, trailers, expectations, folded headers, and unsupported connection tokens.
4. Require `Content-Length` for `POST`, read exactly that many bytes, and fail closed on timeout or early EOF.
5. Close every connection after one response; request pipelining is not supported.
6. Accept only origin-form targets and reject encoded path delimiters, NUL, malformed percent escapes, fragments, and backslashes.
7. Replace permissive multipart message decoding with a strict CRLF/boundary state machine.
8. Preserve file payload bytes exactly and forbid content-transfer decoding.
9. Bound part counts, part headers, JSON bodies, filenames, targets, aggregate headers, and inactivity time.
10. Return stable JSON transport failures without internal exception text or request bytes.
11. Keep `/api/v1` version `0.4.0`; resource semantics are unchanged.
12. Do not interpret this decision as approval for public-network exposure.

## Consequences

### Positive

- Ambiguous HTTP framing is rejected before routing.
- Slow or incomplete body reads are bounded.
- Multipart behavior is small, deterministic, and regression-tested.
- Binary source bytes remain unchanged.
- Connection-close semantics remove pipelining assumptions from the local adapter.
- No runtime dependency or license review is added.

### Negative

- Some permissive or non-conforming clients will be rejected.
- Keep-alive and pipelining performance are deliberately sacrificed.
- RFC extensions such as `filename*`, transfer encodings, nested multipart, chunked transfer, and `Expect: 100-continue` are unsupported.
- Socket inactivity timeout is not a full production request deadline or bandwidth quota.
- Standard-library header parsing still occurs before application-level limits; the socket timeout and Python's own parser ceilings remain the outermost guard.

## Alternatives considered

### Adopt a production ASGI stack immediately

Deferred because it introduces several dependencies and deployment decisions before identity, TLS, proxy, and operations contracts are approved. A future adapter may replace this one behind the pure `ApiV1` router.

### Continue using `email.parser.BytesParser`

Rejected for the upload boundary because permissive MIME recovery and transfer-decoding behavior are broader than the accepted API grammar.

### Support chunked requests and keep-alive

Rejected for this local baseline. They increase request-smuggling and resource-management complexity without advancing the current controlled-use requirement.

## Reversal and migration path

`ApiV1` remains a pure router. A reviewed production server can replace `http_server` while reusing the service contract and strict multipart tests. Any replacement must demonstrate equivalent or stronger limits, exact source-byte preservation, stable errors, identity binding, TLS/proxy policy, and abuse controls before Issue #18 can close.
