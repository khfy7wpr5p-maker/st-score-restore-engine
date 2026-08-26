# Stage 1 Exit Evidence

**Status:** Incomplete — C17 corpus expansion required  
**Stage:** Stage 1C / C17 active  
**Parent issue:** #32  
**Active substage:** #47  
**Historical frozen baseline:** C15/C16  
**Historical realized artifacts:** 2  
**Historical realized pages:** 12  
**Artifact bytes stored in ordinary Git:** 0  
**Latest merged expansion slice:** C17A / PR #68  
**Current continuation:** C17B/C17C/C17D exact-byte ingestion pending  
**Stage 1 final exit:** BLOCKED  
**Stage 2 entry:** BLOCKED

## 1. Purpose

This record assembles the current Stage 1 exit evidence without rewriting historical C15/C16 results. Governance, storage-profile machinery, artifact admission, structural readiness, and the C15 digest-addressed snapshot freeze are complete on `main`. C16 deterministically measured the exact frozen snapshot and concluded that the corpus is insufficient for Stage 1 exit. C17 is the active corpus-expansion phase.

A gate is marked `PASS` only when direct evidence exists. A measured insufficiency is never converted into a pass merely to advance the roadmap.

## 2. Current exit matrix

| Gate | Current result | Evidence boundary |
|---|---|---|
| Stage 1A metadata governance accepted | PASS | Accepted Stage 1A contract and validators |
| Stage 1B custody/operations contract accepted | PASS | Issue #36 closed with accepted security/reference-drill evidence |
| Stage 1C start authorization | PASS | Issue #47 |
| ADR 0016 risk-tiered custody architecture | PASS | Accepted architecture and C6 machine-readable implementation |
| Catalog `1.3.0` storage-profile migration | PASS | C6 / PR #57 |
| Deterministic eligibility resolution | PASS | C7 / PR #58 |
| Managed-standard verification contract | PASS | C8 / PR #59 |
| Managed-restricted verification contract | PASS | C9 / PR #60 |
| High-assurance compatibility contract | PASS STRUCTURALLY | C10 / PR #61; does not prove a real vault |
| Deterministic artifact admission gate | PASS | C11 / PR #62 |
| Authorized development artifact | PASS | C12 / PR #63 |
| Independently authorized held-out artifact | PASS | C14 / PR #65 |
| Per-item rights, privacy, dataset review and purpose authorization | PASS FOR HISTORICAL 2 ITEMS | C12 + C14 evidence |
| Source-family-isolated development/held-out realization | PASS | C13/C14 |
| Minimum structural corpus readiness | PASS | C13 |
| Digest-addressed historical snapshot freeze | PASS | C15 / PR #66 |
| Historical snapshot canonical digest | PASS | `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` |
| Held-out freeze | PASS | `heldOutFrozen=true` |
| Stage 1 training remains disabled | PASS | `trainingUseActivated=false` |
| Metadata-derived C16 coverage measurement | PASS | C16 / PR #67 merged |
| Historical C16 coverage sufficiency | FAIL / `insufficient` | Seven confirmed gap codes |
| Known concentration/limitation register | PASS | C16 merged evidence |
| Stage 1 dataset card reconciliation to C16 | PASS | Current frozen-baseline dataset card |
| Repository remains metadata-only for real dataset bytes | PASS | 0 real score/TAB/PDF/image corpus bytes in ordinary Git |
| Revocation/deletion mechanism | PASS | Stage 1B mechanism accepted; item-specific rules remain binding |
| C17A combined staff+TAB admission | PASS / MERGED | PR #68 exact reviewed head `3424cc22d686b1d08ec0ff1c6be1d372b1ff4146` |
| C17B/C17C/C17D source qualification | QUALIFIED / NOT ADMITTED | Exact preferred public-source bytes not yet in authorized custody |
| Stage 1 final exit | FAIL / INCOMPLETE | Expanded corpus + new snapshot + new coverage decision required |
| Stage 2 entry | BLOCKED | Stage 1 final exit has not passed |

## 3. Accepted historical C15 snapshot

C15 / PR #66 merged the deterministic frozen snapshot with:

