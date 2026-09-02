# ST Score Restore Engine — Technical Specification

**Status:** Current architecture; Stage 3 ACTIVE  
**Version:** 0.8.0-doc  
**Date:** 2026-09-02  
**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Production main before active PR #98:** `6ebe160309c562e9841a3c313d5ca507592f1386`

## 1. Scope

ST Score Restore Engine is a safety-first visual restoration and validation service for music-score and guitar-TAB documents. Supported intake families include PDF, JPG/JPEG, PNG and phone-captured score images.

This repository is not an OMR engine. It produces visual analysis, restoration candidates and derivative evidence. Downstream OMR occurs only after selected visual evidence crosses the ScoreMosaic Safe Intake boundary.

## 2. Architectural invariants

1. Source bytes are immutable.
2. Exact SHA-256 is the artifact identity boundary.
3. A derivative never silently replaces the source.
4. Music-score/TAB preservation has veto priority over cosmetic improvement.
5. Rights, privacy, purpose, retention, provenance and custody are independent fail-closed gates.
6. Evaluation admission does not imply calibration, training, publication or demonstration permission.
7. Historical Stage 1/2 evidence is immutable.
8. Real corpus source and derivative bytes remain outside ordinary Git.
9. CI evidence is exact-head scoped; head movement invalidates it.
10. Stage 1 is COMPLETE / PASS.
11. Stage 2 is COMPLETE / PASS / production-effective; thresholds remain uncalibrated engineering defaults.
12. Stage 3 is ACTIVE and owns the explicit multi-page PDF renderer boundary.
13. Vector and hybrid PDF content must not be silently rasterized.
14. Renderer capability never grants dataset purpose permission.
15. Held-out data may not tune Stage 2/3 thresholds, page policy, hardening constants or renderer/resource limits.
16. Stage 4 remains NOT STARTED / BLOCKED until explicit Stage 3 final exit PASS is production-effective.

## 3. Processing architecture

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

ADR 0015 remains binding for validation/comparator/original-fallback ordering. ADR 0017 defines the Stage 3 PDF renderer and page-policy boundary.

## 4. Runtime baseline

- Python `>=3.11,<3.13`
- CI Python 3.11 / 3.12
- API `0.5.0`
- OpenCV `opencv-python-headless==4.13.0.92`
- NumPy `2.3.5`
- PDF renderer `pypdfium2==5.13.0` / PDFium
- ordinary Git real corpus artifact bytes: zero

## 5. Stage 1 accepted boundary

Stage 1 final acceptance remains at `evidence/stage1c/corpus/stage1-exit-acceptance.v1.json`. Accepted Stage 2 entry main: `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.

Expanded-v2 remains 5 real / 0 synthetic, 3 development families and 2 held-out families with no cross-split family leakage or duplicate exact artifact digest.

Canonical v2 SHA-256 values: catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; coverage report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Historical C15/C16 remain `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` / `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## 6. Stage 2 Complete Quality Analysis

