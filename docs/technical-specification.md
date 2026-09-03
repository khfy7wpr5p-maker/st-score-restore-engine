# ST Score Restore Engine — Technical Specification

**Status:** Current architecture; Stage 4 ACTIVE / NOT_READY after Wikimedia development expansion  
**Date:** 2026-09-03  
**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Current repository main:** `9d2326931707f65c7eb5f5b22680e8fa85665a60` / post-merge Run #324 (`33728459668`) SUCCESS

## 1. Scope and invariants

ST Score Restore Engine is a safety-first visual restoration and validation service for music-score and guitar-TAB documents. It is not an OMR engine. Source bytes and historical evidence remain immutable; exact SHA-256 defines artifact identity; real corpus/derivative bytes and private raw observation metrics remain outside ordinary Git; held-out evidence never tunes thresholds/resources; human reference truth requires actual human expert review; unsupported evidence fails closed.

## 2. Processing architecture

```text
Input document
    ↓
Immutable source registration / structural inspection
    ↓
Rights / privacy / purpose / custody / exact-byte gates
    ↓
PDF page policy
    ├─ raster_only → bounded PDFium derivative
    ├─ vector_only → preserve vector content
    ├─ hybrid → preserve + review
    └─ unknown/over-limit → original fallback + review
    ↓
Deterministic quality analysis
    ↓
Stage 4 development calibration evidence
    ├─ purpose-authorized development source families
    ├─ human reference labels
    ├─ separate reference-bundle acceptance
    ├─ exact execution authorization
    ├─ custody-only raw metrics
    └─ public-safe aggregate/digest evidence
    ↓
Held-out evaluation boundary
    ↓
Separate Stage 4 final acceptance
    ↓
Stage 5 boundary
```

## 3. Runtime baseline

Python `>=3.11,<3.13`; CI Python 3.11/3.12; API `0.5.0`; exact PDF renderer `pypdfium2==5.13.0`. Production thresholds/resource values remain `uncalibrated_engineering_defaults`.

## 4. Historical production stages

Stage 1 COMPLETE / PASS.

Stage 2 COMPLETE / PASS.

Stage 3 COMPLETE / PASS. Immutable digests: purpose `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`; execution `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`; limitations `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`; acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

## 5. Stage 4 framework and evidence chain

**State:** ACTIVE / NOT_READY.  
**Stage 5:** BLOCKED pending Stage 4 final exit PASS.

Historical immutable anchors:

- framework main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` / Run #259;
- entry/start digest `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`;
- Beethoven+Barley purpose main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` / Run #272; digest `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`;
- accepted Beethoven+Barley bundle main `4f663d0c11339b98fd89639fd8f3d5afc8047fb3` / Run #282; bundle digest `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14`; acceptance digest `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c`;
- historical exact execution authorization main `76f5643dde72c8cc4b02b517133331e9dea00146` / Run #287; digest `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`.

The authorization evidence is historically **AUTHORIZED / NOT YET EXECUTED** and retains `executed=false`. Later execution evidence is a separate immutable artifact; earlier authorization is never rewritten.

### 5.1 Beethoven + Barley execution truth

The real development execution later completed and abstained:

- 42 private observation identities;
- 24 measured;
- 18 `not_applicable`;
- 1 measured source family;
- 0 threshold candidates;
- execution evidence accepted: false;
- thresholds calibrated: false;
- resource limits calibrated: false.

Public-safe execution evidence digest: `0d2ce54066d493e3aa5a8b3c3ef3df407532edb5fa51aee14b8a560678731f1a`. Private metric-batch digest: `5bb2c2e081e6e72697a2c3acb8aacd7b4159dfabf3400fb9a0570ecb1a148079`; raw values remain custody-only.

### 5.2 Wikimedia development expansion

PR #125 is production-effective at main `9d2326931707f65c7eb5f5b22680e8fa85665a60`, Run #324 (`33728459668`) SUCCESS. It adds only a separate development purpose-grant overlay and fail-closed review package for:

- item `dataset.item.wikimedia-guitar-technical-exercise-no1.v1`;
- source family `source.family.wikimedia-guitar-technical-exercise-no1.v1`;
- input `png`, page count 1;
- split `development`;
- purpose `safety_calibration`;
- purpose-grant overlay digest `603e3dc7669e6259ab061a8241d76206e7bd2bf76b170fc6dbc8c1d0b9d6be07`.

Current Wikimedia assertions are fail-closed: human labels absent, reference bundle not accepted, execution not authorized, execution not performed, production thresholds/resources unchanged, Stage 4 exit false, Stage 5 entry false.

The work package requires seven labels: `skew`, `blur`, `glare`, `shadow`, `uneven_lighting`, `noise`, `compression`; vocabulary is `clear`, `possible`, `probable`, `not_assessed`. `referenceLabel`, `reviewerReference`, `provenanceReference`, and `reviewedOn` must remain null until actual human review. Automated metrics/model predictions cannot be reference truth.

### 5.3 Development versus held-out boundary

Development evidence may derive candidates only after purpose, human reference, separate acceptance, exact execution authorization, and private metric gates all pass. Chopin `dataset.item.imslp82860-chopin-op69.v2` remains `held_out_evaluation` only. It cannot derive/select/tune thresholds and is excluded from the Wikimedia review package.

Unavailable metrics are represented as `not_applicable`; numerical placeholders such as synthetic zero are forbidden. Public evidence may expose only digests/counts/aggregates, never custody-only raw metric values.

## 6. Current readiness blockers

1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`

The Wikimedia purpose grant alone does not resolve blocker 1. Human completion, reference acceptance, execution authorization, private execution, expanded candidate derivation/abstention, and development evidence governance acceptance are separate gates.

## 7. Binding development sequence

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

## 8. Transition rule

The next external-evidence boundary is genuine human completion of the Wikimedia seven-slot review package. Code, validation, deterministic acceptance preparation, and documentation may proceed before that input; actual labels, acceptance, calibration authorization, private metrics, threshold candidates, held-out evaluation, Stage 4 PASS, Stage 5 entry, training, publication, external export, and production threshold/resource changes must not be fabricated or self-authorized.