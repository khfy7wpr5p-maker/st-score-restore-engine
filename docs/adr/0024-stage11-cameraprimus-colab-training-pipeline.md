# ADR 0024 — Stage 11 CameraPrIMuS Colab training pipeline

Date: 2026-09-07
Status: Accepted for non-production Stage 11 training preparation

## Context

Stage 11 training was authorized, but the repository checkpoint after PR #189 correctly recorded that no accessible admitted training bytes had yet been connected to an execution environment. The project owner has now identified an existing Google Drive corpus at `TEST/CameraPrIMuS/Corpus` and authorized its use for the Stage 11 training workflow.

The observed corpus structure contains paired files such as `<sampleId>_distorted.jpg` and `<sampleId>.png`, plus `.agnostic`, `.semantic`, and `.mei` sidecars. The official PrIMuS site describes Camera-PrIMuS as an extension of PrIMuS where the score images are distorted to simulate camera-capture imperfections.

## Decision

1. Keep CameraPrIMuS artifact bytes in Google Drive; do not copy the real corpus into ordinary Git.
2. Add a dependency-free repository scanner that pairs distorted JPG inputs with clean PNG targets and records SHA-256 provenance.
3. Group split assignment by the stable prefix before the first underscore in the CameraPrIMuS sample id, then use a deterministic hash to create an 80/10/10 train/development/held-out split. A source family may exist in only one split.
4. Missing source/target pairs are rejected from admission rather than silently repaired or guessed.
5. Add a self-contained Google Colab notebook for the first Residual U-Net baseline. The notebook mounts Drive, builds the manifest, requires a GPU, trains with a pixel-plus-edge-preservation objective, writes checkpoints/evidence to Drive, and resumes from the last checkpoint after interruption.
6. Held-out evaluation is disabled by default and is run only after the model/configuration are frozen. Held-out results must not be used to tune the model.
7. No external pretrained model weights are used or downloaded by this baseline notebook.
8. Stage 9A symbol-preservation evidence, Stage 9 comparison, and Stage 10 selection remain mandatory before any release decision.
9. Production inference, automatic final selection, model publication, and Stage 12 remain unauthorized.

## Rights gate

The official Camera-PrIMuS page publicly exposes the dataset and research description, and later OMR research refers to CameraPrIMuS as a public source dataset. During this checkpoint, however, an explicit license grant covering commercial model training was not observed on the official dataset page.

Because ST Score Restore has a commercial product roadmap, the pipeline therefore records `rightsReviewStatus = review_required` and fails closed before the training cells. Training-purpose authorization from the project owner is recorded, but it is not treated as a substitute for dataset licensing rights.

Once documented rights clearance is recorded, the same pipeline can set the rights state to `approved` and perform the first GPU baseline run without redesigning the dataset or model code.

## Consequences

- The previous blocker `ADMITTED_ARTIFACT_BYTES_NOT_ACCESSIBLE` is technically resolved at the data-source level: the Drive source exists and its pair structure has been confirmed.
- The remaining blockers are rights clearance and the first actual Colab GPU execution.
- Training cannot be claimed as started, and model weights cannot be claimed as established, until a real run produces checkpoint and run-evidence artifacts.
- The current notebook is a baseline experiment, not a production model and not an OMR truth engine.
