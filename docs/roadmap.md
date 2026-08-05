# ST Score Restore Engine — Development Roadmap

**Document status:** Approved roadmap baseline  
**Version:** 0.1.1-draft  
**Date:** 2026-08-05  
**Dependency:** `docs/technical-specification.md`

---

## 1. Roadmap principles

The project develops from the safest and most deterministic capability toward controlled AI learning.

Rules governing every milestone:

1. The original document remains immutable.
2. Classical deterministic restoration precedes AI restoration.
3. Music and TAB preservation has veto priority over visual improvement.
4. A new engine is first introduced as an optional candidate, not as the trusted default.
5. Teacher review and explicit training consent are distinct decisions.
6. Models are trained offline, versioned, evaluated and reversible.
7. The engine remains independent; other music applications integrate through a versioned API.
8. Each milestone has objective exit criteria. A milestone does not advance merely because a demo looks good.

---

## 2. Milestone 0 — Repository and governance foundation

### Goal

Create the independent project boundary and prevent premature coupling with existing music applications.

### Deliverables

- independent private repository `st-score-restore-engine`,
- `README.md`,
- approved technical specification,
- approved roadmap,
- contribution and branch policy,
- architecture decision record structure,
- dependency and model license inventory,
- security and data-retention assumptions,
- issue templates for bug, safety regression and model experiment.

### Exit criteria

- repository exists independently,
- existing SesliTab and MusicXML repositories remain unchanged,
- technical scope and non-goals are accepted,
- license review identifies permitted, conditional and blocked dependencies,
- no production code is merged before the safety invariants are documented.

---

## 3. Milestone 1 — Deterministic document-analysis prototype

### Goal

Understand input documents without modifying them.

### Deliverables

- file signature and integrity checks,
- SHA-256 input identity,
- PDF, JPG/JPEG and PNG metadata reader,
- safe EXIF-orientation and color-profile inspection,
- page count, dimensions and rotation extraction,
- vector/scanned/hybrid/photo page classifier,
- deterministic page rendering through a `PdfBackend` interface,
- initial quality metrics: skew, perspective, page boundary, blur, glare, contrast, illumination, shadow and noise,
- command-line analysis report,
- test fixtures for representative PDF notation/TAB documents and phone-captured JPG/JPEG/PNG photos.

### Exit criteria

- analysis never overwrites input,
- repeated runs with the same versions produce equivalent analysis,
- malformed inputs fail safely,
- page classification reaches the agreed reference-corpus threshold,
- vector pages are correctly recognized and marked for pass-through by default,
- phone photos are correctly classified and their EXIF orientation is handled without modifying the source.

---

## 4. Milestone 2 — OpenCV safe restoration MVP

### Goal

Produce a useful enhanced derivative without AI.

### Deliverables

- orientation and EXIF-orientation correction,
- bounded deskew,
- confidence-gated page-boundary crop,
- conservative perspective correction,
- camera-photo shadow and mild-glare reduction outside protected notation regions,
- background and illumination normalization,
- conservative denoise,
- bounded local contrast enhancement,
- border cleanup outside protected content,
- profile system: `safe`, `balanced`, `experimental`,
- operation manifest with exact parameters,
- original/enhanced side-by-side and slider previews,
- derivative page images, approved PNG master export, optional JPEG compatibility export, and PDF export.

### Exit criteria

- safe profile is deterministic,
- page dimensions and ordering are preserved for PDF jobs,
- phone-image aspect ratio changes only through a recorded approved crop or perspective transform,
- no vector page is rasterized without explicit policy,
- every pixel-affecting operation is recorded,
- every enhanced PDF or image has a distinct checksum and filename,
- baseline golden-image regression tests pass.

---

## 5. Milestone 3 — Music and TAB structure protection

### Goal

Make the engine music-aware before introducing third-party AI.

### Deliverables

- staff system detection,
- five-line staff grouping,
- six-line TAB system detection,
- thin-line and symbol-dense region detection,
- `LOCKED`, `CONSERVATIVE` and `BACKGROUND` protection masks,
- transform-coordinate mapping,
- staff/TAB line-count validation,
- connected-component comparison in protected regions,
- page-level risk findings and visual risk map,
- deliberate safety mutation test corpus.

### Exit criteria

- validator catches the required controlled staff/TAB mutations,
- protected regions receive only permitted operations,
- hard-fail conditions block candidate approval,
- risk findings include page coordinates and evidence crops,
- false-positive rate is measured and documented rather than hidden.

---

