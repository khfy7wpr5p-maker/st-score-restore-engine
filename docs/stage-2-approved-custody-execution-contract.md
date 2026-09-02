# Stage 2 Approved-Custody Execution Contract

**Status:** ACTIVE IMPLEMENTATION CONTRACT / Stage 2 exit accepted separately  
**Stage:** 2 — Complete deterministic quality analysis  
**Tracking:** Issue #83  
**Stage 3:** ENTRY ELIGIBLE / NOT STARTED after production-effective Stage 2 acceptance

## Purpose

This contract defines the approved path from admitted corpus metadata to real-byte Stage 2 quality analysis. It does not move real score/PDF/image bytes into ordinary Git and does not broaden any Stage 1 permission.

Runtime entry point: `run_authorized_quality_execution(...)` in `src/st_score_restore/stage2_custody_execution.py`.

## Required pre-analysis gates

The execution boundary fails closed unless all of the following are true:

1. the complete dataset catalog passes canonical validation;
2. the requested dataset item exists;
3. artifact state is `external_available`;
4. dataset review is approved;
5. revocation/deletion state permits use;
6. retention remains valid;
7. split/purpose mapping is exact: `development` → `quality_evaluation`, `held_out` → `held_out_evaluation`;
8. the selected purpose permission is granted and date-valid;
9. split, storage, environment, retention and external-export restrictions are enforced;
10. transient custody bytes match the admitted SHA-256 exactly;
11. transient custody bytes match the admitted byte size exactly.

A mismatch rejects execution before analysis.

## Development versus held-out

Development and held-out data are never interchangeable. Held-out execution remains evaluation-only and must not tune Stage 2 thresholds, choose hardening constants, authorize training or authorize calibration.

## Output separation

Every successful or controlled-deferred execution produces a deterministic public-safe receipt. Public receipts may contain already-admitted operational metadata such as dataset item ID, exact source digest/size, split/purpose, storage class, analyzer version, controlled result state, report digest and authorization reference.

Public receipts must not contain detailed quality metrics or findings. Detailed analyzer output remains a custody-only object unless separately authorized for publication.

C17D is held-out, `managed_restricted`, and `external_export=false`. Its detailed report must not be exported to public Git.

## PDF boundary

Digital PDFs remain vector-preserved and return `not_applicable_vector_pdf`; Stage 2 introduces no rasterization for them.

Accepted scanned/hybrid PDFs pass custody and exact-source gates, but pixel analysis remains intentionally deferred until the Stage 3 renderer boundary. Controlled result:

`deferred_stage3_renderer`

with analyzer error code:

`pdf_renderer_not_available`

This is a fail-closed boundary result, not evidence that Stage 3 has started.

## Accepted expanded-v2 execution roles

- Beethoven Op.48 No.3 — development / `quality_evaluation` / scanned PDF → Stage 3 renderer deferred;
- Wikimedia Guitar Technical Exercise No.1 — development / `quality_evaluation` / combined staff+TAB PNG → raster analysis;
- Barley “Your Face Your Tongue Your Wit” — development / `quality_evaluation` / digital guitar-TAB PDF → vector-preserved;
- Chopin Op.69 metadata-v2 — held-out / `held_out_evaluation` / scanned PDF → Stage 3 renderer deferred;
- Nearer My God to Thee deidentified phone photo — held-out / `held_out_evaluation` / `managed_restricted` JPEG → raster analysis with restricted-output handling.

The separate user-provided sensitive `Fly Me to the Moon` path is not part of the accepted corpus.

## Real execution evidence

Frozen public evidence is `evidence/stage2/corpus/execution-evidence.v1.json` with digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`. Five of five accepted objects matched exact SHA-256 and exact byte size. Outcomes were 2 analyzed, 1 vector not-applicable and 2 controlled Stage-3-renderer deferrals.

The contract itself does not retroactively declare Stage 2 exit PASS. That later decision is separately recorded by `evidence/stage2/corpus/stage2-exit-acceptance.v1.json`, bound to main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`, exact-head Run #220 and post-merge Run #221.

## Non-claims and retained limitations

Neither this contract nor the separate Stage 2 acceptance establishes representativeness, absence of bias, musical correctness, OMR improvement or restoration effectiveness. Thresholds remain `uncalibrated_engineering_defaults`; Stage 4 owns real-data calibration. Training, calibration and publication remain unauthorized.

The separate acceptance makes Stage 3 entry eligible only after that acceptance is production-effective. Stage 3 remains NOT STARTED in this slice.
