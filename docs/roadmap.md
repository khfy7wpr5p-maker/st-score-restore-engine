# ST Score Restore Engine — Development Roadmap

**Document status:** Approved binding sequence; Stage 2 ACTIVE  
**Version:** 0.3.0  
**Date:** 2026-09-02  
**Current Stage 2 tracking:** Issue #83 / PR #84  
**Accepted Stage 2 entry main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`

## 1. Authority and invariant rules

This roadmap is the binding development order. Repository truth is merged `main` plus accepted deterministic evidence; open PR work is in progress until merged. Historical evidence is not rewritten to make later results retroactive.

Non-negotiable rules:

1. Original source bytes remain immutable.
2. Music-score/TAB preservation has veto priority over cosmetic improvement.
3. A later stage cannot start before the previous stage has explicit accepted exit evidence.
4. Draft, Ready-for-review, exact-head CI, review/thread reconciliation and merge are separate gates.
5. Rights, privacy, purpose, provenance, retention and custody remain independent fail-closed controls.
6. Teacher approval, evaluation admission, calibration permission and training consent are separate decisions.
7. Real corpus artifact bytes remain outside ordinary Git.
8. Held-out data is not used for threshold tuning.
9. A queued, cancelled, skipped, zero-job or old-head CI run is not transition evidence.
10. Stage 3 remains blocked until explicit Stage 2 exit PASS.

## 2. Binding delivery sequence

```text
Stage 0  Roadmap update
      ↓
Stage 1  Real and explicitly authorized test dataset
      ↓
Stage 2  Complete quality-analysis system
      ↓
Stage 3  Multi-page PDF pipeline
      ↓
Stage 4  Safety calibration with real data
      ↓
Stage 5  Accessible teacher review interface
      ↓
Stage 6  Identity, network and production infrastructure
      ↓
Stage 7  Preview release
      ↓
Stage 8  DocRes optional candidate
      ↓
Stage 9  Multi-engine comparator
      ↓
Stage 10 ST Restore Selector
      ↓
Stage 11 ST Restore image model
      ↓
