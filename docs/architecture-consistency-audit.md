# Architecture Consistency Audit — 2026-09-02

**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Stage 1:** COMPLETE / PASS  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 2 execution-evidence main:** `ffea7f5aa618187f3cabcfb49801804e3f6658bf`  
**Stage 2 final acceptance / Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Stage 3 core main:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa`  
**Stage 3 authorized-execution main:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b`  
**Stage 3 purpose-grant main / current production baseline:** `6ebe160309c562e9841a3c313d5ca507592f1386`  
**Stage 3:** ACTIVE under Issue #90; Draft PR #98  
**Stage 4:** NOT STARTED / BLOCKED pending Stage 3 final exit PASS

## Purpose

This audit separates immutable historical evidence, merged production truth and active PR state. Authority order is merged `main` plus accepted deterministic evidence. Open PR state is not production truth. CI evidence is exact-head scoped and head movement invalidates earlier runs.

## Fresh-read findings

| Area | Result | Interpretation |
|---|---|---|
| Stage 1 final exit | PASS / EFFECTIVE | accepted data boundary remains valid |
| Historical C15/C16 | PRESERVED | original historical decisions remain immutable |
| Expanded-v2 Stage 1 evidence | ACCEPTED | 5 real / 0 synthetic; 3 development families; 2 held-out families; no split leakage/digest duplication |
| Stage 2 analyzer/custody | MERGED / VERIFIED | production-effective; thresholds uncalibrated |
| Stage 2 public execution evidence | PASS / IMMUTABLE | digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d` |
| Stage 2 final acceptance | PASS / EFFECTIVE | main `87198a5a917ab6b3efc277762016a5f5b0dd3aab`, Run #228 |
| Stage 3 PDFium core | PASS / EFFECTIVE | main `29b4244eeaeb2239ff959e6dd6d4128311f005fa`, Run #232 |
| Stage 3 authorized execution | PASS / EFFECTIVE | main `d834ed42e3f553308aef7f6adb7e8cb873593f0b`, Run #235 |
| Beethoven/Barley purpose overlay | PASS / EFFECTIVE | main `6ebe160309c562e9841a3c313d5ca507592f1386`, Run #238 |
| Purpose grant digest | PASS | `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8` |
| Stage 3 renderer | PRODUCTION-EFFECTIVE | PDFium / `pypdfium2==5.13.0` |
| Vector/hybrid policy | FAIL-CLOSED | no silent rasterization |
| Stage 3 PR #98 | OPEN / DRAFT | fail-closed real-corpus runner, not production-effective yet |
| PR #98 pre-refresh exact-head CI | PASS | head `696729f825ed23ee89edc972cbf46303f3ebba73`, Run #242, Python 3.11/3.12 |
| Beethoven/Barley Stage 3 purpose | GRANTED | exact overlay only; historical catalog remains unchanged |
| Chopin held-out purpose | GRANTED EXISTING | `held_out_evaluation` only; never tuning |
| Real Stage 3 corpus execution | NOT COMPLETE / NOT FROZEN | exact custody execution remains pending |
| Ordinary Git real source/derivative bytes | PASS | zero corpus/derivative bytes permitted |
| Stage 4 | BLOCKED | requires separate Stage 3 final exit PASS |

## Immutable evidence retained

Canonical Stage 1 expanded-v2 digests:

- catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Historical C15 snapshot: `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`; historical C16 report: `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

Stage 2 evidence remains historical and is not rewritten now that Stage 3 can process PDFs. The original scanned/hybrid `deferred_stage3_renderer` outcomes remain valid descriptions of the Stage 2 execution moment.

## Stage 3 production truth

PR #92 made the PDFium page pipeline production-effective. PR #94 made the Stage 3 custody execution boundary production-effective. PR #96 made the separate Beethoven/Barley purpose-grant overlay production-effective. Their post-merge Repository validation runs were #232, #235 and #238 respectively, all successful on Python 3.11 and 3.12.

The purpose overlay does not alter `evidence/stage1c/corpus/catalog.v2.json`; runtime applies it to an in-memory copy only after exact digest/item/purpose validation. Restrictions remain development split, `managed_standard`, `stage1_offline`, `external_export=false`. Training, calibration, publication, demonstration and held-out authorization changes remain false.

Chopin is governed only by its existing held-out permission. Held-out results must not tune thresholds, hardening constants, page policy, renderer limits or resource limits.

## PR #98 runner truth

PR #98 introduces a runner for exactly Beethoven, Barley and Chopin. It requires exact `pypdfium2==5.13.0`, accepted catalog identity, exact admitted source identity, paths outside the ordinary Git worktree, public-safe receipts and custody-only detailed outputs. It keeps `heldOutThresholdTuningUsed=false`, `stage3ExitPass=false`, and `stage4EntryAuthorized=false`.

Run #242 (`33621535491`) passed on head `696729f825ed23ee89edc972cbf46303f3ebba73` before this documentation/validator reconciliation. Because this reconciliation changes the PR head, Run #242 is historical evidence only; the new head requires fresh exact-head CI before merge.

## Real-corpus custody boundary

Accepted exact identities:

- Beethoven `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`, 1,182,561 bytes;
- Barley `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`, 84,689 bytes;
- Chopin `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`, 1,114,479 bytes.

The repository stores metadata/opaque custody locators, not those real PDF bytes. Real execution must materialize exact bytes in approved/transient custody, verify digest and byte size before PDFium processing, keep rendered derivatives and detailed manifests outside ordinary Git, and freeze only redacted public-safe evidence.

## CI and architecture boundary

`tools/validate_architecture_consistency.py` must bind current production main `6ebe160309c562e9841a3c313d5ca507592f1386`, Run #238, purpose-grant digest/status, active PR #98 state, historical Stage 1/2 immutability, Stage 3 renderer/custody/runner contracts and Stage 4 blocking. It must not require obsolete `pdf_pipeline_evaluation=not_requested` as the current effective Beethoven/Barley state.

CI must include `validate_stage3_pdf_pipeline.py`, `validate_stage3_custody_execution.py`, `validate_stage3_real_corpus_runner.py`, full tests and compile on Python 3.11/3.12.

## Safety/non-claims

Stage 3 does not perform OMR, infer notes/rhythm/string-fret information, establish musical correctness, claim OMR improvement or restoration effectiveness, establish representativeness/absence of bias, or authorize training/calibration/publication.

The separate sensitive `Fly Me to the Moon` phone-photo path remains outside this Stage 3 runner and independently blocked pending real high-assurance-vault verification.

## Stage 4 boundary

Stage 4 is NOT STARTED / BLOCKED. No real-data threshold calibration may begin until a separate Stage 3 exit decision is PASS and production-effective.
