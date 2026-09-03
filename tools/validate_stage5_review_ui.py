from __future__ import annotations

from pathlib import Path

from st_score_restore.review_ui import REVIEW_UI_CSS, REVIEW_UI_HTML, REVIEW_UI_JS, UI_VERSION

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    html = REVIEW_UI_HTML.decode("utf-8")
    css = REVIEW_UI_CSS.decode("utf-8")
    js = REVIEW_UI_JS.decode("utf-8")
    http_api = (ROOT / "src/st_score_restore/http_api.py").read_text(encoding="utf-8")

    require(UI_VERSION == "1.0.0", "Stage 5 review UI version drifted")
    require('<html lang="en">' in html, "review UI language declaration missing")
    require('class="skip-link"' in html, "review UI skip link missing")
    require('role="alert"' in html, "review UI alert region missing")
    require('role="status"' in html and 'aria-live="polite"' in html, "review UI live status region missing")
    require('min="0.25" max="8" step="0.25"' in html, "review UI zoom bounds drifted")
    require(all(value in html for value in ('value="fit_width"', 'value="fit_region"', 'value="actual_pixels"')), "review UI fit modes drifted")

    ordered = [
        'id="previous-finding"',
        'id="next-finding"',
        'id="source-view"',
        'id="candidate-view"',
        'id="approve"',
        'id="reject"',
        'id="reprocess"',
    ]
    positions = [html.index(value) for value in ordered]
    require(positions == sorted(positions), "review UI keyboard/DOM order drifted")

    require("does not claim semantic music recognition" in html, "semantic-recognition boundary missing")
    require("color fidelity is not claimed" in html, "display-integrity boundary missing")
    require("not written to browser storage" in html, "credential storage boundary missing")

    require(":focus-visible" in css, "visible focus styling missing")
    require("min-height: 44px" in css, "minimum touch target baseline missing")
    require("@media (max-width: 700px)" in css, "responsive mobile layout missing")
    require("@media (prefers-reduced-motion: reduce)" in css, "reduced-motion support missing")
    require("@media (forced-colors: active)" in css, "forced-colors support missing")

    for marker in (
        "evidenceBundleArtifactId",
        "?purpose=review",
        "stale_review_evidence",
        "review_evidence_not_ready",
        "candidate_not_current",
        "URL.revokeObjectURL",
        "credentials: \"same-origin\"",
        "cache: \"no-store\"",
    ):
        require(marker in js, f"review UI safety marker missing: {marker}")
    require("localStorage" not in js and "sessionStorage" not in js, "review UI writes reviewer credentials to browser storage")
    require("training-consent" not in js, "review UI improperly couples review and training consent")
    require("http://" not in js and "https://" not in js, "review UI contains external JavaScript endpoint")

    for marker in (
        "from .review_ui import review_ui_asset",
        "asset = review_ui_asset(path)",
        '"X-Frame-Options": "DENY"',
        '"Referrer-Policy": "no-referrer"',
        "default-src 'none'",
        "connect-src 'self'",
        "frame-ancestors 'none'",
    ):
        require(marker in http_api, f"review UI HTTP hardening marker missing: {marker}")

    print("Stage 5 accessible teacher review UI contract: VALID")
    print("- same-origin static UI route: /review")
    print("- evidence-bound approve/reject/reprocess: present")
    print("- stale-screen fail-closed recovery: present")
    print("- zoom: 0.25x-8.0x with required fit modes")
    print("- responsive/focus/reduced-motion/forced-colors structural baseline: present")
    print("- color fidelity and semantic-recognition claims: explicitly not made")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
