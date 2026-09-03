from __future__ import annotations

from typing import Final

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
button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible, [tabindex="0"]:focus-visible, [tabindex="-1"]:focus-visible, summary:focus-visible {
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

__all__ = ["REVIEW_UI_CSS"]
