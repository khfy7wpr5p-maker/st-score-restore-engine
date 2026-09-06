# ADR 0018: Stage 9A Music-Symbol Preservation Model

- **Status:** Accepted as future roadmap architecture; implementation and training remain separately gated
- **Date:** 2026-09-06
- **Decision ID:** `adr-0018-stage9a-music-symbol-preservation-model-v1`
- **Repository:** `khfy7wpr5p-maker/st-score-restore-engine`
- **Roadmap placement:** Stage 9A, after Stage 9 Multi-engine Comparator foundation and before Stage 10 ST Restore Selector
- **Supersession relationship:** supplements ADR 0015; it does not weaken or rewrite ADR 0015 safety invariants

## Context

The current trusted baseline uses deterministic OpenCV restoration plus source-versus-candidate music/TAB safety checks. OpenCV can measure geometry, edges, connected components, line structure and image change, but it does not understand notation classes as musical symbols. A restoration can therefore look geometrically plausible while deleting, inventing, merging, splitting or moving a musically significant mark.

The future multi-engine architecture will compare OpenCV, DocRes and later ST-owned restoration models. Before the Stage 10 selector can automatically prefer one engine or restoration profile, the project needs a semantic preservation signal that asks a different question from visual quality:

> Did the restoration preserve the notated musical and TAB symbols that were present in the immutable source, without inventing new ones?

This capability belongs to the safety plane, not to the restoration plane and not to the OMR plane.

## Decision

### 1. Add Stage 9A to the binding roadmap

A new roadmap stage is inserted without renumbering existing stages:

```text
Stage 8   DocRes optional candidate
Stage 9   Multi-engine comparator
Stage 9A  Music-Symbol Preservation Model
Stage 10  ST Restore Selector
Stage 11  ST Restore image model
Stage 12  Music-application integrations
```

Using `9A` preserves existing Stage 10/11/12 identifiers and historical governance references.

### 2. Architectural role

The Stage 9A component is named **ST Music-Symbol Preservation Model** (`MSPM`). It is a learned semantic safety/veto model.

It is **not**:

- a restoration engine,
- an OMR engine,
- a MusicXML generator,
- an automatic score-correction system,
- a replacement for the deterministic Music/TAB Safety Validator,
- a source of human reference truth.

Its purpose is to compare the immutable source and a restoration variant and emit semantic preservation evidence.

### 3. Runtime placement

Stage 9 establishes the engine-neutral comparator foundation first. When Stage 9A is later implemented and accepted, its evidence is inserted into the safety path before a restoration variant may be considered automatically safe for selector-driven use.

Target runtime flow:

```text
Immutable source
      |
      +-----------------------------+
      |                             |
      v                             v
Restoration engine(s)       deterministic source evidence
      |
      v
Restoration variant
      |
      v
Deterministic Music/TAB Safety Validator
      |
      v
ST Music-Symbol Preservation Model (Stage 9A)
source <-> variant semantic comparison
      |
      v
Fused safety evidence / veto state
      |
      v
Multi-engine Comparator
      |
      v
ST Restore Selector (Stage 10)
      |
      +---- unsafe / uncertain -> original or teacher review
      |
      +---- safe + beneficial -> selected restoration variant
```

Appearance quality, comparator ranking or selector preference can never override a hard preservation veto.

### 4. Initial symbol taxonomy

The first production-target taxonomy must cover at least:

- staff lines and TAB lines,
- noteheads,
- stems, flags and beams,
- augmentation dots,
- rests,
- accidentals,
- clefs,
- key signatures and time signatures,
- barlines and repeat symbols,
- ties and slurs,
- TAB digits and string-position relationship,
- core guitar articulations where they are visually distinguishable.

Later versions may add lyrics, fingering, chord symbols, ornaments and instructional markings only through versioned taxonomy changes.

### 5. Evidence contract

The model must not emit only a single opaque score. Its versioned evidence should support, where technically applicable:

- model ID, version and immutable checksum,
- taxonomy version,
- source artifact identity and candidate artifact identity,
- detected symbol class and confidence,
- source-to-candidate correspondence confidence,
- location/bounding geometry or equivalent localization evidence,
- preservation risk codes,
- per-class and aggregate uncertainty,
- explicit `not_assessed` / abstention when evidence is insufficient.

Target preservation risk codes include:

- `symbol_missing_after_restoration`,
- `symbol_invented_after_restoration`,
- `symbol_displaced`,
- `symbol_merged_or_split`,
- `staff_or_tab_relationship_changed`,
- `thin_symbol_at_risk`,
- `semantic_comparison_uncertain`.

The exact schema will require separate implementation-stage approval.

### 6. Fail-closed behavior

