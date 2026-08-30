# ST Score Restore Engine — Development Roadmap

**Document status:** Approved binding sequence; Stage 1C active in C17 corpus expansion  
**Version:** 0.2.6  
**Date:** 2026-08-30  
**Decision record:** Issue #31  
**Current Stage 1 tracking:** Issue #47  
**Dependency:** `docs/technical-specification.md`

---

## 1. Purpose and authority

This document defines the binding development order for ST Score Restore Engine. The project follows a **data-first, measurement-first, gate-controlled** sequence. A later stage may not begin merely because its code appears technically possible.

Current-state details that change more frequently than this roadmap are reconciled in `docs/stage-1c-current-status.md`. Historical C12-C16 evidence remains authoritative for the exact slice it records and must not be rewritten to make later corpus expansion appear retroactive. Cross-document status and evidence invariants are checked by `tools/validate_architecture_consistency.py` and summarized in `docs/architecture-consistency-audit.md`.

## 2. Non-negotiable roadmap rules

1. The original source document remains immutable.
2. Music-score and guitar-TAB preservation has veto priority over visual improvement.
3. Only one implementation stage may be active at a time unless a separately approved exception is recorded.
4. Each implementation slice starts from a fresh repository read and is developed on a focused branch/PR.
5. PRs begin as Draft; Ready-for-review remains a separate technical gate after exact-head evidence is complete.
6. Merge remains a later exact-head technical gate; while the autonomous authorization recorded in Issue #47 remains active, separate per-transition user confirmation is not required. Head movement invalidates earlier head-specific evidence.
7. Every stage must publish objective exit evidence before the next stage can start.
8. A real document may enter testing, calibration or training only under explicit rights, privacy, purpose, retention, provenance, custody and dataset-review records appropriate to that use.
9. Teacher approval, dataset inclusion, calibration permission, and training consent are separate decisions.
10. Preview release must be completed before DocRes, the learned selector, or the project-owned image model is activated.
11. AI engines are optional candidates, never automatically trusted replacements.
12. Music applications integrate only through versioned contracts and only at the final integration stage.
13. No stage authorizes autonomous online learning, automatic teacher approval, or generative reconstruction of unreadable musical symbols.
14. Open issues describe deferred work; their existence is not permission to start them out of order.
15. A queued, cancelled, skipped, or zero-job CI run is not stage-transition evidence; required jobs must actually execute and succeed on the exact reviewed head.
16. Repository-visible current-state documents, package/API versions, Stage 1 evidence, and roadmap/spec stage sequences must remain compatible under the deterministic architecture-consistency check.

## 3. Completed foundation

The following foundation is already present on `main` and is treated as baseline rather than future roadmap work:

- independent repository and governance boundary;
- fixture consent and usage governance;
- immutable input inspection;
- deterministic OpenCV safe-restoration candidate;
- conservative music-score and guitar-TAB safety validator;
- versioned non-production job API and teacher-review workflow;
- durable local SQLite metadata and content-addressed artifact storage;
- attempt-bound worker fencing and crash recovery;
- strict local HTTP and multipart boundary;
- immutable reviewer evidence bundles and stale-screen decision binding.

This baseline is not a production service and does not satisfy later real-data, complete quality-analysis, multi-page PDF, calibration, accessible UI, production infrastructure, preview, or AI-candidate gates by itself.

## 4. Stage 1 current state

Stage 1 is delivered through explicit gated substages under parent Issue #32.

- **Stage 1A — metadata governance:** complete and merged.
- **Stage 1B — provider-neutral high-assurance custody and operations boundary:** complete and formally closed through Issue #36.
- **Stage 1C — authorized artifact onboarding and corpus realization:** active under Issue #47.

ADR 0016 risk-tiered custody is fully implemented in the Stage 1C machine-readable contract. The old statement that the storage-profile migration is still pending is obsolete. Catalog schema `1.3.0` and the C6-C11 profile/eligibility/admission machinery are merged.

Binding storage classification is:

- `open_corpus` → `managed_standard`;
- `restricted_corpus` → `managed_restricted` when exact artifact restrictions permit it;
- `sensitive_custody` → `high_assurance_vault`;
- unresolved/rejected/contradictory governance → `blocked`.

C12 admitted the first real development artifact and C14 admitted an independent held-out artifact. C15 froze a digest-addressed two-item historical snapshot. C16 measured the exact C15 snapshot and concluded `insufficient` with seven confirmed coverage gaps. The historical C15/C16 result remains immutable.