Stage 12 Music-application integrations
```

## 3. Stage 0 — Roadmap update

**State:** COMPLETE.

## 4. Stage 1 — Real and explicitly authorized test dataset

**State:** COMPLETE / PASS.

Stage 1 final exit acceptance is machine-readable at `evidence/stage1c/corpus/stage1-exit-acceptance.v1.json`. PR #82 merged into main `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`; post-merge Repository validation Run #203 (`33588190548`) passed on Python 3.11 and 3.12.

Accepted expanded-v2 structure:

- 5 real items / 0 synthetic items;
- development: 3 items / 3 source families;
- held out: 2 items / 2 source families;
- no cross-split source-family leakage;
- no duplicate exact artifact SHA-256;
- Chopin metadata v2 selected exactly once; v1 excluded from the new aggregate;
- ordinary Git contains zero real corpus artifact bytes.

Canonical v2 evidence digests:

- catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- coverage report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Historical C15/C16 remain immutable. Stage 1 PASS does not establish corpus representativeness, absence of bias, restoration effectiveness, OMR improvement, musical correctness, model-training permission or calibration permission. `source_selection_concentration` remains an accepted known limitation for the Stage 2 evaluation purpose.

## 5. Stage 2 — Complete quality-analysis system

**State:** ACTIVE.  
**Tracking:** Issue #83.  
**Implementation PR:** #84 / `stage2-complete-quality-analysis`.

**Goal:** measure document degradation comprehensively and reproducibly before Stage 3 PDF expansion or Stage 4 real-data threshold calibration.

Required quality dimensions:

- orientation/display-orientation evidence;
- skew angle and confidence;
- page/perspective geometry and confidence;
- crop/page-boundary risk;
- blur/sharpness and motion-blur-oriented evidence where deterministically supportable;
- glare/highlight clipping;
- shadow/local darkness;
- uneven illumination/background variation;
- noise;
- JPEG/compression artifact evidence where applicable;
- low resolution / DPI evidence;
- capture/page-type evidence where deterministically knowable;
- staff/TAB geometric visibility indicators that do not claim OMR or musical correctness.

PR #84 initial slice provides a versioned deterministic OpenCV analyzer for accepted PNG/JPEG inputs, source SHA-256 binding, configuration digest, separate raw metrics and findings, bounded decode, synthetic deterministic regressions and a dedicated CI validator.

Stage 2 interpretation rules:

- thresholds are engineering defaults and remain **uncalibrated** until Stage 4;
- held-out threshold tuning is forbidden;
- unsupported/ambiguous evidence fails closed;
- analysis never modifies source bytes;
- no generative operation, symbol completion, OMR correction or musical inference;
- digital PDFs remain vector preservation; scanned/hybrid PDF pixel analysis is not pulled forward before Stage 3 renderer approval.

Stage 2 is not complete merely because the analyzer code exists or synthetic tests pass.

**Stage 2 exit requires all of the following:**

1. deterministic analyzer/report contract merged and exact-head CI green on Python 3.11/3.12;
2. current architecture/status documentation aligned;
3. authorized development/evaluation corpus can be exercised through approved custody without moving real artifact bytes into ordinary Git;
4. execution evidence is source-digest-bound, reproducible and reviewable;
5. held-out items remain evaluation-only and are not used for threshold selection;
6. known limitations are recorded, including categories that remain `not_assessed` or uncalibrated;
7. review/thread/head reconciliation is clean;
8. post-merge main validation is green;
9. a separate Stage 2 exit acceptance explicitly returns PASS.

Until all exit gates pass, **Stage 3 remains BLOCKED**.

## 6. Stage 3 — Multi-page PDF pipeline

**State:** BLOCKED pending Stage 2 exit PASS.

Goal: safely process supported multi-page PDFs while preserving source identity, page order and vector-content policy. Requires an approved renderer/dependency decision. Unsupported pages fail safely with original fallback; vector pages are not silently rasterized.

## 7. Stage 4 — Safety calibration with real data

**State:** NOT STARTED.

Goal: calibrate decision/review thresholds on authorized development/calibration evidence while preserving held-out isolation. Stage 2 engineering defaults must not be presented as calibrated thresholds.

## 8. Stage 5 — Accessible teacher review interface

**State:** NOT STARTED.

Goal: accessible, evidence-bound source/candidate/risk review with stale-screen rejection and append-only decisions.

## 9. Stage 6 — Identity, network and production infrastructure

**State:** NOT STARTED.

Goal: deployable identity, encrypted storage, production queue/database, network protection, observability, backup/restore and incident controls.

## 10. Stage 7 — Preview release

**State:** NOT STARTED.

Goal: bounded, reversible preview after Stages 1–6 are accepted.

## 11. Stage 8 — DocRes optional candidate

**State:** NOT STARTED.

DocRes may only be evaluated as an optional candidate and cannot bypass safety validation or original fallback.

## 12. Stage 9 — Multi-engine comparator

**State:** NOT STARTED.

Rejected candidates cannot win; immutable original remains selectable.

## 13. Stage 10 — ST Restore Selector

**State:** NOT STARTED.

Selector may not override safety rejection or remove original fallback.

## 14. Stage 11 — ST Restore image model

**State:** NOT STARTED.

Any model training requires independent explicit training authorization.

## 15. Stage 12 — Music-application integrations

**State:** NOT STARTED.

Integration remains through versioned contracts. A selected visual source must still cross ScoreMosaic Safe Intake before downstream OMR.

## 16. Current next safe action

Finish PR #84 architecture/documentation reconciliation; require fresh exact-head Python 3.11/3.12 validation; reconcile reviews/threads/base/head; move Draft → Ready and merge only if those gates remain clean; verify post-merge main CI. Then continue Stage 2 with authorized-corpus execution evidence through approved custody. Do not declare Stage 2 PASS or begin Stage 3 before a separate exit acceptance.