Stage 2 is COMPLETE / PASS / production-effective. Execution-evidence main is `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; final acceptance main / Stage 3 entry main is `87198a5a917ab6b3efc277762016a5f5b0dd3aab`; post-merge Run #228 (`33609061197`) passed Python 3.11/3.12.

Frozen public execution evidence: `evidence/stage2/corpus/execution-evidence.v1.json`, canonical digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

Historical outcomes remain immutable, including scanned/hybrid PDF deferrals, digital-vector preservation, held-out non-tuning and custody-only detailed evidence.

## 7. Stage 3 Multi-page PDF Pipeline

**State:** ACTIVE under Issue #90.  
**Entry main / CI:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab` / Run #228 (`33609061197`).  
**Core main / CI:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa` / Run #232 (`33615937390`).  
**Authorized-execution main / CI:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b` / Run #235 (`33618108204`).  
**Purpose-grant main / CI:** `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238 (`33620323970`).  
**Active branch / PR:** `stage3-real-corpus-runner` / Draft #98.

### 7.1 Page policy

`src/st_score_restore/pdf_pipeline.py` classifies page evidence before rendering:

- `raster_only`: may render to deterministic PNG derivative;
- `vector_only`: preserve vector content, no raster derivative;
- `hybrid`: preserve original page and require review;
- `unknown_or_empty`: original fallback and review.

Unknown content never authorizes rasterization. Source PDFs remain unchanged and selectable.

### 7.2 Resource bounds

Engineering defaults only: 200 DPI; 64 pages; 40,000,000 pixels/rendered page; 160,000,000 aggregate rendered pixels; 8,000-pixel maximum dimension; page-object traversal depth 15. These are uncalibrated and were not selected from held-out results.

### 7.3 Authorized corpus execution

`src/st_score_restore/stage3_custody_execution.py` requires canonical catalog validation, admitted PDF kind, approved review, non-revoked/non-deletion state, valid retention, exact split-specific purpose, restrictions, exact SHA-256 and exact byte size before `process_pdf_bytes(...)`.

Normative purpose mapping:

- development → `pdf_pipeline_evaluation`;
- held-out → `held_out_evaluation`.

Public receipts contain only redacted identity/authorization/renderer/manifest/page-summary metadata. Detailed page records, metrics/findings and rendered derivatives remain custody-only.

### 7.4 Purpose-grant overlay

Historical `evidence/stage1c/corpus/catalog.v2.json` is unchanged. Production-effective grant overlay: `evidence/stage3/governance/purpose-grants.v1.json`, grant-set `stage3.purpose-grants.beethoven-barley.v1`, canonical SHA-256 `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`.

It grants `pdf_pipeline_evaluation` only to the exact Beethoven and Barley development artifacts, restricted to `development`, `managed_standard`, `stage1_offline`, `external_export=false`. Training, calibration, publication, demonstration and held-out permission changes remain unauthorized. Chopin remains governed only by existing `held_out_evaluation`.

### 7.5 Real-corpus execution runner — PR #98

`src/st_score_restore/stage3_real_corpus_execution.py` and `tools/run_stage3_real_corpus_execution.py` implement the fail-closed batch runner for exactly Beethoven, Barley and Chopin. It requires the exact renderer binding and accepted catalog digest, keeps source/output paths outside the ordinary Git working tree, executes Beethoven/Barley through the purpose-grant wrapper and Chopin only through the held-out custody gate, and produces redacted public evidence while detailed manifests/metrics/PNG derivatives remain custody-only.

The runner records `heldOutThresholdTuningUsed=false`, `stage3ExitPass=false`, and `stage4EntryAuthorized=false`.

PR #98 head `696729f825ed23ee89edc972cbf46303f3ebba73` passed Run #242 (`33621535491`) on Python 3.11/3.12 before this architecture-refresh commit. This commit moves the head and therefore requires a fresh exact-head run.

### 7.6 Stage 3 exit

Stage 3 real-corpus execution is not yet accepted/frozen and Stage 3 exit is not yet PASS. Exit requires exact approved custody bytes, production runner execution, public-safe evidence, explicit limitations review, separate versioned final-exit decision, exact-head CI and post-merge main CI. Held-out results cannot tune Stage 2/3 behavior.

## 8. Stage 4 boundary

**State:** NOT STARTED / BLOCKED pending Stage 3 final exit PASS. Stage 4 owns real-data safety calibration.

## 9. Binding development sequence

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

## 10. Required validation

CI must run dependency/repository/architecture validators, Stage 1/2 accepted-evidence validators, `validate_stage3_pdf_pipeline.py`, `validate_stage3_custody_execution.py`, `validate_stage3_real_corpus_runner.py`, full unit tests and Python compile on 3.11 and 3.12.

## 11. Prohibited Stage 3 scope

Do not rewrite historical evidence, place real corpus or rendered derivative bytes in ordinary Git, infer dataset permission from general approval, tune on held-out data, perform OMR/musical inference, silently rasterize vector/hybrid content, claim musical/restoration/OMR correctness, or begin Stage 4 calibration.
