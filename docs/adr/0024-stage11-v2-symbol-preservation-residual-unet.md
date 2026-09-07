# ADR 0024 — Stage 11 V2 Symbol-Preservation Residual U-Net

Status: Accepted for Stage 11 development only  
Date: 2026-09-07

## Context

Stage 11 V1 improved visual restoration but the latest Stage 9A symbol-region result is `review_required`: the model removed too much true music-symbol ink. The operator-reported reference result records `inkRecallDelta=-0.166` while visual pixel/edge metrics improved. The historical V1 evidence is not rewritten by this ADR.

## Decision

Build V2 as the same Residual U-Net family so the main experimental change is symbol-aware supervision rather than a simultaneous architecture replacement.

V2 uses:

- DeepScoresV2 Dense only, under the already admitted commercial-training rights boundary;
- corrected native annotations: `images=list`, `annotations=dict`, image `ann_ids`, ID-keyed categories, and `a_bbox=[left, top, right, bottom]`;
- 512x512 patches;
- an exact 50/50 random versus symbol-centered sampling target;
- hard-example weighting for small/thin noteheads, stems, beams, accidentals, staff lines, rests, articulations and related fine marks;
- a composite loss of `0.40 pixel_l1 + 0.20 edge_l1 + 0.25 symbol_region_l1 + 0.15 ink_recall_penalty`;
- an explicit ink-removal penalty that increases when a prediction makes known target ink whiter inside symbol masks;
- the existing source-family split guard, with the official test split frozen as held-out;
- realistic but bounded camera degradations, including blur, uneven illumination/shadow, JPEG artifacts, noise, mild perspective, motion blur and resolution loss.

PyTorch remains Colab-only. It is not added to the production dependency set. Repository CI validates NumPy reference loss behavior, parser/mask/sampling behavior, notebook/runtime structure and current-truth governance.

## Gates

Development must reach `inkRecallDelta >= -0.05` to become eligible for frozen held-out evaluation; `>= -0.02` is the ideal target. Pixel restoration must remain useful and edge/PSNR behavior must not materially collapse. A cosmetically strong run with excessive ink loss does not pass.

If development misses the gate, V2a/V2b may adjust loss weights, symbol sampling or mask logic using train/development data only. Held-out data is never a tuning playground.

Frozen held-out and V2 Stage 9A evaluation require a passing development-evidence artifact. Evaluation creates no optimizer, executes no backpropagation, records model-state hashes before/after, and fails if checkpoint/config/dataset provenance does not match. Progress is atomically persisted to Drive for interruption-safe resume.

## Boundaries

This decision does not authorize production inference, automatic final model selection, model publication, Stage 12 integration, OMR-correctness claims, musical-truth claims, or training on private/student/user data. Stage 11 V2 remains development-only until real Colab training/evaluation evidence satisfies the gates.
