# ST Score Restore Engine — Architecture Flexibility Principles

**Status:** Normative design guidance  
**Date:** 2026-09-06  
**Updated:** 2026-09-13

ST Score Restore is safety-first, but safety-first does not mean algorithmically narrow. The architecture should protect a small set of product-critical invariants while leaving implementation methods, model families, pipelines, evidence fusion, deployment profiles and future research paths open to improvement.

## 1. Outcomes are constrained; techniques are extensible

Architecture contracts should state what must remain true at the product boundary, not unnecessarily prescribe one internal technique.

Examples:

- musical information must not be silently damaged;
- source identity and provenance must remain traceable;
- unsafe or materially uncertain automatic decisions need a safe fallback or review path;
- user/private data cannot silently become training data;
- released models and engines need a disable/rollback path.

These invariants do **not** require one specific CNN, Transformer, detector, segmenter, OCR/OMR helper, image-processing library, scoring formula, database, cloud provider or deployment topology.

## 2. Prefer pluggable capability interfaces

Restoration, quality analysis, semantic preservation, comparison and selection should accept multiple interchangeable implementations when practical.

A capability may be implemented by:

- deterministic image processing,
- classical computer vision,
- CNN-based models,
- vision transformers,
- segmentation or detection models,
- Siamese/change-detection networks,
- multimodal models,
- ensembles,
- rules plus learned models,
- future techniques not yet selected.

No current model family is a permanent architectural requirement unless a later evidence-backed decision makes it necessary for a specific release profile.

## 3. Taxonomies are versioned and open-ended

Notation/TAB symbol lists are reference taxonomies, not closed vocabularies.

Different document profiles may use different subsets or extensions. Future versions may add, split, merge or reorganize symbol classes, including ornaments, dynamics, pedal markings, tuplets, tremolo, grace notes, fingering, lyrics, chord symbols, historical notation, percussion notation, tablature variants and instrument-specific marks.

A single monolithic model is not required. Multiple specialist heads/models may cover different symbol families and may be fused by a higher-level preservation policy.

## 4. Safety decisions may be multi-signal

No single metric or model score should become the universal truth signal.

The system may combine:

- deterministic geometry/change evidence,
- semantic symbol-preservation evidence,
- document-quality evidence,
- engine provenance,
- OMR-effectiveness experiments,
- teacher review,
- profile-specific heuristics,
- uncertainty/calibration evidence,
- future evidence channels.

Fusion may evolve over time as long as hard safety evidence cannot be silently discarded and the decision remains auditable.

## 5. Uncertainty should route, not unnecessarily block

Fail-safe behavior does not require every uncertain case to become a permanent hard block.

Depending on product profile and accepted evidence, uncertainty may route to:

- immutable original,
- teacher/user review,
- a different restoration engine,
- a more conservative profile,
- a second model or ensemble,
- downstream processing with an explicit warning/non-authoritative status,
- deferred automatic selection.

A hard veto should be reserved for evidence and policies that justify a hard veto. Thresholds and routing policies should be calibrated and versioned rather than made unnecessarily absolute.

## 6. Research can be broader than production activation

The roadmap primarily governs production-effective activation. Isolated research, benchmarking, architecture experiments, synthetic-data work, prototype model comparison and non-production evaluation may run ahead or in parallel when they do not alter production behavior, weaken active safety controls, use unauthorized data, or falsely claim a later stage is complete.

Production activation still requires the appropriate evidence and authorization gates.

## 7. Profiles may differ

The product does not need one universal pipeline for every source.

Separate profiles may be developed for:

- clean digital scores,
- degraded scans,
- phone photographs,
- vector PDF,
- hybrid PDF,
- standard notation,
- guitar TAB,
- historical/engraved material,
- dense orchestral pages,
- educational worksheets,
- future instrument-specific formats.

Profiles can share components without being forced into identical processing paths.

## 8. Stage 9A is a capability, not a single fixed model

The Stage 9A Music-Symbol Preservation Model name represents a semantic preservation **capability**. Production implementations may consist of one model, multiple models, a hybrid rules/AI system, or an ensemble.

The architectural requirement is the capability to produce useful, provenance-bound evidence about whether musically meaningful content survived restoration. The exact network architecture, taxonomy size, localization format, confidence representation and fusion strategy remain replaceable and versioned.

## 9. Stage 11 remains free to evolve

The ST Restore Image Model is not restricted to one training objective or architecture. It may later use restoration, denoising, dewarping, deblurring, illumination correction, super-resolution, structure-preserving objectives, diffusion/transformer approaches or other methods, provided released behavior satisfies the accepted preservation and provenance constraints.

Stage 9A and Stage 11 may share backbones or research components when useful, but production safety evaluation must remain independently measurable enough to avoid circular self-approval.

## 10. Minimal hard invariants

Hard constraints should be limited to product-critical properties such as:

1. immutable/traceable source identity;
2. no silent overwrite of the original;
3. provenance for derived outputs;
4. no silent conversion of user data into training data;
5. no automatic acceptance of known materially unsafe musical changes;
6. auditable handling of uncertainty and safety decisions;
7. reversible/disable-able production model and engine paths;
8. explicit distinction between restoration evidence, OMR output and human musical truth.

Everything else should remain open to evidence-driven improvement unless a later ADR establishes a justified constraint.

## 11. Detector development, scoring and qualification are separate layers

Semantic-preservation detectors may iterate quickly on already-spent development data, but detector construction, teacher scoring and independent qualification must remain architecturally distinct.

For a class-specific source detector:

- inference should consume only the inputs allowed by its declared capability boundary;
- teacher coordinates, review labels and held-out truth must not silently become inference features or page-specific tuning rules;
- a candidate should be frozen before teacher scoring that is used to characterize it;
- repeated use of the same development corpus can demonstrate improvement but cannot by itself qualify a detector;
- acceptance metrics and thresholds should be frozen before a fresh independent holdout is opened;
- weak source detection should not be used to support strong claims about restored-output semantic preservation;
- historical detector versions and evidence should remain immutable so regressions and gains stay auditable.

The Stage 11 V2d staff-line path is the current concrete example. V1.2 improved development recall substantially and then achieved `0.9090909091` teacher-system recall on the independent holdout, but failed the pre-frozen qualification policy on predicted-system precision (`0.625`) and staff-absent specificity (`0.0`). Its final disposition is therefore `REJECTED_CURRENT_DETECTOR`. The implementation remains replaceable; the architectural requirement is the evidence boundary, not the current OpenCV technique.

## 12. A consumed holdout is evidence, not future tuning data

Once an independent holdout has been opened and scored, its role changes permanently: it becomes qualification evidence for the frozen candidate that consumed it.

The architecture therefore requires:

- a failed holdout must not be reused to retune the same detector version;
- a future detector version must not use observed holdout geometry, per-page failures, or holdout-specific thresholds as development input;
- future improvements should be motivated at the failure-mode level (for example generic false-positive suppression) and developed on authorized non-holdout data;
- any changed acceptance policy must be frozen before a new independent holdout is accessed;
- a new candidate must be frozen before a new independent holdout is consumed;
- another independent qualification requires new explicit authorization;
- restored-output comparison remains a later, separately authorized layer even after source-detector qualification.

This prevents the holdout from silently becoming a development set while still allowing the project to learn the high-level engineering lesson that a detector may have strong recall but insufficient false-positive control.
