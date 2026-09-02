# ST Score Restore Engine — Technical Specification

**Status:** Current architecture; Stage 3 COMPLETE / PASS / production-effective  
**Version:** 0.9.0-doc  
**Date:** 2026-09-02  
**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Stage 3 acceptance main:** `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0` / Run #253 (`33646323461`) SUCCESS  
**Stage 4:** ENTRY ELIGIBLE / NOT STARTED

## 1. Scope and invariants

ST Score Restore Engine is a safety-first visual restoration and validation service for music-score and guitar-TAB documents. It is not an OMR engine.

Source bytes are immutable; exact SHA-256 defines artifact identity; derivatives never silently replace sources; rights/privacy/purpose/retention/provenance/custody are independent fail-closed gates; historical evidence is immutable; real corpus and derivative bytes remain outside ordinary Git; held-out data never tunes Stage 2/3 thresholds, page policy, hardening constants or renderer/resource limits; vector/hybrid PDF content is never silently rasterized; CI is exact-head scoped.

## 2. Processing architecture

```text
Input document
    ↓
Immutable source registration / structural inspection
    ↓
Rights / privacy / purpose / custody / exact-byte gates
    ↓
If PDF: page enumeration + page-object policy
    ├─ raster_only → bounded PDFium PNG derivative
    ├─ vector_only → preserve vector page
    ├─ hybrid → preserve + review
    └─ unknown/over-limit → original fallback + review
    ↓
Deterministic quality analysis for raster inputs/derivatives
    ↓
OpenCV restoration candidate
    ↓
Music-score / TAB safety validation
    ↓
Comparator eligibility / original fallback
    ↓
Selected visual source variant
    ↓
ScoreMosaic Safe Intake → OMR → MusicXML
```

ADR 0015 remains binding for validation/comparator/original-fallback ordering. ADR 0017 defines the PDFium page-policy boundary.

## 3. Runtime baseline

- Python `>=3.11,<3.13`
- CI Python 3.11 / 3.12
- API `0.5.0`
- OpenCV `opencv-python-headless==4.13.0.92`
- NumPy `2.3.5`
- PDF renderer `pypdfium2==5.13.0` / PDFium
- ordinary Git real corpus/derivative bytes: zero

## 4. Stage 1 accepted boundary

Stage 1 is COMPLETE / PASS / production-effective. Accepted Stage 2 entry main `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.

Canonical v2 SHA-256: catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; coverage report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`. Historical C15/C16 remain `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` / `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## 5. Stage 2 Complete Quality Analysis

Stage 2 is COMPLETE / PASS / production-effective. Execution-evidence main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; final acceptance / Stage 3 entry main `87198a5a917ab6b3efc277762016a5f5b0dd3aab`; Run #228 (`33609061197`) Python 3.11/3.12 SUCCESS. Frozen execution evidence digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

Historical Stage 2 PDF deferrals/vector-preservation outcomes remain immutable now that Stage 3 owns the renderer.

## 6. Stage 3 Multi-page PDF Pipeline

**State:** COMPLETE / PASS / production-effective.  
**Core main / CI:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa` / Run #232.  
**Authorized-execution main / CI:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b` / Run #235.  
**Purpose-grant main / CI:** `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238.  
**Runner runtime main / CI:** `5e682f1933a7167fc142689306352fe53b4b1833` / Run #246.  
**Execution-evidence main / CI:** `b15d91ff3fbf21b47a0e484b5a337c4611a17355` / Run #251.  
**Acceptance main / CI:** `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0` / Run #253.

### 6.1 Page policy

`src/st_score_restore/pdf_pipeline.py` classifies before rendering: `raster_only` may render; `vector_only` is preserved; `hybrid` is preserved/reviewed; `unknown_or_empty` uses original fallback/review. Unknown content never authorizes rasterization.

### 6.2 Resource bounds

Uncalibrated engineering defaults: 200 DPI; 64 pages; 40,000,000 pixels/page; 160,000,000 aggregate pixels; 8,000-pixel maximum dimension; page-object traversal depth 15. Stage 3 PASS does not convert these defaults into calibrated limits.

### 6.3 Authorized corpus execution

Development execution requires `pdf_pipeline_evaluation`; held-out execution requires `held_out_evaluation`. Exact catalog, split, purpose, retention, environment, storage class, SHA-256 and byte size are checked before processing. Public receipts are redacted; detailed page records, metrics/findings and rendered derivatives remain custody-only.

### 6.4 Purpose-grant overlay

Historical `catalog.v2.json` remains unchanged. Production overlay `evidence/stage3/governance/purpose-grants.v1.json` has canonical SHA-256 `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`. It grants Stage 3 evaluation only to exact Beethoven and Barley development artifacts. Chopin remains held-out evaluation only. Training, calibration, publication and demonstration are not inferred.

### 6.5 Real-corpus execution

`src/st_score_restore/stage3_real_corpus_execution.py` executes exactly Beethoven, Barley and Chopin under the production custody/purpose contracts and exact `pypdfium2==5.13.0`.

Accepted public execution summary: 3 items / 14 pages / 12 raster pages rendered / 2 vector pages preserved / 0 review-required; all page order preserved; vector rasterization false; held-out threshold tuning false.

Execution evidence: `evidence/stage3/corpus/execution-evidence.v1.json`, canonical SHA-256 `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`.

Limitations review: `evidence/stage3/corpus/limitations-review.v1.json`, `PASS_WITH_ACCEPTED_LIMITATIONS`, canonical SHA-256 `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`.

### 6.6 Stage 3 final acceptance

`evidence/stage3/corpus/stage3-exit-acceptance.v1.json` records `decision=PASS`, `stage3ExitPass=true`, `stage4EntryEligible=true`, `stage4Started=false`. Canonical SHA-256: `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

Evidence PR #101 exact head `88737a8dec70e8c84075e141dd9364794b3605bf` passed Run #250; evidence main `b15d91ff3fbf21b47a0e484b5a337c4611a17355` passed Run #251. Acceptance PR #102 exact head `959474ac8487eb15dfcaf27b3a1224872182f03b` passed Run #252; acceptance main `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0` passed Run #253.

## 7. Stage 4 boundary

**State:** ENTRY ELIGIBLE / NOT STARTED.

Stage 4 owns real-data safety calibration. Before Stage 4 starts, a separate entry/start decision must define calibration corpus use, anti-leakage rules, objectives, metrics, thresholds and acceptance gates. Stage 3 PASS alone does not authorize calibration, training or publication.

## 8. Binding development sequence

```text
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

## 9. Required validation

CI runs dependency/repository/architecture validators, Stage 1/2 accepted-evidence validators, Stage 3 PDF/custody/runner/execution-evidence/final-acceptance validators, full unit tests and Python compile on 3.11 and 3.12.

## 10. Prohibited inference

Do not rewrite historical evidence, put real corpus/derivative bytes in ordinary Git, infer dataset permission from general approval, tune Stage 3 on held-out data, perform OMR/musical inference, silently rasterize vector/hybrid content, claim musical/restoration/OMR correctness, or treat Stage 4 entry eligibility as Stage 4 started.