# ST Score Restore Engine — Technical Specification

**Status:** Current architecture; Stage 2 COMPLETE / PASS acceptance slice  
**Version:** 0.6.1-doc  
**Date:** 2026-09-02  
**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Stage 2 evidence main:** `ffea7f5aa618187f3cabcfb49801804e3f6658bf`

## 1. Scope

ST Score Restore Engine is a safety-first visual restoration and validation service for music-score and guitar-TAB documents. Supported intake families include PDF, JPG/JPEG, PNG and phone-captured score images.

This repository is not an OMR engine. It produces visual analysis and `restoration_variant` evidence. Downstream OMR occurs only after a selected visual source crosses ScoreMosaic Safe Intake.

## 2. Architectural invariants

1. Source bytes are immutable.
2. A derivative never silently replaces the source.
3. Music-score/TAB preservation has veto priority over cosmetic improvement.
4. Safety validation precedes comparator eligibility.
5. Rejected candidates cannot win and the immutable original remains selectable.
6. Exact SHA-256 is the artifact identity boundary.
7. Rights, privacy, purpose, retention, provenance and custody remain independent fail-closed gates.
8. Evaluation admission does not imply calibration, training or publication permission.
9. Real corpus artifact bytes remain outside ordinary Git.
10. Historical C15/C16 evidence is immutable.
11. CI evidence is exact-head scoped; head movement invalidates it.
12. Stage 1 is COMPLETE / PASS.
13. Stage 2 is COMPLETE / PASS by a separate evidence-bound acceptance decision; its thresholds remain uncalibrated engineering defaults.
14. Held-out data may not tune Stage 2 thresholds or hardening constants.
15. Stage 3 is ENTRY ELIGIBLE / NOT STARTED and must use a new focused branch after the acceptance commit is production-effective.

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
- CI: Python 3.11 and 3.12;
- API: `0.5.0`;
- OpenCV: `opencv-python-headless==4.13.0.92`;
- NumPy: `2.3.5`;
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

Stage 2 production analyzer version is `0.1.1`; approved-custody execution contract version is `0.1.0`.

### 6.1 Analyzer contract

`src/st_score_restore/quality_analysis.py` provides deterministic quality analysis for accepted PNG/JPEG bytes and vector-preservation handling for digital PDFs. It:

- reuses immutable input inspection;
- enforces bounded decode size;
- applies display orientation without changing source bytes;
- binds reports to source SHA-256 and deterministic configuration digest;
- preserves raw metrics separately from finding states;
- uses `uncalibrated_engineering_defaults`;
- records held-out threshold tuning as false;
- fails closed when evidence is unsupported.

Measured/evidence dimensions include orientation, skew, page/perspective geometry, crop risk, blur, glare, shadow, uneven illumination, noise, JPEG compression/quantization evidence, low-resolution/DPI evidence and geometric staff/TAB visibility indicators.

A quality finding is not an OMR result and does not infer note, rhythm, string/fret or musical correctness.

### 6.2 Approved-custody execution

`src/st_score_restore/stage2_custody_execution.py` is the only approved Stage 2 real-corpus execution boundary. Before analysis it validates canonical catalog membership, artifact state, dataset review, revocation/deletion state, retention, exact split/purpose permission, storage/environment restrictions, exact admitted SHA-256 and exact byte size.

Development maps only to `quality_evaluation`; held-out maps only to `held_out_evaluation`. C17D retains `managed_restricted` storage and `external_export=false`.

Public execution receipts contain no detailed quality metrics/findings. Detailed reports remain custody-only unless independently authorized.

### 6.3 Real accepted-corpus execution evidence

Frozen public evidence is `evidence/stage2/corpus/execution-evidence.v1.json`, canonical digest:

`78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`

Five accepted items matched exact SHA-256 and byte size before execution:

- Beethoven scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
- C17A combined staff+TAB PNG — `analyzed`;
- C17B digital guitar-TAB PDF — `not_applicable_vector_pdf`, vector preserved;
- C17C held-out Chopin scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
- C17D held-out deidentified phone-photo JPEG — `analyzed`, `managed_restricted`, export blocked.

Run #220 (`33606224352`) passed Python 3.11/3.12 on PR #87 exact head `7d6c812dd09a1ce42ae91d224f9d08992884b77a`. PR #87 merged to main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; post-merge Run #221 (`33607016064`) passed Python 3.11/3.12.

### 6.4 Stage 2 final acceptance

`evidence/stage2/corpus/stage2-exit-acceptance.v1.json` records a separate `PASS` decision bound to the exact execution evidence, PR head, merge main and post-merge CI.

Accepted limitations are explicit:

- scanned/hybrid PDF pixel analysis is intentionally deferred to the Stage 3 renderer;
- digital PDFs remain vector-preserved;
- thresholds remain uncalibrated until Stage 4;
- detailed real-corpus evidence remains custody-only;
- C17D detailed export remains blocked;
- no representativeness, absence-of-bias, restoration-effectiveness, OMR-improvement or musical-correctness claim is established;
- training, calibration and publication remain unauthorized.

## 7. Stage 3 boundary

**State:** ENTRY ELIGIBLE / NOT STARTED.

Stage 3 may start only after the Stage 2 acceptance slice is merged and its post-merge main CI is green. It must be a separate branch/PR. The Stage 2 acceptance PR must not contain Stage 3 renderer implementation.

Stage 3 owns multi-page PDF rendering/pipeline work while preserving exact source identity, page order, vector-content policy and original fallback. Unsupported pages fail safely; vector pages are not silently rasterized.

## 8. Stage 4 boundary

**State:** NOT STARTED.

Stage 4 owns real-data threshold calibration. Stage 2 engineering defaults must not be described as calibrated.

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
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

## 11. Prohibited scope in the acceptance slice

Do not rewrite historical evidence, add real corpus bytes to ordinary Git, infer training/calibration/publication rights, tune thresholds on held-out items, or add Stage 3 renderer implementation to the Stage 2 acceptance PR.
