from __future__ import annotations

from typing import Final

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
  const message = "This review screen was stale. Current job and evidence data were reloaded; no decision was recorded from the stale screen.";
  showError(message);
  try {
    await refreshPages();
    await loadPage(state.pageIndex);
    announce("Current review evidence reloaded after stale-screen detection.");
  } catch (_) {
    state.bundleResponse = null;
    updateNavigationState();
  }
  showError(message);
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

__all__ = ["REVIEW_UI_JS"]
