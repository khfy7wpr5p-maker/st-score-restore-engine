# Stage 1 Exit Evidence

**Status:** Incomplete — C17 corpus expansion required  
**As of:** 2026-08-30  
**Stage:** Stage 1C / C17 active  
**Parent issue:** #32  
**Active substage:** #47  
**Historical frozen baseline:** C15/C16  
**Historical realized artifacts:** 2  
**Historical realized pages:** 12  
**Artifact bytes stored in ordinary Git:** 0  
**Latest merged expansion slice:** C17C / PR #72  
**Current continuation:** C17B standalone guitar TAB and C17D admissible phone-photo path; new aggregate snapshot not yet created  
**Stage 1 final exit:** BLOCKED  
**Stage 2 entry:** BLOCKED

## 1. Purpose

This record assembles the current Stage 1 exit evidence without rewriting historical C15/C16 results. Governance, storage-profile machinery, artifact admission, structural readiness, and the C15 digest-addressed snapshot freeze are complete on `main`. C16 deterministically measured the exact frozen snapshot and concluded that the corpus is insufficient for Stage 1 exit. C17 is the active corpus-expansion phase.

A gate is marked `PASS` only when direct evidence exists. A measured insufficiency is never converted into a pass merely to advance the roadmap. A queued, cancelled, or zero-job workflow run is not executable verification evidence.

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
| Stage 1 dataset card reconciliation to C16 | PASS | Historical frozen-baseline dataset card |
| Repository remains metadata-only for real dataset bytes | PASS | 0 real score/TAB/PDF/image corpus bytes in ordinary Git |
| Revocation/deletion mechanism | PASS | Stage 1B mechanism accepted; item-specific rules remain binding |
| C17A combined staff+TAB admission | PASS / MERGED | PR #68 exact reviewed head `3424cc22d686b1d08ec0ff1c6be1d372b1ff4146` |
| C17C exact-byte non-`none` degradation admission | PASS / MERGED | PR #72 exact reviewed head `fe5a280f3574a8a24a477fd10185f4fe6cab6063`; `noise` only |
| C17B standalone guitar TAB | QUALIFIED / NOT ADMITTED | Exact preferred source bytes absent from authorized custody |
| C17D admissible phone-photo path | QUALIFIED / NOT ADMITTED | Exact preferred source bytes absent; privacy review mandatory |
| New aggregate snapshot including C17 expansions | NOT CREATED | Historical C15 remains immutable |
| Architecture consistency guard | ADDED IN PR #73 / CI PENDING | Repository-local deterministic cross-document/evidence checker |
| PR #72 post-merge Run #156 | NO EXECUTABLE EVIDENCE | Completed `cancelled`; zero jobs allocated |
| PR #73 prior Run #157 | NO EXECUTABLE EVIDENCE | Completed `cancelled`; zero jobs allocated |
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

The accepted review correction prevented a combined staff/TAB layout from being counted as standalone guitar TAB. The metadata and regression test were corrected and Repository validation Run #147 (`32895593925`) succeeded on Python 3.11 and 3.12 for the exact reviewed head.

C17A does **not** modify the C15 snapshot and therefore does not modify the historical C16 counts or gap list. Its contribution to coverage can only be measured after inclusion in a new versioned expanded snapshot.

## 6. C17C merged evidence boundary

C17C / PR #72 is merged. Its exact reviewed head was:

`fe5a280f3574a8a24a477fd10185f4fe6cab6063`

The merge commit on `main` is:

`e211893324d47e2084f873c14f5737968cb55cc2`

C17C re-used the already-authorized held-out IMSLP82860 artifact rather than ingesting a new public-source file. The exact custody PDF was re-fetched and all eight pages were re-inspected. The exact artifact identity remained:

- artifact SHA-256 `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`;
- byte size `1114479`;
- page count 8.

Direct exact-byte visual evidence supports the conservative degradation label `noise` only. The new metadata representation is:

- dataset item `dataset.item.imslp82860-chopin-op69.v2`;
- same source family as v1;
- same held-out split;
- same rights basis and managed-standard custody binding;
- only `held_out_evaluation` permission granted;
- canonical metadata-v2 item SHA-256 `6a75bd7d8348c6ba6e47a4bdbc16a1fc9a3f3ec23fb79a36ad7c123608d3ff36`.

Independent C11 admission for v2 passed in Repository validation Run #155 (`32983542768`) on Python 3.11 and 3.12 for the exact PR head.

Historical v1 metadata, historical corpus catalog v1, C15 and C16 remain immutable. A later aggregate snapshot must choose v2 instead of v1 and must not count the two metadata versions as separate artifacts. C17C can satisfy a future non-`none` degradation dimension only when that v2 representation is included in a new versioned snapshot and re-evaluated; it does not retroactively alter the historical C16 report.

