# Stage 2 Approved-Custody Execution Contract

**Status:** ACTIVE IMPLEMENTATION CONTRACT  
**Stage:** 2 — Complete deterministic quality analysis  
**Tracking:** Issue #83  
**Stage 3:** BLOCKED until explicit Stage 2 exit PASS

## Purpose

This contract defines the only approved Stage 2 path from admitted corpus metadata to real-byte quality analysis. It does not move real score/PDF/image bytes into ordinary Git and it does not broaden any Stage 1 permission.

The runtime entry point is `run_authorized_quality_execution(...)` in `src/st_score_restore/stage2_custody_execution.py`.

## Required pre-analysis gates

Before the OpenCV quality analyzer receives source bytes, the execution boundary must fail closed unless all of the following are true:

1. the complete dataset catalog passes the canonical dataset governance validator;
2. the requested `datasetItemId` exists in that validated catalog;
3. the artifact is `external_available`;
4. dataset review is `approved`;
5. revocation is `not_revoked` and the artifact is not pending deletion;
6. artifact retention remains valid on the execution date;
7. Stage 2 split/purpose mapping is exact:
   - `development` → `quality_evaluation`;
   - `held_out` → `held_out_evaluation`;
8. the selected purpose permission is `granted` and valid on the execution date;
9. any `split_allowlist`, `storage_class_allowlist`, `environment_allowlist`, `retention_not_after`, and `external_export` restriction is enforced;
10. the transient custody bytes match the admitted artifact **SHA-256 exactly**;
11. the transient custody bytes match the admitted artifact **byte size exactly**.

A mismatch on either source identity field rejects the execution before analysis.

## Existing custody environment code

The default execution environment is the existing catalog-governed offline custody environment code `stage1_offline`. Reusing this environment code does not mean Stage 2 is part of Stage 1; it preserves compatibility with the already approved dataset restriction vocabulary rather than inventing a new environment authorization.

If an item permission contains an `environment_allowlist`, the runtime environment must be in that allowlist.

## Development versus held-out

Development and held-out data are never interchangeable.

A development item cannot be executed under `held_out_evaluation`. A held-out item cannot be executed under `quality_evaluation`. The execution API requires the caller to provide the purpose explicitly and rejects a purpose/split mismatch.

Held-out execution remains evaluation-only. It must not tune Stage 2 thresholds, choose hardening constants, authorize training, or authorize calibration.

## Output separation

Every successful or controlled-deferred execution produces a deterministic **public-safe receipt**. The receipt may contain source-bound operational facts already admitted by repository metadata, such as:

- dataset item ID;
- exact source SHA-256;
- exact byte size;
- split and purpose;
- storage class and execution environment;
- analyzer version;
- result state;
- detailed report digest when a report exists;
- authorization reference;
- explicit safety assertions.

The public receipt **must not contain quality metrics or findings**.

Detailed analyzer output is kept in a separate custody-only object and is available only through the explicit `restricted_report_for_custody()` API. Stage 2 execution itself never grants publication permission. Therefore detailed real-corpus metrics remain custody-only unless a separate, valid publication authorization exists outside this contract.

For C17D, the accepted held-out permission additionally contains `external_export=false`; the public receipt must record that export is explicitly blocked and detailed metrics/reports must not be exported to public Git.

## PDF boundary

Digital PDFs remain vector-preserved. Their Stage 2 result is `not_applicable_vector_pdf` and no rasterization is introduced.

Accepted `scanned_pdf` or `hybrid_pdf` items pass the custody and source-identity gates, but pixel analysis remains intentionally deferred until the approved Stage 3 renderer boundary exists. The controlled result is:

`deferred_stage3_renderer`

with analyzer error code:

`pdf_renderer_not_available`

This is a fail-closed boundary result, not evidence that Stage 3 has started.

## Public receipt assertions

A valid receipt keeps these claims explicit:

- exact digest matched;
- exact byte size matched;
- purpose permission valid;
- split/storage/environment/retention restrictions satisfied;
- held-out threshold tuning used: false;
- source bytes modified: false;
- real artifact bytes in Git: false;
- training authorized: false;
- calibration authorized: false;
- publication authorized: false.

## Accepted expanded-v2 execution roles

The five accepted Stage 1 expanded-v2 items retain their existing roles:

- Beethoven Op.48 No.3 — `development` / `quality_evaluation` / scanned PDF → Stage 3 renderer deferred;
- Wikimedia Guitar Technical Exercise No.1 — `development` / `quality_evaluation` / combined staff+TAB PNG → Stage 2 raster analysis;
- Barley “Your Face Your Tongue Your Wit” — `development` / `quality_evaluation` / guitar-TAB PDF → vector-preservation or catalog-consistent PDF result;
- Chopin Op.69 metadata-v2 — `held_out` / `held_out_evaluation` / scanned PDF → Stage 3 renderer deferred;
- Nearer My God to Thee deidentified phone photo — `held_out` / `held_out_evaluation` / `managed_restricted` JPEG → Stage 2 raster analysis with restricted-output handling.

The separate user-provided sensitive `Fly Me to the Moon` phone-photo path is not part of this accepted corpus and remains outside Stage 2 execution.

## Non-claims

This contract does not establish:

- representativeness;
- absence of bias;
- musical correctness;
- OMR correctness or improvement;
- restoration effectiveness;
- model-training permission;
- calibration permission;
- Stage 2 exit PASS;
- Stage 3 entry.

Stage 2 exit still requires real approved-custody execution evidence, limitations review, exact-main/post-merge CI evidence, and a separate evidence-bound Stage 2 acceptance decision.
