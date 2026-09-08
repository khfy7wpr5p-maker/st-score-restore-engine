# ADR 0030: Stage 11 V2a approved non-held-out shadow-corpus observation

- **Status:** Accepted for Stage 11 validation only
- **Date:** 2026-09-08
- **Candidate:** frozen Stage 11 V2a TorchScript package
- **Production authorization:** No
- **Stage 12 authorization:** No

## Context

The prior Stage 11 boundary validated an explicit in-process shadow handoff beside the normal restoration job service. That boundary used synthetic execution evidence and deliberately prohibited selection, production inference, real-user rollout, training, tuning, and Stage 12 entry.

The next safe question is narrower: can the exact frozen candidate be observed on an already-approved, non-held-out, public-development corpus item without weakening the existing dataset, privacy, and application-service boundaries?

## Decision

Add a corpus-level validation lane that consumes only Stage 1 catalog items satisfying all of these conditions:

- `eligibilityClass=open_corpus`;
- `split=development`;
- `quality_evaluation=granted`;
- approved dataset and rights review;
- `revocation.status=not_revoked`;
- `privacy.classification=none`;
- `provenance.sourceKind=public_domain`;
- supported input is native grayscale PNG or scanned PDF;
- exact source SHA-256 and byte size must match the admitted Stage 1 record.

Held-out items fail closed before source execution.

## First real-corpus execution

The first accepted execution uses the already-admitted Stage 1 development item:

- dataset item: `dataset.item.imslp799143-beethoven-op48-no3.v1`;
- source family: `source.family.imslp799143-beethoven-op48-no3.v1`;
- source SHA-256: `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`;
- source bytes: `1,182,561`;
- purpose: `quality_evaluation`;
- split: `development`;
- eligibility: `open_corpus`;
- page count: 4.

The exact frozen package SHA-256 is `7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234`, size `7,817,857` bytes.

All four PDF pages were independently inspected as raster-only. The Stage 3 PDF policy renders only raster-only pages and refuses to rasterize vector/hybrid pages. For this observation, rendering uses 72 DPI solely as bounded transport normalization. The resulting grayscale PNGs do not become dataset items and are not training data.

## Comparator boundary

The existing deterministic OpenCV restoration baseline remains the primary comparator. Orientation, deskew, perspective, and crop are disabled only for this shadow comparison so that source, OpenCV primary, and V2a shadow outputs share the same pixel geometry. Photometric cleanup remains the current OpenCV baseline.

This geometry lock is not a production configuration change and does not alter the normal job service.

## Observations

Four page observations completed on CPU. Aggregate observational values are:

- mean of page `meanAbsDiff`: `0.06529849022626877`;
- mean changed-pixel fraction: `0.7433260120585702`;
- page `meanAbsDiff` range: `0.050791654735803604` to `0.08925281465053558`;
- changed-pixel fraction range: `0.6391231696813092` to `0.7999121447028423`.

These values describe differences between the OpenCV primary comparator and the V2a shadow output. They are **not** a quality gate, model-selection score, tuning signal, or promotion decision.

## Safety invariants

This boundary does not:

- access held-out data;
- create an optimizer or execute backpropagation;
- mutate candidate weights;
- train or tune the model;
- use private, student, or real-user data;
- replace or select a primary candidate;
- register a network route;
- authorize production inference or promotion;
- authorize real-user rollout;
- select a final production model;
- authorize Stage 12.

Raw corpus bytes and model-package bytes remain outside ordinary Git. Only metadata, validators, code, and evidence summaries are committed.

## Consequences

Stage 11 now has evidence that the frozen candidate can traverse a real, approved, non-held-out development source through the same fail-closed shadow semantics. This still covers only one source family. No conclusion about general quality or production readiness is justified from this observation.

The next safe boundary is `broaden-nonheldout-shadow-corpus-source-family-coverage`: add independently approved development source families, remain observational, and continue to exclude held-out/private/user data and Stage 12.
