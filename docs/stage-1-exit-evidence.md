# Stage 1 Exit Evidence

**Status:** Incomplete / Stage 1 remains open  
**Stage:** Stage 1C / C15 digest-addressed snapshot freeze candidate  
**Parent issue:** #32  
**Active substage:** #47  
**Real external artifacts admitted:** 2  
**Artifact bytes stored in ordinary Git:** 0  
**Stage 2 entry:** BLOCKED

## 1. Purpose

This record assembles the current Stage 1 exit evidence without treating governance mechanisms,
minimum structural corpus readiness, a frozen two-item snapshot, or a successful CI run as proof
that empirical evaluation coverage is sufficient for final Stage 1 exit.

A gate may be marked `PASS` only when direct evidence exists. Unknown, future, blocked or
not-yet-executed conditions remain non-passing.

## 2. Current exit matrix

| Gate | Current result | Evidence boundary |
|---|---|---|
| Stage 1A metadata governance accepted | PASS | Accepted Stage 1A contract and validators on `main` |
| Stage 1B custody/operations contract accepted | PASS | Issue #36 closed with accepted reference-drill/security evidence |
| Stage 1C start authorization | PASS | Issue #47 records explicit Stage 1C start approval |
| G4 purpose/storage policy binding | PASS | `quality_evaluation` + `held_out_evaluation`; `stage1_offline`; ADR 0016 risk-tiered storage |
| C5-C11 governance/storage/admission mechanisms | PASS | Accepted merged contracts and CI evidence |
| First authorized real development artifact | PASS | C12 / PR #63 admitted one public-domain scanned PDF outside ordinary Git |
| First independently authorized held-out artifact | PASS | C14 / PR #65 merged the independently admitted held-out item |
| Per-item auditable rights and provenance | PASS FOR 2 ITEMS | C12 + C14 exact-artifact public-domain evidence |
| Per-item acceptable privacy review | PASS FOR 2 ITEMS | Both items classify privacy as `none` |
| Per-item approved dataset review | PASS FOR 2 ITEMS | Both catalog items are approved |
| Per-item current allowed-purpose authorization | PASS FOR 2 ITEMS | Development grants only `quality_evaluation`; held-out grants only `held_out_evaluation` |
| Immutable artifact digest/size and opaque custody binding | PASS FOR 2 ITEMS | Exact digest/size plus opaque managed-standard bindings |
| Development split realization | PASS | One authorized development item exists |
| Held-out split realization | PASS | One independently authorized held-out item exists |
| Source-family split realization without leakage | PASS | C13/C14 evidence demonstrates distinct source families and artifact digests |
| Minimum structural corpus readiness | PASS | C14 merged with `development=1`, `held_out=1`, `state=ready`, no reason codes |
| Held-out split freeze and digest-bound snapshot | PASS ON C15 EXACT-HEAD EVIDENCE | PR #66 exact-head CI validates the committed deterministic snapshot with `heldOutFrozen=true` |
| Snapshot catalog binding | PASS ON C15 EXACT-HEAD EVIDENCE | Catalog canonical SHA-256 `059c40b619d3c7815f14377cc8b26fce9a6b0522f2419f481bd93b15ed60e937` |
| Snapshot item metadata bindings | PASS ON C15 EXACT-HEAD EVIDENCE | Development `c1f06342ba4932e2a087e76d424fbb253d63fa19bf7dc7f07196fbe99026b23f`; held-out `b8aab0a86924043c038c44f3f7346199628ae101e520c7f023d934485db3e58b` |
| Snapshot canonical digest | PASS ON C15 EXACT-HEAD EVIDENCE | `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` |
| Stage 1 training remains disabled | PASS | Frozen snapshot requires `trainingUseActivated=false` |
| Realized coverage measurement | PARTIAL / INSUFFICIENT | Snapshot records 2 real items, 0 synthetic items and explicit tiny-corpus gap codes |
| Empirical known-bias assessment | INCOMPLETE | Requires dedicated frozen-snapshot coverage/gap/bias analysis |
| Stage 1 dataset card | INCOMPLETE | Must be reconciled to the frozen snapshot and empirical gap/bias evidence |
| Revocation/deletion behavior applicable to realized items | MECHANISM PASS / ITEM EXERCISE PENDING | Stage 1B mechanism accepted; neither realized item has required revocation |
| Repository remains metadata-only for dataset artifacts | PASS | No real document artifact byte is stored in ordinary Git |
| Training permission inferred from teacher approval | PASS / PROHIBITED INVARIANT | Governance contract rejects this inference |
| Stage 1 final exit | FAIL / INCOMPLETE | Empirical coverage/gap/bias evidence, dataset card and final acceptance remain incomplete |
| Stage 2 entry | BLOCKED | Stage 1 final exit has not passed |