## 6. Milestone 4 — Job API and teacher review workflow

### Goal

Turn the prototype into an independent service usable by future applications.

### Deliverables

- versioned `/api/v1` job API,
- asynchronous job state machine,
- idempotent upload and retry behavior,
- authenticated artifact access,
- candidate listing,
- safety-report endpoint,
- per-page teacher candidate selection,
- approve, reject and reprocess actions,
- separate training-consent control,
- immutable review and audit records,
- cleanup and retention jobs,
- client fixture package or OpenAPI contract.

### Exit criteria

- an integration test completes upload → analysis → processing → validation → review → export,
- teacher can reject one page without approving the entire document,
- approved artifacts cannot be downloaded before approval policy is satisfied,
- cancellation and retry preserve audit history,
- deletion behavior follows documented retention rules.

---

## 7. Milestone 5 — DocRes optional candidate adapter

### Goal

Evaluate a strong ready-made document-restoration model without trusting it by default.

### Deliverables

- isolated DocRes worker/adapter,
- model checksum and version manifest,
- supported-task allowlist,
- CPU/GPU resource controls,
- timeout and memory protection,
- candidate normalization,
- before/after structural comparison,
- complete disable switch,
- license decision record,
- benchmark comparing OpenCV and DocRes on music/TAB corpus.

### Exit criteria

- DocRes is never the sole produced candidate,
- every output passes through the same safety validator,
- unsafe candidates are rejected automatically,
- exact code/model provenance is recorded,
- distribution or hosted deployment is blocked until license review is accepted,
- benchmark reports both visual improvement and notation-preservation failure rates.

---

## 8. Milestone 6 — Multi-engine result comparator

### Goal

Select the safest useful candidate based on evidence, not aesthetics alone.

### Deliverables

- normalized candidate metrics,
- protected-region difference metrics,
- background-quality improvement metrics,
- geometry and topology checks,
- candidate ranking rules,
- hard-safety vetoes,
- explainable recommendation output,
- calibration dataset and score thresholds,
- teacher override capture.

### Exit criteria

- comparator explains why a candidate won or lost,
- structural safety can override a higher visual-quality score,
- ranking is deterministic for fixed inputs and versions,
- teacher overrides are recorded for later analysis,
- no medium/high-risk recommendation bypasses required review.

---

## 9. Milestone 7 — ST Restore Selector

### Goal

Introduce the first project-owned learning component without directly altering pixels.

### Function

The selector predicts:

- page degradation classes,
- safest engine set,
- restoration profile,
- parameter ranges,
- expected risk,
- need for mandatory teacher review.

### Deliverables

- versioned training dataset from synthetic and consented examples,
- baseline heuristic router,
- trainable selector model,
- offline evaluation pipeline,
- model registry,
- shadow-mode deployment,
- disagreement reports between heuristic and learned selector.

### Exit criteria

- selector outperforms the heuristic baseline on predefined routing metrics,
- it does not reduce safety-mutation detection performance,
- shadow results are reviewed before active use,
- model rollback is tested,
- no production weight update occurs online.

---

## 10. Milestone 8 — ST Restore Image Model research track

### Goal

Develop a project-owned restoration model specialized for notation and guitar TAB.

### Deliverables

- synthetic degradation generator,
- paired clean/degraded dataset,
- protected-region-aware training losses,
- staff/TAB topology preservation loss,
- digit and symbol consistency evaluation,
- background restoration objectives,
- ONNX export feasibility study,
- isolated inference adapter,
- benchmark against OpenCV and DocRes,
- model card and known limitations.

### Initial permitted tasks

- shadow reduction,
- illumination normalization,
- conservative deblurring,
- paper-background cleanup,
- noise reduction,
- bounded thin-line enhancement.

### Prohibited initial tasks

- filling missing notation,
- guessing unreadable TAB digits,
- generative reconstruction of symbol regions,
- music-theory correction,
- changing symbol placement.

### Exit criteria

- model meets visual-quality target without exceeding notation-preservation error budget,
- all controlled safety mutations remain detectable,
- model runs only as optional candidate until extended review completes,
- model version, data and training provenance are reproducible,
- ONNX/runtime output matches reference framework within documented tolerance.

---

## 11. Milestone 9 — Controlled continual-learning program

### Goal

Allow improvement over time without uncontrolled self-modification.

### Deliverables

- explicit training-consent workflow,
- annotation taxonomy,
- active-learning queue for uncertain/high-value examples,
- dataset review and de-identification process,
- offline retraining pipeline,
- old/new regression comparison,
- catastrophic-forgetting checks,
- shadow and canary release stages,
- human release approval,
- one-command rollback to approved predecessor.

