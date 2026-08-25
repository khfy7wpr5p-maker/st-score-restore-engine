# Stage 1 Exit Evidence

**Status:** Incomplete / Stage 1 remains open  
**Stage:** Stage 1C / post-C14 corpus realization  
**Parent issue:** #32  
**Active substage:** #47  
**Real external artifacts admitted by current C14 evidence:** 2  
**Artifact bytes stored in ordinary Git:** 0  
**Stage 2 entry:** BLOCKED

## 1. Purpose

This record assembles the current Stage 1 exit evidence without treating governance mechanisms,
minimum structural corpus readiness, or two admitted items as proof that the evaluation corpus is
already sufficient for final Stage 1 exit.

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
| First independently authorized held-out artifact | PASS ON C14 EXACT-HEAD EVIDENCE | C14 exact-head CI requires held-out C11 `decision=eligible` |
| Per-item auditable rights and provenance | PASS FOR 2 ITEMS | C12 + C14 exact-artifact public-domain evidence |
| Per-item acceptable privacy review | PASS FOR 2 ITEMS | Both items classify privacy as `none` |
| Per-item approved dataset review | PASS FOR 2 ITEMS | Both catalog items are approved |
| Per-item current allowed-purpose authorization | PASS FOR 2 ITEMS | Development grants only `quality_evaluation`; held-out grants only `held_out_evaluation` |
| Immutable artifact digest/size and opaque custody binding | PASS FOR 2 ITEMS | Exact digest/size plus opaque managed-standard bindings |
| Development split realization | PASS | One authorized development item exists |
| Held-out split realization | PASS ON C14 EXACT-HEAD EVIDENCE | One independently authorized held-out item exists |
| Source-family split realization without leakage | PASS ON C14 EXACT-HEAD EVIDENCE | C13 reports distinct development/held-out source families and no digest leakage |
| Minimum structural corpus readiness | PASS ON C14 EXACT-HEAD EVIDENCE | C13 reports `development=1`, `held_out=1`, `state=ready`, no reason codes |
| Held-out split freeze and digest-bound snapshot | BLOCKED / NOT YET EXECUTED | Structural readiness does not itself create or approve a snapshot |
| Realized coverage measurement | PARTIAL / INSUFFICIENT | Two real items exist; empirical coverage sufficiency has not been established |
| Empirical known-bias assessment | INCOMPLETE | Requires realized corpus coverage/gap review and dataset-card evidence |
| Revocation/deletion behavior applicable to realized items | MECHANISM PASS / ITEM EXERCISE PENDING | Stage 1B mechanism accepted; neither realized item has required revocation |
| Repository remains metadata-only for dataset artifacts | PASS | No real document artifact byte is stored in ordinary Git |
| Training permission inferred from teacher approval | PASS / PROHIBITED INVARIANT | Governance contract rejects this inference |
| Stage 1 final exit | FAIL / INCOMPLETE | Snapshot freeze, empirical coverage/gap/bias evidence and final acceptance remain incomplete |
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
- C14 exact-head evidence for one independently admitted held-out artifact and a two-item,
  source-family-isolated development/held-out corpus.

## 4. C14 structural-ready boundary

C14 does not weaken C13. It changes the factual input to C13 by adding an independently
admitted held-out item with a distinct source family and distinct artifact digest.

On the C14 exact head, CI requires:

- the existing C12 development admission to remain `eligible`;
- the C14 held-out admission to return `eligible`;
- the combined catalog to return exactly `development=1`, `held_out=1`, `state=ready`, with
  no reason codes;
- the full unit suite and compile checks to pass on Python 3.11 and 3.12.

This `ready` result is a minimum structural prerequisite only. It does not freeze a snapshot,
measure empirical coverage, establish bias sufficiency, or authorize Stage 2.

## 5. Evidence still required for Stage 1 completion

Stage 1 cannot close until direct evidence supports at least:

1. a digest-bound approved development/held-out snapshot with held-out freeze;
2. immutable snapshot membership and split assignments tied to the realized catalog;
3. empirical coverage/gap analysis over the realized corpus;
4. explicit known-bias and limitation documentation;
5. a completed dataset card consistent with the frozen snapshot and coverage evidence;
6. repository validation showing ordinary Git remains free of real dataset artifact bytes;
7. final Stage 1 exit evidence acceptance.

Additional corpus expansion may be required if the empirical coverage/gap analysis shows the
current two-item corpus is insufficient for the approved Stage 1 evaluation scope. Structural
readiness alone must not be treated as coverage sufficiency.

## 6. Current blocker

The first blocking dependency is now **digest-addressed development/held-out snapshot freeze**.
After a valid freeze exists, empirical coverage/gap/bias work must determine whether the realized
corpus is actually sufficient. No coverage PASS, bias PASS, dataset-card completion, or Stage 1
exit PASS may be fabricated merely to advance the roadmap.

## 7. Stage 2 prohibition

Stage 2 Complete Quality Analysis and OpenCV setup/run/completion remain blocked while this
matrix is incomplete. This record does not authorize quality calibration, safety calibration,
DocRes, comparator, selector, ST Image AI, model training or downstream integration.
