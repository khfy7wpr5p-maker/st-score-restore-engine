# ST Score Restore Engine — Development Roadmap

**Document status:** Approved development sequence, Stage 1 substage status aligned  
**Version:** 0.2.1  
**Date:** 2026-08-08  
**Decision record:** Issue #31  
**Dependency:** `docs/technical-specification.md`

---

## 1. Purpose and authority

This document defines the binding development order for ST Score Restore Engine. It replaces the earlier milestone order where DocRes and the comparator could begin before an authorized real-data baseline, complete quality analysis, multi-page PDF processing, and safety calibration.

The project now follows a **data-first, measurement-first and gate-controlled** sequence. A later stage may not begin merely because its code appears technically possible.

## 2. Non-negotiable roadmap rules

1. The original source document remains immutable.
2. Music-score and guitar-TAB preservation has veto priority over visual improvement.
3. Only one implementation stage may be active at a time unless a separately approved exception is recorded.
4. Starting a stage requires explicit approval. Merging its pull request requires a separate explicit approval.
5. Every stage must publish objective exit evidence before the next stage can start.
6. A real document may enter testing, calibration or training only under an explicit rights, privacy, purpose and retention record.
7. Teacher approval, dataset inclusion and training consent are separate decisions.
8. Preview release must be completed before DocRes, the learned selector or the project-owned image model is activated.
9. AI engines are introduced as optional candidates, never as an automatically trusted replacement.
10. Music applications integrate only through versioned contracts and only at the final integration stage.
11. No stage authorizes autonomous online learning, automatic teacher approval or generative reconstruction of unreadable musical symbols.
12. Open issues describe deferred work; their existence is not permission to start them out of order.

## 3. Completed foundation

The following foundation is already present on `main` and is treated as the starting baseline rather than as future roadmap work:

- independent repository and governance boundary,
- fixture consent and usage governance,
- immutable input inspection,
- deterministic OpenCV safe-restoration candidate,
- conservative music-score and guitar-TAB safety validator,
- versioned non-production job API and teacher-review workflow,
- durable local SQLite metadata and content-addressed artifact storage,
- attempt-bound worker fencing and crash recovery,
- strict local HTTP and multipart boundary,
- immutable reviewer evidence bundles and stale-screen decision binding.

This baseline is not a production service. It has not yet passed the complete Stage 1 real-data corpus, complete quality-analysis, multi-page PDF, safety-calibration, accessible-UI, production-infrastructure or preview gates below.

Stage 1 is being delivered through explicit gated substages under parent Issue #32. Stage 1A metadata governance is complete. Stage 1B provider-neutral custody/operations implementation was merged through PR #41 and its ADR/technical-contract acceptance status was synchronized through PR #42. Issue #36 remains open until every Stage 1B exit-evidence item is satisfied. Stage 1C artifact onboarding has not started and requires both formal Stage 1B closure and a separate explicit start approval.

## 4. Binding delivery sequence

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

## 5. Stage 0 — Roadmap update

### Goal

Make the approved sequence unambiguous in repository documentation and issue planning.

### Deliverables

- this roadmap revision,
- README declaration of the binding order and next stage,
- contribution rules that enforce stage gates,
- mapping of open follow-up issues to their new roadmap stages,
- a focused documentation-only pull request.

### Exit gate

- the exact sequence is recorded on `main`,
- no implementation stage was started as part of the roadmap update,
- repository validation passes on Python 3.11 and 3.12,
- Issue #31 is closed only by the approved roadmap pull request.

## 6. Stage 1 — Real and explicitly authorized test dataset

### Current gated-substage status

- **Stage 1A — metadata governance:** complete and merged.
- **Stage 1B — provider-neutral custody and operations boundary:** implementation and acceptance-status changes are merged; Issue #36 remains the formal closure record until all stated exit evidence, including independent exact-head security-audit provenance, is satisfied.
- **Stage 1C — authorized artifact onboarding and corpus realization:** not started and not authorized. It requires formal Stage 1B closure plus a separate explicit start approval.

Completion of Stage 1B is not completion of the whole Stage 1 corpus gate. Stage 2 remains blocked until the Stage 1 exit evidence below is fully satisfied.

### Goal

Create a trustworthy evaluation corpus before expanding quality analysis, PDF processing or safety thresholds.

### Required scope

- rights and provenance register for every source,
- separate permissions for evaluation, calibration and model training,
- privacy classification and de-identification review,
- retention period and deletion process,
- immutable source digest and acquisition metadata,
- dataset-card and known-bias documentation,
- representative score, guitar-TAB and mixed-layout categories,
- representative degradation classes from scans and phone photographs,
- train/calibration/held-out split policy without leakage,
- secure storage outside ordinary Git,
- metadata-only fixture references in the repository,
- deliberate synthetic mutation set kept distinct from real documents.

