# ADR 0024 — Stage 11 V2 Symbol-Preservation Residual U-Net

Status: Accepted for Stage 11 development only; V2a candidate frozen after gated held-out/Stage 9A pass  
Date: 2026-09-07  
Outcome recorded: 2026-09-08

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

Development must reach `inkRecallDelta >= -0.05` to become eligible for frozen held-out evaluation; `>= -0.02` is the ideal target. Pixel restoration must remain useful and edge behavior must not materially collapse. A cosmetically strong run with excessive ink loss does not pass.

If development misses the gate, V2a/V2b may adjust loss weights, symbol sampling or mask logic using train/development data only. Held-out data is never a tuning playground.

Frozen held-out and V2 Stage 9A evaluation require a passing development-evidence artifact. Evaluation creates no optimizer, executes no backpropagation, records model-state hashes before/after, and fails if checkpoint/config/dataset provenance does not match. Progress is atomically persisted to Drive for interruption-safe resume.

## V2 and V2a outcome

V2 completed 20 development-training epochs and materially improved symbol preservation relative to V1, but its development `inkRecallDelta=-0.05993542307987809` missed the `-0.05` minimum. V2 therefore remained `review_required` and did not unlock its frozen held-out path.

V2a warm-started from the exact V2 best checkpoint `363cb63bff2367c1119a4eea449a19d468a802160f45b4fe1f2d98ab04fb894b`, used the frozen config hash `1250731992c01c238dd2376a95ced1d1c6f76dcdf87deb473ec94a0aa58f7818`, and produced candidate checkpoint `15afc73233c91a80a7ef1285cb631d5d3acd681e9cfed9a93b35642bf39fff4c`.

The supplied Colab run evidence shows that the gated pipeline progressed through development to both frozen held-out and Stage 9A, which can occur only after `eligibleForFrozenHeldOutEvaluation=true`. The captured held-out segment reports 352 official held-out images with `inkRecallDelta=-0.037029366940259933`, pixel L1 improvement `53.772181502991145%`, edge L1 improvement `7.465588872979961%`, false-ink delta `-0.09465780964290552`, and MSE improvement `-12.064218277766777%`. The complete captured Stage 9A artifact reports `status=pass`, `inkRecallDelta=-0.030930931214243174`, pixel L1 improvement `47.90019887277439%`, edge L1 improvement `5.336352757154033%`, false-ink delta `-0.07233098943834193`, and MSE improvement `-19.59240047175054%`.

Therefore the required symbol-preservation and cleanup floors pass, while the ideal `inkRecallDelta >= -0.02` target is not reached and an MSE regression remains explicit. The candidate checkpoint is frozen at the exact SHA above. Because the held-out set has now been consumed for final evaluation, it must not be reused as an adaptive tuning set for V2b or any later variant. Any further model tuning requires train/development data and a newly defined independent evaluation boundary.

## Next safe boundary

The next Stage 11 work is checkpoint-custody verification and deterministic inference packaging/smoke validation around the frozen V2a candidate. That work may verify exact bytes, load/inference behavior, output shape/range, deterministic preprocessing/postprocessing and fail-closed artifact identity. It must not change model weights or use the consumed held-out set for tuning.

## Boundaries

This outcome does not authorize production inference, automatic production promotion, final production model selection, model publication, Stage 12 integration, OMR-correctness claims, musical-truth claims, or training on private/student/user data. Stage 11 remains inside its safety boundary until the separately defined packaging/custody and production-acceptance gates are satisfied.
