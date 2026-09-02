# ST Score Restore Engine — Development Roadmap

**Document status:** Binding sequence; Stage 3 ACTIVE  
**Version:** 0.5.0  
**Date:** 2026-09-02  
**Tracking:** Issue #90  
**Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Stage 3 core main:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa`  
**Stage 3 authorized-execution main:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b`  
**Stage 3 purpose-grant main / current production baseline:** `6ebe160309c562e9841a3c313d5ca507592f1386`

## 1. Authority and invariant rules

Repository truth is merged `main` plus accepted deterministic evidence. Historical evidence is never rewritten to make later decisions retroactive.

1. Original source bytes remain immutable.
2. Music-score/TAB preservation has veto priority over cosmetic improvement.
3. A later stage cannot start before the previous stage has explicit accepted exit evidence.
4. Draft/Ready, exact-head CI, reviews/threads, merge and post-merge CI are separate gates.
5. Rights, privacy, purpose, provenance, retention and custody remain independent fail-closed controls.
6. Evaluation admission, calibration permission and training consent are separate decisions.
7. Real corpus artifact and rendered derivative bytes remain outside ordinary Git.
8. Held-out data is not used for threshold tuning, page-policy tuning or hardening decisions.
9. Old-head, queued, cancelled, skipped or zero-job CI is not transition evidence.
10. Vector/hybrid PDF content must not be silently rasterized.
11. Stage 4 starts only after explicit Stage 3 final exit PASS is production-effective.
12. General project approval does not grant a dataset purpose permission.

## 2. Binding delivery sequence

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

## 3. Stage 0

**State:** COMPLETE.

## 4. Stage 1

**State:** COMPLETE / PASS / production-effective.

Final acceptance remains at `evidence/stage1c/corpus/stage1-exit-acceptance.v1.json`. Accepted Stage 2 entry main: `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.

Expanded-v2 remains 5 real / 0 synthetic, 3 development source families and 2 held-out source families, with no cross-split family leakage or duplicate exact artifact digest.

Canonical digests: catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Historical C15/C16 remain immutable: `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` / `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## 5. Stage 2

**State:** COMPLETE / PASS / production-effective.  
**Execution-evidence main:** `ffea7f5aa618187f3cabcfb49801804e3f6658bf`.  
**Final acceptance / Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`.  
**Post-merge CI:** Run #228 (`33609061197`) SUCCESS on Python 3.11/3.12.

Frozen public execution evidence digest: `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

Historical PDF deferrals and vector-preservation outcomes remain immutable. Thresholds remain `uncalibrated_engineering_defaults` and Stage 4 owns calibration.

## 6. Stage 3 — Multi-page PDF pipeline

**State:** ACTIVE.  
**Tracking:** Issue #90.  
**Entry main / CI:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab` / Run #228.  
**Core main / CI:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa` / Run #232.  
**Authorized-execution main / CI:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b` / Run #235.  
**Purpose-grant main / CI:** `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238.  
**Active focused branch / PR:** `stage3-real-corpus-runner` / Draft PR #98.

### 6.1 Production-effective boundary

ADR 0017 selects `pypdfium2==5.13.0` / PDFium. Core invariants are exact source identity, stable page order, pre-render page classification, raster-only rendering, vector preservation, hybrid preservation/review, original fallback, bounded resources, derivative provenance, no held-out tuning and zero real corpus bytes in ordinary Git.

Initial bounds remain engineering defaults: 200 DPI; 64 pages; 40M pixels/page; 160M aggregate rendered pixels; 8,000-pixel dimension; page-object depth 15.

### 6.2 Purpose/custody boundary

Development Stage 3 execution requires `pdf_pipeline_evaluation`; held-out execution requires `held_out_evaluation`. PR #96 made the Beethoven/Barley purpose overlay production-effective at main `6ebe160309c562e9841a3c313d5ca507592f1386`; Run #238 passed Python 3.11/3.12.

Grant set `stage3.purpose-grants.beethoven-barley.v1` canonical SHA-256: `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`. It grants only the exact Beethoven and Barley artifacts for `pdf_pipeline_evaluation`, development split, `managed_standard`, `stage1_offline`, `external_export=false`. Training, calibration, publication, demonstration and held-out permission changes remain non-grants.

Chopin remains held-out under existing `held_out_evaluation` only and must never tune Stage 2/3 thresholds, page policies, renderer/resource limits or hardening constants.

### 6.3 PR #98 runner slice

PR #98 adds the fail-closed real-corpus runner for exactly Beethoven, Barley and Chopin. Pre-refresh exact head `696729f825ed23ee89edc972cbf46303f3ebba73` passed Run #242 (`33621535491`) on Python 3.11/3.12. This architecture-refresh commit moves the head, so a new exact-head run is mandatory.

The runner requires exact renderer binding, accepted catalog digest, exact item set, source/output paths outside the ordinary Git working tree, redacted public receipts and custody-only detailed manifests/metrics/PNG derivatives. It explicitly records `heldOutThresholdTuningUsed=false`, `stage3ExitPass=false`, `stage4EntryAuthorized=false`.

### 6.4 Stage 3 exit boundary

Stage 3 is **not yet PASS**. Remaining gates:

1. fresh exact-head CI for the reconciled PR #98 head;
2. clean review/thread/base/head checks;
3. merge PR #98 and pass post-merge main CI;
4. materialize the exact approved Beethoven/Barley/Chopin custody bytes;
5. run the production Stage 3 batch without putting source/derivative bytes in Git;
6. freeze only public-safe execution evidence;
7. perform explicit limitations review;
8. create a separate machine-readable Stage 3 final-exit acceptance;
9. keep Stage 4 blocked unless that decision is PASS and production-effective.

## 7. Stage 4

**State:** NOT STARTED / BLOCKED pending Stage 3 final exit PASS. Stage 4 owns real-data safety calibration.

## 8. Stage 5

**State:** NOT STARTED.

## 9. Stage 6

**State:** NOT STARTED.

## 10. Stage 7

**State:** NOT STARTED.

## 11. Stage 8

**State:** NOT STARTED.

## 12. Stage 9

**State:** NOT STARTED.

## 13. Stage 10

**State:** NOT STARTED.

## 14. Stage 11

**State:** NOT STARTED. Any model training requires independent explicit authorization.

## 15. Stage 12

**State:** NOT STARTED.

## 16. Current next safe action

Require a fresh exact-head Python 3.11/3.12 Repository validation for the reconciled PR #98 head. Merge only that verified head after clean reviews/threads/base checks; then require post-merge main CI. Real corpus execution remains a separate approved-custody step and Stage 4 remains blocked.
