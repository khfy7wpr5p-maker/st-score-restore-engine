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

This repository is not an OMR engine. It produces visual analysis and restoration evidence. ADR 0015 keeps safety validation before comparator eligibility and preserves the immutable original as a selectable fallback. DocRes, ST Image AI, the multi-engine comparator, selector and learned restoration model remain future stages.

## Current production and stage state

Accepted production main at Stage 2 entry is `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.

- **Stage 1 — real and explicitly authorized evaluation corpus:** COMPLETE / PASS.
- **Stage 2 — Complete Quality Analysis:** ACTIVE under Issue #83 and PR #84.
- **Stage 3 — multi-page PDF pipeline:** BLOCKED until explicit Stage 2 exit PASS.
- **Stage 4 — real-data safety calibration:** NOT STARTED; Stage 2 thresholds remain uncalibrated engineering defaults.

Stage 1 exit acceptance is recorded in `evidence/stage1c/corpus/stage1-exit-acceptance.v1.json`. Post-merge Repository validation Run #203 (`33588190548`) passed on Python 3.11 and 3.12 for main `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.

## Stage 1 accepted evidence

Historical C15/C16 evidence remains immutable. The historical C16 result remains `insufficient` for its original two-item snapshot and is not rewritten by later evidence.

Accepted expanded-v2 evidence contains 5 real items / 0 synthetic items, with development 3 items / 3 source families and held-out 2 items / 2 source families, no source-family leakage, no duplicate exact artifact SHA-256, and Chopin metadata v2 selected once while v1 is excluded.

Canonical v2 digests:

- catalog: `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot: `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- coverage report: `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Accepted C17 exact-artifact bindings remain:

- C17A combined staff+TAB: `36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb`;
- C17B standalone guitar TAB: `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`;
- C17C held-out Chopin: `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`;
- C17D deidentified phone photo: `abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5`.

Real corpus score/PDF/image bytes remain outside ordinary Git. Training and calibration permission are not inferred from evaluation admission.

## Stage 2 quality-analysis core

PR #84 adds a deterministic OpenCV analyzer for accepted PNG/JPEG inputs. The report is bound to immutable source SHA-256 and configuration digest and records raw metrics separately from qualitative findings.

Current measured dimensions include:

- orientation metadata/display orientation;
- skew angle and confidence;
- page-boundary / perspective geometry and confidence;
- crop/margin risk;
- blur/sharpness;
- glare/highlight clipping;
- shadow/local darkness;
- uneven illumination/background variation;
- noise;
- JPEG compression/quantization evidence where applicable;
- low-resolution / DPI evidence;
- geometric staff/TAB visibility indicators.

These are visual evidence only. They do not establish musical correctness, OMR accuracy, restoration effectiveness, training readiness or calibration readiness. Low-confidence or unsupported evidence fails closed to review-oriented or `not_assessed` states. Digital PDFs remain vector-preservation territory; scanned/hybrid PDF pixel analysis waits for the Stage 3 renderer boundary.

## Binding development order

```text
Stage 0  Roadmap update
      ↓
Stage 1  Real and explicitly authorized test dataset
      ↓
Stage 2  Complete quality-analysis system
      ↓
Stage 3  Multi-page PDF pipeline
      ↓
Stage 4  Safety calibration with real data
      ↓
Stage 5  Accessible teacher review interface
      ↓
Stage 6  Identity, network and production infrastructure
      ↓
Stage 7  Preview release
      ↓
Stage 8  DocRes optional candidate
      ↓
Stage 9  Multi-engine comparator
      ↓
Stage 10 ST Restore Selector
      ↓
Stage 11 ST Restore image model
      ↓
Stage 12 Music-application integrations
```

Every transition remains evidence-gated. Head movement invalidates exact-head CI evidence.

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
python tools/validate_fixture_catalog.py
python tools/build_stage1_expanded_snapshot.py --check
python tools/validate_stage1_exit_acceptance.py
python tools/validate_stage2_quality_analysis.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

## References

- `docs/technical-specification.md`
- `docs/roadmap.md`
- `docs/architecture-consistency-audit.md`
- `docs/stage-1-exit-evidence.md`
- `docs/stage-2-current-status.md`
- `docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json`
- ADR 0015 — restoration pipeline validation/comparator/OMR handoff
- ADR 0016 — Stage 1C risk-tiered artifact custody
