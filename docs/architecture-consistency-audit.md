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
| C17B standalone guitar TAB | PASS / MERGED | exact Barley artifact SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e` is admitted on main |
| C17D phone photo | PASS / MERGED | exact deidentified derivative SHA-256 `abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5` is admitted on main |
| C17C v1/v2 dedup rule | PASS | aggregate selects Chopin v2 and excludes v1; the exact artifact is never double-counted |
| Historical C15/C16 immutability | PASS | v1 catalog, frozen snapshot and C16 report remain historical and unchanged |
| Ordinary Git artifact custody | PASS BY CONTRACT | corpus artifacts remain outside ordinary Git; repository stores metadata/evidence only |
| Active PR #81 | OPEN / DRAFT | in-progress; not production truth |
| PR #81 reviews at initial fresh-read | NONE | no submitted reviews |
| PR #81 review threads at initial fresh-read | NONE | no unresolved threads |
| Candidate exact-head CI | PASS FOR OLD HEAD ONLY | Run #177 passed Python 3.11/3.12 on `e733d19cf5cb64d86f70017118d8d06c6863c304`; later head movement invalidates it as merge evidence |
| Expanded-v2 candidate determinism | PASS | Python 3.11/3.12 artifacts were byte-identical for all three generated evidence files |
| Expanded-v2 committed evidence | PASS IN PR | canonical v2 catalog, snapshot and coverage report are committed and CI now checks them with `--check` |
| Focused expanded-v2 regressions | ADDED IN PR | exact membership, split/source-family isolation, digest uniqueness, C17C dedup, historical immutability and zero artifact bytes are covered |
| Repository documentation drift | REMEDIATED IN PR | README, roadmap, technical spec, Stage 1 status/card/register/exit and this audit are reconciled to current main + PR #81 reality |
| Issue #47 body | RECONCILED | issue body now records merged C17B/C17D, PR #81 expanded-v2 acceptance work and the separate sensitive-vault path |
| Run #194 | FAILED / ROOT CAUSE FIXED | both Python jobs stopped at architecture consistency because the dataset card said `Stage 2 authorized: No` rather than the validator's explicit `Stage 2 ... BLOCKED` wording; the card now uses the canonical fail-closed wording without relaxing the rule |
| Stage 1 exit | BLOCKED | separate post-merge acceptance still required |
| Stage 2 entry | BLOCKED | no Stage 2 work before final Stage 1 PASS |

## 3. Historical/current/in-progress separation

Historical C15/C16 evidence is immutable and continues to describe the original two-item corpus and its `insufficient` coverage decision. It is not edited to make C17 coverage appear retroactive.

Current production main contains admitted C17A, C17B, C17C and C17D item-level evidence. PR #81 builds and checks the new aggregate from those admitted inputs. Until PR #81 is merged and post-merge main CI succeeds, the v2 aggregate remains in-progress repository evidence rather than production-main truth.

## 4. Expanded-v2 evidence truth

PR #81's deterministic builder selects exactly five real items and zero synthetic items:

1. Beethoven baseline v1;
2. combined staff+TAB technical exercise v1;
3. Barley standalone guitar TAB v1;
4. Chopin metadata v2;
5. Nearer My God to Thee deidentified phone-photo v1.

Required structure is satisfied by the committed evidence:

- development: 3 items / 3 source families;
- held out: 2 items / 2 source families;
- distinct source families across splits;
- distinct exact artifact SHA-256 values;
- Chopin v1 excluded and v2 selected exactly once;
- six explicit coverage targets all `covered`;
- historical seven C16 gap codes absent.

Canonical v2 digests are:

- catalog: `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot: `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- coverage report: `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

The report nevertheless remains `review_required`, with `stage1ExitSupported=false` and `stage2EntrySupported=false`. This is the intended fail-closed boundary.

## 5. PR #81 finalization sequence

Completed inside the PR:

1. canonical v2 catalog/snapshot/report committed without changing historical v1 evidence;
2. candidate-only workflow generation replaced by committed-evidence `--check`;
3. focused regression tests added;
4. repository-visible architecture/status documents reconciled;
5. Issue #47 current-state wording reconciled;
6. canonical live handoff added at `docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json`;
7. Run #194 wording-only architecture-validator mismatch root cause identified and corrected without weakening any gate.

Still required before merge:

1. fresh-read final base/head;
2. obtain successful exact-head `validate (3.11)` and `validate (3.12)` after the Run #194 root-cause fix;
3. reconcile reviews and review threads at that exact head;
4. Draft -> Ready only if all gates are clean;
5. merge exact verified head only if gates remain clean;
6. verify post-merge main CI.

A queued, cancelled, zero-job or old-head workflow run is not valid final evidence.

## 6. Stage 1 exit boundary

Only after PR #81 merge and successful post-merge CI may Stage 1 final exit be evaluated. A PASS must bind the exact main SHA and accepted v2 catalog/snapshot/report digests plus the successful CI run.

Coverage closure alone does not establish representativeness, absence of bias, restoration effectiveness, OMR improvement or musical correctness.

## 7. Stage 2 prohibition

Stage 2 / OpenCV Complete Quality Analysis remains blocked until the explicit Stage 1 final exit decision is PASS. Stage 1 evidence must not be retroactively rewritten based on later Stage 2 results.
