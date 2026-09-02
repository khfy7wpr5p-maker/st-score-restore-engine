# Architecture Consistency Audit — 2026-09-02

**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Stage 1:** COMPLETE / PASS  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 2 execution-evidence main:** `ffea7f5aa618187f3cabcfb49801804e3f6658bf`  
**Stage 2 final acceptance main / Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Stage 3 core main:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa`  
**Stage 3:** ACTIVE under Issue #90  
**Stage 4:** NOT STARTED / BLOCKED pending Stage 3 exit PASS

## Purpose

This audit separates immutable historical evidence, merged production truth and active Stage 3 authorization work. Authority order is merged `main` plus deterministic accepted evidence. Open PR state is never production truth, and head movement invalidates exact-head CI.

## Fresh-read findings

| Area | Result | Interpretation |
|---|---|---|
| Stage 1 final exit | PASS / EFFECTIVE | accepted data boundary remains valid |
| Historical C15/C16 | PRESERVED | historical C16 remains insufficient for its original snapshot |
| Expanded-v2 Stage 1 evidence | ACCEPTED | 5 real / 0 synthetic; 3 development families; 2 held-out families; no leakage/digest duplication |
| Stage 2 quality analyzer | MERGED / VERIFIED | deterministic analyzer 0.1.1, uncalibrated engineering defaults |
| Stage 2 custody execution contract | MERGED / VERIFIED | contract 0.1.0, exact source and permission gates |
| Frozen Stage 2 execution evidence | PASS / IMMUTABLE | `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d` |
| Stage 2 final acceptance | PASS / EFFECTIVE | PR #89 merged to `87198a5a917ab6b3efc277762016a5f5b0dd3aab` |
| Stage 2 acceptance post-merge CI | PASS | Run #228, Python 3.11/3.12 |
| Stage 3 core merge | PASS / EFFECTIVE | PR #92 merged to `29b4244eeaeb2239ff959e6dd6d4128311f005fa` |
| Stage 3 core post-merge CI | PASS | Run #232 (`33615937390`), Python 3.11/3.12 |
| Stage 3 renderer | PRODUCTION-EFFECTIVE CORE | PDFium via `pypdfium2==5.13.0`, ADR 0017 |
| Stage 3 vector policy | FAIL-CLOSED | vector/hybrid pages not silently rasterized |
| Stage 3 development PDF purpose | BLOCKED | `pdf_pipeline_evaluation=not_requested` on accepted development PDFs |
| Stage 3 held-out Chopin purpose | GRANTED | `held_out_evaluation=granted`; exact custody bytes still required |
| Stage 3 real corpus execution | NOT COMPLETE | no purpose/custody bypass permitted |
| Held-out threshold tuning | FALSE | held-out remains non-tuning |
| C17D detailed export | BLOCKED | `managed_restricted`, `external_export=false` |
| Ordinary Git real artifact bytes | PASS | zero real score/PDF/image corpus bytes under evidence |
| Stage 4 | BLOCKED | requires separate Stage 3 exit PASS |

## Stage 1 evidence retained

Canonical expanded-v2 digests:

- catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Historical C15 snapshot canonical SHA-256 remains `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`; historical C16 report remains `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## Stage 2 production truth

The accepted five-item corpus produced historical controlled outcomes:

1. Beethoven scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
2. C17A combined staff+TAB PNG — `analyzed`;
3. C17B digital guitar-TAB PDF — `not_applicable_vector_pdf`;
4. C17C held-out Chopin scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
5. C17D held-out deidentified JPEG — `analyzed` under `managed_restricted` custody.

The execution evidence remains source-digest-bound and immutable. Final Stage 2 PASS is supplied by the separate acceptance record.

## Stage 3 core production truth

PR #92 merged `src/st_score_restore/pdf_pipeline.py`, exact `pypdfium2==5.13.0`, page-level raster/vector/hybrid policy, synthetic tests and the Stage 3 validator to main `29b4244eeaeb2239ff959e6dd6d4128311f005fa`.

Post-merge Run #232 (`33615937390`) succeeded on Python 3.11 and 3.12, including dependency/repository/architecture gates, historical Stage 1/2 validators, Stage 3 PDF validation, tests and compile.

The pipeline preserves exact source identity and page order. Raster-only pages may produce deterministic PNG derivatives; vector-only pages remain vector; hybrid and unknown/over-limit pages preserve original fallback/review. Initial limits are uncalibrated engineering defaults and held-out data did not choose them.

## Stage 3 authorized execution truth

Renderer availability is not dataset authorization. The new Stage 3 execution boundary requires canonical catalog state, PDF kind, review, revocation/deletion, retention, split-specific purpose permission, restrictions and exact SHA-256/byte size before invoking the PDF pipeline.

Normative purpose mapping:

- development → `pdf_pipeline_evaluation`;
- held-out → `held_out_evaluation`.

Current accepted development PDF records remain `pdf_pipeline_evaluation=not_requested`. They must not be executed simply because Stage 3 code exists or because the project owner approved continued development.

The held-out Chopin record has `held_out_evaluation=granted`, but the real exact PDF bytes remain in approved external custody and are not present in ordinary Git. Therefore synthetic contract validation is permitted while real corpus execution remains incomplete.

Public receipts are redacted to identity/authorization/renderer/manifest-digest/page-summary metadata. Detailed page records, metrics/findings and derivative bytes remain custody-only.

## CI boundary

The current authorized-execution branch must pass exact-head Repository validation on Python 3.11 and 3.12. CI includes both Stage 3 validators before the full test suite and compile.

No branch head may be merged based on an older run. Review/thread/base/head reconciliation and post-merge main validation remain mandatory.

## Safety/non-claims

Stage 3 does not perform OMR, infer notes/rhythm/string-fret information, establish musical correctness, claim OMR improvement or restoration effectiveness, establish representativeness/absence of bias, or authorize training/calibration/publication.

The separate user-provided sensitive `Fly Me to the Moon` phone-photo path remains outside this Stage 3 work and independently blocked.

## Stage 4 boundary

Stage 4 is NOT STARTED / BLOCKED. No real-data threshold calibration may begin until a separate Stage 3 exit decision is PASS and production-effective.
