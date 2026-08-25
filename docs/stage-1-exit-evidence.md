# Stage 1 Exit Evidence

**Status:** Incomplete / corpus expansion required  
**Stage:** Stage 1C / C16 frozen-snapshot coverage-bias evaluation  
**Parent issue:** #32  
**Active substage:** #47  
**Real external artifacts admitted:** 2  
**Artifact bytes stored in ordinary Git:** 0  
**Stage 2 entry:** BLOCKED

## 1. Purpose

This record assembles the current Stage 1 exit evidence. Governance, artifact admission, structural readiness, and the C15 digest-addressed snapshot freeze are complete on `main`; C16 now measures the frozen corpus from validated metadata and records that the current corpus is insufficient for Stage 1 exit.

A gate is marked `PASS` only when direct evidence exists. A measured insufficiency is not converted into a pass merely to advance the roadmap.

## 2. Current exit matrix

| Gate | Current result | Evidence boundary |
|---|---|---|
| Stage 1A metadata governance accepted | PASS | Accepted Stage 1A contract and validators |
| Stage 1B custody/operations contract accepted | PASS | Issue #36 closed with accepted security/reference-drill evidence |
| Stage 1C start authorization | PASS | Issue #47 |
| G4 purpose/storage policy binding | PASS | `quality_evaluation` + `held_out_evaluation`; `stage1_offline`; ADR 0016 |
| C5-C11 governance/storage/admission mechanisms | PASS | Merged contracts and CI evidence |
| Authorized development artifact | PASS | C12 / PR #63 |
| Independently authorized held-out artifact | PASS | C14 / PR #65 |
| Per-item rights, privacy, dataset review and purpose authorization | PASS FOR 2 ITEMS | C12 + C14 item evidence |
| Immutable artifact digest/size and opaque custody binding | PASS FOR 2 ITEMS | Managed-standard bindings |
| Source-family isolated development/held-out realization | PASS | C13/C14 |
| Minimum structural corpus readiness | PASS | `development=1`, `held_out=1`, `state=ready` |
| Digest-addressed snapshot freeze | PASS | C15 / PR #66 merged |
| Snapshot canonical digest | PASS | `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` |
| Held-out freeze | PASS | `heldOutFrozen=true` |
| Stage 1 training remains disabled | PASS | `trainingUseActivated=false` |
| Metadata-derived coverage measurement | PASS ON C16 CANDIDATE | Deterministic report over validated catalog + frozen snapshot |
| Coverage sufficiency | FAIL / INSUFFICIENT | Seven confirmed gap codes; corpus expansion required |
| Known concentration/limitation register | PASS ON C16 CANDIDATE | Source, notation, capture, degradation and held-out limits documented |
| Stage 1 dataset card reconciliation | PASS ON C16 CANDIDATE | Card updated to realized frozen corpus and limitations |
| Repository remains metadata-only for real dataset artifacts | PASS | 0 real score bytes in ordinary Git |
| Revocation/deletion mechanism | PASS | Stage 1B mechanism accepted; no realized item currently requires revocation |
| Stage 1 final exit | FAIL / INCOMPLETE | Current corpus measured insufficient; expansion and new versioned snapshot required |
| Stage 2 entry | BLOCKED | Stage 1 final exit has not passed |

## 3. Accepted frozen snapshot

C15 / PR #66 merged the deterministic frozen snapshot with:

- catalog SHA-256 `059c40b619d3c7815f14377cc8b26fce9a6b0522f2419f481bd93b15ed60e937`;
- development item metadata SHA-256 `c1f06342ba4932e2a087e76d424fbb253d63fa19bf7dc7f07196fbe99026b23f`;
- held-out item metadata SHA-256 `b8aab0a86924043c038c44f3f7346199628ae101e520c7f023d934485db3e58b`;
- snapshot SHA-256 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`;
- `heldOutFrozen=true`;
- `trainingUseActivated=false`;
- zero revoked item IDs.

The freeze is an integrity result, not a representativeness result.

## 4. C16 measured result

`evidence/stage1c/corpus/coverage-bias-report.v1.json` is deterministically derived from the validated catalog and the exact C15 snapshot.

Observed corpus:

- 2 real items / 12 pages;
- development: 1 item / 4 pages / 1 source family;
- held out: 1 item / 8 pages / 1 source family;
- staff notation: 2 items;
- guitar TAB: 0;
- combined staff/TAB: 0;
- scanned PDF: 2;
- phone photo: 0;
- items with any non-`none` degradation metadata: 0.

C16 report SHA-256: `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

Deterministic sufficiency result: **`insufficient`**.

Confirmed gap codes:

- `coverage.missing-combined-staff-tab`;
- `coverage.missing-degraded-source`;
- `coverage.missing-guitar-tab`;
- `coverage.missing-phone-photo`;
- `coverage.single-item-development`;
- `coverage.single-item-held-out`;
- `coverage.two-item-corpus`.

Run #139 demonstrated this decision together with 422 tests PASS and compile PASS before this exit-record update. The final C16 exact head must independently repeat those gates before Ready-for-review.

## 5. Bias and limitation interpretation

The current corpus shows observable concentration:

- 2/2 items are staff-only;
- 2/2 are scanned PDFs;
- 2/2 declare only `none` degradation;
- 2/2 use public-domain source basis;
- held-out contains one source family.

Source-family leakage is controlled by distinct frozen source-family and digest bindings. However, absence of bias, representativeness, restoration effectiveness, OMR improvement, and musical correctness are not established.

## 6. Required next work

Stage 1 cannot close on the current frozen corpus. Corpus expansion must deliberately add independently authorized material addressing at least:

1. guitar TAB;
2. combined staff/TAB;
3. phone-captured sheet music;
4. non-clean/degraded material;
5. broader development and held-out source-family diversity.

Each new item must pass the existing rights/privacy/review/purpose/custody/admission chain. The C15 snapshot must not be mutated. Expansion requires a new versioned snapshot and a new deterministic coverage evaluation.

## 7. Stage 2 prohibition

Stage 2 Complete Quality Analysis / OpenCV setup-run-completion remains blocked until an expanded corpus satisfies Stage 1 exit and that exit is explicitly accepted. C16 does not authorize training, calibration, publication, demonstration, synthetic derivation, restoration execution, OMR evaluation, or downstream integrations.
