# ST Score Restore Engine

AI-assisted, safety-first restoration and validation engine for music scores and guitar TAB supplied as PDF, JPG/JPEG, PNG, or phone-captured sheet-music photos.

## Approved processing flow

```text
PDF / JPG / JPEG / PNG / Phone photo
              ↓
Immutable source + document/quality analysis
              ↓
┌──────────────────────────────────────────────┐
│ OpenCV        DocRes          ST Image AI    │
│ current       future          future         │
└──────────────────────────────────────────────┘
              ↓
Per-variant music-score / TAB safety validation
              ↓
Comparator
(original always remains a selectable baseline)
              ↓
Selected source variant
              ↓
ScoreMosaic Safe Intake
              ↓
ScoreMosaic OMR
              ↓
MusicXML
```

ADR 0015 locks the mandatory ordering: a restoration derivative must pass safety validation before comparator eligibility, a rejected derivative cannot win, and the immutable original remains selectable. The current runtime is OpenCV-only. DocRes, ST Image AI, the multi-engine comparator, selector, OMR dispatch, model training and later roadmap stages are not active.

## Repository boundary

This repository is an independent service. SesliTab Guitar Reader, MusicXML-to-Guitar TAB Engine, Cloud OMR Gateway and ScoreMosaic integrate only through versioned contracts.

ST Score Restore produces visual `restoration_variant` artifacts. It is not an OMR engine. A selected visual source variant must cross ScoreMosaic Safe Intake before OMR processing.

## Current production status

Fresh production main at the start of PR #81 continuation is:

`53ae13d3a1b9bda08c79125674e1b7fca78ee8af`

Stage state:

- **Stage 1A — metadata governance:** complete;
- **Stage 1B — high-assurance custody/operations boundary:** complete and formally closed;
- **Stage 1C — authorized artifact onboarding and corpus realization:** active;
- **Stage 1 final exit:** not yet accepted;
- **Stage 2 — complete quality analysis:** blocked until explicit Stage 1 final PASS.

ADR 0016 risk-tiered custody is implemented. Catalog schema `1.3.0` and deterministic profile/eligibility/admission machinery are merged. Binding custody mapping remains:

- `open_corpus` → `managed_standard`;
- `restricted_corpus` → `managed_restricted` when exact artifact restrictions permit it;
- `sensitive_custody` → `high_assurance_vault`;
- unresolved/rejected governance → `blocked`.

The Stage 1 purpose allowlist remains limited to `quality_evaluation` and `held_out_evaluation`. Rights, privacy, purpose, retention, dataset review, provenance, digest/size binding, custody verification and admission are independent fail-closed gates.

## Historical C15/C16 baseline

C15 froze the original two-item corpus as immutable digest-addressed evidence. C16 measured exactly that historical snapshot and concluded `insufficient` for Stage 1 exit: 2 real items / 12 pages with seven recorded coverage gaps.

Historical files are not rewritten when later C17 evidence improves coverage. In particular:

- `catalog.v1.json` remains historical;
- `snapshot.freeze.v1.json` remains historical;
- `coverage-bias-report.v1.json` remains historical;
- historical C16 report SHA-256 remains `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## Merged C17 expansion on main

Current main contains the independently admitted inputs needed for expanded-v2 aggregation:

- **C17A / PR #68 — combined staff+TAB:** exact PNG SHA-256 `36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb`; taxonomy remains `combined_staff_tab` only.
- **C17B — standalone guitar TAB:** exact Barley PDF SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`; 84689 bytes / 2 pages; `open_corpus -> managed_standard`; `quality_evaluation` only.
- **C17C / PR #72 — degradation metadata v2:** exact Chopin artifact SHA-256 `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`; degradation `noise` only; held out. Any new aggregate must select v2 instead of v1 and must never double-count the same exact artifact.
- **C17D — deidentified phone photo:** exact derivative SHA-256 `abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5`; 647003 bytes; `restricted_corpus -> managed_restricted`; `held_out_evaluation` only.

Real score/PDF/image corpus artifact bytes remain outside ordinary Git. Repository evidence is metadata-only.

## PR #81 — expanded-v2 acceptance

PR #81 (`stage1c-expanded-snapshot-v2`) is the in-progress acceptance slice. Its deterministic aggregate selects exactly five real items and zero synthetic items:

1. Beethoven baseline v1;
2. C17A combined staff+TAB v1;
3. C17B standalone guitar TAB v1;
4. C17C Chopin metadata v2;
5. C17D phone-photo v1.

The committed v2 evidence is:

- `evidence/stage1c/corpus/catalog.v2.json`;
- `evidence/stage1c/corpus/snapshot.expanded.v2.json`;
- `evidence/stage1c/corpus/coverage-bias-report.v2.json`.

Deterministic candidate structure is 3 development items / 3 development source families and 2 held-out items / 2 held-out source families, with no source-family leakage and no duplicate artifact SHA-256. The six explicit coverage targets — staff, guitar TAB, combined staff+TAB, scanned PDF, phone photo and non-`none` degradation — are covered.

This does **not** itself mean Stage 1 PASS. The v2 report deliberately remains `review_required` with `stage1ExitSupported=false` and `stage2EntrySupported=false`. Representativeness, absence of bias, restoration effectiveness, OMR improvement and musical correctness are not established by coverage closure.

PR #81 must pass committed-evidence `--check`, focused regression tests, fresh exact-head Python 3.11/3.12 CI, review/thread/head reconciliation, merge, and post-merge main CI before a separate Stage 1 exit decision can occur.

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

Every transition is evidence-gated. Draft, Ready-for-review and merge are separate objective gates. Head movement invalidates earlier exact-head CI evidence.

## Development baseline

- Primary runtime: Python 3.12
- Compatibility validation: Python 3.11 and 3.12
- Runtime lock: `requirements.lock`
- OpenCV backend: `opencv-python-headless==4.13.0.92`
- NumPy runtime: `numpy==2.3.5`
- Job API: `/api/v1`, version `0.5.0`
- Storage baseline: in-memory by default; optional local SQLite metadata + content-addressed blobs
- HTTP boundary: local/non-production, bounded and fail-closed
- Source identity: SHA-256 artifact manifest
- Candidate identity: separate SHA-256 digest and audit manifest
- Teacher approval: separate from dataset inclusion, calibration and training consent

Validate repository contracts with:

```bash
python tools/validate_dependency_lock.py
python tools/validate_repository.py
python tools/validate_architecture_consistency.py
python tools/validate_fixture_catalog.py
python tools/build_stage1_expanded_snapshot.py --check
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

## Repository references

- [Technical Specification](docs/technical-specification.md)
- [Roadmap](docs/roadmap.md)
- [Architecture consistency audit](docs/architecture-consistency-audit.md)
- [Stage 1C current status](docs/stage-1c-current-status.md)
- [Stage 1 dataset card](docs/stage-1-dataset-card.md)
- [Stage 1 coverage and bias register](docs/stage-1-coverage-and-bias-register.md)
- [Stage 1 exit evidence](docs/stage-1-exit-evidence.md)
- [Canonical live handoff](docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json)
- [ADR 0015 — Restoration pipeline validation, comparator, and OMR handoff](docs/adr/0015-restoration-pipeline-validation-comparator-handoff.md)
- [ADR 0016 — Stage 1C risk-tiered artifact custody](docs/adr/0016-stage-1c-risk-tiered-artifact-custody.md)
