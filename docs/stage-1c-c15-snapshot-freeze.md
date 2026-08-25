# Stage 1C C15 — Digest-Addressed Snapshot Freeze

**Status:** implementation candidate  
**Parent:** Issue #47  
**Corpus input:** `evidence/stage1c/corpus/catalog.v1.json`  
**Environment:** `stage1_offline`  
**Stage 2 authorized:** no

## Purpose

C15 freezes the minimum structurally ready Stage 1 development/held-out corpus into the existing Stage 1 snapshot contract. It does not claim that two items provide sufficient empirical coverage.

The snapshot is deterministic and binds:

- the canonical SHA-256 of the realized two-item catalog;
- each assignment to the canonical SHA-256 of the exact catalog item metadata;
- the existing development item to `development`;
- the independently admitted held-out item to `held_out`;
- `heldOutFrozen=true`;
- `trainingUseActivated=false`;
- the snapshot review to a private external evidence record through an opaque evidence reference.

## Freeze membership

Exactly two items may be present in the C15 candidate:

1. `dataset.item.imslp799143-beethoven-op48-no3.v1` — development;
2. `dataset.item.imslp82860-chopin-op69.v1` — held out.

The assignments must be sorted by dataset item ID. Source-family and artifact-digest split leakage remain prohibited by the lower-level catalog and C13 readiness contracts.

## Coverage boundary

C15 records factual counts only:

- real items: 2;
- synthetic items: 0;
- development items: 1;
- held-out items: 1.

The snapshot intentionally records explicit gap codes for the tiny corpus. These gap codes are not a coverage PASS. Empirical coverage/gap/bias review and the Stage 1 dataset card remain later controlled work.

## Safety boundary

C15 does not:

- add real PDF bytes to ordinary Git;
- change artifact rights, custody, or purpose authorizations;
- activate training, calibration, publication, demonstration, or synthetic derivation;
- run OpenCV quality analysis or restoration against the Stage 1 artifacts;
- claim coverage or bias sufficiency;
- complete Stage 1 exit;
- authorize Stage 2.

## Deterministic verification

`tools/build_stage1_snapshot.py` builds the candidate only if C13 readiness is exactly `development=1`, `held_out=1`, `state=ready`, with one source family per split and no reason codes.

The final C15 CI gate must validate a committed snapshot through the public `validate_dataset_snapshot` boundary and require exact equality with the deterministic builder output. Any catalog, item digest, split, authorization, review, retention, revocation, or freeze drift must fail closed.

Ready-for-review and merge remain separate explicit approval gates.
