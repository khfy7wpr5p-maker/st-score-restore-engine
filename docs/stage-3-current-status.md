# Stage 3 Current Status — Multi-page PDF Pipeline

**Status:** ACTIVE — CORE PRODUCTION-EFFECTIVE / AUTHORIZED EXECUTION SLICE  
**As of:** 2026-09-02  
**Tracking:** Issue #90  
**Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Entry CI:** Run #228 (`33609061197`) — Python 3.11 / 3.12 SUCCESS  
**Core merge main:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa`  
**Core post-merge CI:** Run #232 (`33615937390`) — Python 3.11 / 3.12 SUCCESS  
**Active branch:** `stage3-authorized-pdf-execution`  
**Stage 4:** NOT STARTED / BLOCKED pending explicit Stage 3 exit PASS

## Production-effective core

PR #92 merged the deterministic PDFium core. Run #232 passed dependency, repository, architecture, Stage 1/2, Stage 3 PDF pipeline, full test and compile gates on Python 3.11 and 3.12.

Production core:

- `src/st_score_restore/pdf_pipeline.py`;
- `pypdfium2==5.13.0` / PDFium;
- exact source SHA-256 identity;
- stable PDFium page ordering;
- page-object inspection before rendering;
- `raster_only` rendering only;
- `vector_only` preservation;
- `hybrid` preservation + review;
- unknown/over-limit original fallback;
- source/page/derivative SHA-256 provenance;
- deterministic Stage 2 quality analysis on raster derivatives.

Initial limits remain uncalibrated engineering defaults: 200 DPI, 64 pages, 40M pixels/page, 160M total rendered pixels, 8,000-pixel dimension and object depth 15. Held-out data did not tune them.

## Authorized execution slice

The current slice adds `src/st_score_restore/stage3_custody_execution.py`. Renderer capability does not imply dataset permission.

Before the PDF pipeline can run on a corpus object, the Stage 3 execution boundary requires:

1. canonical catalog validation;
2. PDF input kind;
3. `external_available` artifact state;
4. approved dataset review;
5. non-revoked and non-deletion state;
6. valid retention;
7. exact split-specific purpose;
8. granted/date-valid purpose permission;
9. split/storage/environment/retention/export restrictions;
10. exact artifact SHA-256;
11. exact artifact byte size.

Split-purpose mapping:

- development → `pdf_pipeline_evaluation`;
- held-out → `held_out_evaluation`.

A broad project-development approval or historical `quality_evaluation` permission is not reinterpreted as Stage 3 PDF authorization.

## Current real-corpus authorization state

Accepted PDF corpus items:

- Beethoven development scanned PDF — `pdf_pipeline_evaluation=not_requested` → **blocked**;
- Barley development digital guitar-TAB PDF — `pdf_pipeline_evaluation=not_requested` → **blocked**;
- Chopin C17C held-out scanned PDF — `held_out_evaluation=granted` → purpose gate satisfied, but exact custody bytes must still be materialized through approved custody before execution.

Ordinary Git contains no real corpus PDF/image bytes and does not expose the opaque custody objects as local files. Therefore this slice can validate the execution contract with synthetic bytes but cannot claim real Stage 3 corpus execution complete.

## Output boundary

Public-safe receipts may include:

- dataset item ID;
- source SHA-256 and byte size;
- split/purpose/storage/environment/date;
- authorization reference;
- pipeline/renderer versions;
- deterministic manifest digest;
- aggregate page classification/status counts.

Detailed page manifests, quality metrics/findings and rendered derivative bytes remain custody-only. No receipt authorizes export, calibration, training, publication, OMR or musical correctness claims.

## Remaining Stage 3 exit gates

Stage 3 exit is **not yet PASS**. Remaining gates include:

- real authorized-corpus execution where permissions and custody access permit;
- explicit limitations review;
- frozen public-safe execution evidence without real bytes;
- exact-head and post-merge Python 3.11/3.12 CI;
- separate Stage 3 exit acceptance decision.

Development-purpose permission must be handled in a dedicated governance slice if Stage 3 execution of those development PDFs is desired. It must not be inferred from the user's general approval to continue development.

## Safety/non-claims

Stage 3 does not perform OMR, symbol completion or musical inference. It does not establish musical correctness, OMR improvement, restoration effectiveness, representativeness or absence of bias. Training, calibration and publication remain unauthorized.

C17D `external_export=false`, historical Stage 1/2 evidence immutability and the separate sensitive phone-photo block remain unchanged.
