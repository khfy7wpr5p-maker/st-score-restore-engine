# ADR 0031: Stage 11 V2a non-held-out shadow source-family expansion

- **Status:** Accepted for Stage 11 validation
- **Date:** 2026-09-08
- **Scope:** Development-only observation; no production authorization

## Context

The first real Stage 11 V2a shadow-corpus observation used one approved development source family (`dataset.item.imslp799143-beethoven-op48-no3.v1`) across four raster-only PDF pages. That established the read-only execution path but did not show whether the same frozen package could be observed on an independent notation/source family.

The next safe boundary is therefore to broaden source-family coverage without using held-out data, training, tuning, model selection, private/student/user material, or production traffic.

## Decision

Add a second independently approved Stage 1 development source family to the immutable shadow observation record:

- dataset item: `dataset.item.wikimedia-guitar-technical-exercise-no1.v1`
- source family: `source.family.wikimedia-guitar-technical-exercise-no1.v1`
- exact source SHA-256: `36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb`
- exact byte size: `34,636`
- input: native grayscale PNG, combined staff + guitar TAB
- split: `development`
- eligibility: `open_corpus`
- authorized purpose: `quality_evaluation`

The exact frozen TorchScript package remains:

`7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234`

The Wikimedia source is processed with the same Stage 11 shadow contract and shape-locked OpenCV comparator used by the existing corpus observation. Its full-page observation uses 20 deterministic 512x512 tiles with the already validated overlap/stitching contract.

Historical first-observation evidence remains immutable. A new expanded evidence artifact combines the previously accepted four Beethoven page observations with the independent Wikimedia page observation. The combined package represents five page observations across two source families.

## Observational results

Across the five pages:

- mean of page `meanAbsDiff`: `0.05885308533906937`
- maximum page `meanAbsDiff`: `0.08925281465053558`
- minimum page `meanAbsDiff`: `0.03307146579027176`
- mean changed-pixel fraction: `0.7161675112963365`
- maximum changed-pixel fraction: `0.7999121447028423`
- minimum changed-pixel fraction: `0.6075335082474017`

The second independent source-family page itself recorded:

- `meanAbsDiff`: `0.03307146579027176`
- `maxAbsDiff`: `0.498039186000824`
- `changedPixelFraction`: `0.6075335082474017`
- source-to-OpenCV mean absolute difference: `0.014340299181640148`
- source-to-V2a mean absolute difference: `0.018733080476522446`

These values describe pixel differences only. They are not musical-correctness scores, preservation gates, tuning signals, or deployment criteria.

## Safety invariants

This decision does not authorize or perform:

- held-out access;
- model training or tuning;
- optimizer creation or backpropagation;
- model-weight mutation;
- private/student/real-user data use;
- shadow candidate selection;
- automatic promotion;
- changes to the normal job service, HTTP API, OpenAPI, or `tools/run_api.py`;
- production inference or promotion;
- real-user rollout;
- final production-model selection;
- Stage 12 entry.

Exact source identity, rights/review/privacy status, development split, and the frozen package identity remain fail-closed prerequisites.

## Consequences

Stage 11 now has real, non-held-out shadow observation evidence across two independent public development source families, including both conventional staff material and combined staff + guitar TAB material.

This broader observation still does not establish production readiness. The next safe boundary is a non-held-out shadow preservation-review package that can inspect symbol/notation preservation without tuning the frozen model or converting observational differences into automatic promotion.
