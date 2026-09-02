# ST Score Restore Engine — Development Roadmap

**Document status:** Approved binding sequence; Stage 3 ACTIVE  
**Version:** 0.4.0  
**Date:** 2026-09-02  
**Stage 3 tracking:** Issue #90  
**Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`

## 1. Authority and invariant rules

Repository truth is merged `main` plus accepted deterministic evidence. Historical evidence is not rewritten to make later decisions retroactive.

1. Original source bytes remain immutable.
2. Music-score/TAB preservation has veto priority over cosmetic improvement.
3. A later stage cannot start before the previous stage has explicit accepted exit evidence.
4. Draft, Ready, exact-head CI, review/thread reconciliation, merge and post-merge CI are separate gates.
5. Rights, privacy, purpose, provenance, retention and custody remain independent fail-closed controls.
6. Evaluation admission, calibration permission and training consent are separate decisions.
7. Real corpus artifact bytes remain outside ordinary Git.
8. Held-out data is not used for threshold tuning or hardening decisions.
9. A queued, cancelled, skipped, zero-job or old-head CI run is not transition evidence.
10. Vector PDF content must not be silently rasterized.
11. Stage 4 starts only after explicit Stage 3 exit PASS.

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

## 3. Stage 0 — Roadmap update

**State:** COMPLETE.

## 4. Stage 1 — Real and explicitly authorized test dataset

**State:** COMPLETE / PASS.

Stage 1 final acceptance remains recorded at `evidence/stage1c/corpus/stage1-exit-acceptance.v1.json`. Accepted Stage 2 entry main: `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.

Expanded-v2 remains 5 real / 0 synthetic, development 3 items / 3 source families, held-out 2 items / 2 source families, with no cross-split source-family leakage or duplicate artifact SHA-256. Historical C15/C16 remain immutable.

Canonical v2 digests:

- catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- coverage report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

## 5. Stage 2 — Complete quality-analysis system

**State:** COMPLETE / PASS / production-effective.  
**Accepted execution-evidence main:** `ffea7f5aa618187f3cabcfb49801804e3f6658bf`.  
**Final acceptance merge main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`.  
**Acceptance post-merge verification:** Run #228 (`33609061197`) SUCCESS on Python 3.11 / 3.12.

Stage 2 delivers deterministic, non-generative, measurement-first quality analysis with source SHA-256 binding, raw metrics separated from findings, fail-closed unsupported states, bounded decoding and approved-custody execution.

Frozen execution evidence digest: `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

Accepted limitations remain binding: the historical scanned/hybrid PDF execution outcomes remain `deferred_stage3_renderer`; digital PDFs remained vector-preserved; thresholds remain `uncalibrated_engineering_defaults`; detailed real-corpus reports remain custody-only; C17D remains `external_export=false`; no representativeness, bias-absence, restoration, OMR or musical-correctness claim is established.

## 6. Stage 3 — Multi-page PDF pipeline

**State:** ACTIVE.  
**Tracking:** Issue #90.  
**Entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`.  
**Entry verification:** Run #228 (`33609061197`) SUCCESS on Python 3.11 / 3.12.  
**Focused branch:** `stage3-multipage-pdf-core`.

### Stage 3 first core slice

ADR 0017 selects `pypdfium2==5.13.0` / PDFium for the first renderer boundary.

Core requirements:

1. preserve exact source SHA-256 and immutable source bytes;
2. use PDFium page enumeration for stable Stage 3 page count/order;
3. inspect page content before rendering;
4. render only `raster_only` pages;
5. preserve `vector_only` pages without rasterization;
6. preserve `hybrid` pages and require review in the first slice;
7. fail unknown/empty or over-limit pages to original fallback/review;
8. bind every derivative to source SHA-256 and page index;
9. run existing Stage 2 quality analysis on raster derivatives;
10. keep held-out tuning false and thresholds uncalibrated;
11. use synthetic PDFs for ordinary-Git tests;
12. keep Stage 4 blocked until a separate Stage 3 exit PASS.

Initial engineering bounds: 200 DPI, 64 pages, 40M pixels/page, 160M aggregate rendered pixels, 8,000-pixel render dimension and page-object depth 15.

The core slice does not authorize OMR, musical inference, calibration, training, publication, DocRes, selector logic or Stage 4 work.

### Stage 3 exit boundary

Stage 3 exit is not established by starting the renderer core. Exit will require merged/verified pipeline behavior, real authorized-corpus execution where permitted, explicit limitations review, exact-head/post-merge CI and a separate acceptance decision. Until then Stage 4 remains blocked.

## 7. Stage 4 — Safety calibration with real data

**State:** NOT STARTED / BLOCKED pending Stage 3 exit PASS.

Stage 4 owns real-data threshold calibration. Stage 2/3 engineering defaults must not be presented as calibrated thresholds.

## 8. Stage 5 — Accessible teacher review interface

**State:** NOT STARTED.

## 9. Stage 6 — Identity, network and production infrastructure

**State:** NOT STARTED.

## 10. Stage 7 — Preview release

**State:** NOT STARTED.

## 11. Stage 8 — DocRes optional candidate

**State:** NOT STARTED.

## 12. Stage 9 — Multi-engine comparator

**State:** NOT STARTED.

## 13. Stage 10 — ST Restore Selector

**State:** NOT STARTED.

## 14. Stage 11 — ST Restore image model

**State:** NOT STARTED. Any model training requires independent explicit training authorization.

## 15. Stage 12 — Music-application integrations

**State:** NOT STARTED.

## 16. Current next safe action

Complete the focused Stage 3 core slice, require exact-head Python 3.11/3.12 CI, reconcile review/thread/base/head state, merge only the exact verified head, and require post-merge main CI. Do not begin Stage 4 or real-data calibration.
