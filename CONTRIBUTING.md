# Contributing to ST Score Restore Engine

## Project boundary

This repository contains the independent restoration and validation engine for music-score and guitar-TAB documents supplied as PDF, JPG/JPEG, PNG, or phone-captured photos.

Do not add SesliTab user-interface code, MusicXML-to-TAB conversion logic, OMR recognition logic, MIDI playback, or unrelated application features to this repository. Those systems integrate through versioned contracts.

## Safety-first rule

A visually cleaner result is not acceptable when musical information may have changed. Preservation of notation and TAB content has veto priority over appearance.

The following must never be silently invented, removed, moved, or reinterpreted:

- staff and TAB lines,
- noteheads, stems, flags, beams and augmentation dots,
- rests, accidentals, clefs, key and time signatures,
- barlines, repeats, ties and slurs,
- TAB numbers, string assignment and guitar articulations,
- lyrics, fingering, chord symbols and instructional markings.

## Roadmap stage gate

`docs/roadmap.md` defines the binding development order.

1. Only one implementation stage may be active at a time unless an explicitly approved exception is recorded.
2. A stage requires explicit approval before implementation begins.
3. A pull request requires a separate explicit approval before merge.
4. A later stage must not begin until the previous stage's exit evidence has been published and accepted.
5. An open issue records deferred work but does not authorize starting it out of order.
6. Real documents require documented rights, privacy classification, purpose limitation and retention before use.
7. Evaluation permission, calibration permission and model-training permission must be represented separately.
8. Preview release must precede DocRes, the comparator, ST Restore Selector and the ST Restore image model.
9. Target music-application repositories must not be changed before the final integration stage receives separate approval.

Every pull request must state its roadmap stage and confirm that later stages were not started.

## Change workflow

1. Create a focused branch from `main`.
2. Use one purpose per branch and pull request.
3. Do not commit directly to `main` for implementation work.
4. Document public API or data-contract changes before implementation.
5. Add or update tests for observable behavior.
6. Preserve the immutable original input and audit trail.
7. Open a draft pull request until the acceptance evidence is complete.
8. Stop after presenting the verified pull request; do not merge without separate approval.
9. Do not automatically begin the next roadmap stage after merge.

Recommended branch prefixes:

- `docs/` for documentation,
- `feature/` for new behavior,
- `fix/` for defects,
- `test/` for test-only work,
- `experiment/` for non-production research.

## Required pull-request evidence

A pull request must state:

- roadmap stage and approved issue,
- what changed and why,
- files and interfaces affected,
- safety risks,
- validation commands and results,
- known limitations,
- whether fixtures contain copyrighted, private, or consent-restricted material,
- whether data permission is evaluation-only, calibration-approved or training-approved,
- confirmation that no later roadmap stage was started.

## Data and model governance

- User documents are not training data by default.
- Teacher approval and consent to use data for training are separate decisions.
- Evaluation, calibration and training purposes require distinct authorization records.
- Real document bytes are stored outside ordinary Git under the approved retention policy.
- Training occurs offline; production models do not update themselves during use.
- Model versions are immutable, evaluated against regression sets, and reversible.
- Rejected and high-risk examples may be stored only under an approved privacy and consent policy.

## Licensing

Do not add a dependency or model weight until its license, redistribution terms, commercial-use conditions, and transitive obligations have been recorded in an architecture decision or dependency review.

## Definition of done

Work is complete only when the requested behavior, safety invariants, roadmap exit gate and relevant tests have been freshly verified. A visually convincing demonstration alone is not completion.
