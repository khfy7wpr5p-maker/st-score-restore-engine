# ADR 0021: Stage 10 ST Restore Selector Foundation

- **Status:** Accepted for provider-neutral, controlled non-production foundation
- **Date:** 2026-09-07
- **Decision ID:** `adr-0021-stage10-st-restore-selector-foundation-v1`

## Context

Stage 9 provides a deterministic, explainable multi-engine recommendation after Music/TAB safety. Stage 9A adds provider-neutral semantic preservation evidence and hard-veto/review routing. Stage 10 must use those layers without becoming a shortcut around them.

The selector has two bounded responsibilities:

1. decide which explicitly approved, available and enabled restoration engines are worth invoking;
2. turn a trusted Stage 9 recommendation plus matching Stage 9A preservation evidence into a controlled source-variant decision.

This stage does not authorize live selector activation, production traffic, model training, DocRes runtime/model use, ST Restore Image Model use, or automatic final user-facing approval.

## Decision

The canonical bounded flow is:

```text
immutable source
  -> Stage 10 engine eligibility plan
  -> approved restoration engine variants only
  -> Music/TAB Safety Validator
  -> Stage 9A preservation evidence
  -> Stage 9 Multi-Engine Comparator
  -> Stage 10 original-aware controlled selection decision
```

### Engine planning

An engine may be recommended for invocation only when all three conditions are true:

- `approvalState=approved`
- `availabilityState=available`
- `enabled=true`

Unapproved, unavailable or disabled engines are skipped. No provider-specific preference is allowed in this foundation. Network fetch and model download remain forbidden.

The immutable original is always included as a first-class baseline.

### Controlled source selection

A restoration variant can be selected for controlled non-production use only when:

- Stage 9 contract identity is accepted;
- Stage 9 result is explicitly recommendation-only;
- automatic final selection remains unauthorized;
- original selectability is preserved;
- the recommended variant exists exactly once;
- Stage 9 marks the variant eligible;
- no deterministic hard veto exists;
- no review requirement exists;
- Music/TAB safety verdict is `pass`;
- matching Stage 9A source/candidate evidence exists;
- Stage 9A evidence is `pass`, complete, non-vetoed and not review-required.

Any missing, malformed, uncertain, review-required or scope-expanded evidence routes to the original plus review.

### Original outcomes

When Stage 9 prefers or retains the original, Stage 10 selects the original. When Stage 9 requires review, Stage 10 retains the original and marks review required.

### Locked safety boundaries

Stage 10 may not:

- overwrite the immutable source;
- bypass Music/TAB safety;
- bypass Stage 9 comparison;
- override deterministic hard veto;
- override semantic hard veto;
- convert review-required evidence into automatic variant selection;
- treat selector output as teacher approval;
- claim OMR correctness or human musical truth;
- activate DocRes, ST Image AI, a provider, production resources, or training.

## Consequences

The project now has a deterministic orchestration/selection boundary that can later accept additional approved restoration engines without changing safety ordering. The current implementation is deliberately provider-neutral and non-production.

The Stage 10 decision is a controlled source-selection decision, not final teacher approval and not production activation. Stage 11 remains a separate explicit roadmap gate.
