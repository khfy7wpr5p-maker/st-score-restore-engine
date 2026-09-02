# ST Score Restore Engine — Technical Specification

**Status:** Current architecture; Stage 2 ACTIVE  
**Version:** 0.6.0-doc  
**Date:** 2026-09-02  
**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Accepted Stage 2 entry main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`

## 1. Scope

ST Score Restore Engine is a safety-first visual restoration and validation service for music-score and guitar-TAB documents. Supported intake families include PDF, JPG/JPEG, PNG and phone-captured score images.

This repository is not an OMR engine. It produces visual analysis and `restoration_variant` evidence. Downstream OMR occurs only after a selected visual source crosses ScoreMosaic Safe Intake.

The current runtime uses deterministic OpenCV processing. DocRes, ST Image AI, multi-engine comparison, selector logic, learned restoration models and production music-application integrations remain later-stage work.

## 2. Architectural invariants

1. Source bytes are immutable.
2. A derivative never silently replaces the source.
3. Music-score/TAB preservation has veto priority over cosmetic improvement.
4. Safety validation precedes comparator eligibility.
5. Rejected candidates cannot win.
6. The immutable original remains selectable.
7. Exact SHA-256 is the artifact identity boundary.
8. Rights, privacy, purpose, retention, provenance, custody and admission remain independent fail-closed gates.
9. Teacher approval does not imply evaluation admission, calibration permission or training permission.
10. Real corpus artifact bytes remain outside ordinary Git.
11. Historical C15/C16 evidence is immutable.
12. Open PR state is not production truth.
13. CI evidence is exact-head scoped; head movement invalidates it.
14. Stage 1 is COMPLETE / PASS.
15. Stage 2 is ACTIVE and uses uncalibrated engineering thresholds only.
16. Held-out data may not tune Stage 2 thresholds.
17. Stage 3 cannot start before explicit Stage 2 exit PASS.

## 3. Processing architecture

```text
Input document
    ↓
Immutable source registration / structural inspection
    ↓
Deterministic quality analysis
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

ADR 0015 remains binding for validation/comparator/original-fallback ordering.

## 4. Runtime baseline

- Python: `>=3.11,<3.13`;
- CI compatibility: Python 3.11 and 3.12;
- API: `0.5.0`;
- OpenCV: `opencv-python-headless==4.13.0.92`;
- NumPy: `2.3.5`;
- default job state: in-memory;
- optional local durable state: SQLite metadata + content-addressed blobs;
- built-in HTTP adapter: local/non-production boundary only.

Production identity, encrypted cloud storage, external durable production queues and public network exposure remain outside the current stage.

## 5. Stage 1 accepted data boundary

Stage 1 final acceptance is recorded in `evidence/stage1c/corpus/stage1-exit-acceptance.v1.json`. PR #82 merged into main `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`; post-merge Repository validation Run #203 (`33588190548`) passed on Python 3.11 and 3.12.

Historical C15/C16 remain immutable. Historical C16 still describes its original two-item snapshot as `insufficient`.

Expanded-v2 accepted invariants:

- 5 real items / 0 synthetic items;
- development = 3 items / 3 source families;
- held out = 2 items / 2 source families;
- no cross-split source-family leakage;
- no duplicate exact artifact SHA-256;
- Chopin v2 selected exactly once, v1 excluded from the new aggregate;
- ordinary Git real artifact bytes = 0.

Canonical v2 SHA-256 values:

- catalog: `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot: `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- coverage report: `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

C17 exact artifacts remain bound as:

- C17A: `36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb`;
- C17B: `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`;
- C17C: `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`;
- C17D: `abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5`.

Stage 1 PASS does not establish representativeness, absence of bias, restoration effectiveness, OMR improvement, musical correctness, calibration permission or training permission.

## 6. Stage 2 Complete Quality Analysis

Stage 2 is ACTIVE under Issue #83 and PR #84.

### 6.1 Analyzer contract

`src/st_score_restore/quality_analysis.py` provides deterministic quality analysis for accepted PNG/JPEG bytes. The analyzer:

- reuses immutable input inspection for media acceptance and source identity;
- enforces bounded decode size before and after OpenCV decode;
- applies EXIF/display orientation consistently without modifying the source;
- binds each report to source SHA-256;
- binds the configuration to a deterministic configuration digest;
- preserves raw metrics separately from qualitative finding states;
- records that thresholds are engineering defaults and uncalibrated;
- records that held-out threshold tuning is false.

Digital PDFs return a vector-preservation-oriented result rather than pixel analysis. Scanned/hybrid PDF pixel analysis fails closed pending the Stage 3 renderer boundary.

### 6.2 Quality dimensions

Stage 2 measures or records evidence for:

- orientation/display orientation;
- skew angle and confidence;
- page-boundary and perspective geometry confidence;
- crop/page-margin risk;
- blur/sharpness;
- glare/highlight clipping;
- shadow/local darkness;
- uneven illumination/background variation;
- noise;
- JPEG compression/quantization evidence where applicable;
- low-resolution and DPI evidence;
- geometric staff/TAB visibility indicators.

A quality finding is not an OMR result. Staff/TAB indicators are image-geometry evidence only and do not infer note, rhythm, string/fret or musical correctness.

### 6.3 Fail-closed interpretation

Unsupported or weak evidence yields review-oriented or `not_assessed` output rather than certainty. Stage 2 may not:

- generate or complete notation symbols;
- correct OMR or MusicXML;
- infer musical correctness;
- use held-out items for threshold selection;
- claim calibrated decision thresholds;
- claim restoration or OMR improvement merely because image metrics are available.

### 6.4 Stage 2 tests and validation

Synthetic regression tests cover deterministic report identity and the quality metric/finding contract without placing real corpus bytes in Git. `tools/validate_stage2_quality_analysis.py` is wired into repository CI.

PR #84 must pass exact-head Python 3.11/3.12 repository validation, review/thread/base/head reconciliation and post-merge main validation before its core is considered production-main truth.

## 7. Authorized-corpus execution boundary

Stage 2 exit requires execution evidence on the accepted evaluation corpus through approved custody. Real artifact bytes must not be copied into ordinary Git to achieve this.

Execution evidence must be metadata/report-only and bind at least:

- dataset item ID;
- exact source SHA-256;
- analyzer/configuration version/digest;
- quality report digest or canonical evidence identity;
- execution disposition;
- split and purpose constraints;
- custody/profile provenance sufficient to show the bytes were accessed through the admitted path.

Held-out items remain evaluation-only. Stage 2 may observe held-out metric behavior but may not change thresholds based on held-out results.

## 8. Stage 2 exit and Stage 3 boundary

Stage 2 exit is separate from PR #84 code merge. Exit requires deterministic and reviewable authorized-corpus execution evidence, architecture alignment, exact-head/post-merge CI, clean review gates, limitations and a separate evidence-bound PASS decision.

Until that acceptance is PASS, **Stage 3 remains BLOCKED**.

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
python tools/validate_fixture_catalog.py
python tools/build_stage1_snapshot.py --check
python tools/evaluate_stage1_coverage_bias.py --check --require-insufficient
python tools/build_stage1_expanded_snapshot.py --check
python tools/validate_stage1_exit_acceptance.py
python tools/validate_stage2_quality_analysis.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

## 11. Prohibited scope in the current stage

Do not rewrite historical C15/C16 evidence, add real corpus bytes to ordinary Git, infer training/calibration rights, tune thresholds on held-out items, start Stage 3 PDF renderer work, activate DocRes/ST Image AI, or claim musical/OMR/restoration correctness from Stage 2 image metrics.
