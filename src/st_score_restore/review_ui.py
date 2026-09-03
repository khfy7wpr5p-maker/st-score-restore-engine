"""Dependency-free accessible teacher-review UI assets for the local Stage 5 baseline."""

from __future__ import annotations

from typing import Final

UI_VERSION: Final[str] = "1.0.0"

REVIEW_UI_HTML: Final[bytes] = b'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>ST Score Restore - Teacher Review</title>
  <link rel="stylesheet" href="/review/styles.css">
  <script src="/review/app.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#review-main">Skip to review controls</a>
  <header class="site-header">
    <div>
      <p class="eyebrow">ST Score Restore</p>
      <h1>Teacher review</h1>
      <p class="lede">Compare immutable source and candidate evidence before recording a page decision.</p>
    </div>
  </header>

  <main id="review-main" class="shell" tabindex="-1">
    <section class="panel" aria-labelledby="connection-heading">
      <h2 id="connection-heading">Open a review job</h2>
      <form id="connection-form" class="connection-grid">
        <div class="field">
          <label for="job-id">Job ID</label>
          <input id="job-id" name="jobId" required autocomplete="off" spellcheck="false" inputmode="text">
        </div>
        <div class="field">
          <label for="actor-id">Reviewer ID</label>
          <input id="actor-id" name="actorId" required autocomplete="off" spellcheck="false" inputmode="text">
        </div>
        <div class="field">
          <label for="reviewer-key">Reviewer API key</label>
          <input id="reviewer-key" name="reviewerKey" type="password" required autocomplete="off" spellcheck="false">
        </div>
        <div class="field field-action">
          <button id="load-review" type="submit">Load review</button>
        </div>
      </form>
      <p id="credential-note" class="hint">The API key is kept only in this page's memory and is not written to browser storage.</p>
      <details class="limits">
        <summary>Review evidence limits</summary>
        <p>This interface visualizes validator evidence only. It does not claim semantic music recognition. Evidence crops are grayscale, and color fidelity is not claimed.</p>
      </details>
    </section>

    <section id="workspace" class="workspace" aria-labelledby="workspace-heading" hidden>
      <div class="panel workspace-header">
        <div>
          <p class="eyebrow">Current job</p>
          <h2 id="workspace-heading">Review evidence</h2>
          <p id="job-state" class="status-text"></p>
        </div>
        <button id="refresh-evidence" type="button">Refresh current evidence</button>
      </div>

      <nav class="panel page-nav" aria-label="Page navigation">
        <button id="previous-page" type="button">Previous page</button>
        <p id="page-status" aria-live="polite"></p>
        <button id="next-page" type="button">Next page</button>
      </nav>

      <section class="panel finding-panel" aria-labelledby="finding-heading">
        <div class="finding-nav" role="group" aria-label="Finding navigation">
          <button id="previous-finding" type="button">Previous finding</button>
          <button id="next-finding" type="button">Next finding</button>
        </div>

        <div class="finding-summary">
          <h3 id="finding-heading" tabindex="-1">Finding</h3>
          <dl>
            <div><dt>Index</dt><dd id="finding-index">-</dd></div>
            <div><dt>Code</dt><dd id="finding-code">-</dd></div>
            <div><dt>Severity</dt><dd id="finding-severity">-</dd></div>
            <div><dt>Region</dt><dd id="finding-region">-</dd></div>
          </dl>
        </div>

        <div class="evidence-grid" aria-label="Source and candidate evidence">
          <figure>
            <figcaption>Source evidence</figcaption>
            <div id="source-view" class="image-stage" tabindex="0" role="group" aria-label="Source evidence image. Use the zoom controls to inspect pixels.">
              <img id="source-image" alt="Source evidence crop for the current finding" hidden>
              <p id="source-empty" class="empty-state">No regional source crop for this finding.</p>
            </div>
          </figure>
          <figure>
            <figcaption>Candidate evidence</figcaption>
            <div id="candidate-view" class="image-stage" tabindex="0" role="group" aria-label="Candidate evidence image. Use the zoom controls to inspect pixels.">
              <img id="candidate-image" alt="Candidate evidence crop for the current finding" hidden>
              <p id="candidate-empty" class="empty-state">No regional candidate crop for this finding.</p>
            </div>
          </figure>
        </div>

        <fieldset class="zoom-controls">
          <legend>Evidence zoom</legend>
          <div class="field compact-field">
            <label for="zoom-mode">Mode</label>
            <select id="zoom-mode">
              <option value="fit_width">Fit width</option>
              <option value="fit_region">Fit region</option>
              <option value="actual_pixels">Actual pixels</option>
            </select>
          </div>
          <div class="field zoom-field">
            <label for="zoom-slider">Zoom</label>
            <input id="zoom-slider" type="range" min="0.25" max="8" step="0.25" value="1">
            <output id="zoom-value" for="zoom-slider">1.00x</output>
          </div>
        </fieldset>

        <div class="field notes-field">
          <label for="review-notes">Review notes</label>
          <textarea id="review-notes" rows="3" maxlength="2000" placeholder="Optional page-specific note"></textarea>
        </div>

        <div class="decision-actions" role="group" aria-label="Page review decision">
          <button id="approve" type="button" data-action="approve">Approve candidate</button>
          <button id="reject" type="button" data-action="reject">Reject candidate</button>
          <button id="reprocess" type="button" data-action="reprocess">Reprocess page</button>
        </div>
        <p id="decision-state" class="hint"></p>
      </section>
    </section>

    <div id="alert-region" class="alert" role="alert" tabindex="-1" hidden></div>
    <div id="status-region" class="sr-status" role="status" aria-live="polite" aria-atomic="true"></div>
    <noscript><p class="alert">JavaScript is required for the local teacher review interface.</p></noscript>
  </main>