C17 corpus expansion is the active Stage 1C work. C17A / PR #68 is merged at exact reviewed head `3424cc22d686b1d08ec0ff1c6be1d372b1ff4146`, with merge commit `010db20a4feb71dd36c9c5378d4d486836c5abc0`. It admits one rights-clean Public Domain PNG classified **only** as `combined_staff_tab`, not as standalone `guitar_tab`. C17A does not mutate C15 and does not retroactively change historical C16 counts.

C17C / PR #72 is also merged. It re-uses the exact already-authorized held-out IMSLP82860 artifact and admits metadata-v2 `dataset.item.imslp82860-chopin-op69.v2` with exact artifact SHA-256 `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3` and conservative degradation classification `noise` only. The v1 metadata, C15 and C16 remain immutable. A future aggregate snapshot must select v2 instead of v1 and must not double-count the two metadata versions as independent artifacts.

The remaining continuation targets are C17B standalone rights-clean guitar TAB and C17D an independently admissible genuine phone-photo path. Their preferred public-source exact bytes are not yet present in authorized Stage 1 custody, so no SHA-256, C11 admission, snapshot membership, or coverage closure is claimed. This remains an exact-byte acquisition/transfer workflow blocker rather than a user-upload obligation.

A user-provided phone photo remains fail-closed because `sensitive_custody` requires a genuinely verified `high_assurance_vault`; C10 structural compatibility alone is not operational vault verification.

The 2026-08-30 consistency audit also records two governance/CI constraints: the active GitHub ruleset is weaker than manual review/thread governance, and Runs #156/#157 were cancelled without job allocation. Those cancelled runs are not test failures, but they are not valid fresh CI evidence either.

Stage 2 remains blocked until Stage 1 final exit is objectively supported and accepted.

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

### Goal

Make the approved sequence unambiguous in repository documentation and issue planning.

### Exit gate

- sequence recorded on `main`;
- no later implementation stage started as part of the roadmap update;
- repository validation passes on supported Python versions;
- the roadmap decision is recorded and accepted.

**State:** COMPLETE.

## 7. Stage 1 — Real and explicitly authorized test dataset

### Goal

Create a trustworthy evaluation corpus before expanding quality analysis, PDF processing, or safety thresholds.

### Required scope

- exact-artifact rights and provenance register for every source;
- separate permissions for evaluation, calibration, model training, publication, and demonstration;
- privacy classification and de-identification review where applicable;
- retention, deletion, and revocation process;
- immutable artifact digest and acquisition metadata;
- dataset card and known-bias documentation;
- representative score, guitar-TAB, and mixed-layout categories;
- representative degradation classes from scans and genuine phone photographs;
- development/held-out split policy without source-family or digest leakage;
- artifact-appropriate managed or high-assurance storage outside ordinary Git;
- metadata-only repository evidence for real corpus bytes;
- deliberate synthetic mutation sets kept distinct from real documents.

### Entry gate

- Stage 0 accepted;
- Stage 1 purposes and ADR 0016 custody architecture approved;
- no private or copyrighted score bytes committed to ordinary Git;
- before any item becomes `external_available`, exact rights, privacy, dataset review, purpose, retention, provenance, digest/size and custody/profile gates pass;
- `high_assurance_vault` use additionally requires real operational high-assurance evidence, not structural compatibility alone.

### Exit gate

- every included item has auditable authorization and provenance;
- development and held-out assignments are frozen and digest-addressed;
- deletion/consent-revocation procedures are demonstrated where applicable;
- coverage gaps and known concentrations are measured and documented;
- coverage is sufficient for the agreed Stage 2 evaluation purpose;
- repository remains free of real corpus artifact bytes;
- no training permission is inferred from teacher approval or evaluation permission.

### Prohibited during this stage

- DocRes integration;
- model training;
- safety-threshold tuning on held-out data;
- production user-upload service activation;
- changes to music-application repositories;
- synthetic relabeling intended to fake a missing real capture/source category.

### Current gate

C15/C16 establish a valid but insufficient historical baseline. C17A and C17C are merged but do not by themselves satisfy Stage 1 exit. C17B standalone guitar TAB and C17D admissible genuine phone-photo evidence remain qualified but unadmitted until exact preferred source bytes and all required evidence enter authorized custody. After sufficient independently admitted C17 material exists, the project must produce a new versioned snapshot and re-evaluate coverage. C17C v2 must replace v1 in that new snapshot rather than being counted as a second artifact. Stage 1 remains **ACTIVE / NOT EXITED**.

