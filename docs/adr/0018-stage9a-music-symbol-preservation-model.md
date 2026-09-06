# ADR 0018: Stage 9A Music-Symbol Preservation Capability

- **Status:** Accepted as future roadmap architecture; implementation and training remain separately gated
- **Date:** 2026-09-06
- **Decision ID:** `adr-0018-stage9a-music-symbol-preservation-model-v2`
- **Repository:** `khfy7wpr5p-maker/st-score-restore-engine`
- **Roadmap placement:** Stage 9A, after Stage 9 Multi-engine Comparator foundation and before Stage 10 ST Restore Selector
- **Supersession relationship:** supplements ADR 0015 and is interpreted together with `docs/architecture-flexibility-principles.md`

## Context

The current trusted baseline uses deterministic OpenCV restoration plus source-versus-candidate music/TAB safety checks. OpenCV can measure geometry, edges, connected components, line structure and image change, but it does not natively understand notation classes as musical symbols. A restoration can therefore look geometrically plausible while deleting, inventing, merging, splitting or moving a musically significant mark.

The future multi-engine architecture may compare OpenCV, DocRes, project-owned restoration models and additional engines not yet selected. Before Stage 10 automatically prefers an engine or restoration profile, the system needs a semantic preservation capability that asks a different question from visual quality:

> Did restoration preserve musically meaningful notation/TAB content well enough for the intended downstream use?

This capability belongs primarily to the safety/evidence plane. It does not force ST Score Restore to become an OMR engine.

## Decision

### 1. Add Stage 9A without narrowing later stages

The roadmap adds a Stage 9A capability without renumbering existing stages:

```text
Stage 8   DocRes optional candidate
Stage 9   Multi-engine comparator
Stage 9A  Music-Symbol Preservation capability
Stage 10  ST Restore Selector
Stage 11  ST Restore image model
Stage 12  Music-application integrations
```

`9A` preserves existing Stage 10/11/12 identifiers and historical references. The roadmap position governs production activation order; it does not prohibit isolated research, benchmarking or prototype work from running earlier when production behavior is unaffected.

### 2. Architectural role

Stage 9A is called the **ST Music-Symbol Preservation capability** (`MSPM` as the current working name).

It may be implemented as:

- one learned model,
- several specialist models,
- a detector/segmenter pair,
- Siamese or change-detection networks,
- CNN or vision-transformer families,
- rules plus learned components,
- an ensemble,
- an auxiliary OMR-derived signal that is explicitly non-authoritative,
- or another evidence-backed architecture selected later.

It is not required to be one monolithic neural network.

Its job is to compare the immutable source and one or more restoration variants and emit preservation evidence useful to safety, comparison and selection.

It is **not by itself**:

- a restoration engine,
- authoritative OMR truth,
- a MusicXML generator,
- an automatic score-correction authority,
- a replacement for all deterministic safety checks,
- or human reference truth.

### 3. Runtime placement is a default target, not an unnecessarily rigid topology

The preferred production flow is:

```text
Immutable source
      |
      +-----------------------------+
      |                             |
      v                             v
Restoration engine(s)       deterministic source evidence
      |
      v
Restoration variant(s)
      |
      v
Deterministic Music/TAB safety evidence
      |
      v
Stage 9A semantic preservation evidence
      |
      v
Evidence fusion / comparator
      |
      v
ST Restore Selector (Stage 10)
      |
      +---- unsafe / uncertain -> original, alternate path or review
      |
      +---- safe + useful -> selected restoration variant
```

Alternative implementations may run some evidence producers in parallel, perform multi-pass checks or use profile-specific ordering, provided these product invariants remain true:

1. a known materially unsafe derivative cannot silently become the automatic winner;
2. the immutable original remains available;
3. evidence provenance remains auditable;
4. uncertainty is handled explicitly rather than hidden.

Appearance quality, comparator ranking or selector preference cannot silently erase a justified hard safety veto. However, not every uncertainty signal must become a hard veto; routing policy may choose review, original fallback, alternate engine, conservative profile or another controlled path.

