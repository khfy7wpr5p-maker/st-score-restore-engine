# ADR 0027 — Stage 11 V2a Consumer Adapter Synthetic Integration

Status: Accepted for Stage 11 development integration only  
Date: 2026-09-08

## Context

The exact frozen V2a candidate has already passed development gating, frozen held-out evaluation, Stage 9A preservation proxy, checkpoint freeze, deterministic TorchScript packaging and package custody validation. The package identity is fixed at SHA-256 `7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234` with size `7,817,857` bytes.

The package contract itself is patch-oriented (`1×1×512×512`). Application consumers, however, need a deterministic way to submit grayscale score images whose height and width are not exactly 512 pixels. This integration boundary must prove only that the frozen package can be consumed safely and deterministically. It must not reopen model tuning or use the already consumed held-out set.

## Decision

Introduce a development-only consumer adapter with the following fixed contract:

- only the exact frozen TorchScript package is accepted; SHA-256 and byte size are verified before loading;
- inputs are 2-D grayscale arrays;
- `uint8` inputs are normalized from `[0,255]` to float32 `[0,1]`;
- floating-point inputs must already be finite and inside `[0,1]`; unknown numeric ranges fail closed;
- arbitrary image sizes are divided into `512×512` patches with 64-pixel overlap and 448-pixel stride;
- uncovered patch area is padded with white (`1.0`);
- overlapping outputs are merged by arithmetic mean;
- the restored output keeps the original input height and width and must remain finite inside `[0,1]`;
- exact `512×512` adapter output must match direct package inference within `1e-6` max absolute difference;
- repeated exact-size execution must differ by no more than `1e-7`.

## Real execution evidence

The exact Drive package was executed on CPU with Python 3.13.5, PyTorch 2.10.0+cpu and NumPy 2.3.5 using synthetic-only inputs. No training data, held-out data, Stage 9A artifacts, private/student/user data, optimizer or backpropagation were used.

Three fixed synthetic cases were executed:

1. `white_small_u8`: `300×700`, two tiles, output shape preserved, finite, output range `[1.0,1.0]`.
2. `synthetic_staff_float`: `700×900`, four tiles, output shape preserved, finite, output range `[0.0,1.0]`.
3. `direct_512_float`: `512×512`, one tile, output shape preserved, finite, output range `[0.0,1.0]`.

The exact-size repeated execution max-absolute difference was `0.0`. Direct package versus adapter parity max-absolute difference was also `0.0`.

Execution evidence is committed at `evidence/stage11/v2a/v2a-consumer-adapter-evidence.v1.json` and additionally stored beside the private package in Google Drive as `consumer_adapter_evidence.v1.json`.

## Safety and governance

This boundary validates only consumer mechanics around a frozen candidate. It does not establish musical correctness, OMR correctness, quality on real user documents, production readiness or deployment authorization. The consumed held-out set remains prohibited for adaptive tuning. Model weights remain frozen.

Production inference, production promotion, final production model selection, real-user rollout and Stage 12 remain unauthorized.

## Next boundary

The next safe Stage 11 boundary is a staging-only API request/response adapter around the exact same frozen package. That work may use synthetic or otherwise non-heldout inputs only and must preserve the existing production and Stage 12 closures.