## 8. Stage 2 — Complete quality-analysis system

### Goal

Measure document degradation comprehensively and reproducibly before adding new restoration engines.

### Required scope

- page type: vector, scanned, hybrid, phone photo;
- page count, dimensions, orientation, DPI evidence;
- skew and perspective confidence;
- page-boundary confidence;
- blur and motion-blur indicators;
- glare, shadow, and illumination non-uniformity;
- contrast, background, noise, and compression artifacts;
- staff/TAB line visibility and thin-mark preservation indicators;
- per-page and document-level quality report;
- metric versioning and deterministic configuration;
- invalid/unknown/unsupported states instead of guessed values;
- evaluation against the authorized Stage 1 corpus.

### Entry gate

- Stage 1 final dataset/snapshot/coverage exit accepted.

### Exit gate

- every metric has a documented definition, range, and failure behavior;
- repeatability demonstrated for fixed versions;
- metric accuracy and uncertainty measured on the authorized corpus;
- page-type and degradation-class confusion reports published;
- quality reports never modify source bytes;
- thresholds are not presented as safety guarantees.

**State:** BLOCKED until Stage 1 exit.

## 9. Stage 3 — Multi-page PDF pipeline

### Goal

Process real multi-page PDF documents safely while preserving page order, source identity, and vector-content policy.

### Required scope

- reviewed `PdfBackend` and renderer license decision;
- bounded PDF parsing/rendering resources;
- encrypted, malformed, recursive, and oversized PDF handling;
- ordered page extraction and stable page identity;
- vector/scanned/hybrid per-page policy;
- vector pass-through unless explicit rasterization policy applies;
- per-page analysis, candidate, safety, and evidence lifecycle;
- partial-page failure with original fallback;
- deterministic document reassembly;
- page-size, orientation, and ordering preservation;
- multi-page retry, cancellation, retention, and audit behavior.

### Entry gate

- Stage 2 complete quality reports exist for authorized PDF categories;
- renderer dependency and license review approved.

### Exit gate

- supported multi-page PDFs complete upload through review/export;
- unsupported pages fail safely without corrupting others;
- page order and dimensions verified;
- vector pages never silently rasterized;
- original PDF remains available under fallback policy;
- resource and page-count limits tested.

Issue #15 belongs to this stage.

## 10. Stage 4 — Safety calibration with real data

### Goal

Calibrate validator/review thresholds using authorized real documents plus controlled mutations.

### Required scope

- staff and TAB evaluated separately;
- controlled deletion, insertion, shift, line-break, and digit-risk mutations;
- real unchanged pairs and known-safe deterministic transformations;
- false-negative, false-positive, and mandatory-review measurement;
- severity/verdict threshold calibration;
- degradation-class and page-type stratification;
- held-out evaluation never used for threshold selection;
- uncertainty and unsupported-case policy;
- original fallback and reject behavior verification;
- signed, versioned calibration report.

### Entry gate

- Stage 3 can produce stable page-level source, candidate, report, and evidence artifacts for the authorized corpus.

### Exit gate

- critical mutation detection targets met on held-out data;
- false-positive and mandatory-review rates documented;
- staff/TAB and phone/scan differences visible;
- no automatic approval introduced;
- thresholds reproducible and rollbackable;
- limitations accepted before UI work begins.

## 11. Stage 5 — Accessible teacher review interface

### Goal

Provide a teacher-facing review surface that is keyboard- and assistive-technology usable and cannot bypass evidence binding.

### Required scope

- source/candidate comparison and risk overlays;
- page/finding navigation;
- bounded zoom and actual-pixel inspection;
- approve/reject/reprocess actions;
- current evidence-bundle binding on every decision;
- stale-screen recovery;
- full keyboard operation;
- screen-reader names, roles, states, announcements;
- focus order/error recovery;
- contrast, high-zoom, responsive behavior;
- display-integrity/color-management validation;
- teacher approval separate from training consent;
- accessibility test protocol and recorded results.

### Entry gate

- Stage 4 risk findings and thresholds calibrated/versioned.

### Exit gate

- critical actions work without a pointing device;
- agreed screen-reader/browser combinations pass;
- stale or cross-page evidence cannot be submitted;
- scaling/color handling documented and tested;
- teacher actions create append-only audit records;
- usability findings resolved or explicitly accepted.

Issue #16 belongs to this stage.

## 12. Stage 6 — Identity, network, and production infrastructure

### Goal

Replace development-only controls with a deployable security, storage, and operations boundary.

### Required scope

