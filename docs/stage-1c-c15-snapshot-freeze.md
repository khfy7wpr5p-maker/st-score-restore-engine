# Stage 1C C15 — Digest-Addressed Snapshot Freeze

**Status:** implementation candidate  
**Parent:** Issue #47  
**Corpus input:** `evidence/stage1c/corpus/catalog.v1.json`  
**Snapshot:** `evidence/stage1c/corpus/snapshot.freeze.v1.json`  
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

## Exact digest bindings

The deterministic C15 builder emitted these values before the committed snapshot was introduced:

- catalog SHA-256: `059c40b619d3c7815f14377cc8b26fce9a6b0522f2419f481bd93b15ed60e937`;
- development item metadata SHA-256: `c1f06342ba4932e2a087e76d424fbb253d63fa19bf7dc7f07196fbe99026b23f`;
- held-out item metadata SHA-256: `b8aab0a86924043c038c44f3f7346199628ae101e520c7f023d934485db3e58b`;
- snapshot canonical SHA-256: `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`.

The committed snapshot must reproduce all four bindings exactly under `--check`.

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

The snapshot intentionally records:

- `coverage.single-item-per-split`;
- `coverage.two-item-corpus`.

These gap codes are not a coverage PASS. Empirical coverage/gap/bias review and the Stage 1 dataset card remain later controlled work.

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

The final C15 CI gate validates the committed snapshot through the public `validate_dataset_snapshot` boundary and requires exact equality with deterministic builder output. Any catalog, item digest, split, authorization, review, retention, revocation, or freeze drift fails closed.

The snapshot review points to private external evidence through `evidence:opq_519827b4ec96be85e73e0581de8b8c0d`. No provider, account, path, or private document identifier is written into ordinary Git.

Ready-for-review and merge remain separate explicit approval gates.
