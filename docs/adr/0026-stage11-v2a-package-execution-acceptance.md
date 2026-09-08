# ADR 0026 — Stage 11 V2a Package Execution Acceptance

Status: Accepted for Stage 11 frozen-candidate custody only  
Date: 2026-09-08

## Context

ADR 0025 defined a fail-closed packaging boundary for the frozen V2a candidate checkpoint. Genuine execution evidence is now available for the exact frozen checkpoint SHA-256 `15afc73233c91a80a7ef1285cb631d5d3acd681e9cfed9a93b35642bf39fff4c`.

The execution used the checkpoint retrieved from the authorized Stage 11 Google Drive training output. The package and execution evidence were then stored under the dedicated Stage 11 packaging Drive root. No consumed held-out or Stage 9A evaluation artifact was read during packaging.

## Accepted execution evidence

- checkpoint SHA-256: `15afc73233c91a80a7ef1285cb631d5d3acd681e9cfed9a93b35642bf39fff4c`
- checkpoint size: `23458927` bytes
- model-state SHA-256 before/after: `1d8becbebfb2b86beb21b4f757c6dacb01354c981bc7216b6e988fc74fd2d32b`
- V2a config SHA-256: `1250731992c01c238dd2376a95ced1d1c6f76dcdf87deb473ec94a0aa58f7818`
- source V2 checkpoint SHA-256: `363cb63bff2367c1119a4eea449a19d468a802160f45b4fe1f2d98ab04fb894b`
- package format: TorchScript trace
- package SHA-256: `7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234`
- package size: `7817857` bytes
- execution device: CPU
- execution Python: `3.13.5`
- execution PyTorch: `2.10.0+cpu`
- eager repeat max-absolute difference: `0.0`
- eager/reloaded max-absolute difference: `0.0`
- output range observed on the fixed probe: `[0.0, 1.0]`
- output shape: `1×1×512×512`

The committed evidence artifact is `evidence/stage11/v2a/v2a-candidate-package-evidence.v1.json`.

## Drive custody

The private candidate artifacts are stored under:

`MyDrive/ST_SCORE_RESTORE_STAGE11_PACKAGING/deepscoresv2_dense_v2a_candidate/`

Drive folder ID: `1oBL1P_6slQ0j5aOguCLzJYIKAgQXnCXL`.

The package file ID is `1oJ9lOEpq7trDD8XZpVwCzQzMQ2mk-wWD` and the evidence file ID is `1d6WRb43tItsdjTtarAHkwccdn2dKWP8D`.

## Decision

Accept the packaging execution as a Stage 11 portable-candidate PASS. The candidate checkpoint remains frozen. The TorchScript artifact is a derivative custody artifact of that exact frozen checkpoint, not a newly trained or tuned model.

No optimizer was created, no backpropagation was executed, model weights did not mutate, and consumed held-out data was not accessed.

## Non-authorization

This acceptance does **not** authorize:

- production inference;
- production promotion;
- final production model selection;
- Stage 12 entry;
- any retuning against the already consumed held-out set;
- claims of OMR correctness or musical truth.

## Next safe boundary

The next safe Stage 11 boundary is non-training consumer/inference integration validation around the exact frozen package, using synthetic or otherwise non-heldout inputs. Any such work must preserve package identity and keep production and Stage 12 closed.
