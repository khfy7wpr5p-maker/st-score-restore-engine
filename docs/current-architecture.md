# ST Score Restore Engine — Current Architecture

**Updated:** 2026-09-13  
**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Working branch:** `stage11-v2c-semantic-detector-corpus-expansion`  
**PR:** #211 — Draft / Open / Unmerged

## Product purpose

ST Score Restore Engine is a safety-first visual restoration and validation system for music scores and guitar TAB received as PDF, JPG/JPEG, PNG or phone-captured images. Its purpose is to improve document legibility and recoverability without silently damaging musically meaningful visual information.

The repository is **not an OMR engine**. It does not treat automatic recognition output as musical truth. Immutable source identity, provenance, deterministic evidence, human review boundaries and conservative abstention/review paths are part of the architecture.

## High-level architecture

```text
Input score/TAB
  PDF / image / phone capture
          |
          v
Immutable ingestion + source identity
  exact bytes / SHA-256 / provenance
          |
          v
Document and page preparation
  multi-page PDF handling / rasterization / source normalization
          |
          v
Quality analysis + safety diagnostics
  skew / blur / lighting / noise / compression / geometry
          |
          v
Restoration candidate layer
  deterministic or learned restoration engines
  frozen ST Restore package when evaluating preservation
          |
          +------------------------------+
          |                              |
          v                              v
Visual quality evidence          Semantic-preservation evidence
                                 class-specific source detectors
                                 + independent teacher truth
                                 + frozen qualification policy
          |                              |
          +---------------+--------------+
                          v
Comparator / selector / safety routing
  accept candidate / choose conservative variant / abstain / review
                          |
                          v
Teacher review and auditable evidence
                          |
                          v
API / downstream music-application integrations
```

## Architectural layers

1. **Source and provenance layer** — source bytes are immutable and exact SHA-256 binds derived evidence to the correct input.
2. **Document-processing layer** — handles PDF/image page preparation and quality analysis without silently replacing the original.
3. **Restoration layer** — may use classical CV, learned restoration models or future pluggable engines.
4. **Deterministic safety layer** — checks source/output geometry and other hard invariants independently of model quality scores.
5. **Semantic-preservation layer** — Stage 9A/Stage 11 V2c/V2d class-specific evidence asks whether musically meaningful content survived restoration; it is not OMR truth.
6. **Human-reference layer** — teacher annotations and review are independent evaluation evidence, never inference features unless a separately governed future design explicitly permits it.
7. **Qualification/governance layer** — development, frozen scoring, independent holdout qualification, restored-output comparison, production promotion and Stage 12 entry are separate gates.
8. **API/integration layer** — normal product/API behavior remains separated from experimental detector qualification.

## Binding development order

```text
Stage 0   Roadmap update
Stage 1   Real and explicitly authorized test dataset
Stage 2   Complete quality-analysis system
Stage 3   Multi-page PDF pipeline
Stage 4   Safety calibration with real data
Stage 5   Accessible teacher review interface
Stage 6   Identity, network and production infrastructure
Stage 7   Preview release
Stage 8   DocRes optional candidate
Stage 9   Multi-engine comparator
Stage 9A  Music-Symbol Preservation Model capability
Stage 10  ST Restore Selector
Stage 11  ST Restore image model
Stage 12  Music-application integrations
```

Historical stage evidence remains immutable; later overlays do not rewrite earlier checkpoints.

## Current Stage 11 semantic-preservation state

The frozen V2a Restore package remains unchanged with SHA-256 `7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234`.

Current class disposition remains conservative:

- `PASS`: `notehead` at canonical class-evidence level only;
- `REVIEW_ONLY`: `clef`;
- `REJECTED_CURRENT_DETECTOR`: `accidental`, `barline`, `beam_or_flag`, `rest`, `staff_line`, `stem`;
- `UNSUPPORTED`: `tab_digit`, `tab_line`, `tab_string`, `tie_or_slur`.

No class-level result establishes overall semantic preservation by itself.

## Staff-line development and independent holdout result

The development progression on the already-spent 20-page development corpus was:

