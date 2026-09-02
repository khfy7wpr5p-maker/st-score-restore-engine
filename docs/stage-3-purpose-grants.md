# Stage 3 Purpose Grants — Beethoven and Barley

**Status:** explicit authorization recorded in a dedicated Stage 3 overlay; effective only after this slice merges and post-merge CI succeeds  
**Authorized on:** 2026-09-02  
**Purpose:** `pdf_pipeline_evaluation` only  
**Grant set:** `stage3.purpose-grants.beethoven-barley.v1`  
**Canonical grant SHA-256:** `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`

## Why this is an overlay

Historical Stage 1 catalog evidence is immutable. The accepted `evidence/stage1c/corpus/catalog.v2.json` therefore remains byte/content stable with its original `pdf_pipeline_evaluation=not_requested` fields. The new authorization is represented separately at:

`evidence/stage3/governance/purpose-grants.v1.json`

Runtime code accepts that overlay only when its canonical SHA-256 equals the approved digest above. An arbitrary caller-created grant object cannot widen Stage 3 permissions.

## Granted items

The overlay grants `pdf_pipeline_evaluation` only for these exact development artifacts:

- Beethoven: `dataset.item.imslp799143-beethoven-op48-no3.v1`, exact artifact SHA-256 `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`;
- Barley: `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1`, exact artifact SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`.

The grant is restricted to:

- split: `development`;
- storage class: `managed_standard`;
- environment: `stage1_offline`;
- external export: `false`.

## Explicit non-grants

This authorization does **not** grant:

- model training;
- Stage 4 calibration;
- publication;
- demonstration;
- external export;
- held-out permission changes;
- OMR or musical-correctness claims.

Chopin remains governed only by its existing `held_out_evaluation` permission. Historical Stage 1/2 evidence remains unchanged.

## Runtime boundary

`src/st_score_restore/stage3_purpose_grants.py` validates the immutable overlay, confirms the exact item/artifact/purpose tuple, refuses to override any historical catalog state other than `not_requested`, applies the grant only to an in-memory catalog copy, and then delegates to the existing Stage 3 custody executor.

All existing gates still apply after the grant: approved dataset review, revocation/retention state, split/storage/environment restrictions, exact artifact SHA-256, exact byte size, PDF policy, resource bounds, vector/hybrid preservation, and custody-only detailed output.

A valid grant therefore advances Beethoven and Barley only to the exact-byte custody gate; it does not fabricate or bypass the admitted source bytes.