The model is an additional safety signal and cannot approve a candidate by itself.

- High-confidence evidence that a significant symbol was deleted, invented or materially displaced must be eligible to trigger a hard veto.
- Ambiguous or low-confidence evidence must produce abstention/review, not automatic pass.
- Model unavailability must not silently remove the deterministic safety boundary.
- The immutable original remains a first-class safe fallback.
- Teacher review remains available for uncertain cases.

### 7. Relationship to Stage 9 comparator

Stage 9 may be implemented first using deterministic safety and quality evidence. Stage 9A then adds semantic preservation evidence to the comparator contract.

The comparator must keep visual quality, deterministic structural safety, semantic symbol preservation and downstream OMR effectiveness as distinct evidence dimensions. It must not collapse them into one uncalibrated score.

### 8. Relationship to Stage 10 selector

The Stage 10 selector may use Stage 9A evidence to decide which restoration engine/profile is worth invoking or which validated result should be preferred. The selector must never be allowed to override a Stage 9A hard veto or deterministic safety rejection.

Stage 10 activation therefore requires an explicit policy for how semantic preservation evidence participates in selection, abstention and teacher-review routing.

### 9. Relationship to Stage 11 ST Restore image model

Stage 11 remains the project-owned **restoration** model. Stage 9A is a separate **safety verification** model.

Keeping them separate prevents a learned restorer from grading its own output without an independent preservation check. A future shared visual backbone may be researched, but production safety heads, model identities, evaluation evidence and rollback controls must remain independently testable.

### 10. Training boundary

This ADR and roadmap amendment do **not** authorize model training.

Before training begins, a separate authorization must define:

- lawful and purpose-bound training data,
- synthetic-data policy,
- human symbol annotation protocol,
- development/validation/held-out separation,
- rare-symbol coverage targets,
- source-family leakage controls,
- privacy and retention rules,
- model architecture and compute plan,
- model-weight licensing/distribution policy.

Production/user documents are not training data by default. Teacher review is not training consent.

### 11. Evaluation requirements

Stage 9A cannot exit based only on generic object-detection accuracy. Evaluation must include preservation-specific metrics such as:

- per-class symbol recall and precision,
- false symbol-removal detection rate,
- false symbol-invention detection rate,
- localization/displacement sensitivity,
- calibration/reliability of confidence,
- rare-symbol and small/thin-mark performance,
- TAB digit and string-assignment preservation,
- source-family generalization,
- abstention quality and coverage/risk curves,
- regression comparison against the deterministic safety baseline.

Downstream OMR effectiveness may be measured separately but cannot substitute for preservation safety.

### 12. Production controls

Any released MSPM must have:

- immutable model/version/checksum identity,
- reproducible inference configuration,
- offline training only,
- no online self-training from user uploads,
- kill switch / full disable path,
- rollback to the previous accepted model,
- deterministic fallback behavior when the model is unavailable,
- privacy-safe audit events,
- independent regression tests against symbol-loss and symbol-invention cases.

## Consequences

Positive consequences:

- ST Score Restore gains semantic notation-awareness without becoming an OMR engine.
- Stage 10 Selector receives a musically meaningful safety signal rather than relying only on visual quality.
- DocRes and future learned restoration models can be evaluated against the same independent preservation layer.
- The project creates a defensible product distinction around music-specific restoration safety.

Costs and risks:

- a new labeled dataset and training/evaluation program will be required,
- tiny and visually ambiguous symbols are difficult and require careful calibration,
- degraded source images may make source-side recognition uncertain,
- false vetoes may reduce automatic coverage,
- the model introduces GPU/runtime and model-governance complexity.

These risks are accepted because uncertain cases fail closed to the immutable original or teacher review.

## Safety and privacy impact

This change strengthens the safety architecture. It does not authorize collection of new user data, model training, production inference, model-weight publication or automated musical correction. All existing source immutability, custody, purpose, held-out and teacher-review rules remain binding.

## Alternatives considered

1. **Use OpenCV geometry only.** Rejected as the long-term target because geometry does not provide symbol-class semantics.
2. **Use an OMR engine as the preservation validator.** Rejected as the primary design because it couples restoration safety to OMR behavior and risks conflating OMR output with source truth.
3. **Put preservation logic inside Stage 11 restoration model.** Rejected as the sole safety design because the restorer should not be the only judge of its own output.
4. **Renumber Stages 10–12.** Rejected to preserve existing architecture references and immutable governance history.

## Reversal or migration path

Stage 9A can remain disabled while the deterministic validator and original fallback continue operating. A future ADR may replace the model architecture or taxonomy without removing the invariant that learned restoration output requires independent music-symbol preservation evidence before automatic selector-driven use.