### Entry gate

- Stage 0 is merged and accepted,
- dataset purpose and storage location are explicitly approved,
- no private or copyrighted bytes are committed to Git.

### Exit gate

- every included item has auditable authorization and provenance,
- test and held-out splits are frozen and digest-addressed,
- deletion and consent-revocation procedures are demonstrated,
- coverage gaps and biases are documented,
- repository fixtures remain metadata-only,
- no training permission is inferred from teacher approval.

### Prohibited during this stage

- DocRes integration,
- model training,
- safety-threshold tuning on the held-out set,
- production user uploads,
- changes to music-application repositories.

## 7. Stage 2 — Complete quality-analysis system

### Goal

Measure document degradation comprehensively and reproducibly before adding new restoration engines.

### Required scope

- page type: vector, scanned, hybrid and phone photo,
- page count, dimensions, orientation and DPI evidence,
- skew and perspective confidence,
- page-boundary confidence,
- blur and motion-blur indicators,
- glare, shadow and illumination non-uniformity,
- contrast, background, noise and compression artifacts,
- staff/TAB line visibility and thin-mark preservation indicators,
- per-page and document-level quality report,
- metric versioning and deterministic configuration,
- invalid/unknown/unsupported states rather than guessed values,
- calibration against the authorized Stage 1 dataset.

### Entry gate

- Stage 1 dataset governance and frozen evaluation splits are accepted.

### Exit gate

- every metric has a documented definition, range and failure behavior,
- repeatability is demonstrated for fixed versions,
- metric accuracy and uncertainty are measured on the authorized corpus,
- page-type and degradation-class confusion reports are published,
- quality reports never modify source bytes,
- thresholds are not presented as safety guarantees.

## 8. Stage 3 — Multi-page PDF pipeline

### Goal

Process real multi-page PDF documents safely while preserving page order, source identity and vector content policy.

### Required scope

- reviewed `PdfBackend` and renderer license decision,
- bounded PDF parsing and rendering resources,
- encrypted, malformed and oversized PDF handling,
- ordered page extraction and stable page identity,
- vector/scanned/hybrid per-page policy,
- vector pass-through unless an explicit rasterization policy applies,
- per-page analysis, candidate, safety and evidence lifecycle,
- partial-page failure and original fallback,
- deterministic document reassembly,
- page-size, orientation and ordering preservation,
- multi-page retention, retry, cancellation and audit behavior.

### Entry gate

- complete Stage 2 quality reports exist for authorized PDF categories,
- renderer dependency and license review are approved.

### Exit gate

- supported multi-page PDFs complete upload through review and export,
- unsupported pages fail safely without corrupting other pages,
- page order and dimensions are verified,
- vector pages are never silently rasterized,
- original PDF remains downloadable under the fallback policy,
- resource and page-count limits are tested.

### Existing issue mapping

Issue #15 belongs to this stage and remains blocked until Stages 1 and 2 are complete.

## 9. Stage 4 — Safety calibration with real data

### Goal

Calibrate validator and review thresholds using authorized real documents plus controlled mutations.

### Required scope

- staff and TAB evaluated separately,
- controlled deletion, insertion, shift, line-break and digit-risk mutations,
- real unchanged pairs and known-safe deterministic transformations,
- false-negative, false-positive and review-rate measurement,
- severity and verdict threshold calibration,
- degradation-class and page-type stratification,
- held-out evaluation never used for threshold selection,
- uncertainty and unsupported-case policy,
- original-fallback and reject behavior verification,
- signed calibration report with component and dataset versions.

### Entry gate

- Stage 3 can produce stable page-level source, candidate, report and evidence artifacts for the authorized corpus.

### Exit gate

- critical mutation detection targets are met on held-out data,
- false-positive and mandatory-review rates are documented,
- staff/TAB and phone/scan performance differences are visible,
- no automatic approval is introduced,
- thresholds are reproducible and rollbackable,
- calibration limitations are accepted before UI work begins.

## 10. Stage 5 — Accessible teacher review interface

### Goal

Provide a teacher-facing review surface that is usable with keyboard and assistive technology and that cannot bypass evidence binding.

### Required scope

- source/candidate comparison and risk overlays,
- page and finding navigation,
- bounded zoom and actual-pixel inspection,
- approve, reject and reprocess actions,
- current evidence-bundle binding on every decision,
- stale-screen recovery,
- full keyboard operation,
- screen-reader names, roles, states and announcements,
- focus order and error recovery,
- contrast, high-zoom and responsive behavior,
- display-integrity and color-management validation,
- teacher approval kept separate from training consent,
- accessibility test protocol and recorded results.

