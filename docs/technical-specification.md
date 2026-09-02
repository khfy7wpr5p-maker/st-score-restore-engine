# ST Score Restore Engine — Technical Specification

**Status:** Current architecture; Stage 3 ACTIVE  
**Version:** 0.7.0-doc  
**Date:** 2026-09-02  
**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`

## 1. Scope

ST Score Restore Engine is a safety-first visual restoration and validation service for music-score and guitar-TAB documents. Supported intake families include PDF, JPG/JPEG, PNG and phone-captured score images.

This repository is not an OMR engine. It produces visual analysis and derivative evidence. Downstream OMR occurs only after a selected visual source crosses ScoreMosaic Safe Intake.

## 2. Architectural invariants

1. Source bytes are immutable.
2. A derivative never silently replaces the source.
3. Music-score/TAB preservation has veto priority over cosmetic improvement.
4. Safety validation precedes comparator eligibility.
5. Rejected/unsupported candidates cannot win and the immutable original remains selectable.
6. Exact SHA-256 is the artifact identity boundary.
7. Rights, privacy, purpose, retention, provenance and custody remain independent fail-closed gates.
8. Evaluation admission does not imply calibration, training or publication permission.
9. Real corpus artifact bytes remain outside ordinary Git.
10. Historical C15/C16 and Stage 2 execution evidence are immutable.
11. CI evidence is exact-head scoped; head movement invalidates it.
12. Stage 1 is COMPLETE / PASS.
13. Stage 2 is COMPLETE / PASS / production-effective; its thresholds remain uncalibrated engineering defaults.
14. Held-out data may not tune Stage 2/3 thresholds or hardening constants.
15. Stage 3 is ACTIVE and owns the explicit multi-page PDF renderer boundary.
16. Vector PDF page content must not be silently rasterized.
17. Stage 4 is NOT STARTED / BLOCKED until explicit Stage 3 exit PASS.

## 3. Processing architecture

```text
Input document
    ↓
Immutable source registration / structural inspection
    ↓
If PDF: Stage 3 page enumeration + page-object policy
    ├─ raster_only → bounded PDFium PNG derivative
    ├─ vector_only → preserve vector page
    ├─ hybrid → preserve + review in core slice
    └─ unknown/over-limit → original fallback + review
    ↓
Deterministic quality analysis for raster inputs/derivatives
    ↓
OpenCV restoration candidate
    ↓
Music-score / TAB safety validation
    ↓
Comparator eligibility
    ↓
Original-aware selection
    ↓
Selected visual source variant
    ↓
ScoreMosaic Safe Intake
    ↓
OMR → MusicXML
```

ADR 0015 remains binding for validation/comparator/original-fallback ordering. ADR 0017 defines the Stage 3 PDF renderer and page-policy boundary.

## 4. Runtime baseline

- Python: `>=3.11,<3.13`;
- CI: Python 3.11 and 3.12;
- API: `0.5.0`;
- OpenCV: `opencv-python-headless==4.13.0.92`;
- NumPy: `2.3.5`;
- PDF renderer binding: `pypdfium2==5.13.0` / PDFium;
- source identity: exact SHA-256;
- ordinary Git real corpus artifact bytes: zero.

## 5. Stage 1 accepted data boundary

Stage 1 final acceptance remains at `evidence/stage1c/corpus/stage1-exit-acceptance.v1.json`. Accepted Stage 2 entry main: `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.

Expanded-v2 remains 5 real / 0 synthetic, development 3 items / 3 source families and held-out 2 items / 2 source families, with no source-family leakage or duplicate exact artifact digest.

Canonical v2 SHA-256 values:

- catalog: `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot: `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- coverage report: `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Historical C15 snapshot remains `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`; historical C16 report remains `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## 6. Stage 2 Complete Quality Analysis

Stage 2 is COMPLETE / PASS / production-effective. Production analyzer version is `0.1.1`; approved-custody execution contract version is `0.1.0`.

Frozen public execution evidence is `evidence/stage2/corpus/execution-evidence.v1.json`, canonical digest:

`78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`

Five accepted items matched exact SHA-256 and byte size before execution:

- Beethoven scanned PDF — historical `deferred_stage3_renderer` / `pdf_renderer_not_available`;
- C17A combined staff+TAB PNG — `analyzed`;
- C17B digital guitar-TAB PDF — `not_applicable_vector_pdf`, vector preserved;
- C17C held-out Chopin scanned PDF — historical `deferred_stage3_renderer` / `pdf_renderer_not_available`;
- C17D held-out deidentified phone-photo JPEG — `analyzed`, `managed_restricted`, export blocked.

