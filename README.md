# ST Score Restore Engine

Safety-first visual restoration and validation engine for music scores and guitar TAB supplied as PDF, JPG/JPEG, PNG, or phone-captured images.

## Processing boundary

```text
PDF / JPG / JPEG / PNG / Phone photo
              ↓
Immutable source registration + inspection
              ↓
Rights / privacy / purpose / custody / exact-byte gates
              ↓
Stage 3 PDF page policy when input is PDF
              ├─ raster_only → bounded PDFium derivative
              ├─ vector_only → preserve vector content
              ├─ hybrid → preserve + review
              └─ unsupported/over-limit → original fallback + review
              ↓
Deterministic quality analysis
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

This repository is not an OMR engine. Source bytes remain immutable, exact SHA-256 is the artifact identity boundary, and rejected or unsupported derivatives cannot replace the original fallback.

## Current production truth — 2026-09-02

- **Stage 1:** COMPLETE / PASS. Accepted Stage 2 entry main: `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.
- **Stage 2:** COMPLETE / PASS / production-effective. Execution-evidence main: `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; final acceptance main / Stage 3 entry main: `87198a5a917ab6b3efc277762016a5f5b0dd3aab`; post-merge Run #228 (`33609061197`) passed Python 3.11/3.12.
- **Stage 3:** ACTIVE under Issue #90. PDFium core main: `29b4244eeaeb2239ff959e6dd6d4128311f005fa` / Run #232. Authorized-execution main: `d834ed42e3f553308aef7f6adb7e8cb873593f0b` / Run #235. Purpose-grant main: `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238. Active focused PR: **#99** (`stage3-real-corpus-runner`), replacing Draft PR #98 after the Draft→Ready connector failed; #98 is closed unmerged.
- **Stage 4:** NOT STARTED / BLOCKED pending explicit Stage 3 final exit PASS.

PR #98 exact head `7778cdf790daa806efd166d9d3bf1f5a011ecc71` passed Repository validation Run #243 (`33639819769`) on Python 3.11 and 3.12 before replacement. PR #99 points to the same branch/head lineage, but the replacement itself requires fresh exact-head CI after this reconciliation commit.

## Immutable Stage 1/2 evidence

Historical C15/C16 and Stage 2 execution evidence are not rewritten retroactively.

Canonical Stage 1 expanded-v2 digests:

- catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- coverage report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Historical C15 snapshot: `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`. Historical C16 report: `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

Frozen Stage 2 public execution evidence: `evidence/stage2/corpus/execution-evidence.v1.json`, canonical digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

## Stage 3 production boundary

ADR 0017 selects `pypdfium2==5.13.0` / PDFium. `src/st_score_restore/pdf_pipeline.py` applies page-level policy before rendering. Raster-only pages may render; vector-only pages remain vector-preserved; hybrid pages remain preserved and review-oriented; unknown/empty/over-limit pages retain original fallback.

Initial Stage 3 resource limits are uncalibrated engineering defaults only: 200 DPI, 64 pages, 40M rendered pixels/page, 160M aggregate rendered pixels, 8,000-pixel render dimension and page-object depth 15. Held-out data did not tune these values.

`src/st_score_restore/stage3_custody_execution.py` separates renderer capability from corpus authorization. Development execution requires `pdf_pipeline_evaluation`; held-out execution requires `held_out_evaluation`; exact SHA-256 and byte size must match before processing.

## Stage 3 purpose grants

The accepted Stage 1 catalog remains immutable with historical `pdf_pipeline_evaluation=not_requested` values. A separate production-effective overlay at `evidence/stage3/governance/purpose-grants.v1.json` grants only Beethoven and Barley the Stage 3 development purpose.

Grant set: `stage3.purpose-grants.beethoven-barley.v1`; canonical SHA-256 `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`.

Restrictions: development split only, `managed_standard`, `stage1_offline`, `external_export=false`. Training, calibration, publication, demonstration and held-out permission changes are not granted. Chopin remains held-out under existing `held_out_evaluation` only.

## Stage 3 real-corpus runner

PR #99 carries the fail-closed offline runner for exactly Beethoven, Barley and Chopin. It requires `pypdfium2==5.13.0`, the accepted catalog digest, exact admitted identities and custody paths outside the ordinary Git working tree. Public output is redacted; detailed manifests, quality findings and rendered derivatives remain custody-only. The runner explicitly keeps `heldOutThresholdTuningUsed=false`, `stage3ExitPass=false`, and `stage4EntryAuthorized=false`.

Real Stage 3 corpus execution is not yet frozen as accepted evidence. Stage 3 exit still requires runner merge + post-merge CI, approved-custody execution, public-safe evidence, limitations review, separate final-exit acceptance, exact-head CI and post-merge main CI.

## Binding development order

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

## Development baseline

- Python `>=3.11,<3.13`
- CI Python 3.11 and 3.12
- OpenCV `opencv-python-headless==4.13.0.92`
- NumPy `2.3.5`
- PDF renderer binding `pypdfium2==5.13.0`
- API `/api/v1`, version `0.5.0`
- ordinary Git real corpus bytes: zero

Validation includes `tools/validate_architecture_consistency.py`, both Stage 3 validators, `tools/validate_stage3_real_corpus_runner.py`, full unit tests and Python compile.

## Safety/non-claims

Stage 3 does not perform OMR, infer musical correctness, establish restoration effectiveness, tune held-out thresholds, authorize calibration/training/publication, or move real corpus artifacts into ordinary Git. Stage 4 remains blocked until a separate Stage 3 PASS is production-effective.
