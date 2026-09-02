# ST Score Restore Engine — Development Roadmap

**Document status:** Approved binding sequence; Stage 1C active  
**Version:** 0.2.7  
**Date:** 2026-09-02  
**Decision record:** Issue #31  
**Current Stage 1 tracking:** Issue #47  
**Current production main at refresh:** `53ae13d3a1b9bda08c79125674e1b7fca78ee8af`

## 1. Purpose and authority

This roadmap defines the binding development order. The project is data-first, measurement-first and gate-controlled. A later stage may not begin merely because implementation is technically possible.

Current-state details are reconciled in `docs/stage-1c-current-status.md`. Historical C15/C16 evidence is immutable. Open-PR work is in-progress and is not production truth. Exact-head CI evidence is invalid after head movement.

## 2. Non-negotiable roadmap rules

1. The original source remains immutable.
2. Music-score and guitar-TAB preservation has veto priority over visual improvement.
3. Only the authorized stage may be active.
4. Each implementation slice starts with a fresh repository read and focused branch/PR.
5. Draft, Ready-for-review and merge are separate objective gates.
6. Every stage publishes objective exit evidence before transition.
7. Rights, privacy, purpose, retention, provenance, custody and dataset review are independent fail-closed gates.
8. Teacher approval, dataset inclusion, calibration permission and training consent are separate decisions.
9. Real corpus artifact bytes remain outside ordinary Git.
10. A queued, cancelled, skipped, zero-job or old-head CI run is not transition evidence.
11. Historical evidence is never rewritten to make later results retroactive.
12. Stage 2 cannot start until Stage 1 final exit is explicitly accepted as PASS.

## 3. Completed foundation

The repository already contains the baseline architecture for immutable input inspection, deterministic OpenCV restoration candidates, conservative music-score/TAB validation, a versioned non-production job/review API, optional durable local storage, attempt-bound worker fencing/recovery, a strict local HTTP/multipart boundary, immutable review evidence and append-only audit behavior.

This baseline is not a production deployment and does not satisfy later real-data, complete quality-analysis, PDF, calibration, accessible UI, production infrastructure, preview or AI-candidate gates by itself.

## 4. Stage 1 current state

Stage 1A metadata governance and Stage 1B custody/operations closure are complete. Stage 1C authorized artifact onboarding/corpus realization is active.

Historical baseline:

- C15 froze the two-item v1 corpus;
- C16 measured exactly that snapshot and concluded `insufficient`;
- C15/C16 files remain immutable historical evidence.

Merged C17 expansion on current main:

- **C17A / PR #68:** exact combined staff+TAB PNG admitted as `combined_staff_tab` only;
- **C17B:** exact standalone guitar-TAB PDF admitted, SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`;
- **C17C / PR #72:** exact held-out Chopin artifact represented by metadata v2 with degradation `noise` only; v2 replaces v1 in new aggregate snapshots and the same artifact must never be double-counted;
- **C17D:** exact deidentified phone-photo derivative admitted, SHA-256 `abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5`.

PR #81 is the active expanded-v2 acceptance slice. It commits a deterministic 5-real-item / 0-synthetic aggregate with development 3 items / 3 source families and held out 2 items / 2 source families. It covers staff, guitar TAB, combined staff+TAB, scanned PDF, phone photo and non-`none` degradation without cross-split source-family leakage or duplicate artifact digests.

The expanded-v2 coverage report remains `review_required`, with `stage1ExitSupported=false` and `stage2EntrySupported=false`. Coverage closure is not final Stage 1 acceptance.

## 5. Binding delivery sequence

```text
Stage 0  Roadmap update
      ↓
Stage 1  Real and explicitly authorized test dataset
      ↓
Stage 2  Complete quality-analysis system
      ↓
Stage 3  Multi-page PDF pipeline
      ↓
Stage 4  Safety calibration with real data
      ↓
Stage 5  Accessible teacher review interface
      ↓
Stage 6  Identity, network and production infrastructure
      ↓
Stage 7  Preview release
      ↓
Stage 8  DocRes optional candidate
      ↓
Stage 9  Multi-engine comparator
      ↓
Stage 10 ST Restore Selector
      ↓
Stage 11 ST Restore image model
      ↓
