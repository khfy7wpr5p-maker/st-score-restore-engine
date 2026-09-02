# ST Score Restore Engine

AI-assisted, safety-first visual restoration and validation engine for music scores and guitar TAB supplied as PDF, JPG/JPEG, PNG, or phone-captured sheet-music images.

## Processing boundary

```text
PDF / JPG / JPEG / PNG / Phone photo
              ↓
Immutable source registration + inspection
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

This repository is not an OMR engine. Source bytes remain immutable, exact SHA-256 is the artifact identity boundary, and rejected candidates cannot replace the original fallback.

## Current production and stage state

- **Stage 1 — real and explicitly authorized evaluation corpus:** COMPLETE / PASS.
- **Stage 2 — Complete Quality Analysis:** COMPLETE / PASS acceptance recorded in this slice. The accepted evidence main is `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; post-merge Repository validation Run #221 (`33607016064`) succeeded on Python 3.11 and 3.12.
- **Stage 3 — multi-page PDF pipeline:** ENTRY ELIGIBLE / NOT STARTED. Stage 3 work must begin only in a new focused branch after the Stage 2 acceptance commit is merged and its own post-merge main CI is green.
- **Stage 4 — real-data safety calibration:** NOT STARTED. Stage 2 thresholds remain `uncalibrated_engineering_defaults`.

Stage 2 final acceptance is machine-readable at `evidence/stage2/corpus/stage2-exit-acceptance.v1.json`. The acceptance does not authorize training, calibration or publication and does not establish musical correctness, OMR improvement, restoration effectiveness, representativeness or absence of bias.

## Stage 1 accepted evidence

Historical C15/C16 evidence remains immutable. Expanded-v2 contains 5 real / 0 synthetic items, with 3 development source families and 2 held-out source families, no source-family leakage, no duplicate artifact SHA-256, and Chopin metadata v2 selected once while v1 is excluded.

Canonical Stage 1 v2 digests:

- catalog: `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot: `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- coverage report: `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Historical C15 snapshot: `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`. Historical C16 report: `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## Stage 2 accepted evidence

Production analyzer version is `0.1.1`; custody execution contract version is `0.1.0`. The accepted five-item corpus was exercised through approved custody with exact SHA-256 and exact byte-size gates before analysis.

Frozen public execution evidence:

- `evidence/stage2/corpus/execution-evidence.v1.json`
- canonical digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`

Controlled outcomes:

- 2 raster items: `analyzed`;
- 1 digital PDF: `not_applicable_vector_pdf`, vector preserved;
- 2 scanned/hybrid PDFs: `deferred_stage3_renderer` with `pdf_renderer_not_available`;
- held-out threshold tuning: false;
- real corpus artifact bytes in ordinary Git: zero;
- C17D detailed held-out report: `managed_restricted`, `external_export=false`.

The two scanned/hybrid PDF deferrals are accepted Stage 2 limitations. They deliberately preserve the Stage 3 renderer boundary rather than claiming pixel analysis that Stage 2 does not own.

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

- Python: `>=3.11,<3.13`
- CI: Python 3.11 and 3.12
- OpenCV: `opencv-python-headless==4.13.0.92`
- NumPy: `2.3.5`
- API: `/api/v1`, version `0.5.0`
- source identity: exact SHA-256
- ordinary Git real corpus bytes: zero

Validation includes:

```bash
python tools/validate_dependency_lock.py
python tools/validate_repository.py
python tools/validate_architecture_consistency.py
python tools/build_stage1_expanded_snapshot.py --check
python tools/validate_stage1_exit_acceptance.py
python tools/validate_stage2_quality_analysis.py
python tools/validate_stage2_custody_execution.py
python tools/validate_stage2_corpus_execution_evidence.py
python tools/validate_stage2_exit_acceptance.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

## References

- `docs/technical-specification.md`
- `docs/roadmap.md`
- `docs/architecture-consistency-audit.md`
- `docs/stage-2-current-status.md`
- `docs/stage-2-approved-custody-execution-contract.md`
- `docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json`
- ADR 0015 — restoration pipeline validation/comparator/OMR handoff
- ADR 0016 — Stage 1C risk-tiered artifact custody