### Exit criteria

- no unconsented document enters the training set,
- every dataset and model release is versioned,
- new model passes old and new regression corpora,
- degradation in any critical safety metric blocks release,
- rollback drill succeeds,
- release report records who approved the model and why.

---

## 12. Milestone 10 — Integration with music applications

### Goal

Connect stable engine capabilities without merging repositories.

### Integration order

1. Cloud OMR Gateway preprocessing integration,
2. SesliTab Guitar Reader teacher workflow,
3. ScoreMosaic/Scremosaik document workflow,
4. MusicXML-to-Guitar Engine only where it needs source-document provenance or preprocessing status.

### Deliverables

- stable OpenAPI specification,
- client authentication model,
- example client adapters,
- webhook or polling contract according to available infrastructure,
- artifact and error-code mapping,
- compatibility tests for each client,
- integration feature flags,
- rollback/fallback to original document.

### Exit criteria

- client can always choose original rather than enhanced document,
- restoration failure does not break the client’s core workflow,
- client records restoration job and artifact identifiers,
- API version compatibility is tested,
- no restoration implementation is copied into client repositories.

---

## 13. Milestone 11 — OMR effectiveness laboratory

### Goal

Measure whether restoration actually improves OMR rather than assuming it does.

### Deliverables

- authorized original-vs-enhanced OMR experiment flow,
- measure and staff count comparison,
- note/rest/duration consistency metrics,
- TAB recognition metrics where supported,
- engine/profile effectiveness by degradation class,
- negative-result database showing when restoration harms OMR,
- policy for selecting original or enhanced input.

### Exit criteria

- OMR effectiveness is reported separately from visual quality,
- system can prefer original input when enhancement reduces recognition quality,
- metrics are reproducible on a held-out corpus,
- client integration receives evidence, not only a binary “enhanced” label.

---

## 14. Release channels

Suggested channels:

- `research`: models and features not eligible for user production,
- `experimental`: teacher review always required,
- `preview`: bounded real use with enhanced monitoring,
- `stable`: approved safety and regression thresholds satisfied.

A model or engine may be stable for one task and experimental for another. Capability flags must express this explicitly.

---

## 15. Priority order

Highest priority:

1. immutable original and audit trail,
2. PDF/page classification,
3. deterministic OpenCV safe profile,
4. music/TAB structure protection,
5. safety validation and teacher review,
6. independent API and export,
7. DocRes as optional candidate,
8. result comparator,
9. ST Restore Selector,
10. ST Restore Image Model,
11. controlled continual learning,
12. external application integrations.

Items that must not be pulled forward prematurely:

- generative symbol reconstruction,
- autonomous online learning,
- automatic approval before validator calibration,
- direct embedding into SesliTab or MusicXML repositories,
- destructive replacement of original PDFs.

---

## 16. Initial issue backlog

Recommended first repository issues:

1. Define repository license and third-party dependency policy.
2. Create `PdfBackend` interface and pypdfium2 proof of concept.
3. Add immutable input hashing and metadata schema.
4. Build vector/scanned/hybrid page classifier baseline.
5. Define quality-analysis schema and metric implementations.
6. Implement OpenCV safe-profile operation registry.
7. Build staff and TAB line reference corpus.
8. Implement protection-mask data format.
9. Define safety finding taxonomy.
10. Create deliberate notation/TAB mutation fixtures.
11. Define restoration job state machine.
12. Publish OpenAPI draft for `/api/v1/restoration-jobs`.
13. Implement audit-manifest schema validation.
14. Design teacher review wireframes and page-selection contract.
15. Complete DocRes license and deployment review before adapter work.

---

## 17. First implementation checkpoint

The first implementation checkpoint should demonstrate:

```text
One scanned score/TAB PDF and one phone-captured JPG/PNG sample
      ↓
Immutable input hash
      ↓
Page classification and quality report
      ↓
OpenCV safe restoration candidate
      ↓
Staff/TAB line validation
      ↓
Before/after comparison
      ↓
Manual teacher approval
      ↓
Separate enhanced PDF/image derivatives and manifest
```

It should not include DocRes, ST Restore training, OMR, MusicXML, speech or MIDI. The phone-photo sample must demonstrate safe EXIF orientation, page-boundary analysis, conservative perspective correction, before/after comparison and teacher approval. This narrow checkpoint establishes the trustworthy foundation on which later AI components depend.
