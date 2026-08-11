# ADR 0001: Independent Safety-First Restoration Engine

- **Status:** Accepted; processing-order detail superseded by ADR 0015
- **Date:** 2026-08-05
- **Decision owners:** Project owner and ST Score Restore maintainers
- **Supersession note:** ADR 0015 is the normative authority for restoration-variant validation, comparator eligibility, original-aware selection, and ScoreMosaic handoff ordering.

## Context

Music scores and guitar TAB documents may arrive as PDF, JPG/JPEG, PNG, or phone-captured photographs. Restoration can improve readability and OMR performance, but aggressive processing or generative enhancement can alter musical meaning by changing staff lines, TAB numbers, rhythm marks, accidentals, dots, barlines or other notation.

The capability must later serve SesliTab Guitar Reader, MusicXML-to-Guitar TAB Engine, Cloud OMR Gateway and ScoreMosaic/Scremosaik without coupling their codebases or forcing heavy image and AI dependencies into each application.

## Decision

ST Score Restore Engine remains an independent, versioned service. The following diagram records the original 2026-08-05 high-level flow for historical context; its **comparator-before-validator ordering is superseded by ADR 0015 and is not the current normative processing order**:

```text
PDF / JPG / JPEG / PNG / phone-captured photo
      ↓
Document and quality analysis
      ↓
OpenCV safe restoration
DocRes AI adapter
ST Restore engine
      ↓
Result comparator                 # historical ordering; superseded
      ↓
Music-score and TAB safety validator
      ↓
Teacher approval when required
      ↓
Enhanced PDF and/or image plus audit report
```

The current normative ordering is defined by ADR 0015:

```text
restoration variant
      ↓
Music-score / TAB safety validation
      ↓
Comparator eligibility and original-aware selection
      ↓
Selected source variant
      ↓
ScoreMosaic Safe Intake / downstream OMR when the roadmap permits
```

The engine will apply these rules:

1. The original input is immutable.
2. Deterministic OpenCV processing is the first trusted baseline.
3. DocRes and ST Restore are candidate engines whose outputs must be validated.
4. Musical preservation has veto priority over visual improvement.
5. The engine does not perform OMR or convert content to MusicXML.
6. Other applications integrate through versioned API contracts rather than repository merging.
7. Production models do not learn live from user documents.
8. Teacher approval and permission to use a document for training are separate decisions.
9. Model versions, parameters, risk findings and approval decisions are auditable and reversible.

## Consequences

### Positive

- Heavy AI and image-processing dependencies stay isolated.
- All consuming applications can use the same restoration and safety behavior.
- The deterministic baseline provides a fallback when AI output is risky.
- Models can evolve without silently changing the consumer applications.
- Teacher review and audit records support safe educational use.

### Costs

- A service boundary adds deployment, storage and API-contract work.
- Result comparison and notation/TAB validation require dedicated test data.
- Phone photographs require additional geometry, shadow, glare and crop handling.
- AI results may be rejected even when they look visually attractive.

## Safety and privacy impact

The architecture minimizes accidental musical mutation and requires explicit handling of retention, consent and training use. Original and enhanced files must be distinguishable. User documents are not retained or used as training data by default.

## Alternatives considered

### Embed restoration separately in every music application

Rejected because it would duplicate algorithms, dependencies, validation behavior and model versions.

### Use only DocRes or another ready-made AI model

Rejected because a general document model cannot be assumed to preserve music notation and TAB semantics.

### Develop only a custom model from the beginning

Rejected as the initial path because there is not yet enough approved music-specific training and regression data.

### Allow automatic online learning

Rejected because incorrect teacher choices, corrupted inputs or adversarial examples could alter production behavior without controlled evaluation.

## Reversal or migration path

Consumers remain insulated through the API contract. Individual engines can be disabled or replaced while retaining the deterministic baseline and previous model versions. If the service architecture later becomes unsuitable, the versioned core interfaces may be packaged as a library without changing the preservation principles.