- approved identity provider and token validation;
- client, teacher, operator, service roles;
- job/resource ownership authorization;
- TLS and trusted-proxy policy;
- secret manager and rotation;
- encrypted object storage and lifecycle rules;
- production database and external durable queue;
- distributed worker claims/idempotency;
- backup/restore and disaster-recovery drills;
- structured logging, metrics, traces, alerting;
- rate limits, quotas, abuse controls;
- threat model, security review, dependency scanning;
- concurrency, cleanup, and download-race tests;
- deployment, rollback, and incident runbooks.

### Entry gate

- Stage 5 review contract/accessibility behavior stable enough to protect as a production interface.

### Exit gate

- development keys/caller-provided identities removed from production path;
- cross-tenant/cross-role tests pass;
- encrypted storage, queue recovery, backup restore, and key rotation demonstrated;
- production HTTP/multipart security review accepted;
- load/race/failure-recovery targets met;
- no public exposure before security sign-off.

Issues #13, #14, #17, and #18 belong to this stage.

## 13. Stage 7 — Preview release

### Goal

Run a bounded, reversible preview using the deterministic OpenCV baseline and calibrated human-review workflow before AI candidates.

### Required scope

- explicitly named preview users/use cases;
- supported inputs/document limits;
- service-level objectives and monitoring;
- privacy notice and retention controls;
- support and incident channel;
- feature flags and kill switches;
- rollback to previous approved release;
- original-document fallback;
- preview feedback taxonomy;
- release notes and known limitations;
- no DocRes, selector, or ST Restore image model in the initial preview.

### Entry gate

- Stages 1-6 accepted;
- preview risk and cohort explicitly approved.

### Exit gate

- bounded real use completes without unresolved critical safety/privacy findings;
- monitoring and incident response demonstrated;
- rollback/original fallback succeed;
- teacher review completion/error rates reported;
- deterministic preview baseline frozen for later AI comparison.

## 14. Stage 8 — DocRes optional candidate

### Goal

Evaluate DocRes only after a stable preview baseline exists.

### Required scope

- code and model-weight license decision;
- isolated adapter/worker;
- immutable model checksum and provenance;
- supported-task allowlist;
- CPU/GPU, timeout, memory limits;
- complete disable switch;
- output normalization;
- same validator/review boundary as OpenCV;
- benchmark against frozen Stage 7 baseline.

### Entry gate

- Stage 7 deterministic preview baseline/evaluation reports frozen.

### Exit gate

- DocRes never sole candidate;
- unsafe outputs rejected by existing gates;
- visual improvement and notation/TAB preservation both reported;
- license/deployment conditions accepted;
- disabling DocRes leaves preview workflow intact.

## 15. Stage 9 — Multi-engine comparator

### Goal

Rank immutable original, OpenCV, and enabled Stage 8 candidates using calibrated safety and quality evidence.

### Required scope

- normalized quality metrics;
- protected-region/topology differences;
- hard safety vetoes;
- deterministic ranking;
- explainable recommendation;
- original-as-candidate policy;
- disagreement/no-safe-candidate outcomes;
- teacher override capture;
- calibration against frozen datasets and preview evidence.

### Entry gate

- Stage 8 supplies versioned, repeatable DocRes results.

### Exit gate

- fixed inputs/versions produce identical rankings;
- structural safety overrides appearance scores;
- original input can win;
- medium/high-risk results cannot bypass review;
- recommendation explanations/failure modes audited.

## 16. Stage 10 — ST Restore Selector

### Goal

Introduce a project-owned learning component that selects engines/profiles without generating pixels.

### Required scope

- heuristic routing baseline;
- consented, purpose-approved training subset;
- degradation/routing labels;
- offline reproducible training/evaluation;
- shadow-mode deployment;
- model registry, model card, rollback;
- disagreement reports against heuristic/comparator;
- no online self-training.

### Entry gate

- Stage 9 comparator provides stable labels/outcomes;
- training permission explicit and separate from evaluation permission.

### Exit gate

- selector improves predefined routing metrics without degrading safety outcomes;
- shadow-mode results accepted;
- rollback demonstrated;
- no automatic production model update;
- uncertain cases default to safe deterministic routing and review.

## 17. Stage 11 — ST Restore image model

### Goal

Research/evaluate a project-owned restoration model specialized for notation and guitar TAB.

### Initially permitted tasks

- shadow reduction;
- illumination normalization;
- conservative deblurring;
- paper-background cleanup;
- noise reduction;
- bounded thin-line enhancement.

