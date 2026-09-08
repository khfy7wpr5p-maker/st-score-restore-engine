# ADR 0034 — Stage 11 V2c applicable-class semantic evidence

## Status

Accepted for Stage 11 development/evaluation only. This ADR does not authorize training, held-out access, production inference, production promotion, or Stage 12.

## Context

Stage 11 V2b established a repeatable CPU execution profile for the frozen V2a package, but its semantic-preservation coverage denominator counted every supported class on every page. That mixed three different states: a class genuinely absent from the page, a class present but not detected, and a class whose presence had never been independently established. The result could not support a class-aware preservation conclusion.

A second issue is circular evidence. A detector under evaluation cannot be allowed to declare that a class is present and then use that same declaration as proof of its own coverage.

## Decision

Stage 11 V2c introduces a development-only semantic evidence layer with these rules:

1. Every evaluated page enumerates the twelve semantic classes: `staff_line`, `tab_line`, `notehead`, `stem`, `beam_or_flag`, `rest`, `accidental`, `clef`, `barline`, `tie_or_slur`, `tab_digit`, and `tab_string`.
2. Every class is assigned exactly one expected state: `present`, `absent`, `not_applicable`, or `unknown_review_required`.
3. `present` and `absent` require provenance independent of the detector being evaluated: public ground truth, approved teacher annotation, or independent review evidence.
4. Detector output is forbidden as expected-presence provenance.
5. Applicable-class detector coverage uses only independently established `present` classes in its source-recall denominator. Independently established `absent` classes are measured separately for candidate-only/invention evidence. `not_applicable` is excluded. `unknown_review_required` cannot create automatic-pass evidence.
6. Matching is same-class and one-to-one. Cross-class matching is forbidden. Duplicate detections are suppressed conservatively within class.
7. Detector failure produces abstention, never pass.
8. The first automatic detector in V2c is deliberately narrow: conservative five-line staff / six-line TAB geometry. Other class IDs are supported by the interface but remain abstentions until a trusted inference-only detector or independently validated conservative rule detector is admitted.
9. Pixel drift, connected-component drift, and line geometry remain separate evidence layers. None may be described as pitch, rhythm, note identity, or TAB-digit identity without class-specific evidence.
10. Corpus admission remains Stage 1 governance-bound: open-corpus, development split, quality-evaluation grant, approved rights review, privacy `none`, not revoked, exact SHA-256 and byte size.
11. The V2c corpus target is at least five independent approved source families and twenty pages. A shortage is a blocker, not a reason to weaken admission rules.
12. The frozen candidate identity remains SHA-256 `7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234`, 7,817,857 bytes. The canonical execution profile remains CPU / Torch 2.10.0+cpu / intra-op 5 / inter-op 1, applied before package load.

## Current evidence boundary

Repository and connected-Drive reconciliation identifies three approved development source families totaling seven pages: Beethoven Op.48 No.3 (4 scanned pages), Wikimedia Guitar Technical Exercise No.1 (1 PNG), and the admitted Barley/Meg-Noah guitar-TAB source (2-page digital PDF). The historical V2a shadow runner can directly execute only the first two because its input contract is limited to PNG and scanned PDF; V2c does not silently reinterpret that limitation.

The independent expected-class manifest currently marks all real-corpus classes `unknown_review_required`. Catalog notation metadata is not promoted into per-class ground truth. Therefore annotation coverage is zero and no automatic semantic-preservation pass is currently supported.

## Consequences

- Stage 11 V2c can improve semantic measurement without modifying production behavior.
- The coverage denominator is no longer circular or penalized by naturally absent classes.
- Real progress can be committed even when the correct disposition remains `BLOCKED`.
- The next safe work is: expand approved non-held-out corpus, establish independent per-page labels, add trusted class detectors conservatively, and execute the exact frozen package twice under the canonical profile.
- Any confidently evidenced systematic music-symbol deletion or invention remains a hard blocker.
