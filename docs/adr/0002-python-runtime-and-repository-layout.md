# ADR 0002: Python Runtime and Repository Layout

- **Status:** Accepted
- **Date:** 2026-08-05
- **Decision owners:** Project owner and ST Score Restore maintainers

## Context

The engine will combine deterministic image processing, document inspection, future AI adapters, validation and an API service. The repository needs an implementation-ready structure without prematurely selecting restoration libraries or model frameworks.

The project also needs a runtime that is widely usable in server and ML tooling while remaining conservative enough for future native dependencies.

## Decision

1. Python is the initial implementation language.
2. Python 3.12 is the primary development runtime.
3. Milestone M0 validates compatibility with Python 3.11 and 3.12.
4. The project uses a `src/` package layout with the import name `st_score_restore`.
5. `pyproject.toml` is the dependency-intent manifest.
6. Milestone M0 has no third-party runtime dependency and no restoration behavior.
7. The first third-party dependency requires a generated frozen lock artifact in the same pull request.
8. Source, tests, fixtures, tools, models, API notes, examples and license records remain separate top-level concerns.
9. The reference CI environment is Linux; other environments must still pass reference validation.

## Consequences

### Positive

- Python aligns with image-processing and ML ecosystems without committing to a specific library.
- The `src/` layout avoids accidental imports from the repository root.
- An empty M0 dependency set keeps the foundation reproducible and license-neutral.
- Explicit fixture, model and license directories reinforce safety and governance boundaries.

### Costs

- Native image and ML dependencies will require later platform and lock decisions.
- Python 3.13 or newer is not part of the initial compatibility promise.
- A service deployment and performance strategy remains a later decision.

## Safety and privacy impact

The layout keeps fixtures, private inputs, model weights and generated artifacts distinct. Ignore rules reduce accidental commits, but do not replace consent, review or secure storage controls.

## Alternatives considered

### TypeScript/Node.js as the core runtime

Deferred because the first engine stages are expected to depend heavily on Python-oriented document, image and ML tooling. TypeScript remains suitable for client SDKs or orchestration layers.

### C++ as the primary implementation

Deferred because it would increase development and safety-verification cost before performance requirements are measured.

### Add OpenCV, PDF and AI dependencies immediately

Rejected for M0 because exact package, license, native-binary and platform decisions require separate evidence-backed reviews.

### Support every current Python version

Rejected because unbounded compatibility would increase native dependency and CI risk before the implementation exists.

## Reversal or migration path

Public contracts will remain independent from the implementation language. Performance-sensitive components may later move behind adapters or service boundaries. Python support ranges may be expanded by a future ADR after dependency compatibility is verified.