| Version | Predicted systems | Matched @ 0.5 spacing | Recall | Precision | Present-page coverage | Absent specificity |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 10 | 10 | 0.050761 | 1.000000 | 10/18 | 2/2 |
| v1 | 89 | 71 | 0.360406 | 0.797753 | 15/18 | 2/2 |
| v1.1 | 114 | 91 | 0.461929 | 0.798246 | 18/18 | 2/2 |
| v1.2 | 187 | 141 | 0.715736 | 0.754011 | 18/18 | 2/2 |

V1.2 passed development-readiness floors but was not qualified by development data. A qualification policy was frozen before fresh holdout access, then exactly one independent holdout was authorized and consumed.

Independent Chopin Op.69 holdout result for frozen `stage11-v2d-staff-multisystem-source.v1.2`:

- holdout pages: 8/8;
- teacher truth: 88 standard five-line systems across 7 staff-present pages and 1 staff-absent page;
- frozen detector predictions: 128;
- matched systems: 80;
- teacher-system recall @ 0.5 spacing: `0.9090909091` — PASS vs `>= 0.65`;
- predicted-system precision: `0.625` — **FAIL** vs `>= 0.80`;
- present-page coverage: `1.0` — PASS;
- absent-page specificity: `0.0` — **FAIL** vs required `1.0`;
- five-line count correctness: `1.0` — PASS;
- line-order correctness: `1.0` — PASS;
- synthetic six-line/TAB rejection: `1.0` — PASS;
- source identity: `8/8` — PASS;
- byte-repeat determinism: PASS;
- scorer compatibility anchor: historical v1 `71/197` reproduced exactly before holdout scoring.

Because the qualification policy is conjunctive, the official disposition is:

`QUALIFICATION_COMPLETE_REJECTED_CURRENT_DETECTOR`

The failure mode is now primarily **false-positive control**, not insufficient source recall. The detector found most true staff systems but produced too many extra systems, including five predictions on the single teacher-confirmed staff-absent page.

Authoritative evidence:

- `evidence/stage11/v2d/v2d-staff-line-source-detector-qualification-policy.v1.json`
- `evidence/stage11/v2d/v2d-staff-line-independent-holdout-source-freeze.v1.json`
- `evidence/stage11/v2d/v2d-staff-line-independent-holdout-qualification-result-binding.v1.json`
- `docs/live/ST_SCORE_RESTORE_STAGE11_V2D_STAFF_LINE_HOLDOUT_CURRENT_TRUTH.json`

## Current stop boundary

The one authorized independent staff-line holdout is **consumed**. Frozen v1.2 must not be retuned against it. The holdout must not become an informal development set or source of page-specific rules.

Still closed / false:

- `detectorQualified`;
- `sourceDetectorAdequacyEstablished`;
- `staff_line=PASS`;
- restored-output staff-topology comparison;
- `semanticPreservationEstablished`;
- overall Stage 11 PASS;
- production promotion/readiness;
- Stage 12 entry;
- PR #211 merge or ready-for-review transition.

## Next engineering boundary

If `staff_line` development continues, the next candidate must be separately versioned (for example v1.3) and developed using **non-holdout development evidence only**.

The technical objective is to preserve the strong holdout recall regime while improving general false-positive suppression and staff-absent rejection. Appropriate research directions include source-derived negative evidence, stronger text/decorative-line rejection, bounded support/spacing consistency checks, and generic confidence/routing logic. The consumed Chopin holdout must not be used to select thresholds, hard-code page rules or tune candidate behavior.

Before another independent qualification:

1. create a separately versioned candidate;
2. use only authorized development data for candidate construction/tuning;
3. freeze code, configuration and raw development evidence;
4. establish development readiness without consulting the consumed holdout for tuning;
5. define/freeze any new qualification policy changes before new holdout access;
6. obtain a new explicit authorization for a genuinely independent holdout;
7. only after source-detector qualification may restored-output staff-topology comparison be considered under a separate authorization.

## Governance principle

Development improvement, independent qualification, restored-output preservation comparison, overall Stage 11 PASS, production promotion and Stage 12 entry are intentionally different decisions. No earlier layer may silently authorize a later one.