### Entry gate

- Stage 4 risk findings and thresholds are calibrated and versioned.

### Exit gate

- all critical review actions work without a pointing device,
- supported screen-reader/browser combinations pass the agreed protocol,
- stale or cross-page evidence cannot be submitted,
- display scaling and color handling are documented and tested,
- teacher actions create append-only audit records,
- usability findings are resolved or explicitly accepted.

### Existing issue mapping

Issue #16 belongs to this stage. Immutable evidence generation is complete, but the accessible browser UI and display QA remain blocked until Stages 1–4 are complete.

## 11. Stage 6 — Identity, network and production infrastructure

### Goal

Replace development-only controls with a deployable security, storage and operations boundary.

### Required scope

- approved identity provider and token validation,
- client, teacher, operator and service roles,
- job/resource ownership authorization,
- TLS and trusted-proxy policy,
- secret manager and rotation process,
- encrypted object storage and lifecycle rules,
- production database and external durable queue,
- distributed worker claims and idempotency,
- backup, restore and disaster-recovery drills,
- structured logging, metrics, traces and alerting,
- rate limits, quotas and abuse controls,
- threat model, security review and dependency scanning,
- concurrency, cleanup and download race tests,
- deployment, rollback and incident runbooks.

### Entry gate

- the Stage 5 review contract and accessibility behavior are stable enough to protect as a production interface.

### Exit gate

- development API keys and caller-provided actor identities are removed from the production path,
- cross-tenant and cross-role access tests pass,
- encrypted storage, queue recovery, backup restore and key rotation are demonstrated,
- production HTTP and multipart security review is accepted,
- load, race and failure-recovery targets are met,
- no public exposure occurs before the security sign-off.

### Existing issue mapping

- Issue #13: production persistence and deployment hardening,
- Issue #14: production identity and authorization,
- Issue #17: broader multi-worker stress and race validation,
- Issue #18: production HTTP/multipart security review.

These issues are Stage 6 work and must not be interpreted as permission to bypass Stages 1–5.

## 12. Stage 7 — Preview release

### Goal

Run a bounded, reversible preview using the deterministic OpenCV baseline and calibrated human-review workflow before adding AI candidates.

### Required scope

- explicitly named preview users and use cases,
- supported input and document limits,
- service-level objectives and monitoring,
- privacy notice and retention controls,
- support and incident channel,
- feature flags and kill switches,
- rollback to previous approved release,
- original-document fallback,
- preview feedback taxonomy,
- release notes and known limitations,
- no DocRes, selector or ST Restore image model in the initial preview.

### Entry gate

- Stages 1–6 are accepted,
- preview risk and user cohort are explicitly approved.

### Exit gate

- bounded real use completes without unresolved critical safety or privacy findings,
- monitoring and incident response are demonstrated,
- rollback and original fallback succeed,
- teacher review completion and error rates are reported,
- the deterministic preview baseline is frozen for later AI comparison.

## 13. Stage 8 — DocRes optional candidate

### Goal

Evaluate DocRes only after a stable preview baseline exists.

### Required scope

- model and code license decision,
- isolated adapter/worker,
- immutable model checksum and provenance,
- supported-task allowlist,
- CPU/GPU, timeout and memory limits,
- complete disable switch,
- output normalization,
- same validator and review boundary as OpenCV,
- benchmark against the frozen Stage 7 baseline.

### Entry gate

- Stage 7 deterministic preview baseline and evaluation reports are frozen.

### Exit gate

- DocRes is never the sole candidate,
- unsafe outputs are rejected by existing gates,
- visual improvement and notation/TAB preservation are both reported,
- license and deployment conditions are accepted,
- disabling DocRes leaves the preview workflow intact.

## 14. Stage 9 — Multi-engine comparator

### Goal

Rank OpenCV and DocRes candidates using calibrated safety and quality evidence.

### Required scope

- normalized quality metrics,
- protected-region and topology differences,
- hard safety vetoes,
- deterministic ranking,
- explainable recommendation,
- original-as-candidate policy,
- disagreement and no-safe-candidate outcomes,
- teacher override capture,
- calibration against frozen datasets and preview evidence.

### Entry gate

- Stage 8 supplies versioned, repeatable DocRes candidate results.

### Exit gate

- fixed inputs and versions produce identical rankings,
- structural safety overrides appearance scores,
- original input can win,
- medium/high-risk results cannot bypass review,
- recommendation explanations and failure modes are audited.