</body>
</html>
'''

REVIEW_UI_CSS: Final[bytes] = b''':root {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #111111;
  background: #f4f6f8;
  line-height: 1.5;
  --border: #68737d;
  --panel: #ffffff;
  --muted: #454f59;
  --accent: #005ea8;
  --accent-dark: #003f73;
  --danger: #9f1d20;
  --warning: #6b4f00;
  --focus: #ffbf47;
}

* { box-sizing: border-box; }
body { margin: 0; min-width: 320px; }
button, input, select, textarea { font: inherit; }
button, input, select { min-height: 44px; }
button {
  border: 2px solid #1d2730;
  border-radius: 0.35rem;
  background: #ffffff;
  color: #111111;
  padding: 0.55rem 0.85rem;
  cursor: pointer;
}
button:hover:not(:disabled) { background: #eef4f8; }
button:disabled { cursor: not-allowed; opacity: 0.55; }
button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible, [tabindex="0"]:focus-visible, summary:focus-visible {
  outline: 4px solid var(--focus);
  outline-offset: 3px;
}

.skip-link {
  position: absolute;
  left: 0.75rem;
  top: -6rem;
  z-index: 10;
  background: #ffffff;
  color: #111111;
  padding: 0.75rem 1rem;
  border: 2px solid #111111;
}
.skip-link:focus { top: 0.75rem; }
.site-header { background: #102a43; color: #ffffff; padding: 1.25rem max(1rem, calc((100vw - 1180px) / 2)); }
.site-header h1 { margin: 0.15rem 0 0.35rem; }
.eyebrow { margin: 0; font-size: 0.83rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
.lede { margin: 0; max-width: 70ch; }
.shell { width: min(1180px, calc(100% - 2rem)); margin: 1rem auto 3rem; }
.panel { background: var(--panel); border: 1px solid #c7ced4; border-radius: 0.6rem; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.panel + .panel, .workspace > .panel + .panel { margin-top: 1rem; }
.connection-grid { display: grid; grid-template-columns: 1fr 1fr 1fr auto; gap: 0.9rem; align-items: end; }
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field label { font-weight: 650; }
.field input, .field select, .field textarea, select, textarea { width: 100%; border: 2px solid var(--border); border-radius: 0.35rem; padding: 0.55rem; background: #ffffff; color: #111111; }
.field-action { justify-content: end; }
.hint { color: var(--muted); }
.limits { margin-top: 0.75rem; }
.workspace { margin-top: 1rem; }
.workspace-header { display: flex; justify-content: space-between; align-items: center; gap: 1rem; }
.status-text { margin-bottom: 0; }
.page-nav { display: grid; grid-template-columns: auto 1fr auto; gap: 0.75rem; align-items: center; text-align: center; }
.page-nav p { margin: 0; font-weight: 650; }
.finding-nav { display: flex; gap: 0.75rem; margin-bottom: 1rem; }
.finding-summary dl { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.65rem; }
.finding-summary dl div { border-left: 4px solid #7f8c96; padding-left: 0.65rem; }
dt { font-size: 0.82rem; color: var(--muted); }
dd { margin: 0.15rem 0 0; font-weight: 650; overflow-wrap: anywhere; }
.evidence-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin-top: 1rem; }
figure { margin: 0; min-width: 0; }
figcaption { font-weight: 700; margin-bottom: 0.45rem; }
.image-stage { min-height: 260px; max-height: 70vh; overflow: auto; border: 2px solid #4c5964; background: #e5e9ed; padding: 0.5rem; position: relative; }
.image-stage img { display: block; transform-origin: top left; image-rendering: auto; }
.image-stage.fit-width img { width: 100%; height: auto; max-width: none; }
.image-stage.fit-region img { max-width: 100%; max-height: 62vh; width: auto; height: auto; object-fit: contain; }
.image-stage.actual-pixels img { width: auto; height: auto; max-width: none; }
.empty-state { color: #343d45; margin: 1rem; }
.zoom-controls { display: grid; grid-template-columns: minmax(180px, 0.5fr) 1.5fr; gap: 1rem; margin-top: 1rem; border: 1px solid #8b959e; border-radius: 0.45rem; padding: 0.85rem; }
.zoom-controls legend { font-weight: 700; }
.zoom-field { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 0.65rem; }
.zoom-field input { width: 100%; }
.zoom-field output { min-width: 4.5rem; font-variant-numeric: tabular-nums; }
.notes-field { margin-top: 1rem; }
.decision-actions { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1rem; }
#approve { border-color: #176b3a; }
#reject { border-color: var(--danger); }
#reprocess { border-color: var(--warning); }
.alert { margin-top: 1rem; border: 3px solid var(--danger); background: #fff0f0; color: #551014; padding: 0.85rem; font-weight: 650; }
.sr-status { min-height: 1px; }

@media (max-width: 840px) {
  .connection-grid { grid-template-columns: 1fr 1fr; }
  .field-action { justify-content: stretch; }
  .field-action button { width: 100%; }
  .finding-summary dl { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 700px) {
  .shell { width: min(100% - 1rem, 1180px); }
  .connection-grid, .evidence-grid, .zoom-controls { grid-template-columns: 1fr; }
  .workspace-header { align-items: stretch; flex-direction: column; }
  .page-nav { grid-template-columns: 1fr 1fr; }
  .page-nav p { grid-column: 1 / -1; grid-row: 1; }
  .finding-nav, .decision-actions { display: grid; grid-template-columns: 1fr; }
  .zoom-field { grid-template-columns: 1fr; }
  .image-stage { min-height: 200px; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; animation: none !important; }
}

@media (forced-colors: active) {
  button, input, select, textarea, .panel, .image-stage, .alert { forced-color-adjust: auto; }
  .finding-summary dl div { border-left-color: CanvasText; }
}
'''

REVIEW_UI_JS: Final[bytes] = rb'''"use strict";

const state = {
  jobId: "",
  actorId: "",
  apiKey: "",
  pages: [],
  jobState: "",
  pageIndex: 0,
  bundleResponse: null,
  findingIndex: 0,
  objectUrls: [],
  busy: false,
};

const byId = (id) => document.getElementById(id);
const workspace = byId("workspace");
const alertRegion = byId("alert-region");
const statusRegion = byId("status-region");

class ApiFailure extends Error {
  constructor(message, code = "request_failed", status = 0, details = {}) {
    super(message);
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

function announce(message) {
  statusRegion.textContent = "";
  window.requestAnimationFrame(() => { statusRegion.textContent = message; });
}

function showError(message) {
  alertRegion.textContent = message;
  alertRegion.hidden = false;
  alertRegion.focus();
}

function clearError() {
  alertRegion.hidden = true;
  alertRegion.textContent = "";
}

function requireSafeJobId(value) {
  const trimmed = value.trim();
  if (!trimmed || /[\s\/?#]/.test(trimmed)) {
    throw new ApiFailure("Job ID contains unsupported characters.", "invalid_job_id");
  }
  return trimmed;
}

function authHeaders(json = false) {
  const headers = {
    "X-Api-Key": state.apiKey,
    "X-Actor-Id": state.actorId,
    "X-Request-Id": `review-ui-${Date.now()}-${Math.random().toString(16).slice(2)}`,
  };
  if (json) headers["Content-Type"] = "application/json";
  return headers;
}

async function apiJson(path, options = {}) {
  const response = await fetch(path, {
    method: options.method || "GET",
    headers: authHeaders(Boolean(options.json)),
    body: options.json ? JSON.stringify(options.json) : undefined,
    cache: "no-store",
    credentials: "same-origin",
    redirect: "error",
  });
  let payload = {};
  try { payload = await response.json(); } catch (_) { payload = {}; }
  if (!response.ok) {
    const error = payload.error || {};
    throw new ApiFailure(error.message || `Request failed with status ${response.status}.`, error.code || "request_failed", response.status, error.details || {});
  }
  return payload;
}

async function artifactBlob(artifactId) {
  const response = await fetch(`/api/v1/restoration-jobs/${state.jobId}/artifacts/${artifactId}?purpose=review`, {
    method: "GET",
    headers: authHeaders(false),
    cache: "no-store",
    credentials: "same-origin",
    redirect: "error",
  });
  if (!response.ok) {
    let payload = {};
    try { payload = await response.json(); } catch (_) { payload = {}; }
    const error = payload.error || {};
    throw new ApiFailure(error.message || "Evidence artifact could not be loaded.", error.code || "artifact_load_failed", response.status, error.details || {});
  }
  return response.blob();
}

function revokeEvidenceUrls() {
  for (const url of state.objectUrls) URL.revokeObjectURL(url);
  state.objectUrls = [];
}

function currentPage() {
  return state.pages[state.pageIndex] || null;
}

function currentBundle() {
  return state.bundleResponse ? state.bundleResponse.bundle : null;
}

function setBusy(value) {
  state.busy = value;
  for (const id of ["load-review", "refresh-evidence", "previous-page", "next-page", "previous-finding", "next-finding", "approve", "reject", "reprocess"]) {
    const element = byId(id);
    if (element) element.disabled = value;
  }
  updateNavigationState();
}

function updateNavigationState() {
  const page = currentPage();
  const bundle = currentBundle();
  const findings = bundle && Array.isArray(bundle.findings) ? bundle.findings : [];
  byId("previous-page").disabled = state.busy || state.pageIndex <= 0;
  byId("next-page").disabled = state.busy || state.pageIndex >= state.pages.length - 1;
  byId("previous-finding").disabled = state.busy || state.findingIndex <= 0 || findings.length === 0;
  byId("next-finding").disabled = state.busy || state.findingIndex >= findings.length - 1 || findings.length === 0;
  const decided = Boolean(page && page.reviewDecision);
  for (const id of ["approve", "reject", "reprocess"]) byId(id).disabled = state.busy || !page || !state.bundleResponse || decided;
}

function pageDecisionText(page) {
  if (!page || !page.reviewDecision) return "No page decision recorded yet.";
  return `Recorded decision: ${page.reviewDecision.action}.`;
}

async function refreshPages() {
  const [job, pages] = await Promise.all([
    apiJson(`/api/v1/restoration-jobs/${state.jobId}`),
    apiJson(`/api/v1/restoration-jobs/${state.jobId}/pages`),
  ]);
  state.jobState = job.state || "unknown";
  state.pages = Array.isArray(pages.pages) ? pages.pages : [];
  byId("job-state").textContent = `Job state: ${state.jobState}.`;
  if (!state.pages.length) throw new ApiFailure("This job has no reviewable pages.", "no_pages");
  if (state.pageIndex >= state.pages.length) state.pageIndex = state.pages.length - 1;
}

async function loadReview(event) {
  event.preventDefault();
  clearError();
  try {
    const jobId = requireSafeJobId(byId("job-id").value);
    const actorId = byId("actor-id").value.trim();
    const apiKey = byId("reviewer-key").value;
    if (!actorId || !apiKey) throw new ApiFailure("Reviewer ID and API key are required.", "missing_credentials");
    state.jobId = jobId;
    state.actorId = actorId;
    state.apiKey = apiKey;
    byId("reviewer-key").value = "";
    state.pageIndex = 0;
    setBusy(true);
    await refreshPages();
    workspace.hidden = false;
    await loadPage(0);
    announce(`Loaded ${state.pages.length} review page${state.pages.length === 1 ? "" : "s"}.`);
    byId("workspace-heading").focus();
  } catch (error) {
    showError(error instanceof ApiFailure ? error.message : "Review could not be loaded safely.");
    workspace.hidden = true;
  } finally {
    setBusy(false);
  }
}

async function loadPage(index) {
  clearError();
  revokeEvidenceUrls();
  state.pageIndex = Math.max(0, Math.min(index, state.pages.length - 1));
  const page = currentPage();
  byId("page-status").textContent = `Page ${page.pageNumber} of ${state.pages.length}`;
  byId("decision-state").textContent = pageDecisionText(page);
  state.bundleResponse = await apiJson(`/api/v1/restoration-jobs/${state.jobId}/pages/${page.pageNumber}/review-bundle`);
  state.findingIndex = 0;
  await renderFinding();
  updateNavigationState();
}

async function movePage(delta) {
  if (state.busy) return;
  setBusy(true);
  try {
    await loadPage(state.pageIndex + delta);
    announce(byId("page-status").textContent);
    byId("finding-heading").focus();
  } catch (error) {
    await handleReviewError(error, "Page evidence could not be loaded.");
  } finally {
    setBusy(false);
  }
}

async function moveFinding(delta) {
  const bundle = currentBundle();
  const findings = bundle && Array.isArray(bundle.findings) ? bundle.findings : [];
  state.findingIndex = Math.max(0, Math.min(state.findingIndex + delta, Math.max(findings.length - 1, 0)));
  await renderFinding();
  announce(`Finding ${findings.length ? state.findingIndex + 1 : 0} of ${findings.length}.`);
  byId("finding-heading").focus();
}

function regionText(finding) {
  if (!finding || !finding.sourceRegion) return "No pixel region supplied";
  const region = finding.sourceRegion;
  return `x ${region.x}, y ${region.y}, width ${region.width}, height ${region.height} source pixels`;
}

async function renderFinding() {
  revokeEvidenceUrls();
  const bundle = currentBundle();
  const findings = bundle && Array.isArray(bundle.findings) ? bundle.findings : [];
  const finding = findings[state.findingIndex] || null;
  byId("finding-index").textContent = finding ? `${state.findingIndex + 1} of ${findings.length}` : `0 of ${findings.length}`;
  byId("finding-code").textContent = finding ? finding.code : "No validator findings";
  byId("finding-severity").textContent = finding ? finding.severity : "Not applicable";
  byId("finding-region").textContent = regionText(finding);
  await renderEvidenceImage("source", finding ? finding.sourceCropArtifactId : null);
  await renderEvidenceImage("candidate", finding ? finding.candidateCropArtifactId : null);
  applyZoom();
  updateNavigationState();
}

async function renderEvidenceImage(kind, artifactId) {
  const image = byId(`${kind}-image`);
  const empty = byId(`${kind}-empty`);
  image.hidden = true;
  image.removeAttribute("src");
  empty.hidden = false;
  if (!artifactId) return;
  const blob = await artifactBlob(artifactId);
  const objectUrl = URL.createObjectURL(blob);
  state.objectUrls.push(objectUrl);
  image.src = objectUrl;
  image.hidden = false;
  empty.hidden = true;
}

function applyZoom() {
  const mode = byId("zoom-mode").value;
  const zoom = Number(byId("zoom-slider").value);
  byId("zoom-value").textContent = `${zoom.toFixed(2)}x`;
  for (const kind of ["source", "candidate"]) {
    const stage = byId(`${kind}-view`);
    const image = byId(`${kind}-image`);
    stage.classList.remove("fit-width", "fit-region", "actual-pixels");
    stage.classList.add(mode.replaceAll("_", "-"));
    image.style.transform = `scale(${zoom})`;
  }
}

async function submitDecision(action) {
  if (state.busy) return;
  const page = currentPage();
  const response = state.bundleResponse;
  if (!page || !response) return;
  clearError();
  setBusy(true);
  try {
    const decision = {
      pageNumber: page.pageNumber,
      action,
      candidateArtifactId: page.currentCandidateArtifactId,
      evidenceBundleArtifactId: response.evidenceBundleArtifactId,
      notes: byId("review-notes").value,
    };
    await apiJson(`/api/v1/restoration-jobs/${state.jobId}/review`, {
      method: "POST",
      json: { reviewerId: state.actorId, decisions: [decision] },
    });
    byId("review-notes").value = "";
    await refreshPages();
    if (action === "reprocess") {
      state.bundleResponse = null;
      revokeEvidenceUrls();
      byId("decision-state").textContent = "Reprocessing requested. Refresh when the new attempt is ready.";
      announce(`Page ${page.pageNumber} was sent for reprocessing.`);
    } else {
      await loadPage(state.pageIndex);
      announce(`Page ${page.pageNumber} decision recorded: ${action}.`);
    }
  } catch (error) {
    await handleReviewError(error, "The review decision was not recorded.");
  } finally {
    setBusy(false);
  }
}

async function recoverStaleEvidence(error) {
  showError("This review screen was stale. Current job and evidence data are being reloaded; no decision was recorded from the stale screen.");
  try {
    await refreshPages();
    await loadPage(state.pageIndex);
    announce("Current review evidence reloaded after stale-screen detection.");
  } catch (_) {
    state.bundleResponse = null;
    updateNavigationState();
  }
  alertRegion.focus();
}

async function handleReviewError(error, fallback) {
  if (error instanceof ApiFailure && ["stale_review_evidence", "review_evidence_not_ready", "candidate_not_current"].includes(error.code)) {
    await recoverStaleEvidence(error);
    return;
  }
  showError(error instanceof ApiFailure ? error.message : fallback);
}

async function refreshEvidence() {
  if (state.busy || !state.jobId) return;
  clearError();
  setBusy(true);
  try {
    await refreshPages();
    await loadPage(state.pageIndex);
    announce("Current review evidence refreshed.");
  } catch (error) {
    await handleReviewError(error, "Current evidence could not be refreshed.");
  } finally {
    setBusy(false);
  }
}

byId("connection-form").addEventListener("submit", loadReview);
byId("previous-page").addEventListener("click", () => movePage(-1));
byId("next-page").addEventListener("click", () => movePage(1));
byId("previous-finding").addEventListener("click", () => moveFinding(-1));
byId("next-finding").addEventListener("click", () => moveFinding(1));
byId("refresh-evidence").addEventListener("click", refreshEvidence);
byId("zoom-mode").addEventListener("change", applyZoom);
byId("zoom-slider").addEventListener("input", applyZoom);
for (const id of ["approve", "reject", "reprocess"]) {
  byId(id).addEventListener("click", () => submitDecision(byId(id).dataset.action));
}
window.addEventListener("beforeunload", revokeEvidenceUrls);
window.addEventListener("keydown", (event) => {
  if (event.altKey && event.key === "ArrowLeft") { event.preventDefault(); moveFinding(-1); }
  if (event.altKey && event.key === "ArrowRight") { event.preventDefault(); moveFinding(1); }
});
applyZoom();
updateNavigationState();
'''


def review_ui_asset(path: str) -> tuple[str, bytes] | None:
    if path == "/review":
        return "text/html; charset=utf-8", REVIEW_UI_HTML
    if path == "/review/styles.css":
        return "text/css; charset=utf-8", REVIEW_UI_CSS
    if path == "/review/app.js":
        return "application/javascript; charset=utf-8", REVIEW_UI_JS
    return None


__all__ = ["UI_VERSION", "REVIEW_UI_HTML", "REVIEW_UI_CSS", "REVIEW_UI_JS", "review_ui_asset"]
