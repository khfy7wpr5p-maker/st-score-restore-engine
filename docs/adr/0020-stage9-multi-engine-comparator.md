# ADR 0020: Stage 9 Multi-Engine Comparator Foundation

- **Status:** Accepted for Stage 9 provider-neutral implementation
- **Date:** 2026-09-06
- **Decision ID:** `adr-0020-stage9-multi-engine-comparator-foundation-v1`
- **Repository:** `khfy7wpr5p-maker/st-score-restore-engine`

## Context

Stage 8 established an optional DocRes candidate boundary but intentionally stopped before comparator selection. ADR 0015 already locks the ordering invariant `restoration variant -> safety validation -> comparator`, requires the immutable original to remain selectable, and forbids visual quality from overriding a hard music/TAB safety veto.

Stage 9 implements the provider-neutral comparator foundation without activating a live DocRes runtime, Stage 9A MSPM, Stage 10 Selector, production deployment, or model training.

## Decision

The Stage 9 comparator is an evidence-fusion and recommendation component. It is not a restoration engine, OMR engine, teacher-approval system, or production selector.

### Hard eligibility rules

A restoration variant is comparator-eligible only when:

1. provenance is complete and binds it to the exact immutable source;
2. music/TAB safety verdict is `pass`;
3. no hard deterministic veto exists;
4. when semantic Stage 9A evidence is later present, no hard semantic veto exists.

`reject`, provenance mismatch, or a hard veto can never be reversed by visual-quality evidence. `review_required` and unknown safety evidence cannot become automatic winners.

### Original baseline

The immutable original is always present as a first-class selectable baseline. A derivative must have explicit positive quality evidence to be preferred over the original. Merely being safe is not proof that it is better.

### Ranking policy

The first Stage 9 policy is deterministic and lexicographic rather than a single opaque universal score. The ordered evidence dimensions are:

1. document quality delta,
2. legibility delta,
3. contrast delta,
4. noise-reduction evidence,
5. lower structural risk as a final soft dimension.

Exact evidence ties route to review with the original retained. Artifact identity is used only for stable ordering, not to break a substantive evidence tie.

The policy contains no new calibrated production threshold. Cost/latency may be added later only as non-safety ranking evidence and may never override a hard veto.

### Outcomes

The comparator can recommend:

- `original_preferred`,
- `restoration_variant_preferred`,
- `review_required`,
- `original_retained_no_acceptable_derivative`.

Every result includes reason codes, original identity, candidate evidence and explicit flags that recommendation is not automatic final selection, teacher approval, OMR correctness, or musical truth.

### Stage boundaries

This Stage 9 implementation does **not** authorize:

- DocRes dependency/model download or live runtime activation,
- provider-specific integration,
- Stage 9A dataset collection, training, publication or inference,
- Stage 10 Selector entry or activation,
- ST Restore Image Model training,
- production deployment/live resources,
- threshold/resource-limit changes,
- held-out retuning,
- real/private document bytes or raw metrics in ordinary Git.

## Verification

Stage 9 is verified with synthetic-only drills and unit tests covering:

- rejected-but-visually-attractive variants cannot win,
- semantic hard veto cannot win,
- original wins when no positive improvement is established,
- review/unknown evidence retains original and routes to review,
- provenance mismatch is ineligible,
- exact evidence ties route to review,
- ordering is deterministic across input permutations,
- non-finite quality evidence fails closed,
- result remains recommendation-only.

## Consequences

Stage 9 creates the stable engine-neutral comparison spine needed by future OpenCV, DocRes and ST Restore Image Model candidates. Stage 9A may later add semantic preservation evidence as an additional hard-veto dimension, and Stage 10 may consume Stage 9 evidence, but neither later stage may weaken Stage 9 safety ordering.
