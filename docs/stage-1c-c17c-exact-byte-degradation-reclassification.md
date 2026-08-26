# Stage 1C C17C Exact-Byte Degradation Reclassification

**Status:** implementation candidate  
**Stage:** Stage 1C / C17C  
**Parent issue:** #47  
**Historical baseline:** C15/C16 remains immutable  
**Artifact:** existing admitted held-out IMSLP82860 bytes; no new artifact bytes in Git

## Purpose

C17C closes a metadata evidence gap without inventing or synthetically degrading a score. The exact already-authorized held-out PDF `IMSLP82860-Chopin-Waltzes-Op69-heldout-candidate.pdf` was fetched from the authorized Stage 1 custody workspace and re-inspected page by page.

The exact custody bytes remain:

- SHA-256: `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`
- byte size: `1114479`
- MIME: `application/pdf`
- page count: `8`
- source family: `source.family.imslp82860-chopin-op69.v1`
- split: `held_out`
- purpose: `held_out_evaluation`
- eligibility/profile: `open_corpus -> managed_standard`

## Exact-byte observation

A fresh render of the exact custody PDF shows naturally occurring scan/print contamination. Page 1 contains widespread small dark speckles, broken/dirty print regions, border contamination, and isolated marks in otherwise light areas. These features are present in the source bytes and were not synthetically generated.

The conservative Stage 1 degradation taxonomy therefore encodes only:

```text
noise
```

No `skew`, `perspective`, `blur`, `shadow`, `glare`, `uneven_lighting`, `compression`, or `low_resolution` label is added by this slice.

## Versioning rule

The historical admitted item `dataset.item.imslp82860-chopin-op69.v1` and historical `evidence/stage1c/corpus/catalog.v1.json` remain unchanged. C15/C16 continue to report the historical `degradations=[none]` state.

C17C introduces a metadata-v2 item for future corpus expansion:

`dataset.item.imslp82860-chopin-op69.v2`

It references the same exact artifact digest and source family but records the newly reviewed exact-byte degradation classification. The metadata-v2 item must independently pass C11 because the canonical dataset-item digest changes when metadata changes.

Canonical metadata-v2 dataset-item SHA-256:

`6a75bd7d8348c6ba6e47a4bdbc16a1fc9a3f3ec23fb79a36ad7c123608d3ff36`

Private review evidence reference:

`evidence:opq_3a902965b5bd4020ef7e4f3e4a02dcbe`

## Safety boundary

This slice:

- does not change the exact PDF bytes;
- does not add PDF/image bytes to ordinary Git;
- does not mutate the C15 snapshot or C16 report;
- does not change source-family split assignment;
- does not expand the authorized purpose beyond `held_out_evaluation`;
- does not authorize training, calibration, publication, demonstration, synthetic derivation, or Stage 2;
- does not claim the standalone guitar-TAB or phone-photo gaps are closed.

A later new versioned aggregate snapshot may count this metadata-v2 item as non-`none` degradation coverage only after this C11 package is merged and the future snapshot explicitly selects the v2 item instead of the historical v1 metadata record.
