# ADR 0032 — Stage 11 V2a non-held-out shadow preservation review

## Status

Accepted for Stage 11 governance. The preservation-review result is **blocked** for any automatic promotion.

## Context

PR #208 broadened frozen V2a shadow observations to two independently approved non-held-out development source families: four raster pages from the Beethoven scanned PDF and one native combined staff + guitar-TAB PNG. Whole-page difference metrics alone cannot establish notation preservation, so the next safe boundary required a structural preservation review without retraining, held-out reuse, or production promotion.

The frozen package remains:

- SHA-256: `7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234`
- size: `7,817,857` bytes
- format: TorchScript

## Decision

Run a fresh exact-source/exact-package non-held-out review and feed every V2a shadow output through the existing deterministic music/TAB safety-validator logic. The review assesses:

- staff/TAB system geometry and line continuity,
- non-line dark-ink loss/invention,
- thin connected-component loss/invention/shift,
- registration reliability.

It does **not** claim semantic per-class identity. A dark connected component is not automatically called a notehead, stem, beam, accidental, TAB digit, or other authoritative musical symbol. Therefore structural findings cannot by themselves prove pitch/rhythm/TAB semantic changes.

## Actual execution result

Five pages across two independent source families were reviewed. All five structural validator verdicts were `reject`, so the Stage 11 shadow preservation-review disposition is `blocked`.

Aggregate results:

- mean non-line ink recall: `0.95896717`
- minimum non-line ink recall: `0.94285043`
- mean component recall: `0.509732472`
- minimum component recall: `0.21262058`
- mean/max structural risk score: `80.0`
- automatic promotion performed: `false`

The native Wikimedia staff + guitar-TAB page is particularly informative because geometry recognition is clean:

- staff systems: `3 -> 3`, line-break fraction `0.0`
- TAB systems: `3 -> 3`, line-break fraction `0.0`
- non-line ink recall: `0.97646035`
- component recall: `0.96259843`
- structural reject reasons: `component_shift_severe`, `symbol_invention_severe`

This means the review does **not** support a claim that V2a is erasing most musical ink on this page. Instead, the conservative validator is reacting to fine-structure change/dark-pixel invention and a severe maximum component-shift signal. Those findings block promotion, but they do not prove that new semantic notes or TAB digits were created.

The four Beethoven pages also reject. Their 72-DPI raster transport exposes substantial component-loss/invention signals and, on some pages, uncertain or changed staff-system detection. Therefore these pages cannot be used to claim clean structural preservation.

## Cross-run byte identity finding

The fresh review preserved the exact normalized source-page identities and exact frozen package identity, but only one of five fresh shadow PNG hashes matched the previously committed shadow-observation hash for the same page.

This is recorded as a separate unresolved determinism/root-cause finding. No cause is asserted in this ADR. In particular, it is not evidence of weight mutation, training, or held-out access.

## Relationship to previous V2a acceptance

The earlier V2a development/held-out/Stage 9A pass remains an immutable historical result. This preservation review does not rewrite those metrics. It adds a stricter downstream safety boundary: a model that passed the earlier preservation gate is still not eligible for automatic promotion when real non-held-out structural review produces veto findings.

The consumed held-out set remains frozen and may not be used for adaptive retuning.

## Safety consequences

The following remain false/forbidden:

- production inference authorization,
- production promotion,
- real-user rollout,
- final production-model selection,
- training or tuning from this review,
- held-out reuse for tuning,
- Stage 12 entry.

No existing HTTP route, normal job-service selection path, OpenAPI contract, or production surface is changed by this ADR.

## Next safe boundary

Diagnose, with non-held-out data only:

1. why fresh exact-package/source executions do not reproduce four of five prior shadow PNG hashes, and
2. whether the structural invention/component-shift vetoes arise from actual symbol-shape damage versus photometric thickening/darkening or detector limitations.

That diagnostic work must not retune V2a against the consumed held-out set and cannot authorize production by itself.
