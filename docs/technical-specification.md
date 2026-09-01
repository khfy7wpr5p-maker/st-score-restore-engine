# ST Score Restore Engine — Technical Specification

**Status:** Current architecture and Stage 1C acceptance specification  
**Version:** 0.5.1-doc  
**Date:** 2026-09-02  
**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Production main at refresh:** `53ae13d3a1b9bda08c79125674e1b7fca78ee8af`

## 1. Scope

ST Score Restore Engine is a safety-first visual restoration and validation service for music-score and guitar-TAB documents. Supported intake families include PDF, JPG/JPEG, PNG and phone-captured score images.

This repository is **not** an OMR engine. It produces and validates visual `restoration_variant` artifacts. A selected variant must pass the ScoreMosaic Safe Intake boundary before downstream OMR and MusicXML generation.

The current runtime uses deterministic OpenCV processing only. DocRes, ST Image AI, the future multi-engine comparator, selector, project-owned learned image model and downstream music-application integrations are not active.

## 2. Architectural invariants

1. Source bytes are immutable.
2. A restoration candidate never replaces the source implicitly.
3. Music-score/TAB preservation has veto priority over cosmetic improvement.
4. Validation occurs before comparator eligibility.
5. Rejected candidates cannot win.
6. The immutable original remains selectable as fallback.
7. Artifact identity uses exact SHA-256; provider SHA-1 or descriptive metadata is not a substitute.
8. Rights, privacy, purpose, retention, dataset review, custody and admission are independent fail-closed gates.
9. Teacher approval does not imply dataset, calibration or training permission.
10. Real corpus artifact bytes remain outside ordinary Git.
11. Historical C15/C16 evidence is immutable.
12. Open PR state is not production truth.
13. CI evidence is exact-head scoped; head movement invalidates it.
14. Stage 2 cannot start before explicit Stage 1 final exit PASS.

## 3. Processing architecture

```text
Input document
    ↓
Immutable source registration / inspection
    ↓
Document + quality analysis
    ↓
Current restoration candidate: OpenCV
Future optional candidates: DocRes / ST Image AI
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

ADR 0015 is binding for validation/comparator/original-fallback ordering. Later selectors or candidate engines may not bypass this sequence.

## 4. Repository and service boundaries

ST Score Restore remains independent from:

- SesliTab Guitar Reader;
- MusicXML-to-Guitar TAB Engine;
- Cloud OMR Gateway;
- ScoreMosaic / downstream OMR services.

Integration occurs through versioned contracts. No downstream repository is merged into this engine and no restoration result is treated as an OMR result.

## 5. Runtime baseline

- Python runtime contract: `>=3.11,<3.13`;
- primary development runtime: Python 3.12;
- CI compatibility matrix: Python 3.11 and 3.12;
- API version: `0.5.0`;
- OpenCV package: `opencv-python-headless==4.13.0.92`;
- NumPy: `2.3.5`;
- runtime lock: `requirements.lock`;
- validation dependency lock: `requirements.validation.lock`;
- default state store: in-memory;
- optional durable local state: SQLite metadata + content-addressed blobs;
- built-in HTTP adapter: local/non-production boundary only.

The application does not provide encrypted cloud object storage, an external durable production queue, production identity, public network hardening or production deployment in the current stage.

## 6. Input and restoration safety

Immutable source inspection records source identity and media characteristics without silently converting vector PDFs to raster data. Candidate generation produces separate artifacts and audit manifests.

Safety validation evaluates music-score/TAB preservation signals such as staff/TAB geometry, line continuity, local-symbol/component risk and source/candidate relationships. Safety reports and reviewer evidence remain separate from source identity.

Teacher review is evidence-bound and stale-screen decisions are rejected. Automatic teacher approval is not supported.

## 7. Stage 1 custody and governance model

ADR 0016 risk-tiered custody is implemented. Catalog schema `1.3.0` binds:

- `open_corpus` → `managed_standard`;
- `restricted_corpus` → `managed_restricted` where exact restrictions permit it;
- `sensitive_custody` → `high_assurance_vault`;
- unresolved/rejected governance → `blocked`.

The Stage 1 purpose allowlist is limited to `quality_evaluation` and `held_out_evaluation`. A real item becomes admissible only after exact artifact identity, rights, privacy, purpose, retention, provenance, custody/profile verification and dataset review all pass.

High-assurance structural compatibility does not by itself prove that a real vault exists.

## 8. Historical C15/C16 evidence

C15 froze the historical two-item Stage 1 corpus. C16 measured exactly that snapshot and returned `insufficient`.

Historical invariants:

- 2 real items / 12 pages;
- one development source family and one held-out source family;
- snapshot canonical SHA-256 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`;
- C16 report SHA-256 `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`;
- `heldOutFrozen=true`;
- `trainingUseActivated=false`;
- historical sufficiency `insufficient`.

The v1 catalog, frozen snapshot and C16 report are historical evidence and must remain byte-for-byte unchanged.

## 9. Current merged C17 item-level evidence

Production main includes:

### C17A / PR #68 — combined staff+TAB

- dataset item: `dataset.item.wikimedia-guitar-technical-exercise-no1.v1`;
- exact artifact SHA-256: `36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb`;
- notation taxonomy: `combined_staff_tab` only;
- use: `quality_evaluation`;
- custody: `open_corpus -> managed_standard`.

