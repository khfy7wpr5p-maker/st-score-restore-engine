# Stage 4 Wikimedia Development Corpus Expansion

This directory contains a separate, immutable Stage 4 development-corpus expansion package for `dataset.item.wikimedia-guitar-technical-exercise-no1.v1`.

Current state:

- purpose: `safety_calibration`;
- split: `development`;
- source family: `source.family.wikimedia-guitar-technical-exercise-no1.v1`;
- input: one-page PNG;
- human review required: `human_expert_review`;
- human labels present: false;
- reference bundle accepted: false;
- expansion calibration execution authorized: false;
- expansion calibration executed: false;
- held-out Chopin included: false;
- production threshold/resource changes authorized: false;
- Stage 5 entry authorized: false.

The parent Beethoven+Barley purpose grant remains immutable. This overlay exists because the previous real development execution abstained with zero threshold candidates due insufficient measured source-family and reference-class support.

## Human-reference ingestion boundary

`src/st_score_restore/stage4_wikimedia_reference_gate.py` prepares the next external-evidence boundary without modifying this committed work package or inventing labels. It accepts only a separate payload containing exactly seven completed human-review rows matching the existing label/observation/finding identities. Reviewer and provenance references must be opaque non-PII tokens and `reviewedOn` must be an ISO date.

Even when all seven external rows validate, the result is only `human_labels_complete_pending_separate_acceptance`. It does **not** accept the reference bundle, authorize candidate derivation or calibration execution, change thresholds/resources, include Chopin in development work, grant Stage 4 PASS, or authorize Stage 5. Those remain separate gates.
