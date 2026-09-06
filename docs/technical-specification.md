# ST Score Restore Engine — Technical Specification

**Status:** Current architecture with historical Stage 4 evidence retained; Stage 6 S6-07 current truth is authoritative for production state  
**Date:** 2026-09-06  
**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Historical Wikimedia expansion baseline:** main `9d2326931707f65c7eb5f5b22680e8fa85665a60` / Run #324 (`33728459668`) SUCCESS  
**Historical human-label completion checkpoint:** main `2ce6151e7ce37198c5b264ddd577df71f49da8bf` / PR #128 / Run #340 (`33745945427`) SUCCESS  
**Historical reference-bundle acceptance checkpoint:** main `3353b281a4022f107929fae296368390da45a4fb` / PR #130 / Run #348 (`33748180036`) SUCCESS

> **Current-truth note (2026-09-06):** Stage 4 and Stage 5 have subsequently completed. Stage 6 is active; S6-07 synthetic operational safety/recovery drills are complete; provider selection and production deployment remain unperformed. Sections 4–6 and the Stage 4 transition wording in Section 8 are retained as historical evidence context and must not be read as the current production state. Current production truth is recorded by the latest `docs/live/ST_SCORE_RESTORE_STAGE6_*_CURRENT_TRUTH.json` overlay.

## 1. Scope and invariants

ST Score Restore Engine is a safety-first visual restoration and validation service for music-score and guitar-TAB documents. It is not an OMR engine. Source bytes and historical evidence remain immutable; exact SHA-256 defines artifact identity; real corpus/derivative bytes and private raw observation metrics remain outside ordinary Git; held-out evidence never tunes thresholds/resources; human reference truth requires actual human expert review; unsupported evidence fails closed.

The future Stage 9A ST Music-Symbol Preservation Model is also not an OMR engine. It may recognize/localize notation classes for preservation verification, but it does not generate MusicXML, infer authoritative musical truth or automatically correct scores.

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

### 2.1 Future semantic preservation architecture — Stage 9A

ADR 0018 adds a learned semantic safety/veto layer between the Stage 9 comparator foundation and Stage 10 Selector in delivery order. At runtime, once separately implemented and accepted, its evidence participates in candidate safety before selector-driven automatic use:

```text
Immutable source
      |
      +------------------------------+
      |                              |
      v                              v
Restoration engine(s)       deterministic source evidence
      |
      v
Restoration variant
      |
      v
Deterministic Music/TAB Safety Validator
      |
      v
ST Music-Symbol Preservation Model (MSPM)
source <-> candidate semantic comparison
      |
      v
Fused preservation evidence / veto state
      |
      v
Multi-engine Comparator
      |
      v
ST Restore Selector
      |
      +-- unsafe or uncertain -> immutable original / teacher review
      +-- safe and beneficial -> selected restoration variant
```

The MSPM is an independent safety model, not a restoration model. Initial target classes are staff/TAB lines, noteheads, stems, flags, beams, augmentation dots, rests, accidentals, clefs, key/time signatures, barlines/repeats, ties/slurs, TAB digits/string relationship and core visually distinguishable guitar articulations.

The model must emit versioned, provenance-bound preservation evidence rather than a single opaque score. Evidence is expected to distinguish deletion, invention, displacement, merge/split, staff/TAB relationship changes, thin-symbol risk and uncertainty. Low-confidence evidence fails closed to abstention/review. Neither comparator ranking nor visual-quality improvement may override a deterministic or semantic hard veto.

Stage 9A architecture does not authorize training. Training data, annotations, model architecture, model weights, evaluation, publication and production activation require separate purpose-specific authorization and accepted evidence.

## 3. Runtime baseline

Python `>=3.11,<3.13`; CI Python 3.11/3.12; API `0.5.0`; exact PDF renderer `pypdfium2==5.13.0`. Historical Stage 2/3 thresholds and resource values referenced below were recorded as `uncalibrated_engineering_defaults`; later production-effective acceptance overlays govern current truth.

## 4. Historical production stages

Stage 1 COMPLETE / PASS.

Stage 2 COMPLETE / PASS.

Stage 3 COMPLETE / PASS. Immutable digests: purpose `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`; execution `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`; limitations `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`; acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

## 5. Stage 4 framework and evidence chain

**Historical state at this retained checkpoint:** ACTIVE / NOT_READY.  
**Historical Stage 5 state at this retained checkpoint:** BLOCKED pending Stage 4 final exit PASS.

Historical immutable anchors:

- framework main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` / Run #259;
- entry/start digest `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`;
- Beethoven+Barley purpose main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` / Run #272; digest `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`;
- accepted Beethoven+Barley bundle main `4f663d0c11339b98fd89639fd8f3d5afc8047fb3` / Run #282; bundle digest `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14`; acceptance digest `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c`;
- historical exact Beethoven+Barley execution authorization main `76f5643dde72c8cc4b02b517133331e9dea00146` / Run #287; digest `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`.

The authorization evidence is historically **AUTHORIZED / NOT YET EXECUTED** and retains `executed=false`. Later execution evidence is a separate immutable artifact; earlier authorization is never rewritten.

