# Stage 1 Exit Evidence

**Status:** PASS DECISION RECORDED — effective when the Stage 1 exit acceptance PR is merged  
**As of:** 2026-09-02  
**Stage:** Stage 1C / final exit acceptance  
**Parent:** #32  
**Tracking:** #47  
**Accepted evidence main:** `8b5bdf3ff58898cfb85b8ef4d4f22c21e3b774e1`  
**Post-merge repository validation:** Run #199 (`33573656067`) — Python 3.11 PASS / Python 3.12 PASS  
**Artifact bytes stored in ordinary Git:** 0  
**Stage 2 entry:** BLOCKED until this acceptance record merges; after merge it is ELIGIBLE / NOT STARTED

## 1. Decision

Stage 1 final exit is accepted as **PASS**, subject only to this acceptance record being merged through the normal exact-head PR gate.

This is a separate governance acceptance. It does not rewrite the deterministic expanded-v2 coverage report and does not turn that report into an automatic stage-transition authority.

The machine-readable acceptance is:

`evidence/stage1c/corpus/stage1-exit-acceptance.v1.json`

## 2. Evidence bound to the decision

The accepted production evidence boundary is merge commit:

`8b5bdf3ff58898cfb85b8ef4d4f22c21e3b774e1`

Post-merge Repository validation Run #199 (`33573656067`) executed and succeeded on both supported Python versions. It included architecture consistency, all C17 admission gates, historical C15/C16 checks, committed expanded-v2 `--check`, full tests and compile.

Accepted canonical v2 digests:

- catalog v2: `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- expanded snapshot v2: `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- coverage report v2: `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Accepted C17 exact-artifact bindings retained in this exit record:

- C17A combined staff+TAB artifact SHA-256: `36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb`;
- C17B standalone guitar TAB artifact SHA-256: `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`;
- C17C held-out Chopin exact artifact SHA-256: `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`;
- C17D deidentified phone-photo derivative SHA-256: `abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5`.

Historical evidence remains immutable:

- C15 frozen snapshot canonical SHA-256: `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`;
- C16 coverage report SHA-256: `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`;
- historical C16 decision remains `insufficient` for its original two-item snapshot.

## 3. Accepted expanded-v2 boundary

The accepted aggregate contains exactly 5 real items and 0 synthetic items:

- development: 3 items / 3 source families;
- held out: 2 items / 2 source families;
- unique exact artifact digests: 5;
- cross-split source-family leakage: none;
- Chopin metadata v2 selected exactly once; v1 excluded from the new aggregate;
- ordinary Git real corpus artifact bytes: 0.

Tracked coverage dimensions are present for staff notation, standalone guitar TAB, combined staff+TAB, scanned PDF, phone photo and non-`none` degradation. The seven historical C16 gap codes are absent from the expanded-v2 report.

## 4. Why the source report remains fail-closed

`coverage-bias-report.v2.json` deliberately remains:

- `sufficiency.state = review_required`;
- `requiresCorpusExpansion = false`;
- `stage1ExitSupported = false`;
- `stage2EntrySupported = false`.

Those flags mean the deterministic metadata report does not automatically authorize a stage transition. This acceptance record performs the required separate governance review.

The source report is therefore not modified as part of Stage 1 exit acceptance.

## 5. Gate result

| Gate | Result |
|---|---|
| Governance / dataset review | PASS |
| Exact-artifact rights / provenance | PASS for accepted corpus items |
| Privacy / de-identification | PASS for accepted corpus items |
| Purpose authorization | PASS for Stage 1 evaluation use |
| Custody/profile verification | PASS |
| Development/held-out isolation | PASS |
| Artifact digest uniqueness | PASS |
| C17C v1/v2 de-duplication | PASS |
| Historical C15/C16 immutability | PASS |
| Ordinary Git real artifact bytes | PASS — zero |
| Exact-head PR verification for PR #81 | PASS — Run #198 |
| Post-merge main verification | PASS — Run #199 |
| Review/thread reconciliation | PASS |
| Remaining blocker codes | NONE |

## 6. Accepted limitations

Stage 1 PASS does **not** establish any of the following:

- corpus representativeness;
- absence of bias;
- restoration effectiveness;
- OMR improvement;
- musical correctness;
- model-training permission;
- calibration permission.

`source_selection_concentration` remains an accepted known limitation because the aggregate is public-domain-majority with one licensed item. This limitation does not require further corpus expansion for the agreed Stage 2 Complete Quality Analysis evaluation purpose.

The separate user-provided sensitive phone-photo path remains blocked on real `high_assurance_vault` verification and is not required by the accepted corpus because C17D uses the separately admitted deidentified restricted derivative.

## 7. Stage transition boundary

After this acceptance record is merged and its exact-head/post-merge CI is green:

- Stage 1 is COMPLETE / PASS;
- Stage 2 entry becomes ELIGIBLE;
- Stage 2 is still NOT STARTED;
- a separate focused Stage 2 branch/PR is required before OpenCV Complete Quality Analysis work begins.

No Stage 2 implementation is included in this acceptance slice.