The item is deliberately not also counted as standalone guitar TAB.

### C17B — standalone guitar TAB

- dataset item: `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1`;
- exact artifact SHA-256: `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`;
- byte size: 84689;
- pages: 2;
- notation taxonomy: `guitar_tab`;
- use: `quality_evaluation`;
- custody: `open_corpus -> managed_standard`.

### C17C / PR #72 — exact-byte degradation metadata v2

- dataset item: `dataset.item.imslp82860-chopin-op69.v2`;
- exact artifact SHA-256: `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`;
- split: held out;
- degradation: `noise` only;
- training permission: not granted.

Metadata v2 represents the same exact artifact as v1. Any new aggregate must select v2 instead of v1 and must not count both versions as separate items, source families or artifact diversity.

### C17D — deidentified phone photo

- dataset item: `dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1`;
- exact derivative SHA-256: `abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5`;
- byte size: 647003;
- kind: `phone_photo`;
- privacy: `deidentified` using metadata scrub;
- use: `held_out_evaluation` only;
- custody: `restricted_corpus -> managed_restricted`;
- external export: not allowed by the item restriction.

## 10. Expanded-v2 aggregate contract — PR #81

PR #81 (`stage1c-expanded-snapshot-v2`) is the in-progress aggregate acceptance slice. The canonical v2 evidence paths are:

- `evidence/stage1c/corpus/catalog.v2.json`;
- `evidence/stage1c/corpus/snapshot.expanded.v2.json`;
- `evidence/stage1c/corpus/coverage-bias-report.v2.json`.

Required exact membership:

1. `dataset.item.imslp799143-beethoven-op48-no3.v1`;
2. `dataset.item.wikimedia-guitar-technical-exercise-no1.v1`;
3. `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1`;
4. `dataset.item.imslp82860-chopin-op69.v2`;
5. `dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1`.

Required invariants:

- exactly 5 real items and 0 synthetic items;
- development = 3 items / 3 source families;
- held out = 2 items / 2 source families;
- development/held-out source-family sets are disjoint;
- all selected exact artifact SHA-256 values are unique;
- Chopin v1 is excluded and v2 appears once;
- historical v1 evidence files remain unchanged;
- no real corpus PDF/image bytes appear under ordinary Git evidence paths.

Required coverage targets:

- `notation.staff`;
- `notation.guitar_tab`;
- `notation.combined_staff_tab`;
- `capture.scanned_pdf`;
- `capture.phone_photo`;
- `degradation.non_none`.

All are covered by the deterministic v2 aggregate. The seven historical C16 gap codes are absent from the v2 report.

Canonical v2 digests:

- catalog SHA-256: `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot SHA-256: `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- coverage report SHA-256: `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

The CI boundary is `python tools/build_stage1_expanded_snapshot.py --check`; candidate-only `--write` output is not the final acceptance boundary.

## 11. Coverage interpretation

The v2 report deliberately records:

- `sufficiency.state = review_required`;
- `requiresCorpusExpansion = false`;
- `stage1ExitSupported = false`;
- `stage2EntrySupported = false`.

Therefore target coverage does not establish:

- corpus representativeness;
- absence of bias;
- restoration effectiveness;
- OMR improvement;
- musical correctness;
- calibration readiness;
- training readiness;
- Stage 1 final PASS.

## 12. Stage 1 final acceptance contract

PR #81 may move Draft -> Ready -> merge only if all objective gates are clean:

1. final branch head and base are fresh-read;
2. committed v2 evidence passes `--check`;
3. focused regressions pass;
4. full repository validation passes on Python 3.11 and 3.12 for the exact head;
5. reviews are reconciled;
6. no unresolved blocking review thread exists;
7. head does not move after verification;
8. merge occurs at the exact verified head.

After merge, `main` must pass the same validation matrix. Only then may Stage 1 exit be evaluated separately.

A Stage 1 PASS must bind the accepted main SHA, post-merge CI run and canonical v2 evidence digests. Any unresolved governance/custody/rights/privacy/source-family/digest/CI/review blocker keeps the result FAIL/BLOCKED.

## 13. Stage 2 boundary

Stage 2 Complete Quality Analysis remains blocked until explicit Stage 1 final PASS. After authorization, Stage 2 may address skew, perspective, blur, motion blur, glare, shadow, uneven lighting, noise, compression, low resolution, page type, boundaries/orientation/DPI and other quality-analysis categories.

Stage 1 evidence is not retroactively rewritten based on later Stage 2 outcomes.

## 14. Binding development sequence

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

## 15. Validation commands

```bash
python tools/validate_dependency_lock.py
python tools/validate_repository.py
python tools/validate_architecture_consistency.py
python tools/validate_fixture_catalog.py
python tools/build_stage1_snapshot.py --check
python tools/evaluate_stage1_coverage_bias.py --check --require-insufficient
python tools/build_stage1_expanded_snapshot.py --check
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

## 16. Prohibited scope in the current stage

Until Stage 1 exit PASS, do not start Stage 2, change historical C15/C16 evidence, place real corpus artifact bytes in ordinary Git, infer training rights, integrate DocRes/ST Image AI, start multi-page Stage 3 work, tune safety thresholds on held-out data, activate production identity/network services, or claim restoration/OMR improvement from metadata coverage alone.
