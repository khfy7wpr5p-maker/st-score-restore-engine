# ST Score Restore Engine — Development Roadmap

**Document status:** Binding sequence; Stage 3 ACTIVE  
**Version:** 0.5.1  
**Date:** 2026-09-02  
**Tracking:** Issue #90  
**Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Stage 3 core main:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa`  
**Stage 3 authorized-execution main:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b`  
**Stage 3 purpose-grant main / current production baseline:** `6ebe160309c562e9841a3c313d5ca507592f1386`

## Authority and invariant rules

Repository truth is merged `main` plus accepted deterministic evidence. Historical evidence is never rewritten to make later decisions retroactive. Source bytes remain immutable; real corpus/derivative bytes stay outside ordinary Git; held-out data never tunes thresholds/page-policy/hardening/resource limits; vector/hybrid content is never silently rasterized; exact-head and post-merge CI are mandatory; Stage 4 remains blocked until separate Stage 3 PASS is production-effective.

## Binding delivery sequence

```text
Stage 0  Roadmap update
Stage 1  Real and explicitly authorized test dataset
Stage 2  Complete quality-analysis system
Stage 3  Multi-page PDF pipeline
Stage 4  Safety calibration with real data
Stage 5  Accessible teacher review interface
Stage 6  Identity, network and production infrastructure
Stage 7  Preview release
Stage 8  DocRes optional candidate
Stage 9  Multi-engine comparator
Stage 10 ST Restore Selector
Stage 11 ST Restore image model
Stage 12 Music-application integrations
```

## Stage 1

**State:** COMPLETE / PASS / production-effective. Accepted Stage 2 entry main `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.

Canonical digests: catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`; historical C15/C16 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` / `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## Stage 2

**State:** COMPLETE / PASS / production-effective. Execution-evidence main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; final acceptance / Stage 3 entry main `87198a5a917ab6b3efc277762016a5f5b0dd3aab`; post-merge Run #228 (`33609061197`) Python 3.11/3.12 SUCCESS. Frozen execution evidence digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

## Stage 3 — Multi-page PDF pipeline

**State:** ACTIVE.  
**Tracking:** Issue #90.  
**Core main / CI:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa` / Run #232.  
**Authorized-execution main / CI:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b` / Run #235.  
**Purpose-grant main / CI:** `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238.  
**Active focused branch / PR:** `stage3-real-corpus-runner` / **PR #99 (non-draft)**.

PR #99 replaces Draft PR #98 after the Draft→Ready connector failed on `Repository.fullDatabaseId`. PR #98 was closed unmerged; no gate was bypassed. Its exact head `7778cdf790daa806efd166d9d3bf1f5a011ecc71` passed Run #243 (`33639819769`) on Python 3.11/3.12 before replacement. The replacement branch is being reconciled to PR #99, so a fresh exact-head run after this commit is mandatory.

ADR 0017 selects `pypdfium2==5.13.0` / PDFium. Resource defaults remain uncalibrated: 200 DPI; 64 pages; 40M pixels/page; 160M aggregate; 8,000-pixel dimension; page-object depth 15.

### Purpose/custody boundary

Development Stage 3 execution requires `pdf_pipeline_evaluation`; held-out execution requires `held_out_evaluation`. PR #96 made Beethoven/Barley grant overlay production-effective. Grant set `stage3.purpose-grants.beethoven-barley.v1` canonical SHA-256 `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`. Restrictions: development, `managed_standard`, `stage1_offline`, `external_export=false`. Training, calibration, publication, demonstration and held-out permission changes remain non-grants. Chopin remains held-out evaluation only.

### Real-corpus runner — PR #99

PR #99 carries the fail-closed runner for exactly Beethoven, Barley and Chopin. It requires exact renderer binding/catalog/item identities; keeps sources/private outputs outside ordinary Git; executes Beethoven/Barley through the purpose overlay and Chopin through held-out custody; emits only public-safe receipts; and preserves `heldOutThresholdTuningUsed=false`, `stage3ExitPass=false`, `stage4EntryAuthorized=false`.

### Remaining Stage 3 exit gates

1. fresh exact-head Python 3.11/3.12 CI for final PR #99 head;
2. clean review/thread/base/head checks;
3. merge exact verified head and pass post-merge main CI;
4. materialize exact approved Beethoven/Barley/Chopin custody bytes;
5. run production Stage 3 batch;
6. freeze public-safe execution evidence only;
7. limitations review;
8. separate machine-readable Stage 3 final-exit acceptance;
9. keep Stage 4 blocked unless PASS is production-effective.

## Stage 4

**State:** NOT STARTED / BLOCKED pending Stage 3 final exit PASS.

## Stages 5–12

**State:** NOT STARTED.

## Current next safe action

Finish PR #99 reconciliation, require fresh exact-head Repository validation on Python 3.11/3.12, re-read reviews/threads/base/head, merge only the verified head, then require post-merge main CI. Real corpus execution remains a separate approved-custody step.