### Prohibited tasks

- filling missing notation;
- guessing unreadable TAB digits;
- generative reconstruction of symbol regions;
- music-theory correction;
- changing symbol placement.

### Required scope

- authorized paired or synthetic dataset;
- protected-region-aware losses;
- topology/thin-mark preservation evaluation;
- isolated inference adapter;
- model/version/data provenance;
- benchmark against OpenCV/DocRes;
- optional-candidate deployment only;
- model card, rollback, kill switch.

### Entry gate

- Stage 10 selector and Stage 9 comparator provide stable routing/evaluation infrastructure.

### Exit gate

- notation/TAB preservation remains within accepted error budget;
- controlled mutations remain detectable;
- model reproducible/reversible;
- framework/runtime output equivalence documented;
- model remains optional until a separate release decision.

## 18. Stage 12 — Music-application integrations

### Goal

Connect the stable engine to music applications without merging repositories or copying restoration logic.

### Planned integration order

1. Cloud OMR Gateway preprocessing/evidence experiment;
2. SesliTab Guitar Reader teacher workflow;
3. ScoreMosaic/Scremosaik document workflow;
4. MusicXML-to-Guitar Engine only where source provenance/preprocessing status is needed.

### Required scope

- stable versioned API/client contracts;
- client identity/authorization;
- polling/webhook policy according to approved infrastructure;
- artifact/audit/error-code mapping;
- compatibility tests per application;
- feature flags/rollback;
- original-document fallback;
- OMR effectiveness reported separately from visual quality.

### Entry gate

- Stages 1-11 accepted for the capabilities being integrated;
- each target repository separately authorized before modification.

### Exit gate

- restoration failure cannot break the client core workflow;
- clients can always choose the original artifact;
- API compatibility/rollback tested;
- no restoration implementation copied into client repositories;
- downstream improvement supported by measured evidence rather than appearance alone.

## 19. Stage transition evidence

Every stage-completion report must include:

1. approved issue and exact scope;
2. changed files, schemas, APIs, and infrastructure;
3. data-rights/privacy impact;
4. safety risks and mitigations;
5. fresh verification commands/results;
6. known limitations and unsupported cases;
7. rollback/original-fallback evidence;
8. explicit statement that later stages were not started;
9. exact PR head and required CI status, where CI status counts only if the required jobs actually executed and succeeded;
10. separate Ready-for-review and merge technical gates according to repository governance; per-transition user confirmation follows the active authorization record;
11. architecture-consistency validation for repository-visible current-state and immutable-evidence invariants.

## 20. Work that must not be pulled forward

- real-data collection without documented authorization;
- PDF renderer adoption before dependency/license review;
- threshold calibration before accepted frozen held-out data exists;
- browser UI decisions before calibrated risk evidence;
- public exposure before identity/network/production gates;
- DocRes before deterministic preview baseline;
- comparator before DocRes evidence;
- selector before comparator outcomes stabilize;
- image-model training before model governance/training authorization;
- music-application repository changes before Stage 12 authorization;
- generative music-symbol reconstruction;
- automatic teacher approval;
- autonomous online learning;
- destructive replacement of original documents.

## 21. Immediate next gate

The active roadmap stage remains **Stage 1**, with **Stage 1C / C17 corpus expansion** active under Issue #47.

C17A / PR #68 is merged and covers `combined_staff_tab` only; standalone `guitar_tab` remains missing after the accepted taxonomy correction. C17C / PR #72 is merged and provides exact-byte `noise` evidence on the existing held-out artifact through metadata-v2. The historical C15/C16 snapshot remains immutable and `insufficient`.

The remaining corpus work is C17B standalone guitar TAB and C17D a genuine phone-photo artifact with an admissible custody path. Their preferred public-source exact bytes are not currently present in authorized custody, so admission remains fail-closed. Once exact bytes are available, the project may continue through digest/size verification, rights/privacy/provenance binding, storage-profile verification, negative tests, C11 admission, focused Draft PR, exact-head CI/review reconciliation, Ready-for-review, and merge. C17C v2 must replace rather than duplicate v1 in any future aggregate snapshot. After enough C17 items are admitted, the project must create a **new versioned snapshot** and run a fresh deterministic coverage/bias decision. Only a passing Stage 1 exit decision can unlock Stage 2.

Before PR #73 or any later Stage 1 slice crosses a merge boundary, required Python 3.11 and 3.12 jobs must actually execute and succeed on the exact head; the cancelled zero-job Runs #156/#157 do not satisfy that requirement.
