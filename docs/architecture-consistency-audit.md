# Architecture Consistency Audit — 2026-09-02

**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Stage 1:** COMPLETE / PASS / production-effective  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3:** COMPLETE / PASS / production-effective  
**Stage 3 acceptance main:** `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0`  
**Stage 3 acceptance post-merge CI:** Run #253 (`33646323461`) — Python 3.11 / 3.12 SUCCESS  
**Stage 4:** ENTRY ELIGIBLE / NOT STARTED

## Authority

Merged `main` plus accepted deterministic evidence is production truth. Historical evidence remains immutable. Open PR state is not production-effective. CI is exact-head scoped. Stage 4 entry eligibility does not imply Stage 4 started or calibration authorized.

## Current findings

| Area | Result |
|---|---|
| Stage 1 final exit | PASS / EFFECTIVE |
| Historical C15/C16 | PRESERVED |
| Stage 2 final exit | PASS / EFFECTIVE |
| Stage 2 execution evidence | IMMUTABLE / `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d` |
| Stage 3 PDFium core | EFFECTIVE / Run #232 |
| Stage 3 authorized execution | EFFECTIVE / Run #235 |
| Beethoven/Barley purpose overlay | EFFECTIVE / Run #238 |
| Purpose grant digest | `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8` |
| Stage 3 renderer | PDFium / exact `pypdfium2==5.13.0` |
| Vector/hybrid policy | no silent rasterization |
| Stage 3 runner | EFFECTIVE / runtime main `5e682f1933a7167fc142689306352fe53b4b1833` / Run #246 |
| Real Stage 3 execution | COMPLETE / 3 items / 14 pages |
| Raster pages | 12 rendered |
| Vector pages | 2 preserved |
| Review-required | 0 |
| Page order | PRESERVED |
| Held-out tuning | FALSE |
| Execution evidence | EFFECTIVE / `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6` / Run #251 |
| Limitations review | PASS_WITH_ACCEPTED_LIMITATIONS / `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d` |
| Stage 3 final acceptance | PASS / `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90` / Run #253 |
| Stage 4 | ENTRY ELIGIBLE / NOT STARTED |

## Exact production chain

- Stage 3 entry: `87198a5a917ab6b3efc277762016a5f5b0dd3aab` / Run #228.
- Core: `29b4244eeaeb2239ff959e6dd6d4128311f005fa` / Run #232.
- Authorized execution: `d834ed42e3f553308aef7f6adb7e8cb873593f0b` / Run #235.
- Purpose grants: `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238.
- Runner runtime: `5e682f1933a7167fc142689306352fe53b4b1833` / Run #246.
- Evidence freeze: `b15d91ff3fbf21b47a0e484b5a337c4611a17355` / PR #101 / exact-head Run #250 / post-merge Run #251.
- Final acceptance: `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0` / PR #102 / exact-head Run #252 / post-merge Run #253.

## Immutable evidence retained

Canonical Stage 1 expanded-v2 digests: catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Historical C15/C16 remain `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` / `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`. Historical Stage 2 PDF deferrals are not rewritten.

## Corpus/purpose boundary

Beethoven and Barley execute only under the exact Stage 3 purpose overlay. Chopin remains held-out evaluation only. Exact source identity was verified before execution; source PDFs and detailed PNG/manifests/metrics remain outside ordinary Git.

The accepted real Stage 3 batch does not contain a real hybrid page and does not exercise all malformed/resource-limit fallback paths. Those remain deterministic contract/test coverage. The batch does not establish representativeness, absence of bias, OMR improvement, restoration effectiveness or musical correctness.

## Stage 4 boundary

Stage 4 is now eligible to receive a separate entry/start decision. It has **not started**. No Stage 3 result is interpreted as calibration authorization, training authorization or publication authorization. Stage 4 must independently define real-data calibration and anti-leakage gates.

## Sensitive path

The separate `Fly Me to the Moon` phone-photo path remains outside the accepted Stage 3 batch and independently blocked pending real high-assurance-vault verification.