## 7. Current C17 continuation

The remaining independently qualified targets are:

- **C17B:** standalone rights-clean guitar TAB, preferred candidate IMSLP #911664;
- **C17D:** independently rights-clean genuine phone-photo source with an admissible open-corpus path where exact rights/privacy evidence permits it.

The authorized Stage 1 workspace does not contain the preferred C17B or C17D public-source exact bytes. Therefore no SHA-256, C11 admission, new snapshot membership, or coverage closure is claimed for those candidates yet. This remains an exact-byte acquisition/transfer workflow blocker rather than a user-upload requirement.

## 8. Phone-photo and high-assurance boundary

A real user-provided phone photograph remains outside the realized corpus. The current mapping is `sensitive_custody` → `high_assurance_vault`. C10 demonstrates structural compatibility with the legacy C4 high-assurance evidence format, but the current compatibility record explicitly does not prove a real vault or authorize sensitive artifact onboarding.

The preferred public C17D candidate also requires deliberate privacy review because its source metadata exposes device/GPS EXIF. Public availability alone does not imply `privacy:none`.

Therefore a phone-photo gap must remain visible until a genuine independently authorized artifact has a compliant custody path. A synthetic transformation or relabeling cannot satisfy this real-data coverage category.

## 9. Architecture / governance consistency findings

The 2026-08-30 compatibility audit identified two repository-governance drifts in addition to the stale C17C status text corrected by PR #73:

- parent Issue #32 still contained obsolete pre-entry wording and must be reconciled to Stage 1C active status;
- active server-side ruleset `main-safety-gate` enforces PR + Python 3.11/3.12 checks but does not enforce approving-review count or review-thread resolution, so manual governance remains the stronger merge contract.

`tools/validate_architecture_consistency.py` is added to prevent the repository-internal portions of this drift from recurring.

## 10. Exact-head CI boundary

PR #72 pre-merge Run #155 remains valid evidence for the exact reviewed PR head. By contrast:

- post-merge Run #156 for `e211893324d47e2084f873c14f5737968cb55cc2` completed `cancelled` without allocating jobs;
- earlier PR #73 Run #157 for `b03c6eb9a6484501a9a26cf9ce31f9a16806acb6` completed `cancelled` without allocating jobs.

These cancellations do not prove a code/test regression, because no test jobs ran. They also cannot satisfy the fresh exact-head gate. PR #73 must remain Draft until a new head triggers both required jobs and both complete successfully, followed by review/thread reconciliation.

## 11. PR transition governance

Ready-for-review and merge remain separate objective technical gates. Under the active authorization recorded in Issue #47, separate per-transition user confirmation is not required.

Fresh base/head verification, exact-head CI, review reconciliation, blocking-thread resolution, and exact-head merge requirements remain mandatory. Head movement invalidates earlier head-specific evidence.

## 12. Bias and limitation interpretation

Historical C16 concentration remains visible until a new snapshot is evaluated:

- 2/2 historical items are staff-only;
- 2/2 are scanned PDFs;
- 2/2 declare only `none` degradation;
- 2/2 use Public Domain source basis;
- held-out contains one source family.

C17A and C17C provide new evidence outside that historical snapshot, but no updated concentration or sufficiency claim is valid until a new aggregate snapshot is frozen and evaluated. Source-family leakage remains controlled by distinct source-family and digest bindings, and v1/v2 metadata versions of the same exact artifact must never be treated as independent source diversity.

Absence of bias, representativeness, restoration effectiveness, OMR improvement, and musical correctness are not established.

## 13. Required next work

Stage 1 cannot close on the historical frozen corpus. C17 must continue independently authorized expansion covering remaining dimensions, especially:

1. standalone guitar TAB;
2. genuine phone-captured sheet music with an admissible custody path;
3. broader development source-family diversity;
4. broader held-out source-family diversity;
5. additional capture/degradation diversity beyond the single exact held-out scan now classified as `noise`.

After sufficient additions:

1. validate all new item-level governance/admission evidence;
2. verify split/source-family/digest isolation and de-duplicate metadata versions of the same artifact;
3. create a **new versioned snapshot** rather than changing C15;
4. run a fresh deterministic coverage/bias evaluation;
5. reconcile the dataset card and this exit record;
6. decide Stage 1 exit only from that new evidence.

## 14. Stage 2 prohibition

Stage 2 Complete Quality Analysis / OpenCV quality-analysis execution remains blocked until expanded-corpus evidence satisfies Stage 1 exit and that exit is accepted. Neither C16, C17A nor C17C authorizes model training, calibration, publication, demonstration, synthetic derivation, Stage 3 PDF work, OMR evaluation, or downstream integrations.
