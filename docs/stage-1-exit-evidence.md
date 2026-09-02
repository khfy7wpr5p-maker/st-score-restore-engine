# Stage 1 Exit Evidence

**Status:** PASS / EFFECTIVE / HISTORICAL  
**As of:** 2026-09-02  
**Accepted Stage 2 entry main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`  
**Acceptance PR:** #82 — merged  
**Post-merge repository validation:** Run #203 (`33588190548`) — Python 3.11 / 3.12 PASS  
**Artifact bytes stored in ordinary Git:** 0  
**Stage 2 current state:** COMPLETE / PASS / production-effective  
**Stage 3 current state:** COMPLETE / PASS / production-effective; final acceptance main `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0` / Run #253  
**Stage 4 current state:** ENTRY ELIGIBLE / NOT STARTED

## Decision

Stage 1 final exit is **PASS and effective**. The machine-readable decision remains `evidence/stage1c/corpus/stage1-exit-acceptance.v1.json`.

The decision is a separate governance acceptance and does not rewrite the deterministic expanded-v2 coverage report.

## Accepted evidence

Stage 1 acceptance was built on production evidence main `8b5bdf3ff58898cfb85b8ef4d4f22c21e3b774e1`, then merged through PR #82. Final acceptance-main post-merge verification is main `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`, Run #203.

Canonical v2 digests remain:

- catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- expanded snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- coverage report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Exact C17 artifact bindings:

- C17A `36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb`;
- C17B `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`;
- C17C `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`;
- C17D `abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5`.

Historical evidence remains immutable:

- C15 snapshot `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`;
- C16 report `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`;
- historical C16 decision remains `insufficient` for its original snapshot.

## Accepted aggregate boundary

- 5 real / 0 synthetic items;
- development 3 items / 3 source families;
- held out 2 items / 2 source families;
- no cross-split source-family leakage;
- 5 unique exact artifact digests;
- Chopin v2 selected once, v1 excluded;
- zero real corpus artifact bytes in ordinary Git.

## Automatic report remains fail-closed

`coverage-bias-report.v2.json` deliberately remains `review_required`, `requiresCorpusExpansion=false`, `stage1ExitSupported=false`, `stage2EntrySupported=false`. These automatic fields were not modified to force a transition. Stage 1 PASS came from separate acceptance evidence.

## Gate result

Stage 1 governance, exact-artifact rights/provenance, privacy/de-identification, approved Stage 2 evaluation purpose, custody/profile verification, split isolation, digest uniqueness, C17C v1/v2 de-duplication, historical immutability and zero ordinary-Git corpus bytes passed the accepted Stage 1 exit gates.

## Accepted limitations

Stage 1 PASS does not establish corpus representativeness, absence of bias, restoration effectiveness, OMR improvement, musical correctness, model-training permission or calibration permission. `source_selection_concentration` remains an accepted known limitation.

The separate sensitive phone-photo path remains blocked pending real `high_assurance_vault` verification and is not part of the accepted aggregate.

## Current stage context

Stage 1 remains COMPLETE / PASS. Stage 2 later completed PASS and is production-effective at final acceptance main `87198a5a917ab6b3efc277762016a5f5b0dd3aab`. Stage 3 later completed PASS and is production-effective at final acceptance main `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0`, Run #253. Stage 3 work did not rewrite this evidence. Stage 4 is entry eligible but not started; calibration/training/publication remain separate decisions.
