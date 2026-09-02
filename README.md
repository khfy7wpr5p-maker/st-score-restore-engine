# ST Score Restore Engine

AI-assisted, safety-first visual restoration and validation engine for music scores and guitar TAB supplied as PDF, JPG/JPEG, PNG, or phone-captured sheet-music images.

## Processing boundary

```text
PDF / JPG / JPEG / PNG / Phone photo
              ↓
Immutable source registration + inspection
              ↓
Rights / privacy / purpose / custody / exact-byte gates
              ↓
Deterministic quality analysis
              ↓
Stage 3 page-level PDF policy / raster-only rendering when applicable
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

This repository is not an OMR engine. Source bytes remain immutable, exact SHA-256 is the artifact identity boundary, and rejected/unsupported derivatives cannot replace the original fallback.

## Current production and stage state

Accepted Stage 2 entry main is `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.

- **Stage 1 — real and explicitly authorized evaluation corpus:** COMPLETE / PASS.
- **Stage 2 — Complete Quality Analysis:** COMPLETE / PASS / production-effective. Frozen execution-evidence main is `ffea7f5aa618187f3cabcfb49801804e3f6658bf`. Final acceptance PR #89 merged to main `87198a5a917ab6b3efc277762016a5f5b0dd3aab`; post-merge Repository validation Run #228 (`33609061197`) succeeded on Python 3.11 and 3.12.
- **Stage 3 — multi-page PDF pipeline:** ACTIVE under Issue #90. The first PDFium core slice merged through PR #92 to main `29b4244eeaeb2239ff959e6dd6d4128311f005fa`; post-merge Run #232 (`33615937390`) succeeded on Python 3.11 and 3.12. The current focused slice is `stage3-authorized-pdf-execution`.
- **Stage 4 — real-data safety calibration:** NOT STARTED / BLOCKED pending explicit Stage 3 exit PASS. Stage 2/3 engineering thresholds remain uncalibrated.

Stage 2 final acceptance is machine-readable at `evidence/stage2/corpus/stage2-exit-acceptance.v1.json`. Historical execution evidence is not rewritten retroactively.

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
- 2 scanned/hybrid PDFs: historical `deferred_stage3_renderer` with `pdf_renderer_not_available`;
- held-out threshold tuning: false;
- real corpus artifact bytes in ordinary Git: zero;
- C17D detailed held-out report: `managed_restricted`, `external_export=false`.

The two Stage 2 PDF deferrals remain immutable evidence. Stage 3 resolves the renderer boundary prospectively rather than rewriting those outcomes.

## Stage 3 multi-page PDF core

ADR 0017 selects `pypdfium2==5.13.0` / PDFium. The core is production-effective at main `29b4244eeaeb2239ff959e6dd6d4128311f005fa` after PR #92 and post-merge Run #232.

`src/st_score_restore/pdf_pipeline.py` applies page-level policy before rendering:

- `raster_only` pages may be rendered to PNG derivatives;
- `vector_only` pages are preserved without rasterization;
- `hybrid` pages are preserved and require review;
- unknown/empty pages use original fallback and require review.

Every raster derivative is bound to the immutable source SHA-256 and page index and is then analyzed by the deterministic Stage 2 quality analyzer. The source PDF remains selectable and unchanged.

Initial Stage 3 bounds are engineering defaults only: 200 DPI, maximum 64 pages, 40M pixels per rendered page, 160M aggregate rendered pixels, 8,000-pixel render dimension and object traversal depth 15. Held-out data did not tune these values.

## Stage 3 authorized PDF execution boundary

`src/st_score_restore/stage3_custody_execution.py` keeps dataset authorization separate from renderer capability. It requires the canonical dataset review/custody state, split-specific purpose permission, restrictions, retention and exact admitted SHA-256/byte size before `process_pdf_bytes(...)` can run.

Purpose mapping is intentionally strict:

- development → `pdf_pipeline_evaluation`;
- held-out → `held_out_evaluation`.

The accepted development PDF records currently have `pdf_pipeline_evaluation=not_requested`, so they remain fail-closed for real Stage 3 execution. The held-out Chopin record has `held_out_evaluation=granted`, but real execution still requires exact custody bytes; those bytes are not stored in ordinary Git.

Public Stage 3 receipts contain only identity, authorization, renderer version, manifest digest and page-summary counts. Detailed page manifests, quality findings/metrics and derivative PNG bytes remain custody-only. This slice does not grant new dataset permissions and does not complete real Stage 3 corpus execution.

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
- PDF renderer binding: `pypdfium2==5.13.0`
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
python tools/validate_stage3_pdf_pipeline.py
python tools/validate_stage3_custody_execution.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

## Safety/non-claims

Stage 3 does not perform OMR, infer musical correctness, establish restoration effectiveness, tune held-out thresholds, authorize calibration/training/publication, or move real corpus artifacts into ordinary Git. A general project-development approval is not a dataset purpose grant.

## References

- `docs/technical-specification.md`
- `docs/roadmap.md`
- `docs/architecture-consistency-audit.md`
- `docs/stage-2-current-status.md`
- `docs/stage-3-current-status.md`
- `docs/stage-2-approved-custody-execution-contract.md`
- `docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json`
- ADR 0015 — restoration pipeline validation/comparator/OMR handoff
- ADR 0016 — Stage 1C risk-tiered artifact custody
- ADR 0017 — Stage 3 PDFium multi-page PDF pipeline
