# ST Score Restore Engine — Development Roadmap

**Document status:** Approved binding sequence; Stage 2 exit PASS acceptance slice  
**Version:** 0.3.1  
**Date:** 2026-09-02  
**Stage 2 tracking:** Issue #83  
**Stage 2 accepted evidence main:** `ffea7f5aa618187f3cabcfb49801804e3f6658bf`

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
10. Stage 3 starts only after the Stage 2 PASS acceptance is production-effective.

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

**State:** COMPLETE / PASS acceptance recorded in this slice.  
**Tracking:** Issue #83.  
**Accepted evidence main:** `ffea7f5aa618187f3cabcfb49801804e3f6658bf`.  
**Post-merge verification:** Run #221 (`33607016064`) SUCCESS on Python 3.11 / 3.12.

Stage 2 delivers deterministic, non-generative, measurement-first quality analysis with source SHA-256 binding, raw metrics separated from findings, fail-closed unsupported states, bounded decoding, and approved-custody execution.

Measured/evidence dimensions include orientation, skew, perspective/page geometry, crop risk, blur, glare, shadow, uneven illumination, noise, JPEG compression evidence, low resolution/DPI and geometric staff/TAB visibility indicators.

### Stage 2 production chain

- PR #84 — deterministic quality-analysis core: merged;
- PR #85 — development-corpus hardening: merged;
- PR #86 — approved-custody execution boundary: merged;
- PR #87 — frozen five-item real-corpus execution evidence and validator: merged as `ffea7f5aa618187f3cabcfb49801804e3f6658bf`;
- PR #87 exact-head Run #220 (`33606224352`): Python 3.11 / 3.12 SUCCESS;
- post-merge main Run #221 (`33607016064`): Python 3.11 / 3.12 SUCCESS.

Frozen execution evidence digest: `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

### Stage 2 exit gates

All objective exit gates are satisfied by the separate `stage2.exit.acceptance.v1` decision:

1. deterministic analyzer/report contract merged and CI green;
2. architecture/status evidence reconciled in the acceptance slice;
3. authorized five-item corpus exercised through approved custody with exact SHA-256 and byte-size gates;
4. execution evidence is source-digest-bound, deterministic and reviewable;
5. held-out items remained evaluation-only and did not tune thresholds;
6. limitations explicitly reviewed;
7. PR #87 review/thread/head reconciliation clean;
8. post-merge main validation green;
9. separate machine-readable Stage 2 exit acceptance returns PASS.

Accepted limitations remain binding: scanned/hybrid PDF pixel analysis is deferred to the Stage 3 renderer; digital PDFs remain vector-preserved; thresholds remain `uncalibrated_engineering_defaults` until Stage 4; detailed real-corpus reports remain custody-only; C17D remains `external_export=false`; no representativeness, bias absence, restoration, OMR or musical-correctness claim is established.

## 6. Stage 3 — Multi-page PDF pipeline

**State:** ENTRY ELIGIBLE / NOT STARTED.

Stage 3 must begin only in a new focused branch after this Stage 2 acceptance slice is merged and its post-merge main CI is green. Its goal is to safely process supported multi-page PDFs while preserving source identity, page order and vector-content policy. It requires an explicit renderer/dependency decision. Unsupported pages fail safely with original fallback; vector pages are not silently rasterized.

## 7. Stage 4 — Safety calibration with real data

**State:** NOT STARTED.

Stage 4 owns real-data threshold calibration. Stage 2 engineering defaults must not be presented as calibrated thresholds.

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

Validate the Stage 2 acceptance slice on exact head, reconcile review/thread/base/head state, merge only if objective gates remain clean, and require post-merge main CI. Only then create a new focused Stage 3 branch. Do not combine Stage 3 implementation into the Stage 2 acceptance PR.