## 15. Stage 10 — ST Restore Selector

### Goal

Introduce a project-owned learning component that selects engines and profiles without directly generating pixels.

### Required scope

- heuristic routing baseline,
- consented and purpose-approved training subset,
- degradation and routing labels,
- offline training and reproducible evaluation,
- shadow-mode deployment,
- model registry, model card and rollback,
- disagreement reports against the heuristic and comparator,
- no online self-training.

### Entry gate

- Stage 9 comparator provides stable labels and outcomes suitable for selector evaluation,
- training permission is explicit and separate from evaluation permission.

### Exit gate

- selector improves predefined routing metrics without degrading safety outcomes,
- shadow-mode results are accepted,
- rollback is demonstrated,
- no model update occurs automatically in production,
- uncertain cases default to safe deterministic routing and mandatory review.

## 16. Stage 11 — ST Restore image model

### Goal

Research and evaluate a project-owned restoration model specialized for notation and guitar TAB.

### Initial permitted tasks

- shadow reduction,
- illumination normalization,
- conservative deblurring,
- paper-background cleanup,
- noise reduction,
- bounded thin-line enhancement.

### Prohibited tasks

- filling missing notation,
- guessing unreadable TAB digits,
- generative reconstruction of symbol regions,
- music-theory correction,
- changing symbol placement.

### Required scope

- authorized paired or synthetic dataset,
- protected-region-aware losses,
- topology and thin-mark preservation evaluation,
- isolated inference adapter,
- model/version/data provenance,
- benchmark against OpenCV and DocRes,
- optional-candidate deployment only,
- model card, rollback and kill switch.

### Entry gate

- Stage 10 selector and Stage 9 comparator provide stable routing and evaluation infrastructure.

### Exit gate

- notation/TAB preservation stays within the accepted error budget,
- controlled mutations remain detectable,
- model is reproducible and reversible,
- framework/runtime output equivalence is documented,
- the model remains optional until a separately approved release decision.

## 17. Stage 12 — Music-application integrations

### Goal

Connect the stable engine to music applications without merging repositories or copying restoration logic.

### Planned integration order

1. Cloud OMR Gateway preprocessing and evidence experiment,
2. SesliTab Guitar Reader teacher workflow,
3. ScoreMosaic/Scremosaik document workflow,
4. MusicXML-to-Guitar Engine only where source provenance or preprocessing status is needed.

### Required scope

- stable versioned API and client contracts,
- client identity and authorization,
- polling/webhook policy according to approved infrastructure,
- artifact, audit and error-code mapping,
- compatibility tests per application,
- feature flags and rollback,
- original-document fallback,
- OMR effectiveness reported separately from visual quality.

### Entry gate

- Stages 1–11 are accepted for the capabilities being integrated,
- each target repository receives separate explicit authorization before modification.

### Exit gate

- restoration failure cannot break the client’s core workflow,
- clients can always choose the original artifact,
- API version compatibility and rollback are tested,
- no restoration implementation is copied into client repositories,
- OMR or downstream improvements are supported by measured evidence rather than appearance alone.

## 18. Stage transition evidence

Every stage-completion report must include:

1. approved issue and exact scope,
2. changed files, schemas, APIs and infrastructure,
3. data-rights and privacy impact,
4. safety risks and mitigations,
5. fresh verification commands and results,
6. known limitations and unsupported cases,
7. rollback or original-fallback evidence,
8. explicit statement that later stages were not started,
9. separate user approval before merge,
10. explicit approval before activating the next stage.

## 19. Work that must not be pulled forward

- real-data collection without documented authorization,
- PDF renderer adoption before dependency and license review,
- threshold calibration before frozen held-out data exists,
- browser UI decisions before calibrated risk evidence exists,
- public exposure before identity/network/production gates pass,
- DocRes before the deterministic preview baseline,
- comparator before DocRes evidence exists,
- selector before comparator outcomes are stable,
- image-model training before selector and model governance are ready,
- music-application repository changes before Stage 12 approval,
- generative music-symbol reconstruction,
- automatic teacher approval,
- autonomous online learning,
- destructive replacement of original documents.

## 20. Immediate next gate

The active roadmap stage remains Stage 1 under parent Issue #32.

> **Stage 1A is complete. Stage 1B implementation and acceptance-status changes are merged, while Issue #36 remains the formal Stage 1B closure gate. Stage 1C has not started.**

The next permitted action is to satisfy and verify every remaining Issue #36 exit-evidence item. Only after formal Stage 1B closure may Stage 1C be considered, and Stage 1C still requires a separate explicit start authorization. Stage 2 remains blocked until the complete Stage 1 corpus exit gate is accepted.