### 4. Symbol taxonomy is extensible

The initial reference taxonomy includes common high-value classes such as:

- staff and TAB lines,
- noteheads,
- stems, flags and beams,
- augmentation dots,
- rests,
- accidentals,
- clefs,
- key and time signatures,
- barlines and repeats,
- ties and slurs,
- TAB digits and string-position relationships,
- visually distinguishable guitar articulations.

This is not a closed vocabulary and not a requirement that one first model cover every class equally.

Versioned profiles may add, split, merge or specialize classes such as ornaments, tuplets, tremolo, grace notes, dynamics, fingering, lyrics, chord symbols, historical notation, percussion notation, pedal markings, instrument-specific signs and tablature variants.

Different specialist models may cover different symbol families.

### 5. Evidence contract is expressive, not fixed to one schema shape

The preservation layer should expose enough versioned evidence for downstream audit and decision-making. Depending on model type, useful fields may include:

- model/component ID and version,
- immutable checksum or equivalent artifact identity,
- taxonomy/profile version,
- source and candidate artifact identity,
- detected or inferred symbol class,
- source-to-candidate correspondence evidence,
- localization/bounding geometry, masks, keypoints or equivalent spatial evidence,
- preservation/change risk codes,
- confidence or calibrated uncertainty,
- explicit `not_assessed` / abstention where appropriate.

A single opaque score should not be the only available signal, but the exact evidence schema may evolve by version and may differ across capability implementations.

Example risk concepts include:

- `symbol_missing_after_restoration`,
- `symbol_invented_after_restoration`,
- `symbol_displaced`,
- `symbol_merged_or_split`,
- `staff_or_tab_relationship_changed`,
- `thin_symbol_at_risk`,
- `semantic_comparison_uncertain`.

These are extensible concepts, not a permanently closed enum.

### 6. Safety routing should be calibrated, not universally blocking

Stage 9A is an additional safety/evidence signal and cannot approve a candidate merely because it assigns a high score.

Recommended policy:

- strong evidence of materially harmful symbol deletion, invention or displacement may trigger a hard veto;
- ambiguous or low-confidence evidence may route to abstention, alternate-engine processing, conservative restoration, immutable original or teacher/user review;
- model unavailability should preserve a safe deterministic/original path rather than silently pretending semantic validation succeeded;
- hard-veto thresholds should be evidence-backed and calibrated rather than chosen as arbitrary permanent constants.

A future product profile may safely permit downstream non-authoritative processing of uncertain material when the uncertainty is explicit and the original remains available. Stage 9A should avoid unnecessary blocking when a safer routed path exists.

### 7. Relationship to Stage 9 comparator

Stage 9 may begin with deterministic safety and quality evidence. Stage 9A adds one or more semantic-preservation evidence channels.

The comparator may combine:

- visual/document quality,
- deterministic structural safety,
- semantic symbol preservation,
- engine provenance,
- downstream OMR-effectiveness experiments,
- uncertainty/calibration evidence,
- teacher review signals where appropriate,
- future evidence sources.

These dimensions may be fused by a versioned policy, but a hard safety finding should not be silently washed out by an unrelated quality score.

### 8. Relationship to Stage 10 selector

Stage 10 may use Stage 9A evidence to choose:

- which restoration engine/profile to invoke,
- which candidate to prefer,
- whether to preserve the original,
- whether to invoke a second model/engine,
- whether to use a conservative profile,
- whether human review is useful,
- or whether downstream use should continue with an explicit non-authoritative warning.

The selector is therefore not limited to a simple pass/fail choice.

### 9. Relationship to Stage 11 ST Restore image model

Stage 11 remains the project-owned restoration capability. Stage 9A remains a preservation-evidence capability.

They may share backbones, embeddings, datasets, feature extractors or research components when that improves efficiency. The important production property is that restoration quality and preservation safety remain independently measurable enough to avoid circular self-approval.