### 5.1 Beethoven + Barley execution truth

The real development execution later completed and abstained:

- 42 private observation identities;
- 24 measured;
- 18 `not_applicable`;
- 1 measured source family;
- 0 threshold candidates;
- execution evidence accepted: false at this retained checkpoint;
- thresholds calibrated: false at this retained checkpoint;
- resource limits calibrated: false at this retained checkpoint.

Public-safe execution evidence digest: `0d2ce54066d493e3aa5a8b3c3ef3df407532edb5fa51aee14b8a560678731f1a`. Private metric-batch digest: `5bb2c2e081e6e72697a2c3acb8aacd7b4159dfabf3400fb9a0570ecb1a148079`; raw values remain custody-only.

### 5.2 Wikimedia development expansion, human completion, and reference acceptance

PR #125 is the immutable expansion baseline at main `9d2326931707f65c7eb5f5b22680e8fa85665a60`, Run #324 (`33728459668`) SUCCESS. It added a separate development purpose-grant overlay and fail-closed review package for:

- item `dataset.item.wikimedia-guitar-technical-exercise-no1.v1`;
- source family `source.family.wikimedia-guitar-technical-exercise-no1.v1`;
- input `png`, page count 1;
- split `development`;
- purpose `safety_calibration`;
- purpose-grant overlay digest `603e3dc7669e6259ab061a8241d76206e7bd2bf76b170fc6dbc8c1d0b9d6be07`.

PR #128 later froze genuine external human review completion at main `2ce6151e7ce37198c5b264ddd577df71f49da8bf`, Run #340 (`33745945427`) SUCCESS:

- **7/7 findings are `clear`**;
- immutable completion snapshot state is `human_labels_complete_pending_separate_acceptance`;
- work-package digest `9ccec309f611f8057b8b4a20a1aba732544c1638f2b959656b9503718206337c`;
- completion bundle digest `37af98bbeb04832fc94382f246287da0b738c2520225cdcd9f5ea2028bde71f4`.

PR #130 then recorded the separate governance acceptance at main `3353b281a4022f107929fae296368390da45a4fb`, Run #348 (`33748180036`) SUCCESS:

- decision `ACCEPT_REAL_REFERENCE_BUNDLE`;
- acceptance digest `79771e291768ba4979abc1e44dd0ecebfd95892ff2e5861d77706c1cb4563eb3`;
- accepted-reference receipt digest `036bb31ca2672e443885ed06e213ef6913be7c66609ab5017b6f22ed3f33c801`;
- reference bundle accepted: true;
- candidate derivation eligible: true;
- execution authorized: false at this retained checkpoint;
- execution performed: false at this retained checkpoint;
- production thresholds/resources unchanged at this retained checkpoint;
- Stage 4 exit false at this retained checkpoint;
- Stage 5 entry false at this retained checkpoint.

The work package taxonomy remains `skew`, `blur`, `glare`, `shadow`, `uneven_lighting`, `noise`, `compression`; vocabulary is `clear`, `possible`, `probable`, `not_assessed`. The immutable work package remains null-filled, while completed human records live separately in `human-label-completion.v1.json` and the later acceptance decision lives in `reference-bundle-acceptance.v1.json`. Automated metrics/model predictions cannot be reference truth.

### 5.3 Development versus held-out boundary

Development evidence may derive candidates only after purpose and human-reference acceptance gates pass. Actual calibration execution still requires a separate exact execution authorization plus custody-only metric gates. Chopin `dataset.item.imslp82860-chopin-op69.v2` remains `held_out_evaluation` only. It cannot derive/select/tune thresholds and is excluded from the Wikimedia development review and acceptance scope.

Unavailable metrics are represented as `not_applicable`; numerical placeholders such as synthetic zero are forbidden. Public evidence may expose only digests/counts/aggregates, never custody-only raw metric values.

## 6. Historical Stage 4 readiness blockers retained

At the historical checkpoint represented by Sections 4–6, the blockers were:

1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`

These blocker codes are retained as immutable evidence context. They were resolved by later Stage 4 acceptance work and do not describe the current Stage 6 production state.

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
Stage 9A Music-Symbol Preservation Model
Stage 10 ST Restore Selector
Stage 11 ST Restore image model
Stage 12 Music-application integrations
```

Stage 9A preserves existing Stage 10/11/12 identifiers. It is a semantic safety stage, not an OMR or restoration stage. Its detailed contract is defined by ADR 0018.

## 8. Transition rule

The historical Stage 4 transition rule required a separate exact Wikimedia expanded-development calibration execution authorization. That rule is retained as evidence history and has been superseded operationally by later accepted Stage 4/5 work and current Stage 6 governance overlays.

For the newly added Stage 9A architecture, no implementation or training is authorized by this specification update. A future Stage 9A entry authorization must separately define the model contract, training/evaluation permissions, dataset governance, acceptance targets, rollback/kill-switch behavior and integration policy with Stage 9 comparator evidence before Stage 10 selector activation.