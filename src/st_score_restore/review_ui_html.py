from __future__ import annotations

from typing import Final

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
          <h2 id="workspace-heading" tabindex="-1">Review evidence</h2>
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

__all__ = ["REVIEW_UI_HTML"]
