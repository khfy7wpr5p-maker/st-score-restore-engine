# Architecture Consistency Audit — 2026-09-02

**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Fresh-read production main:** `53ae13d3a1b9bda08c79125674e1b7fca78ee8af`  
**Active PR:** #81 / `stage1c-expanded-snapshot-v2`  
**Stage 1 exit:** BLOCKED  
**Stage 2 entry:** BLOCKED

## 1. Purpose

This audit separates current production truth, immutable historical evidence and in-progress PR state. It changes no accepted ADR and creates no roadmap authorization.

Authority order is: merged `main` + accepted deterministic evidence > stale status prose. An open PR is not production truth. Exact-head CI evidence becomes stale after head movement.

## 2. Fresh-read findings

| Area | Result | Current interpretation |
|---|---|---|
| Production main | PASS | main is `53ae13d3a1b9bda08c79125674e1b7fca78ee8af` |
| C17B standalone guitar TAB | PASS / MERGED | exact Barley artifact admitted; older docs/Issue #47 wording that says pending is stale |
| C17D phone photo | PASS / MERGED | exact deidentified restricted derivative admitted; older pending wording is stale |
| C17C v1/v2 dedup rule | PASS | aggregate must select Chopin v2 and exclude v1; never double-count exact artifact |
| Historical C15/C16 immutability | PASS | v1 catalog, frozen snapshot and C16 report remain historical and unchanged |
| Ordinary Git artifact custody | PASS BY CONTRACT | corpus artifacts remain outside ordinary Git; repository stores metadata/evidence only |
| Active PR #81 | OPEN / DRAFT | in-progress, mergeable; not production truth |
| PR #81 reviews | NONE | no submitted reviews at fresh-read |
| PR #81 review threads | NONE | no unresolved threads at fresh-read |
| Candidate exact-head CI | PASS FOR OLD HEAD | Run #177 passed Python 3.11/3.12 on `e733d19cf5cb64d86f70017118d8d06c6863c304`; any later head invalidates it as merge evidence |
| Expanded-v2 candidate determinism | PASS | Python 3.11/3.12 workflow artifacts were byte-identical for all three generated evidence files |
| Expanded-v2 committed evidence | PENDING | must be added to PR #81 and checked from Git |
| Stage 1 exit | BLOCKED | separate post-merge acceptance still required |
| Stage 2 entry | BLOCKED | no Stage 2 work before final Stage 1 PASS |

## 3. Documentation drift found

Fresh-read identified stale current-state wording in:

- `README.md`;
- `docs/roadmap.md`;
- `docs/technical-specification.md`;
- `docs/stage-1c-current-status.md`;
- `docs/stage-1-exit-evidence.md`;
- `docs/stage-1-dataset-card.md`;
- `docs/stage-1-coverage-and-bias-register.md`;
- this audit;
- Issue #47.

The primary drift was the claim that C17B/C17D were still unadmitted and that only C17A/C17C were merged. Current main disproves that claim.

Historical C15/C16 evidence documents are deliberately not rewritten to make current coverage retroactive.

## 4. Expanded-v2 candidate truth

PR #81's deterministic builder selects exactly five real items and zero synthetic items:

1. Beethoven baseline v1;
2. combined staff+TAB technical exercise v1;
3. Barley standalone guitar TAB v1;
4. Chopin metadata v2;
5. Nearer My God to Thee deidentified phone-photo v1.

Candidate structure:

- development: 3 items / 3 source families;
- held out: 2 items / 2 source families;
- distinct source families across splits;
- distinct exact artifact SHA-256 values;
- Chopin v1 excluded;
- six explicit coverage targets all `covered`;
- historical seven C16 gap codes absent.

The candidate report nevertheless remains `review_required`, with `stage1ExitSupported=false` and `stage2EntrySupported=false`. This is the intended fail-closed boundary.

## 5. Required PR #81 finalization sequence

1. commit canonical v2 catalog/snapshot/report without changing historical v1 evidence;
2. replace candidate-only workflow generation with committed-evidence `--check`;
3. add focused regression tests for exact membership, split/source-family isolation, digest uniqueness, C17C dedup, historical immutability and zero artifact bytes in ordinary Git;
4. update repository-visible current-state documentation and the canonical live handoff;
5. fresh-read base/head;
6. obtain successful exact-head `validate (3.11)` and `validate (3.12)`;
7. reconcile reviews and review threads;
8. Draft -> Ready only if gates are clean;
9. merge exact verified head only if gates remain clean;
10. verify post-merge main CI.

A queued, cancelled, zero-job or old-head workflow run is not valid final evidence.

## 6. Stage 1 exit boundary

Only after PR #81 merge and successful post-merge CI may Stage 1 final exit be evaluated. A PASS must bind the exact main SHA and accepted v2 catalog/snapshot/report digests plus the successful CI run.

Coverage closure alone does not establish representativeness, absence of bias, restoration effectiveness, OMR improvement or musical correctness.

## 7. Stage 2 prohibition

Stage 2 / OpenCV Complete Quality Analysis remains blocked until the explicit Stage 1 final exit decision is PASS. Stage 1 evidence must not be retroactively rewritten based on later Stage 2 results.