The architecture does not require physically separate infrastructure or completely unrelated model families.

### 10. Training boundary

This ADR does **not** itself authorize model training.

Future training work should define, to the degree needed for the selected approach:

- lawful and purpose-bound training/evaluation data,
- synthetic-data strategy,
- annotation or weak-supervision approach,
- development/validation/held-out separation,
- source-family leakage controls,
- privacy and retention rules,
- compute/model plan,
- model-weight licensing/distribution policy.

The exact annotation protocol, model family and dataset composition remain open to evidence-driven design. Production/user documents are not training data by default, and teacher review is not automatically training consent.

### 11. Evaluation should match the capability, not one benchmark template

Stage 9A evaluation should measure preservation usefulness rather than rely only on generic object-detection accuracy.

Depending on the implementation, suitable measures may include:

- per-class precision/recall,
- symbol-loss and symbol-invention detection quality,
- localization/displacement sensitivity,
- calibration/reliability,
- rare/small/thin-mark performance,
- TAB digit/string preservation,
- source-family generalization,
- abstention quality,
- coverage/risk curves,
- regression against deterministic safety,
- downstream OMR-effectiveness impact,
- teacher-review burden reduction,
- latency/cost trade-offs.

Not every implementation must use every metric. Acceptance targets should be profile-specific and evidence-backed.

### 12. Production controls

Released Stage 9A implementations should remain traceable and reversible. Depending on deployment profile, controls may include:

- immutable model/component identity,
- versioned inference configuration,
- kill switch or disable path,
- rollback to a previous accepted implementation,
- deterministic/original fallback,
- privacy-safe audit evidence,
- regression coverage for symbol-loss/invention cases.

The exact operational mechanism may vary by provider and deployment architecture.

## Consequences

Positive consequences:

- ST Score Restore gains semantic notation-awareness without becoming an OMR-only system.
- Stage 10 gains musically meaningful evidence rather than relying only on visual quality.
- OpenCV, DocRes and future engines can be compared using a common preservation capability.
- The project remains free to adopt better AI architectures and specialist models over time.
- Different document and notation profiles can evolve independently.

Costs and risks:

- training/evaluation data and annotation or weak-supervision work may be required,
- tiny/ambiguous symbols remain difficult,
- degraded source images can make source-side interpretation uncertain,
- false vetoes can reduce automatic coverage if thresholds are too strict,
- multi-model approaches add runtime and governance complexity.

These risks should be managed through calibrated routing, extensible profiles and reversible deployment rather than by narrowing the architecture prematurely.

## Safety and privacy impact

This change strengthens preservation awareness while keeping implementation options broad. It does not authorize collection of new user data, model training, production inference, model-weight publication or automated musical correction.

The minimal hard invariants are those defined by `docs/architecture-flexibility-principles.md`: source traceability, no silent overwrite, provenance, no silent training-data conversion, no automatic acceptance of known materially unsafe musical changes, auditable uncertainty handling, reversible production paths and clear separation between restoration evidence, OMR output and human musical truth.

## Alternatives considered

1. **Use OpenCV geometry only forever.** Rejected as the sole long-term strategy because geometry does not provide enough symbol semantics.
2. **Use one OMR engine as the only preservation validator.** Rejected as the sole design because it would couple restoration safety too tightly to one OMR behavior. OMR-derived signals may still be useful as one evidence channel.
3. **Put all preservation logic only inside Stage 11.** Rejected as the sole production-safety design because restoration and preservation should remain independently measurable. Shared backbones/components are still allowed.
4. **Freeze a single CNN architecture now.** Rejected because future evidence may favor transformers, segmentation, ensembles, multimodal models or other methods.
5. **Renumber Stages 10–12.** Rejected to preserve existing references and governance history.

## Reversal or migration path

Stage 9A may remain disabled while deterministic safety and original fallback continue operating. Future ADRs may replace the model architecture, evidence schema, taxonomy, routing policy or implementation topology without removing the minimal preservation and provenance invariants.
