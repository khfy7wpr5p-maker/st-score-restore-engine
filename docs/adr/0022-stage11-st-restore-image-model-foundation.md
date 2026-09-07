# ADR 0022: Stage 11 ST Restore Image Model Foundation

- **Status:** Accepted for provider-neutral, non-training foundation
- **Date:** 2026-09-07
- **Decision ID:** `adr-0022-stage11-st-restore-image-model-foundation-v1`

## Context

Stage 10 completed a provider-neutral selector that can plan approved restoration engines and make controlled source/variant decisions only after Music/TAB safety, Stage 9A preservation evidence and Stage 9 comparison. Stage 11 introduces the future learned ST Restore Image Model, but the repository's architecture rules deliberately do not lock the product to one neural architecture or one training objective.

The user authorized Stage 11 development to continue. This authorization is interpreted as Stage 11 entry/start and foundation work only. It does not authorize dataset collection, use of private/user documents for training, model training, weight creation/download, model publication, production inference or Stage 12 integration.

## Decision

Stage 11 is split at an explicit safe boundary:

```text
Stage 11A foundation (this decision)
  -> model capability contract
  -> training-readiness manifest contract
  -> release-manifest validation contract
  -> synthetic-only adapter drills
  -> Stage 10-compatible disabled capability descriptor

separate authorization required
  -> dataset admission/collection
  -> architecture/objective experiment selection
  -> training
  -> held-out evaluation/calibration
  -> release approval
  -> controlled inference activation
```

### Architecture remains open

No CNN, transformer, diffusion model, ensemble or other family is selected by this ADR. Future work may use denoising, dewarping, deblurring, illumination correction, super-resolution, structure-preserving objectives or combinations, provided accepted safety and provenance constraints remain measurable.

### Training boundary

At this foundation checkpoint:

- dataset collection is unauthorized;
- user/private document training use is unauthorized;
- model training and held-out retuning are unauthorized;
- weight creation/download and network fetch are unauthorized;
- no trained model is claimed;
- no real model inference is claimed.

A training-readiness manifest may describe intended objective families but cannot admit real training data or authorize execution.

### Selector handoff

Until separate training, evaluation and release approval are accepted, the Stage 11 engine must advertise to Stage 10 as:

- `approvalState=unapproved`
- `availabilityState=unavailable`
- `enabled=false`

Therefore Stage 10 deterministically skips it.

### Independent safety remains mandatory

The image model may generate future restoration candidates, but it cannot self-approve them. A candidate must remain subject to independent Stage 9A preservation evidence, Stage 9 comparison and Stage 10 controlled selection. Model output is not OMR truth, teacher approval or human musical truth.

## Consequences

Stage 11 can now evolve without prematurely choosing a model family or training on unauthorized data. The repository has an executable contract for future image-model integration and release governance, while current production behavior remains unchanged.

The next safe boundary is `separate_stage11_training_and_dataset_authorization`. Stage 12 remains blocked until a later accepted Stage 11 exit.
