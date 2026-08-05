# ADR 0004: Immutable Standard-Library Input Inspection

- **Status:** Accepted
- **Date:** 2026-08-05
- **Decision owners:** Project owner and ST Score Restore maintainers

## Context

The restoration pipeline needs a trustworthy first boundary for PDF, JPEG, PNG, and phone-captured images. The boundary must preserve original bytes, identify clean digital PDFs so they are not unnecessarily rasterized, expose uncertainty, and reject unsafe inputs before restoration dependencies are introduced.

## Decision

1. Input inspection is read-only and deterministic.
2. Accepted source bytes receive a SHA-256 artifact ID and immutable source manifest.
3. Artifact and analysis contracts use schema version `1.0.0`.
4. PDF, JPEG, and PNG are detected by content signature, not trusted filename extension.
5. Symbolic links and files that change during reading are rejected.
6. PDF classification uses visible structural evidence and may return `unknown`.
7. A digital PDF receives the action `preserve_vector_pdf`.
8. Encrypted, malformed, unsupported, empty, and oversized inputs fail with stable error codes.
9. EXIF orientation changes reported display dimensions only; source bytes remain untouched.
10. Pixel-level risks remain `not_assessed` until an approved decoder or image backend exists.
11. No third-party dependency is added for this milestone.
12. Inspection produces no enhanced or derived artifact.

## Consequences

The project gains a stable source identity, a machine-readable inspection contract, safe failure behavior, and protection for vector PDFs without committing to a PDF renderer or image library. The baseline cannot inspect compressed PDF internals fully or measure glare, blur, shadow, noise, and perspective from pixels.

## Safety and privacy impact

The inspector records only deterministic structural metadata and the source filename, not an absolute path. It does not upload data, retain a copy, strip metadata, or use documents for training. Source bytes are never rewritten.

## Alternatives considered

Adding a PDF/image dependency immediately was deferred until a separate license, native-binary, lockfile, and platform review. Trusting filename extensions was rejected. Automatically rasterizing unknown PDFs was rejected. Claiming that unassessed pixel risks are absent was rejected.

## Reversal or migration path

A future adapter may provide deeper PDF and pixel inspection behind the same versioned contracts. Contract-breaking fields require a new schema version and migration notes. The standard-library inspector remains a fallback and audit reference.
