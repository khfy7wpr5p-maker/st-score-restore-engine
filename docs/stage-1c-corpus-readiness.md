# Stage 1C Corpus Readiness Gate

**Status:** C13 implementation candidate  
**Stage:** Stage 1C  
**Parent issue:** #47  
**Stage 2 entry:** BLOCKED

## Purpose

C13 adds a deterministic structural readiness gate between individual artifact admission and any digest-bound Stage 1 development/held-out snapshot proposal.

The gate does not freeze a snapshot, measure quality, run OpenCV analysis or claim that corpus coverage is sufficient. It answers only whether the repository-visible authorized corpus has the minimum split structure needed before a snapshot can be proposed.

## Minimum structural conditions

A `ready` result requires all of the following at the explicit evaluation date:

- at least one authorized `development` item;
- at least one authorized `held_out` item;
- `development` items use current `quality_evaluation` permission;
- `held_out` items use current `held_out_evaluation` permission;
- each realized item has exactly its expected active Stage 1 purpose and no active training/calibration/publication/demonstration purpose;
- realized items are approved `external_available` artifacts and are not revoking/deleting;
- no source family appears in both development and held-out;
- the same artifact digest cannot appear in both development and held-out;
- assigned realized items outside the approved development/held-out evaluation scope block readiness.

The ordinary dataset catalog validator remains authoritative for rights, privacy, review, eligibility/storage pairing, split-family invariants, retention and other item semantics. C13 does not bypass those checks.

## Current repository state after C12

C12 admits one real public-domain scanned PDF for `quality_evaluation` on the `development` split. It is a valid realized development item.

There is no independently authorized held-out item yet. Therefore C13 must report:

- `state=blocked`;
- development item count `1`;
- held-out item count `0`;
- reason code `missing_held_out_item`.

CI intentionally uses `--require-blocked` for this state. A later focused PR that adds independently authorized held-out evidence must deliberately change the gate to `--require-ready`; readiness must never flip silently.

## CLI

```text
python tools/evaluate_stage1_corpus_readiness.py \
  evidence/stage1c/imslp799143/catalog.v1.json \
  --as-of 2026-08-25 \
  --require-blocked
```

`--as-of` is mandatory so CI and review evidence are deterministic and do not depend on wall-clock time.

`--require-ready` exits non-zero unless structural readiness is complete. `--require-blocked` exits non-zero if the catalog unexpectedly becomes ready without an explicit gate transition.

## Safety boundary

C13 does not:

- add or read artifact bytes;
- create storage/provider resources or credentials;
- authorize a new artifact;
- create a held-out item;
- reuse the current development source family as held-out evidence;
- create or approve a dataset snapshot;
- claim coverage sufficiency or empirical bias completion;
- activate model training, calibration, publication, demonstration or synthetic derivation;
- begin Stage 2 or change OpenCV/restoration/API/model behavior.

## Next boundary

After C13 is accepted, corpus expansion must add at least one independently authorized held-out artifact through the same rights, storage-profile and C11 admission gates. Only after C13 becomes `ready` may a digest-addressed development/held-out snapshot be proposed and validated by the existing Stage 1 snapshot contract.
