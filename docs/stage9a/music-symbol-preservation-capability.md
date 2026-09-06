# Stage 9A — ST Music-Symbol Preservation capability

Status: **authorized provider-neutral non-production implementation**

Stage 9A implements the repository-side contract and safe routing foundation described by ADR 0018. It does **not** claim that a trained semantic model exists, that OMR output is correct, or that production inference is active.

## What is implemented

- versioned `stage9a.mspm-evidence.v1` preservation evidence contract;
- extensible initial music/TAB taxonomy;
- provenance binding between immutable source and restoration candidate;
- explicit `assessed`, `not_assessed`, and `unavailable` states;
- explicit complete/partial/unknown coverage;
- material symbol-loss/invention/displacement/relationship-change hard-veto handling;
- review routing for uncertain, partial, unknown, future-taxonomy, or malformed evidence;
- Stage 9 comparator handoff that cannot erase deterministic or semantic hard vetoes;
- original fallback retained in every uncertain/unavailable path;
- synthetic drills for accidental loss, TAB uncertainty, safe evidence, and provenance mismatch;
- Python 3.11/3.12 CI.

## Initial taxonomy

The first profile covers staff/TAB lines, noteheads, stems, flags, beams, augmentation dots, rests, accidentals, clefs, key/time signatures, barlines/repeats, ties/slurs, TAB digits and string-position relationships, and visually distinguishable guitar articulations.

The taxonomy is intentionally extensible. New classes or risk concepts can be added by a later version without pretending the current policy already understands them. Unknown concepts route to review under the current policy.

## Safety behavior

Stage 9A cannot approve a candidate by itself. A complete preservation assessment with no material harm merely allows the candidate to remain eligible for the Stage 9 comparator. Known material semantic harm becomes a hard veto. Uncertainty, incomplete coverage, component unavailability, malformed evidence, or provenance mismatch retains the immutable original and routes to review/original.

No single opaque universal preservation score is used as the sole signal.

## Explicitly not performed

This stage does not authorize or perform:

- collection of new user documents for training;
- conversion of production/user documents into training data;
- model training;
- model-weight download or publication;
- external network fetch;
- production inference;
- automatic final restoration selection;
- Stage 10 selector activation;
- provider-specific runtime activation;
- live resources or production deployment.

## Next boundary

After Stage 9A final-exit acceptance, the next architectural boundary is **Stage 10 — ST Restore Selector entry authorization**. Any learned MSPM training program remains separately gated even if Stage 10 work later begins with the provider-neutral evidence contract.
