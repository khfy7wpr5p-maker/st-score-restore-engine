# Stage 4 Wikimedia Development Corpus Expansion

This directory contains a separate, immutable Stage 4 development-corpus expansion package for `dataset.item.wikimedia-guitar-technical-exercise-no1.v1`.

Current state:

- purpose: `safety_calibration`;
- split: `development`;
- source family: `source.family.wikimedia-guitar-technical-exercise-no1.v1`;
- input: one-page PNG;
- human review required: `human_expert_review`;
- human labels present in separate completion evidence: true;
- label result: 7/7 `clear`;
- completion state: `human_labels_complete_pending_separate_acceptance`;
- original `reference-label-work-package.v1.json` remains pristine/null-filled;
- reference bundle accepted: false;
- candidate derivation eligible: false;
- expansion calibration execution authorized: false;
- expansion calibration executed: false;
- held-out Chopin included: false;
- production threshold/resource changes authorized: false;
- Stage 4 exit pass: false;
- Stage 5 entry authorized: false.

The parent Beethoven+Barley purpose grant remains immutable. This overlay exists because the previous real development execution abstained with zero threshold candidates due insufficient measured source-family and reference-class support.

## Human-reference completion boundary

`src/st_score_restore/stage4_wikimedia_reference_gate.py` validates external human review without modifying the committed work package or inventing labels. PR #128 froze the supplied seven `human_expert_review` decisions as `human-label-completion.v1.json` and post-merge Run #340 validated the production checkpoint at main `2ce6151e7ce37198c5b264ddd577df71f49da8bf`.

The seven findings are `skew`, `blur`, `glare`, `shadow`, `uneven_lighting`, `noise`, and `compression`; all seven completed labels are `clear`. Reviewer and provenance references are opaque non-PII tokens and `reviewedOn` is an ISO date.

This completion does **not** accept the reference bundle, authorize candidate derivation or calibration execution, change thresholds/resources, include Chopin in development work, grant Stage 4 PASS, or authorize Stage 5. Those remain separate gates.