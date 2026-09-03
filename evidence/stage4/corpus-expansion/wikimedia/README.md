# Stage 4 Wikimedia Development Corpus Expansion

This directory contains a separate, immutable Stage 4 development-corpus expansion package for `dataset.item.wikimedia-guitar-technical-exercise-no1.v1`.

Current state:

- purpose: `safety_calibration`;
- split: `development`;
- source family: `source.family.wikimedia-guitar-technical-exercise-no1.v1`;
- input: one-page PNG;
- human review required: `human_expert_review`;
- human labels present in separate completion evidence: true;
- label result: **7/7 `clear`**;
- immutable completion snapshot state: `human_labels_complete_pending_separate_acceptance`;
- original `reference-label-work-package.v1.json` remains pristine/null-filled;
- separate governance acceptance decision: `ACCEPT_REAL_REFERENCE_BUNDLE`;
- reference bundle accepted: true;
- candidate derivation eligible: true;
- expansion calibration execution authorized: false;
- expansion calibration executed: false;
- held-out Chopin included: false;
- production threshold/resource changes authorized: false;
- Stage 4: **ACTIVE / NOT_READY**;
- Stage 4 exit pass: false;
- Stage 5: **BLOCKED**;
- Stage 5 entry authorized: false.

The parent Beethoven+Barley purpose grant remains immutable. This overlay exists because the previous real development execution abstained with zero threshold candidates due insufficient measured source-family and reference-class support.

## Human-reference completion boundary

`src/st_score_restore/stage4_wikimedia_reference_gate.py` validates external human review without modifying the committed work package or inventing labels. PR #128 froze the supplied seven `human_expert_review` decisions as `human-label-completion.v1.json` and post-merge Run #340 validated the production checkpoint at main `2ce6151e7ce37198c5b264ddd577df71f49da8bf`.

The seven findings are `skew`, `blur`, `glare`, `shadow`, `uneven_lighting`, `noise`, and `compression`; all seven completed labels are `clear`. Reviewer and provenance references are opaque non-PII tokens and `reviewedOn` is an ISO date.

The completion snapshot remains immutable and therefore still says acceptance is pending. It is not retroactively rewritten.

## Separate reference-bundle acceptance boundary

PR #130 separately recorded the user's explicit governance decision at production main `3353b281a4022f107929fae296368390da45a4fb`; post-merge Run #348 (`33748180036`) succeeded on Python 3.11 and 3.12.

Binding acceptance evidence is `reference-bundle-acceptance.v1.json`:

- decision: `ACCEPT_REAL_REFERENCE_BUNDLE`;
- exact human bundle digest: `37af98bbeb04832fc94382f246287da0b738c2520225cdcd9f5ea2028bde71f4`;
- accepted reference receipt digest: `036bb31ca2672e443885ed06e213ef6913be7c66609ab5017b6f22ed3f33c801`;
- acceptance digest: `79771e291768ba4979abc1e44dd0ecebfd95892ff2e5861d77706c1cb4563eb3`;
- reference bundle accepted: true;
- candidate derivation eligible: true.

This acceptance does **not** authorize calibration execution, change thresholds/resources, include Chopin in development work, grant Stage 4 PASS, or authorize Stage 5. The next substantive gate is separate exact Wikimedia expanded-development calibration execution authorization.

## Current Stage 4 readiness blockers

Reference acceptance does not close the remaining global Stage 4 blockers:

1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`
