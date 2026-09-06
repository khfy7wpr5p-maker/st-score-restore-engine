# Contributing to ST Score Restore Engine

## Project boundary

This repository contains the independent restoration and validation engine for music-score and guitar-TAB documents supplied as PDF, JPG/JPEG, PNG, or phone-captured photos.

Do not place SesliTab user-interface code, MusicXML-to-TAB conversion logic, general MIDI playback or unrelated application features directly into this repository when they belong behind a versioned integration contract. Research adapters and experimental interoperability work are allowed when isolated from production behavior and clearly labeled.

## Safety-first rule

A visually cleaner result is not sufficient when musical information may have changed. Preservation of notation and TAB content has veto priority over appearance when there is justified evidence of material musical damage.

Examples of content that should not be silently invented, removed, materially moved or reinterpreted include:

- staff and TAB lines,
- noteheads, stems, flags, beams and augmentation dots,
- rests, accidentals, clefs, key and time signatures,
- barlines, repeats, ties and slurs,
- TAB numbers, string assignment and guitar articulations,
- lyrics, fingering, chord symbols and instructional markings.

These examples are not a closed taxonomy. New notation systems, instruments and symbol families may extend the preservation vocabulary through versioned profiles.

## Architecture flexibility rule

Read `docs/architecture-flexibility-principles.md` together with the roadmap and ADRs.

Safety-critical product invariants may be strict. Internal techniques should remain replaceable unless evidence justifies a narrower decision.

Prefer contracts that define required outcomes while allowing multiple implementations, including deterministic vision, OpenCV, CNNs, transformers, segmentation/detection networks, ensembles, OMR-derived auxiliary signals and future methods.

Do not treat a current model family, taxonomy, cloud provider, scoring formula or pipeline topology as permanent merely because it is the first implementation.

## Roadmap and stage gates

`docs/roadmap.md` defines production delivery order. The roadmap is primarily a **production-activation and evidence sequence**, not a ban on useful parallel research.

1. One production-effective stage is active by default unless an explicitly bounded exception is recorded.
2. Isolated research, benchmarking, documentation, synthetic-data work, architecture experiments and non-production prototypes may run in parallel when they do not alter production behavior, weaken active safety controls, use unauthorized data or falsely claim a later stage is complete.
3. Production implementation/activation requires the relevant stage authorization and acceptance evidence.
4. A pull request that changes production behavior requires the appropriate review/approval before merge.
5. An open issue may record deferred or exploratory work without implying production activation.
6. Real documents require appropriate rights, privacy classification, purpose limitation and retention controls for the intended use.
7. Evaluation, calibration and model-training permissions remain distinct where the data-governance risk differs.
8. Preview release precedes production activation of DocRes, Stage 9 comparator, Stage 9A preservation capability, Stage 10 Selector and Stage 11 image model; however, non-production research for later stages may proceed in isolated branches/experiments.
9. Stage 9A is a semantic preservation capability, not a requirement for one fixed model architecture.
10. Target music-application repositories should integrate through versioned contracts; experimental adapters may be developed earlier if they remain isolated and do not change target production repositories without approval.

Every production-effective pull request should identify its roadmap stage or explicitly state that it is research/documentation only.

## Change workflow

1. Prefer a focused branch from `main`.
2. Keep each pull request understandable and reviewable; multiple tightly related changes may share a PR when separating them would make validation harder rather than safer.
3. Avoid unreviewed direct production changes to `main`.
4. Document public API or data-contract changes before or with implementation.
5. Add or update tests for observable behavior where useful.
6. Preserve immutable original input identity and auditability.
7. Use draft PRs while acceptance evidence is incomplete when appropriate.
8. Do not merge production-effective work before its required approval/evidence gate.
9. Do not automatically claim the next production stage active merely because experimental work exists.

Recommended branch prefixes include:

- `docs/` for documentation,
- `feature/` for new behavior,
- `fix/` for defects,
- `test/` for test-only work,
- `experiment/` for non-production research.

These prefixes are conventions, not architectural constraints.

## Pull-request evidence

Production-effective pull requests should communicate enough evidence for a reviewer to understand:

- roadmap stage or research-only status,
- what changed and why,
- files/interfaces affected,
- relevant safety risks,
- validation performed,
- known limitations,
- data-rights/privacy implications when fixtures or real documents are involved,
- whether data use is evaluation, calibration, training or another explicitly defined purpose,
- whether any later-stage production behavior was activated.

The exact PR template may evolve as the project matures.

## Data and model governance

- User documents are not training data by default.
- Teacher approval and consent to use data for training are separate decisions unless an explicitly designed consent flow later combines them transparently.
- Evaluation, calibration and training purposes may use separate authorization records when their risks differ.
- Real document bytes should remain under the approved storage/retention policy rather than ordinary Git.
- Production models do not silently self-train from uploads.
- Released model versions should be traceable, regression-tested enough for their risk profile and reversible/disable-able.
- Rejected/high-risk examples may be retained only under an appropriate privacy, rights and retention basis.

Synthetic, public-domain, licensed, generated, weakly supervised and human-labeled datasets may all be considered when their provenance and intended use are clear.

## Licensing

Before a dependency or model weight becomes production-relevant, record its license, redistribution/commercial-use terms and material transitive obligations at an appropriate level of detail. Experimental evaluation of a dependency may occur earlier when clearly isolated and legally permitted.

## Definition of done

Production work is complete when its intended behavior, relevant safety invariants and acceptance evidence are verified for the release profile being claimed.

Research work may be considered complete when its question, method, evidence and limitations are documented even if it is not production-ready. A visually convincing demonstration alone does not establish production readiness.
