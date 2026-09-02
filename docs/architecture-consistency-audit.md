# Architecture Consistency Audit — 2026-09-02

**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Stage 1:** COMPLETE / PASS  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 2 execution-evidence main:** `ffea7f5aa618187f3cabcfb49801804e3f6658bf`  
**Stage 2 final acceptance / Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Stage 3 core main:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa`  
**Stage 3 authorized-execution main:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b`  
**Stage 3 purpose-grant main / production baseline:** `6ebe160309c562e9841a3c313d5ca507592f1386`  
**Stage 3:** ACTIVE under Issue #90; non-draft PR #99  
**Stage 4:** NOT STARTED / BLOCKED pending Stage 3 final exit PASS

## Authority

Merged `main` plus accepted deterministic evidence is production truth. Historical Stage 1/2 evidence remains immutable. Open PR state is not production-effective. CI is exact-head scoped.

## Current findings

| Area | Result |
|---|---|
| Stage 1 final exit | PASS / EFFECTIVE |
| Historical C15/C16 | PRESERVED |
| Stage 2 final exit | PASS / EFFECTIVE |
| Stage 2 execution evidence | IMMUTABLE / `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d` |
| Stage 3 PDFium core | EFFECTIVE / main `29b4244...` / Run #232 |
| Stage 3 authorized execution | EFFECTIVE / main `d834ed42...` / Run #235 |
| Beethoven/Barley purpose overlay | EFFECTIVE / main `6ebe1603...` / Run #238 |
| Purpose grant digest | `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8` |
| Stage 3 renderer | PDFium / `pypdfium2==5.13.0` |
| Vector/hybrid policy | no silent rasterization |
| Draft PR #98 | CLOSED UNMERGED after Draft→Ready connector failure |
| Replacement PR #99 | OPEN / NON-DRAFT / same runner branch lineage |
| PR #98 final exact-head CI | Run #243 success on `7778cdf790daa806efd166d9d3bf1f5a011ecc71`, Python 3.11/3.12 |
| PR #99 final exact-head CI | MUST rerun after this PR-number reconciliation commit |
| Beethoven/Barley Stage 3 purpose | GRANTED via exact overlay |
| Chopin held-out purpose | existing `held_out_evaluation` only |
| Real Stage 3 corpus execution | NOT COMPLETE / NOT FROZEN |
| Stage 4 | BLOCKED |

## Immutable evidence retained

Canonical Stage 1 expanded-v2 digests: catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Historical C15/C16 remain `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` / `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

Historical Stage 2 PDF deferrals and vector-preservation results are not rewritten now that Stage 3 has PDFium.

## Purpose grant boundary

PR #96 / Run #238 made `evidence/stage3/governance/purpose-grants.v1.json` production-effective. Runtime applies it only to an in-memory catalog copy after exact digest/item/purpose validation. Restrictions remain development, `managed_standard`, `stage1_offline`, `external_export=false`. Training, calibration, publication, demonstration and held-out permission changes remain false.

Chopin remains held-out evaluation only. Held-out results must not tune thresholds, hardening constants, page policy, renderer/resource limits or other Stage 2/3 constants.

## Replacement PR history

Draft PR #98 carried the runner and architecture refresh. Its final head `7778cdf790daa806efd166d9d3bf1f5a011ecc71` passed Run #243 (`33639819769`) on Python 3.11/3.12. Draft→Ready failed only at the connector GraphQL response field `Repository.fullDatabaseId`. Per governance, #98 was closed unmerged and non-draft replacement PR #99 was opened from the same branch/head lineage; this does not reuse Run #243 as the replacement merge gate. This reconciliation moves the head and requires fresh exact-head CI on #99.

## Exact corpus identities

- Beethoven `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`, 1,182,561 bytes;
- Barley `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`, 84,689 bytes;
- Chopin `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`, 1,114,479 bytes.

Repository stores metadata/opaque custody locators, not real PDFs. Real execution must resolve exact approved bytes outside ordinary Git, verify SHA-256 and size before PDFium, keep detailed output custody-only, and freeze only redacted public evidence.

## CI / architecture boundary

`tools/validate_architecture_consistency.py` must bind production main `6ebe160309c562e9841a3c313d5ca507592f1386`, Run #238, purpose-grant digest/status, active replacement PR #99, historical Stage 1/2 immutability, Stage 3 renderer/custody/runner contracts and Stage 4 blocking.

CI must include `validate_stage3_pdf_pipeline.py`, `validate_stage3_custody_execution.py`, `validate_stage3_real_corpus_runner.py`, full tests and compile on Python 3.11/3.12.

## Safety/non-claims

Stage 3 does not perform OMR, infer musical correctness, establish restoration/OMR effectiveness, establish representativeness/absence of bias, or authorize training/calibration/publication.

The separate sensitive `Fly Me to the Moon` phone-photo path remains outside this runner and independently blocked pending high-assurance-vault verification.