Stage 2 evidence main is `ffea7f5aa618187f3cabcfb49801804e3f6658bf`. Final acceptance PR #89 merged to `87198a5a917ab6b3efc277762016a5f5b0dd3aab`; post-merge Run #228 (`33609061197`) passed Python 3.11/3.12.

The earlier execution evidence remains immutable with its historical Stage 3 authorization fields unchanged; final Stage 2 PASS is a separate acceptance layer.

## 7. Stage 3 Multi-page PDF Pipeline

**State:** ACTIVE under Issue #90.  
**Entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`.  
**Entry CI:** Run #228 (`33609061197`) SUCCESS on Python 3.11 / 3.12.  
**Core branch:** `stage3-multipage-pdf-core`.

### 7.1 Renderer decision

ADR 0017 selects PDFium through `pypdfium2==5.13.0`. The binding is pinned as an exact runtime dependency and must be available as a wheel in both supported Python versions.

The renderer is used only after existing immutable input inspection. PDFium provides authoritative Stage 3 page enumeration, page geometry, page-object inspection and raster rendering for eligible pages.

### 7.2 Page-level policy

`src/st_score_restore/pdf_pipeline.py` classifies page evidence before rendering:

- `raster_only`: image evidence with no detected text/path/shading vector evidence; may render;
- `vector_only`: text/path/shading evidence without image evidence; preserve vector page, no raster derivative;
- `hybrid`: image and vector evidence coexist; preserve original page and require review in first core slice;
- `unknown_or_empty`: original fallback and review.

Form content is traversed only to a bounded depth. Unknown content does not authorize rasterization.

### 7.3 Raster derivative contract

An eligible raster-only page is rendered as a deterministic PNG derivative. The page record binds:

- exact source SHA-256;
- source page index;
- derivative SHA-256;
- PNG media type;
- render DPI;
- pixel dimensions/count;
- subsequent deterministic Stage 2 quality-analysis result.

Derivative bytes remain separate from the public-safe manifest. The source PDF remains unchanged and selectable.

### 7.4 Resource bounds

Initial engineering defaults:

- render DPI 200;
- maximum pages 64;
- maximum rendered pixels/page 40,000,000;
- maximum aggregate rendered pixels 160,000,000;
- maximum render dimension 8,000 pixels;
- maximum page-object depth 15.

Page-count overflow rejects the PDF. Per-page render limits produce fail-closed original fallback/review. These values are uncalibrated and were not tuned with held-out data.

### 7.5 Determinism and non-claims

The Stage 3 manifest records stable source identity, page order, renderer/binding version, configuration digest, page policy, derivative provenance and explicit false claims for OMR, musical correctness, restoration effectiveness, calibration and training authorization.

Stage 3 is a document/rendering pipeline, not an OMR system or musical-correction system.

### 7.6 Validation

`tools/validate_stage3_pdf_pipeline.py` and `tests/test_pdf_pipeline.py` use synthetic PDFs only and require:

- deterministic output for identical bytes/configuration;
- source SHA-256 preservation;
- page-order preservation;
- raster-only rendering;
- vector-page preservation;
- no silent vector rasterization;
- original fallback;
- page/resource limits;
- Python 3.11/3.12 compatibility.

## 8. Stage 4 boundary

**State:** NOT STARTED / BLOCKED pending Stage 3 exit PASS.

Stage 4 owns real-data threshold calibration. Stage 2/3 engineering defaults must not be described as calibrated.

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

## 10. Validation commands

```bash
python tools/validate_dependency_lock.py
python tools/validate_repository.py
python tools/validate_architecture_consistency.py
python tools/build_stage1_snapshot.py --check
python tools/evaluate_stage1_coverage_bias.py --check --require-insufficient
python tools/build_stage1_expanded_snapshot.py --check
python tools/validate_stage1_exit_acceptance.py
python tools/validate_stage2_quality_analysis.py
python tools/validate_stage2_custody_execution.py
python tools/validate_stage2_corpus_execution_evidence.py
python tools/validate_stage2_exit_acceptance.py
python tools/validate_stage3_pdf_pipeline.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

## 11. Prohibited scope in Stage 3 core

Do not rewrite historical evidence, add real corpus bytes to ordinary Git, infer training/calibration/publication rights, tune thresholds on held-out items, perform OMR/musical inference, silently rasterize vector/hybrid content, or begin Stage 4 calibration.