Stage 12 Music-application integrations
```

## 6. Stage 0 — Roadmap update

**Goal:** record the approved sequence and gates.  
**Exit:** binding order accepted and repository validation green.  
**State:** COMPLETE.

## 7. Stage 1 — Real and explicitly authorized test dataset

**Goal:** establish a trustworthy evaluation corpus before expanding quality analysis or calibration.

Required scope includes exact-artifact rights/provenance, independent purpose permissions, privacy/de-identification review, retention/deletion/revocation, immutable digest/size identity, dataset review, development/held-out isolation, representative notation/capture/degradation categories, managed custody outside ordinary Git and a documented bias/coverage register.

**Current gate:** ACTIVE / NOT EXITED.

PR #81 must complete all of the following before exit evaluation:

1. canonical expanded-v2 catalog/snapshot/report committed;
2. committed-evidence `--check` wired into CI;
3. regression coverage for exact membership, split/source-family isolation, digest uniqueness, C17C v1/v2 dedup, historical immutability and zero artifact bytes in ordinary Git;
4. fresh exact-head Python 3.11/3.12 CI success;
5. review/thread/head reconciliation;
6. Ready transition only with clean objective gates;
7. exact verified-head merge;
8. successful post-merge main CI;
9. separate Stage 1 exit evidence review.

**Exit gate:** every included item remains auditable and authorized; split assignments are frozen/digest-addressed; coverage and known concentrations are measured; repository remains metadata-only for real corpus bytes; and the evidence supports the agreed Stage 2 evaluation purpose without inferring training rights.

If any governance, custody, rights, privacy, source-family, digest, CI or review blocker remains, Stage 1 exit is FAIL/BLOCKED.

## 8. Stage 2 — Complete quality-analysis system

**Goal:** measure document degradation comprehensively and reproducibly before adding new restoration engines.

Planned categories include skew, perspective, blur, motion blur, glare, shadow, uneven lighting, noise, compression, low resolution, page boundary/orientation/DPI evidence, page type and staff/TAB visibility indicators.

**Entry gate:** explicit Stage 1 final PASS bound to exact main SHA, CI run and accepted v2 evidence digests.

**State:** BLOCKED.

No Stage 2 implementation or execution is authorized by PR #81 coverage closure alone.

## 9. Stage 3 — Multi-page PDF pipeline

**Goal:** safely process supported multi-page PDFs while preserving page order, source identity and vector-content policy.

Entry requires Stage 2 quality reports and an approved PDF renderer/dependency decision. Unsupported pages fail safely with original fallback. Vector pages must not be silently rasterized.

**State:** NOT STARTED.

## 10. Stage 4 — Safety calibration with real data

**Goal:** calibrate validation/review thresholds on authorized real data plus controlled mutations.

Held-out data is evaluation-only and cannot be used for threshold selection. Calibration must report false negatives, false positives, mandatory-review rates and limitations.

**State:** NOT STARTED.

## 11. Stage 5 — Accessible teacher review interface

**Goal:** deliver a keyboard- and assistive-technology-usable review UI without weakening evidence binding.

Required behavior includes source/candidate comparison, risk overlays, stale-screen rejection, keyboard operation, screen-reader semantics and append-only decision audit.

**State:** NOT STARTED.

## 12. Stage 6 — Identity, network and production infrastructure

**Goal:** replace development-only controls with deployable identity, encrypted storage, durable queue/database, secrets, network protection, observability, backup/restore and incident controls.

No public production exposure occurs before security acceptance.

**State:** NOT STARTED.

## 13. Stage 7 — Preview release

**Goal:** run a bounded, reversible preview using the deterministic OpenCV baseline and human review before AI candidates.

Requires Stages 1-6 accepted, explicit cohort/support/retention limits, monitoring, kill switches and rollback/original fallback.

**State:** NOT STARTED.

## 14. Stage 8 — DocRes optional candidate

**Goal:** evaluate DocRes only as an optional restoration candidate after preview evidence exists.

DocRes may not bypass safety validation, comparator ordering or original fallback.

**State:** NOT STARTED.

## 15. Stage 9 — Multi-engine comparator

**Goal:** compare eligible restoration candidates under a deterministic, safety-first policy.

Rejected candidates cannot win and the immutable original remains selectable.

**State:** NOT STARTED.

## 16. Stage 10 — ST Restore Selector

**Goal:** choose eligible engine/profile candidates while preserving ADR 0015 ordering and auditability.

The selector may not override a safety rejection or remove original fallback.

**State:** NOT STARTED.

## 17. Stage 11 — ST Restore image model

**Goal:** consider a project-owned learned restoration candidate only after earlier deterministic and preview evidence exists.

Training requires explicit dataset/training authorization independent of evaluation permissions.

**State:** NOT STARTED.

## 18. Stage 12 — Music-application integrations

**Goal:** integrate the accepted restoration service with music applications through versioned contracts.

Repository boundaries remain independent. A selected visual source must still cross ScoreMosaic Safe Intake before OMR.

**State:** NOT STARTED.

## 19. Current next safe action

Finish PR #81 documentation/validator reconciliation, run committed-evidence and full repository validation on the exact final head, reconcile review/thread/head movement, then Ready/merge only if all gates are clean. After successful post-merge main CI, perform the separate Stage 1 exit acceptance. Stage 2 remains blocked unless that decision is PASS.