- catalog SHA-256 `059c40b619d3c7815f14377cc8b26fce9a6b0522f2419f481bd93b15ed60e937`;
- development item metadata SHA-256 `c1f06342ba4932e2a087e76d424fbb253d63fa19bf7dc7f07196fbe99026b23f`;
- held-out item metadata SHA-256 `b8aab0a86924043c038c44f3f7346199628ae101e520c7f023d934485db3e58b`;
- snapshot SHA-256 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`;
- `heldOutFrozen=true`;
- `trainingUseActivated=false`;
- zero revoked item IDs.

The freeze is an integrity result, not a representativeness result. C17 must not mutate these historical bytes or metadata to make later coverage appear retroactive.

## 4. Accepted historical C16 result

C16 / PR #67 is merged to `main` at merge commit `71e9b1852832f4bd5c2fc312e58546f2ee595cdc`; its exact PR head was `14f305cfc1651781d8b5b0fedad72a4552b1d423`. Repository validation Run #142 succeeded, including Python 3.11/3.12 validation, C15 snapshot checks, deterministic C16 report checks, full tests, and compile.

`evidence/stage1c/corpus/coverage-bias-report.v1.json` is derived from the validated catalog and exact C15 snapshot.

Historical observed corpus:

- 2 real items / 12 pages;
- development: 1 item / 4 pages / 1 source family;
- held out: 1 item / 8 pages / 1 source family;
- staff notation: 2 items;
- standalone guitar TAB: 0;
- combined staff/TAB: 0;
- scanned PDF: 2;
- phone photo: 0;
- items with any non-`none` degradation metadata: 0.

C16 report SHA-256:

`0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`

Deterministic sufficiency result: **`insufficient`**.

Historical gap codes:

- `coverage.missing-combined-staff-tab`;
- `coverage.missing-degraded-source`;
- `coverage.missing-guitar-tab`;
- `coverage.missing-phone-photo`;
- `coverage.single-item-development`;
- `coverage.single-item-held-out`;
- `coverage.two-item-corpus`.

## 5. C17A merged evidence boundary

C17A / PR #68 is merged. Its exact reviewed head was:

`3424cc22d686b1d08ec0ff1c6be1d372b1ff4146`

The merge commit on `main` is:

`010db20a4feb71dd36c9c5378d4d486836c5abc0`

C17A admits one exact Public Domain PNG for `quality_evaluation` under `open_corpus` / `managed_standard` with:

- artifact SHA-256 `36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb`;
- byte size `34636`;
- one page;
- notation taxonomy **only** `combined_staff_tab`;
- canonical item digest `5deed5fac92ff98e10177eb1ff45d742e15863d58235a18af2dedcb4b1880449`;
- no model training, calibration, publication, demonstration, synthetic derivation, or Stage 2 authorization;
- no artifact bytes in ordinary Git.

Codex review correctly identified that the original metadata would have counted a combined staff/TAB layout as standalone guitar TAB. The metadata and regression test were corrected. The review thread was resolved, and Repository validation Run #147 (`32895593925`) succeeded on Python 3.11 and 3.12 for the exact merged head.

C17A does **not** modify the C15 snapshot and therefore does not modify the historical C16 counts or gap list. Its contribution to coverage can only be measured after inclusion in a new versioned expanded snapshot.

## 6. Current C17 continuation

The next independently qualified targets are:

- **C17B:** standalone rights-clean guitar TAB, preferred candidate IMSLP #911664;
- **C17C:** naturally degraded/non-clean real score, preferred candidate Wikimedia `File:Notenblatt-music-vintage-alt.jpg`;
- **C17D:** independently rights-clean genuine phone-photo source with an admissible open-corpus path where exact rights/privacy evidence permits it.

The fresh authorized-custody inventory does not contain the preferred C17B/C17C/C17D public-source exact bytes. Therefore no SHA-256, C11 admission, new snapshot membership, or coverage closure is claimed for those candidates yet.

## 7. Phone-photo and high-assurance boundary

A real user-provided phone photograph remains outside the realized corpus. The current mapping is `sensitive_custody` → `high_assurance_vault`. C10 demonstrates structural compatibility with the legacy C4 high-assurance evidence format, but the current compatibility record explicitly does not prove a real vault or authorize sensitive artifact onboarding.

Therefore a phone-photo gap must remain visible until a genuine independently authorized artifact has a compliant custody path. A synthetic transformation or relabeling cannot satisfy this real-data coverage category.

## 8. PR transition governance

Ready-for-review and merge remain separate objective technical gates. Under the current autonomous authorization recorded in Issue #47, separate per-transition user confirmation is not required while that authorization remains in force.

Fresh base/head verification, exact-head CI, review reconciliation, blocking-thread resolution, and exact-head merge requirements remain mandatory. Head movement invalidates earlier head-specific evidence.

## 9. Bias and limitation interpretation

Historical C16 concentration remains visible until a new snapshot is evaluated:

- 2/2 historical items are staff-only;
- 2/2 are scanned PDFs;
- 2/2 declare only `none` degradation;
- 2/2 use Public Domain source basis;
- held-out contains one source family.

Source-family leakage is controlled by distinct frozen source-family and digest bindings. Absence of bias, representativeness, restoration effectiveness, OMR improvement, and musical correctness are not established.

## 10. Required next work

Stage 1 cannot close on the current historical frozen corpus. C17 must continue independently authorized expansion covering remaining dimensions, especially:

1. standalone guitar TAB;
2. real non-clean/degraded material;
3. genuine phone-captured sheet music with an admissible custody path;
4. broader development source-family diversity;
5. broader held-out source-family diversity.

After sufficient additions:

1. validate all new item-level governance/admission evidence;
2. verify split/source-family/digest isolation;
3. create a **new versioned snapshot** rather than changing C15;
4. run a fresh deterministic coverage/bias evaluation;
5. reconcile the dataset card and this exit record;
6. decide Stage 1 exit only from that new evidence.

## 11. Stage 2 prohibition

Stage 2 Complete Quality Analysis / OpenCV quality-analysis execution remains blocked until expanded-corpus evidence satisfies Stage 1 exit and that exit is accepted. Neither C16 nor C17A authorizes model training, calibration, publication, demonstration, synthetic derivation, Stage 3 PDF work, OMR evaluation, or downstream integrations.
