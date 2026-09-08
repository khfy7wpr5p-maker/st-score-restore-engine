# ADR 0025 — Stage 11 V2a Frozen Candidate Packaging

Status: Accepted for Stage 11 candidate packaging implementation only  
Date: 2026-09-08

## Context

Stage 11 V2a passed its gated development path, frozen held-out evaluation and Stage 9A preservation proxy. The exact candidate checkpoint is frozen at SHA-256 `15afc73233c91a80a7ef1285cb631d5d3acd681e9cfed9a93b35642bf39fff4c`. The consumed held-out set cannot be reused for adaptive tuning, and the passing result does not by itself authorize production inference or Stage 12.

The next engineering requirement is to prove that the exact frozen checkpoint can be loaded and packaged deterministically without mutating weights, touching held-out data or silently changing the model contract.

## Decision

Introduce a Stage 11 development-only candidate packaging boundary with the following rules:

- the input checkpoint SHA-256, V2a config SHA-256, dataset MD5, source V2 checkpoint SHA-256 and model-state SHA-256 are pinned;
- the model family remains the existing Residual U-Net with `baseChannels=32`;
- the package contract accepts grayscale `float32` NCHW `1×1×512×512` tensors in `[0,1]`, where white is `1.0` and ink is `0.0`;
- output shape must equal input shape, output must be finite and remain in `[0,1]`;
- packaging uses a CPU TorchScript trace of the already frozen model;
- a deterministic fixed linear-ramp probe is executed twice on the eager model and once after TorchScript reload;
- eager repeat max-absolute difference must be `<=1e-7` and eager-versus-reloaded difference must be `<=1e-5`;
- model-state SHA-256 must be identical before and after packaging;
- optimizer creation, backpropagation, training and held-out access are forbidden;
- the produced package remains a private Stage 11 candidate artifact. The package is not committed to ordinary Git.

The package SHA-256 is intentionally learned only from the real execution artifact. Repository truth keeps package identity/size null until that execution occurs; CI must not fabricate a successful package artifact.

## Execution environment

A CPU Colab notebook mounts Google Drive, verifies the exact frozen `best.pt`, executes the packaging runtime, writes the TorchScript package and `candidate_package_evidence.v1.json` under the Stage 11 packaging Drive root, and displays the evidence. GPU is unnecessary because this operation is packaging/smoke validation rather than training.

## Safety and governance

The packaging flow cannot read the consumed held-out or Stage 9A evaluation artifacts and does not load dataset truth. It only reads the frozen candidate checkpoint. Static CI rejects training/dataset access tokens in the packaging runtime and validates the pending current truth fail-closed.

A packaging smoke-test PASS would establish portable candidate construction and exact-byte custody evidence only. It would not establish OMR correctness, musical truth, production readiness, automatic production promotion, final production model selection or Stage 12 entry.

## Next boundary

After genuine packaging evidence is returned and accepted, the next safe Stage 11 boundary may define integration-facing inference adapter validation around that exact package. Any such boundary must remain separate from production authorization and must not use the consumed held-out set for tuning.
