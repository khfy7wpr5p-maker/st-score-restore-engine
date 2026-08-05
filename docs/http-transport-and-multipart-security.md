# Built-in HTTP and Multipart Security Boundary

**Status:** M4.3 bounded local-adapter hardening  
**API contract:** `/api/v1`, version `0.4.0`  
**Tracking:** Issues #18 and #24

## Purpose

The repository keeps a dependency-free HTTP adapter for local development, deterministic integration tests, and controlled single-host demonstrations. This hardening slice narrows the byte-level request grammar before a request reaches the `/api/v1` router.

It does **not** approve the adapter for an untrusted or public network. TLS termination, production identity, rate limiting, trusted-proxy handling, external abuse controls, and deployment review remain outside this boundary.

## Transport rules

The built-in adapter accepts only `GET`, `POST`, and `DELETE` and closes the TCP connection after every response. Request pipelining and protocol upgrades are intentionally unsupported.

It rejects:

- multiple or non-decimal `Content-Length` values,
- every `Transfer-Encoding`, `Upgrade`, `Trailer`, and `Expect` header,
- duplicate headers, including duplicate `Host`,
- obsolete folded header lines and control characters,
- missing `Content-Length` on `POST`,
- bodies on `GET` and `HEAD`,
- unsupported connection tokens,
- absolute-form, authority-form, fragment-bearing, malformed-percent, encoded-slash, encoded-backslash, or encoded-NUL request targets,
- incomplete bodies and inactive connections that exceed the configured socket timeout.

Transport failures return a deterministic JSON error and close the connection. Python tracebacks, filesystem paths, credential values, and body fragments are not included.

## Default limits

| Limit | Default |
|---|---:|
| Request body | upload limit + 2,000,000 bytes |
| Request target | 4,096 bytes |
| Query fields | 32 |
| Header count | 64 |
| One header line | 8,192 bytes |
| Aggregate headers | 32,768 bytes |
| JSON body | 1,000,000 bytes |
| Multipart parts | 101 |
| Headers per part | 16 |
| One multipart header line | 4,096 bytes |
| Multipart headers per part | 16,384 bytes |
| Filename | 255 UTF-8 bytes |
| Connection inactivity timeout | 10 seconds |
| Concurrent request threads | 32 |

All values are deployment configuration in `JobApiConfig` and have bounded validation ranges.

## Multipart grammar

`multipart/form-data` is parsed by a small deterministic CRLF/boundary state machine rather than permissive message decoding.

Rules include:

1. one ASCII boundary parameter, 1–70 safe characters;
2. no preamble or epilogue;
3. CRLF framing only;
4. no nested multipart;
5. no header folding or duplicate part headers;
6. only `Content-Disposition`, `Content-Type`, and the explicitly rejected `Content-Transfer-Encoding` header are recognized;
7. file parts require `name="file"`, a safe filename, and an allowed exact media type without parameters;
8. `restorationConfig` is optional, unique, filename-free, UTF-8 JSON;
9. unknown fields and transfer encodings are rejected;
10. raw file bytes are copied exactly and are never base64/quoted-printable decoded.

A boundary-looking byte sequence inside a file is treated as data unless it is followed by the exact MIME delimiter trailer. An actual delimiter sequence inside a payload remains invalid MIME and terminates the part as required by the declared boundary contract.

## Filename and path handling

User filenames never select a storage path. Windows and POSIX parent components are removed, control characters and hidden/dot-only names are rejected, and the retained basename is length-bounded. Durable artifact storage continues to use SHA-256 content-addressed paths only.

## Response hardening

The server adapter adds `no-store`, `nosniff`, a deny-all Content Security Policy, frame denial, no-referrer, same-origin resource policy, and a restrictive Permissions Policy. These headers are defense in depth; they do not replace a production reverse proxy or TLS configuration.

## Verification boundary

The regression suite covers the pure router/parser and real loopback sockets, including malformed framing, duplicate lengths, folded headers, slow body timeout, incomplete bodies, binary preservation, part/header limits, unsupported MIME, deterministic malformed-input fuzz cases, and valid-request compatibility.

## Remaining work

Issue #18 remains open for production-grade review, longer-running fuzz campaigns, proxy/load-balancer-specific request-smuggling analysis, rate limiting, and deployment evidence. Issue #14 remains open for non-self-asserted identity. Issue #13 remains open for full production deployment hardening.
