# Stage 1 Exit Evidence

**Status:** PASS / EFFECTIVE  
**As of:** 2026-09-02  
**Accepted Stage 2 entry main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`  
**Acceptance PR:** #82 — merged  
**Post-merge repository validation:** Run #203 (`33588190548`) — Python 3.11 PASS / Python 3.12 PASS  
**Artifact bytes stored in ordinary Git:** 0  
**Stage 2:** ACTIVE under Issue #83 / PR #84

## Decision

Stage 1 final exit is **PASS and effective**. The machine-readable decision remains:

`evidence/stage1c/corpus/stage1-exit-acceptance.v1.json`

The decision is a separate governance acceptance and does not rewrite the deterministic expanded-v2 coverage report.

## Accepted evidence

The Stage 1 acceptance work was built on production evidence main `8b5bdf3ff58898cfb85b8ef4d4f22c21e3b774e1`, validated after PR #81 by Run #199, then merged through PR #82. Final acceptance-main post-merge verification is main `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`, Run #203.

Canonical v2 digests remain:

- catalog v2: `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- expanded snapshot v2: `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- coverage report v2: `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Exact C17 artifact bindings:

- C17A combined staff+TAB: `36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb`;
- C17B standalone guitar TAB: `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`;
- C17C held-out Chopin: `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`;
- C17D deidentified phone photo: `abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5`.

Historical evidence remains immutable:

- C15 frozen snapshot canonical SHA-256 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`;
- C16 coverage report SHA-256 `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`;
- historical C16 decision remains `insufficient` for its original snapshot.

## Accepted aggregate boundary

- 5 real / 0 synthetic items;
- development 3 items / 3 source families;
- held out 2 items / 2 source families;
- no cross-split source-family leakage;
- 5 unique exact artifact digests;
- Chopin v2 selected once, v1 excluded;
- zero real corpus artifact bytes in ordinary Git.

Tracked coverage is present for staff notation, standalone guitar TAB, combined staff+TAB, scanned PDF, phone photo and non-`none` degradation. The seven historical C16 gap codes are absent from the expanded-v2 report.

## Automatic report remains fail-closed

`coverage-bias-report.v2.json` deliberately remains:

- `sufficiency.state = review_required`;
- `requiresCorpusExpansion = false`;
- `stage1ExitSupported = false`;
- `stage2EntrySupported = false`.

These automatic fields were not modified to force a transition. Stage 1 PASS came from the separate evidence-bound acceptance.

## Gate result

| Gate | Result |
|---|---|
| Governance / dataset review | PASS |
| Exact-artifact rights / provenance | PASS for accepted items |
| Privacy / de-identification | PASS for accepted items |
| Purpose authorization | PASS for Stage 2 quality-analysis evaluation |
| Custody/profile verification | PASS |
| Development/held-out isolation | PASS |
| Artifact digest uniqueness | PASS |
| C17C v1/v2 de-duplication | PASS |
| Historical C15/C16 immutability | PASS |
| Ordinary Git real artifact bytes | PASS — zero |
| PR #81 exact-head verification | PASS — Run #198 |
| PR #81 post-merge verification | PASS — Run #199 |
| PR #82 acceptance exact-head verification | PASS — Run #202 |
| PR #82 post-merge verification | PASS — Run #203 |
| Remaining Stage 1 blocker codes | NONE |

## Accepted limitations

Stage 1 PASS does not establish corpus representativeness, absence of bias, restoration effectiveness, OMR improvement, musical correctness, model-training permission or calibration permission. `source_selection_concentration` remains an accepted known limitation.

The separate user-provided sensitive phone-photo path remains blocked pending real `high_assurance_vault` verification and is not part of the accepted aggregate.

## Stage transition

Stage 1 is COMPLETE / PASS. Stage 2 entry is satisfied and Stage 2 is ACTIVE. Stage 3 remains BLOCKED until a separate Stage 2 exit acceptance returns PASS.
