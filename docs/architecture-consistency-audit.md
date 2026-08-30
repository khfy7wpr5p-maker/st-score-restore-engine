# Architecture Consistency Audit — 2026-08-30

**Audit scope:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Fresh-read main:** `e211893324d47e2084f873c14f5737968cb55cc2`  
**Active Stage:** Stage 1C / C17 corpus expansion  
**Stage 1 exit:** BLOCKED  
**Stage 2 entry:** BLOCKED

## 1. Purpose

This record reconciles architecture, implementation contracts, Stage 1 evidence, repository governance, and CI enforcement after C17C / PR #72. It is a maintenance audit, not a new roadmap authorization. Accepted ADR decisions remain unchanged.

## 2. Compatibility / inconsistency matrix

| Area | Result | Evidence / interpretation |
|---|---|---|
| Package vs OpenAPI version | PASS | `pyproject.toml` and `api/openapi.v1.json` are both `0.5.0`. |
| Python compatibility | PASS BY CONTRACT | Runtime is `>=3.11,<3.13`; CI matrix is 3.11 and 3.12. Fresh CI execution is separately blocked below. |
| ADR 0015 processing order | PASS BY IMPLEMENTATION REGRESSION | `tests/test_restoration_pipeline_architecture.py` requires safety validation before comparator use, excludes rejected variants, and keeps the immutable original selectable. |
| C17A notation taxonomy | PASS | Exact catalog classifies the artifact only as `combined_staff_tab`; standalone `guitar_tab` remains open. |
| C17C exact-byte evidence | PASS | PR #72 merged metadata-v2 for the existing held-out artifact, exact SHA-256 `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`, degradation `noise` only. |
| C15/C16 historical immutability | PASS | Historical snapshot remains `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`; C16 remains `insufficient`, 2 real items / 12 pages. |
| Stage boundary | PASS | Stage 1 remains active/not exited; Stage 2 remains blocked. |
| Ordinary Git artifact custody | PASS | Stage 1 evidence remains metadata-only; no PDF/JPG/JPEG/PNG/TIFF corpus bytes are permitted under `evidence/stage1c`. |
| Architecture/status documentation | FAIL ON CURRENT MAIN → REMEDIATED IN PR #73 | README, roadmap, technical specification, Stage 1C status and exit evidence contained stale C17C-pending wording after PR #72. This PR reconciles them. |
| Parent Stage 1 issue state | FAIL → GOVERNANCE CORRECTION REQUIRED | Issue #32 still describes Stage 1 as planned/blocked even though Stage 1A/B are complete and Stage 1C is active. Its body must be reconciled without changing the Stage 1 exit gate. |
| Server-side review enforcement | WARNING | Active ruleset requires PR plus `validate (3.11)` / `validate (3.12)`, but requires zero approving reviews and does not require review-thread resolution. Manual repository governance is therefore stronger than server-side enforcement. |
| Fresh exact-head CI | BLOCKED | Post-merge Run #156 and PR #73 Run #157 completed as `cancelled` after extended queueing and allocated zero jobs. They are not test failures, but they provide no executable CI evidence. |

## 3. Ordered remediation plan

1. **Reconcile repository-visible current state.** Update README, Stage 1C current status, Stage 1 exit evidence, roadmap and technical specification so C17C is consistently recorded as merged and only C17B/C17D remain exact-byte admission targets.
2. **Add deterministic drift detection.** `tools/validate_architecture_consistency.py` must verify package/API version parity, roadmap/spec stage-sequence parity, C17A taxonomy, C17C exact-byte metadata-v2, immutable historical C15/C16 evidence, Stage 2 blocking, metadata-only corpus evidence, and CI wiring.
3. **Wire the consistency test into CI.** Repository validation must execute the new checker on Python 3.11 and 3.12 before Stage 1 admission checks.
4. **Correct parent Issue #32.** Replace obsolete pre-entry wording with the current Stage 1A/B/C state while preserving its parent-scope and exit requirements.
5. **Preserve exact-head merge discipline.** A `queued`, `cancelled`, or zero-job workflow run is not verification evidence. PR #73 remains Draft until a new exact-head run actually executes both required matrix jobs successfully and review/thread reconciliation is complete.
6. **Harden GitHub ruleset when capability is available.** Raise server-side enforcement toward documented governance: approving review requirement and review-thread resolution. Until then, manual gates remain authoritative.
7. **Continue Stage 1 corpus expansion only after governance consistency is restored.** C17B standalone guitar TAB and C17D admissible real phone-photo path remain fail-closed until exact bytes and all rights/privacy/custody/admission evidence pass.
8. **Create a new aggregate snapshot only after sufficient C17 admission.** Never mutate C15/C16 and never double-count C17C v1/v2 metadata for the same exact artifact.

## 4. CI interpretation rule

A GitHub Actions run counts as fresh evidence only when the exact PR/main head is unchanged and the required `validate (3.11)` and `validate (3.12)` jobs actually execute and succeed. Cancellation before job allocation is an infrastructure/execution-state blocker, not a product-test failure and not a success.

## 5. Ruleset enforcement gap

The active `main-safety-gate` ruleset is a minimum server-side gate, not the complete project governance contract. Until the ruleset is hardened, merge decisions must additionally enforce:

- Draft → Ready as a separate transition;
- fresh base/head verification;
- exact-head CI success;
- review reconciliation;
- no unresolved blocking review threads/findings;
- exact verified head at merge time;
- Stage/custody/rights/privacy boundaries.

## 6. Stage 1 evidence interpretation

C17C improves future degradation coverage evidence but does not retroactively change C16. A future expanded snapshot must select the C17C v2 representation of IMSLP82860 instead of v1 and must not count both metadata versions as separate artifacts or source families.

C17B remains the standalone Guitar TAB gap. C17D remains the genuine phone-photo gap. The user-provided phone photo remains a separate `sensitive_custody -> high_assurance_vault` path and is not an open-corpus substitute while real vault verification is absent.

## 7. Safety statement

This audit changes no accepted ADR, does not add real document bytes to Git, does not grant training/calibration/publication permission, does not authorize Stage 2, and does not activate DocRes, the future multi-engine comparator, Selector, ST Restore image model, production deployment, OMR, or MusicXML integration.
