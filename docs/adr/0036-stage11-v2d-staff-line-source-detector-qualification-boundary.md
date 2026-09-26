# ADR 0036 — Stage 11 V2d staff-line source detector qualification boundary

## Status

Accepted for Stage 11 development/evaluation architecture. This decision does not qualify `staff_line`, authorize restored-image topology comparison, open a fresh independent holdout, authorize production promotion, declare overall Stage 11 PASS, or authorize Stage 12 entry.

## Context

Stage 11 V2c/V2d requires semantic-preservation evidence that is independent of the frozen V2a Restore package. For `staff_line`, the original conservative line-system detector and the later multi-system source detector v1 both preserved important safety properties but did not provide adequate source detection coverage.

The v1.1 source-only iteration is now frozen and scored on the already-spent 20-page development corpus after its source output was frozen. The detector remains a deterministic OpenCV/NumPy specialist and does not load teacher coordinates, restored outputs, held-out data, training state, page identities, or page-specific rules during inference.

Frozen v1.1 development result:

- source identities matched: 20/20;
- staff-present pages covered: 18/18;
- staff-absent specificity: 2/2 = 1.0;
- predicted systems: 114;
- teacher-confirmed systems: 197;
- one-to-one matches at the diagnostic 0.5 staff-spacing tolerance: 91;
- teacher-system recall at that diagnostic: 0.4619289340101523;
- predicted-system precision at that diagnostic: 0.7982456140350878;
- five-line count correctness: 1.0;
- line-order correctness: 1.0;
- local regression tests: 7/7 PASS;
- byte-repeat determinism: verified.

Compared with v1, matched systems increased from 71 to 91, recall increased from 0.3604060913705584 to 0.4619289340101523, page coverage increased from 15/18 to 18/18, and precision remained approximately unchanged. The improvement is material but 106/197 teacher-confirmed systems still remain unmatched at the same diagnostic.

The same development corpus was used to iterate v1.1. Therefore this result is development evidence only and cannot be used to qualify the detector.

## Decision

1. Keep the source detector and qualification decision as separate architectural layers.
2. Preserve `stage11-v2d-staff-multisystem-source.v1` and its evidence as immutable historical anchors.
3. Freeze `stage11-v2d-staff-multisystem-source.v1.1` as the current development candidate, not as a qualified detector.
4. Keep inference source-only. Teacher truth may be used only after a candidate output is frozen for scoring; teacher coordinates must never become inference input or page-specific tuning data.
5. Keep restored V2a outputs closed to staff-line topology comparison until source-detector adequacy is established under a separately frozen qualification/acceptance policy.
6. Before any fresh independent holdout is opened, freeze a qualification policy that defines the metrics, matching rules, acceptance thresholds, specificity requirements, determinism requirements, TAB six-line rejection requirements, and failure/abstention behavior.
7. Development-corpus improvement cannot produce `PASS` or `detectorQualified=true`.
8. If a v1.2 development iteration is undertaken before qualification, it must remain source-only, use only already-spent development data, keep v1/v1.1 frozen, and must not silently move the qualification thresholds after teacher or holdout results are seen.
9. `staff_line` remains `REJECTED_CURRENT_DETECTOR` until a separately governed qualification run supports another disposition.
10. The detector implementation remains replaceable. Classical CV, learned detectors, ensembles, or profile-specific specialists may later replace or supplement v1.1 as long as the source/teacher/holdout boundaries remain auditable.

## Consequences

- The current architecture records real development progress without overstating detector maturity.
- Teacher truth remains an evaluation authority rather than an inference dependency.
- A future holdout cannot be used as an informal tuning set because acceptance criteria must be frozen first.
- Restored-output topology comparison cannot become circular evidence while the source detector is still inadequate.
- A later v1.2 may target remaining low-recall source families, but it cannot erase or rewrite v1.1 evidence.
- The class matrix remains: `notehead` PASS at class-evidence level, `clef` REVIEW_ONLY, `staff_line` REJECTED_CURRENT_DETECTOR, with other classes unchanged unless separately governed evidence changes them.

## Safety and privacy impact

No training/fine-tuning is authorized by this ADR. No new private/user/student data is admitted. No held-out access is authorized. The frozen V2a Restore package is unchanged. Shared music-safety validators, HTTP API, OpenAPI and normal job-service behavior are unchanged. `semanticPreservationEstablished`, `overallStage11PassAuthorized`, `productionReady`, `productionPromotionAuthorized`, and `stage12EntryAuthorized` remain false.

## Alternatives considered

1. **Declare v1.1 adequate because it improved materially.** Rejected because the detector still misses 106/197 teacher-confirmed systems and was developed on the same corpus used for scoring.
2. **Open a fresh holdout immediately.** Rejected because acceptance criteria have not yet been frozen; doing so would risk turning holdout observations into tuning input.
3. **Compare restored outputs now despite weak source detection.** Rejected because detector inadequacy would make preservation conclusions ambiguous and potentially circular.
4. **Hard-code page/source-family exceptions.** Rejected because it would damage generalization and auditability.

## Reversal or migration path

A later ADR may supersede this boundary after a frozen qualification policy and independent evidence justify a new disposition. Any replacement detector must retain provenance, deterministic/reproducible evaluation, source-only inference during qualification, and separation of teacher/holdout truth from candidate generation.

## Post-decision evidence update — 2026-09-13

This update records what happened after the original architectural decision without rewriting the decision history above.

A separately versioned v1.2 candidate was developed and frozen on the already-spent development corpus. Its development result materially improved source recall to `0.7157360406` while retaining `1.0` staff-present page coverage and `1.0` staff-absent specificity on development data. The qualification policy was frozen before fresh holdout access.

Exactly one fresh independent Chopin Op.69 holdout qualification was then explicitly authorized, executed and consumed. The source-only v1.2 raw output was frozen before teacher truth, teacher review was completed independently, and the historical v1 scorer anchor `71/197` was reproduced exactly before holdout scoring.

Holdout result:

- teacher systems: 88;
- predicted systems: 128;
- matched systems: 80;
- teacher-system recall @ 0.5 spacing: `0.9090909091` — PASS;
- predicted-system precision: `0.625` — FAIL against the frozen `>= 0.80` threshold;
- present-page coverage: `1.0` — PASS;
- absent-page specificity: `0.0` — FAIL against the required `1.0`;
- five-line count correctness: `1.0` — PASS;
- line-order correctness: `1.0` — PASS;
- six-line/TAB rejection: `1.0` — PASS;
- source identity and byte-repeat determinism: PASS.

The conjunctive qualification therefore failed. The binding disposition is `QUALIFICATION_COMPLETE_REJECTED_CURRENT_DETECTOR`; `detectorQualified=false` and `sourceDetectorAdequacyEstablished=false` remain authoritative.

The engineering lesson is now primarily about false-positive suppression rather than raw source recall. However, the consumed holdout may not be used to retune v1.2 or to tune a future candidate. Future staff-line work requires a separately versioned candidate developed on non-holdout development evidence, frozen before any new independent holdout, followed by new explicit authorization for another independent qualification. Restored-output topology comparison remains separately closed.

Authoritative post-decision evidence:

- `evidence/stage11/v2d/v2d-staff-line-source-detector-qualification-policy.v1.json`
- `evidence/stage11/v2d/v2d-staff-line-independent-holdout-source-freeze.v1.json`
- `evidence/stage11/v2d/v2d-staff-line-independent-holdout-qualification-result-binding.v1.json`
- `docs/live/ST_SCORE_RESTORE_STAGE11_V2D_STAFF_LINE_HOLDOUT_CURRENT_TRUTH.json`