## 3. Evidence already accepted or demonstrated

The following foundations are accepted or directly demonstrated by the current chain:

- Stage 1A purpose-bound dataset governance;
- Stage 1B provider-neutral custody/operations contract and security reference evidence;
- Stage 1C authorization and ADR 0016 risk-tiered storage architecture;
- C5-C10 storage/eligibility/profile verification chain;
- C11 deterministic artifact admission gate;
- C12 first real authorized development artifact with exact rights, digest, storage and purpose evidence;
- C13 deterministic structural corpus readiness gate;
- C14 merged independently admitted held-out artifact and two-item source-family-isolated corpus;
- C15 exact-head snapshot candidate binding the realized catalog and both item metadata records by canonical SHA-256.

## 4. C15 snapshot-freeze boundary

The C15 committed snapshot candidate is `evidence/stage1c/corpus/snapshot.freeze.v1.json`.
It is validated through the public Stage 1 snapshot boundary and then compared byte-for-byte at
canonical-JSON level against deterministic builder output.

C15 requires:

- exactly one development and one held-out item;
- distinct source families and artifact digests inherited from C13/C14 validation;
- catalog SHA-256 `059c40b619d3c7815f14377cc8b26fce9a6b0522f2419f481bd93b15ed60e937`;
- development item metadata SHA-256 `c1f06342ba4932e2a087e76d424fbb253d63fa19bf7dc7f07196fbe99026b23f`;
- held-out item metadata SHA-256 `b8aab0a86924043c038c44f3f7346199628ae101e520c7f023d934485db3e58b`;
- snapshot SHA-256 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`;
- `heldOutFrozen=true`;
- `trainingUseActivated=false`;
- zero revoked item IDs at snapshot time;
- explicit gap codes `coverage.single-item-per-split` and `coverage.two-item-corpus`.

Run #136 on PR #66 exact head validates this candidate on Python 3.11 and 3.12. Python 3.12
records 416 tests PASS and compile PASS. This is technical exact-head evidence only until C15 is
accepted and merged through the repository's separate Ready-for-review and merge gates.

## 5. Evidence still required for Stage 1 completion

Stage 1 cannot close until direct evidence supports at least:

1. empirical coverage/gap analysis tied to the frozen snapshot;
2. explicit known-bias and limitation documentation;
3. a completed Stage 1 dataset card consistent with the frozen snapshot and empirical evidence;
4. a decision on whether the current two-item corpus is sufficient for the approved Stage 1 evaluation scope;
5. additional authorized corpus expansion if that empirical decision is insufficient;
6. repository validation showing ordinary Git remains free of real dataset artifact bytes;
7. final Stage 1 exit evidence acceptance.

The C15 snapshot intentionally records tiny-corpus gaps. A frozen snapshot is an integrity result,
not a coverage-sufficiency result.

## 6. Current blocker

The first blocking dependency after C15 is **empirical frozen-snapshot coverage/gap/bias analysis
and dataset-card reconciliation**. The current corpus contains only one development item and one
held-out item. No coverage PASS, bias PASS, dataset-card completion, or Stage 1 exit PASS may be
fabricated merely to advance the roadmap.

If empirical analysis finds the corpus insufficient, Stage 1 must remain open while additional
independently authorized artifacts are admitted and a new versioned snapshot is deliberately
created. The frozen held-out membership must not be silently mutated.

## 7. Stage 2 prohibition

Stage 2 Complete Quality Analysis and OpenCV setup/run/completion remain blocked while this
matrix is incomplete. This record does not authorize quality calibration, safety calibration,
DocRes, comparator, selector, ST Image AI, model training or downstream integration.
