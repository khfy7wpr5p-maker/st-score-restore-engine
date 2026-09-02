# Architecture Consistency Audit — 2026-09-02

**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Stage 1:** COMPLETE / PASS  
**Stage 2:** COMPLETE / PASS acceptance recorded in this slice  
**Stage 2 evidence main:** `ffea7f5aa618187f3cabcfb49801804e3f6658bf`  
**Stage 3:** ENTRY ELIGIBLE / NOT STARTED

## Purpose

This audit separates immutable historical evidence, merged production truth and the final Stage 2 acceptance transition. Authority order is merged `main` plus deterministic accepted evidence. Open PR state is never production truth, and head movement invalidates exact-head CI.

## Fresh-read findings

| Area | Result | Interpretation |
|---|---|---|
| Stage 1 final exit | PASS / EFFECTIVE | accepted entry to Stage 2 remains valid |
| Historical C15/C16 | PRESERVED | historical C16 remains insufficient for its original snapshot |
| Expanded-v2 Stage 1 evidence | ACCEPTED | 5 real / 0 synthetic; 3 development families; 2 held-out families; no leakage or digest duplication |
| Stage 2 quality analyzer | MERGED / VERIFIED | deterministic analyzer 0.1.1, uncalibrated engineering defaults |
| Stage 2 custody execution contract | MERGED / VERIFIED | contract 0.1.0, exact source and permission gates |
| Real accepted-corpus execution | PASS | 5/5 exact SHA-256 and byte-size identity bindings |
| Frozen execution evidence | PASS | `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d` |
| PR #87 exact-head CI | PASS | Run #220, Python 3.11/3.12 |
| PR #87 merge | PASS | main `ffea7f5aa618187f3cabcfb49801804e3f6658bf` |
| Post-merge main CI | PASS | Run #221, Python 3.11/3.12 |
| Review/thread/head reconciliation | PASS | Ready head remained exact verified head; no reviews or unresolved threads |
| Held-out threshold tuning | FALSE | held-out remained evaluation-only |
| C17D detailed export | BLOCKED | `managed_restricted`, `external_export=false` |
| Ordinary Git real artifact bytes | PASS | zero real score/PDF/image corpus bytes under evidence |
| Limitations review | PASS | two scanned/hybrid PDF renderer deferrals explicitly accepted as Stage 2 boundary |
| Stage 2 final exit | PASS decision recorded | separate machine-readable acceptance layer |
| Stage 3 | ENTRY ELIGIBLE / NOT STARTED | must use a new focused branch after acceptance is production-effective |

## Stage 1 evidence retained

Canonical expanded-v2 digests:

- catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Historical C15 snapshot canonical SHA-256 remains `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`; historical C16 report remains `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## Stage 2 execution truth

The accepted five-item corpus produced controlled outcomes:

1. Beethoven scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
2. C17A combined staff+TAB PNG — `analyzed`;
3. C17B digital guitar-TAB PDF — `not_applicable_vector_pdf`;
4. C17C held-out Chopin scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
5. C17D held-out deidentified JPEG — `analyzed` under `managed_restricted` custody.

These results are source-digest-bound. Public evidence contains no detailed metrics/findings or provider/local custody locator. Detailed C17A/C17B/C17D reports remain external custody evidence; C17D export is explicitly blocked.

## Limitations acceptance

The two PDF deferrals are intentional fail-closed boundaries, not hidden failures. Stage 2 does not own scanned/hybrid PDF rendering; Stage 3 does. Digital PDFs remain vector-preserved. Thresholds remain uncalibrated until Stage 4.

No Stage 2 evidence establishes musical correctness, OMR correctness/improvement, restoration effectiveness, representativeness or absence of bias. Training, calibration and publication remain unauthorized.

## Stage 2 exit decision

`evidence/stage2/corpus/stage2-exit-acceptance.v1.json` records the separate `PASS` decision bound to:

- evidence main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`;
- PR #87 exact head `7d6c812dd09a1ce42ae91d224f9d08992884b77a`;
- exact-head Run #220 (`33606224352`) success on Python 3.11/3.12;
- post-merge Run #221 (`33607016064`) success on Python 3.11/3.12;
- frozen corpus execution evidence digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

The historical execution evidence remains immutable with `stage2ExitPass=false` and `stage3EntryAuthorized=false`; the PASS is intentionally a separate later acceptance layer.

## Stage 3 boundary

Stage 3 is ENTRY ELIGIBLE / NOT STARTED. No Stage 3 renderer code belongs in this acceptance slice. After this acceptance commit is merged and post-merge main CI is green, Stage 3 may begin in a new focused branch/PR.
