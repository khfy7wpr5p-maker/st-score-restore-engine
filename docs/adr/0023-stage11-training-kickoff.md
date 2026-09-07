# ADR 0023: Stage 11 bounded training kickoff

- **Status:** Accepted for bounded dataset admission and model-training kickoff
- **Date:** 2026-09-07
- **Decision ID:** `adr-0023-stage11-training-kickoff-v1`

## Context

Stage 11 foundation is complete. The project owner explicitly authorized continuation into dataset and model-training work. Historical Stage 1 corpus evidence remains immutable, so new training permissions are represented as a Stage 11 purpose overlay rather than rewriting Stage 1 records.

The accepted Stage 1 corpus contains three development items and two held-out items. Real artifact bytes are not stored in ordinary Git. The first training candidates are restricted to the three rights-cleared development items; the two held-out items remain excluded from training and tuning.

## Decision

Stage 11 may now admit rights-cleared public/open data, create provenance-bound synthetic derivatives, select experiment architectures, train models, create weights and evaluate on development data. Private, student or user documents remain excluded without separate explicit consent.

The first experiment matrix is deliberately small:

1. `residual_unet` as a local-detail baseline;
2. `hybrid_cnn_transformer` as a local/global challenger.

This is an experiment plan, not a final architecture selection. Recent restoration research continues to show value in both efficient convolutional/local processing and global-attention hybrids; the product must decide from score-specific evidence rather than generic-image benchmark reputation.

## Execution gate

Authorization does not imply that training has already run. Training is executable only after every admitted exact artifact byte is accessible through approved custody and its digest is verified. Ordinary Git remains metadata/code only for real corpus material.

Until then:

- `trainingAuthorized=true`;
- `trainingStarted=false`;
- `trainingExecutable=false`;
- `modelWeightsEstablished=false`.

## Locked safety rules

- held-out source families never train or tune;
- historical evidence is immutable;
- private/student/user documents need separate consent;
- model output cannot self-approve musical safety;
- Stage 9A preservation evidence, Stage 9 comparison and Stage 10 selection remain mandatory;
- model publication, production inference, automatic final selection and Stage 12 remain separately gated.

The next safe boundary is `admit_accessible_training_bytes_then_execute_reproducible_experiments`.
