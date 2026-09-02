# ST Score Restore Engine — Technical Specification

**Status:** Current architecture; Stage 3 ACTIVE  
**Version:** 0.8.1-doc  
**Date:** 2026-09-02  
**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Production main before active PR #99:** `6ebe160309c562e9841a3c313d5ca507592f1386`

## 1. Scope and invariants

ST Score Restore Engine is a safety-first visual restoration and validation service for music-score and guitar-TAB documents. It is not an OMR engine.

Source bytes are immutable; exact SHA-256 defines artifact identity; derivatives never silently replace sources; rights/privacy/purpose/retention/provenance/custody are independent fail-closed gates; historical Stage 1/2 evidence is immutable; real corpus and derivative bytes remain outside ordinary Git; held-out data never tunes Stage 2/3 thresholds, page policy, hardening constants or renderer/resource limits; vector/hybrid PDF content is never silently rasterized; CI is exact-head scoped; Stage 4 remains blocked pending explicit Stage 3 final exit PASS.

## 2. Processing architecture

```text
Input document
    ↓
Immutable source registration / structural inspection
    ↓
Dataset rights / privacy / purpose / custody / exact-byte gates when corpus-backed
    ↓
If PDF: Stage 3 page enumeration + page-object policy
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

ADR 0015 remains binding for validation/comparator/original-fallback ordering. ADR 0017 defines the Stage 3 PDF renderer/page-policy boundary.

## 3. Runtime baseline

- Python `>=3.11,<3.13`
- CI Python 3.11 / 3.12
- API `0.5.0`
- OpenCV `opencv-python-headless==4.13.0.92`
- NumPy `2.3.5`
- PDF renderer `pypdfium2==5.13.0` / PDFium
- ordinary Git real corpus artifact bytes: zero

## 4. Stage 1 accepted boundary

Stage 1 is COMPLETE / PASS. Accepted Stage 2 entry main `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.

Canonical v2 SHA-256: catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; coverage report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`. Historical C15/C16 remain `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` / `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## 5. Stage 2 Complete Quality Analysis

Stage 2 is COMPLETE / PASS / production-effective. Execution-evidence main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; final acceptance / Stage 3 entry main `87198a5a917ab6b3efc277762016a5f5b0dd3aab`; post-merge Run #228 (`33609061197`) Python 3.11/3.12 SUCCESS. Frozen execution evidence digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

Historical Stage 2 PDF deferrals/vector-preservation outcomes remain immutable now that Stage 3 owns the renderer.

## 6. Stage 3 Multi-page PDF Pipeline

**State:** ACTIVE under Issue #90.  
**Core main / CI:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa` / Run #232 (`33615937390`).  
**Authorized-execution main / CI:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b` / Run #235 (`33618108204`).  
**Purpose-grant main / CI:** `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238 (`33620323970`).  
**Active branch / PR:** `stage3-real-corpus-runner` / **non-draft PR #99**.

PR #99 replaces Draft PR #98 after the Draft→Ready GraphQL connector failed on `Repository.fullDatabaseId`. PR #98 was closed unmerged; no merge/review gate was bypassed. Head `7778cdf790daa806efd166d9d3bf1f5a011ecc71` passed Run #243 (`33639819769`) on Python 3.11/3.12 before replacement. This PR-number reconciliation moves the head, so final PR #99 exact-head CI must run again.

### 6.1 Page policy

`src/st_score_restore/pdf_pipeline.py` classifies before rendering: `raster_only` may render; `vector_only` is preserved; `hybrid` is preserved/reviewed; `unknown_or_empty` uses original fallback/review. Unknown content never authorizes rasterization.

### 6.2 Resource bounds

Uncalibrated engineering defaults only: 200 DPI; 64 pages; 40,000,000 pixels/page; 160,000,000 aggregate pixels; 8,000-pixel maximum dimension; page-object traversal depth 15.

### 6.3 Authorized corpus execution

`src/st_score_restore/stage3_custody_execution.py` requires canonical catalog validation, admitted PDF kind, approved review, non-revoked/non-deletion state, valid retention, exact split-specific purpose/restrictions, exact SHA-256 and exact byte size.

Development → `pdf_pipeline_evaluation`; held-out → `held_out_evaluation`. Public receipts are redacted; detailed page records, metrics/findings and rendered derivatives remain custody-only.

### 6.4 Purpose-grant overlay

Historical `catalog.v2.json` remains unchanged. Production-effective overlay `evidence/stage3/governance/purpose-grants.v1.json`: grant set `stage3.purpose-grants.beethoven-barley.v1`, canonical SHA-256 `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`.

It grants `pdf_pipeline_evaluation` only to exact Beethoven and Barley development artifacts, restricted to development / `managed_standard` / `stage1_offline` / `external_export=false`. Training, calibration, publication, demonstration and held-out permission changes remain unauthorized. Chopin remains existing held-out evaluation only.

### 6.5 Real-corpus runner — PR #99

`src/st_score_restore/stage3_real_corpus_execution.py` and `tools/run_stage3_real_corpus_execution.py` implement the fail-closed batch for exactly Beethoven, Barley and Chopin. The runner requires exact renderer/catalog/item identities, keeps source/private-output paths outside ordinary Git, executes Beethoven/Barley through the purpose-grant wrapper and Chopin through held-out custody, and produces redacted public evidence while detailed manifests/metrics/PNG derivatives remain custody-only.

The runner records `heldOutThresholdTuningUsed=false`, `stage3ExitPass=false`, and `stage4EntryAuthorized=false`.

### 6.6 Stage 3 exit

Stage 3 exit is not PASS. It requires final PR #99 exact-head CI, clean review/thread/base/head gates, exact-head merge, post-merge main CI, exact approved custody bytes, production runner execution, public-safe evidence, explicit limitations review and separate versioned exit acceptance.

## 7. Stage 4 boundary

**State:** NOT STARTED / BLOCKED pending Stage 3 final exit PASS. Stage 4 owns real-data safety calibration.

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

CI must run dependency/repository/architecture validators, Stage 1/2 accepted-evidence validators, `validate_stage3_pdf_pipeline.py`, `validate_stage3_custody_execution.py`, `validate_stage3_real_corpus_runner.py`, full unit tests and Python compile on 3.11 and 3.12.

## 10. Prohibited Stage 3 scope

Do not rewrite historical evidence, put real corpus/derivative bytes in ordinary Git, infer dataset permission from general approval, tune on held-out data, perform OMR/musical inference, silently rasterize vector/hybrid content, claim musical/restoration/OMR correctness, or begin Stage 4 calibration.
