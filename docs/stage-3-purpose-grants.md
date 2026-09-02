# Stage 3 Purpose Grants — Beethoven and Barley

**Status:** PRODUCTION-EFFECTIVE  
**Authorized on:** 2026-09-02  
**Purpose:** `pdf_pipeline_evaluation` only  
**Grant set:** `stage3.purpose-grants.beethoven-barley.v1`  
**Canonical grant SHA-256:** `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`  
**Merged by:** PR #96  
**Production main:** `6ebe160309c562e9841a3c313d5ca507592f1386`  
**Post-merge validation:** Run #238 (`33620323970`) — Python 3.11 / 3.12 SUCCESS

## Overlay semantics

Historical Stage 1 catalog evidence is immutable. `evidence/stage1c/corpus/catalog.v2.json` remains unchanged with original `pdf_pipeline_evaluation=not_requested` fields. Later Stage 3 authorization is stored separately at `evidence/stage3/governance/purpose-grants.v1.json` and runtime accepts only its approved canonical digest.

## Granted items

- Beethoven: `dataset.item.imslp799143-beethoven-op48-no3.v1`, SHA-256 `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`;
- Barley: `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1`, SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`.

Restrictions: split `development`; storage `managed_standard`; environment `stage1_offline`; external export `false`.

## Non-grants

No model training, Stage 4 calibration, publication, demonstration, external export or held-out permission change is granted. Chopin remains governed only by existing `held_out_evaluation`.

## Runtime boundary

`src/st_score_restore/stage3_purpose_grants.py` validates the immutable overlay, exact item/artifact/purpose tuple and historical baseline state, applies the grant only in memory, and delegates to the existing Stage 3 custody executor. Approved review, retention/revocation, storage/environment, exact SHA-256, exact byte size, PDF policy/resource limits and vector/hybrid preservation still apply.

## Current execution state

The grant itself is already production-effective. The Stage 3 real-corpus runner is carried by **non-draft PR #99** on `stage3-real-corpus-runner`. Draft PR #98 was closed unmerged after the Draft→Ready connector failed; no authorization or merge gate was bypassed. Real Stage 3 corpus execution is still not frozen/accepted, and the runner keeps `stage3ExitPass=false` and `stage4EntryAuthorized=false` until separate exit evidence is accepted.
