from __future__ import annotations

from pathlib import Path
import unittest

from st_score_restore.review_ui import REVIEW_UI_CSS, REVIEW_UI_HTML, REVIEW_UI_JS, UI_VERSION, review_ui_asset

ROOT = Path(__file__).resolve().parents[1]


class ReviewUiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = REVIEW_UI_HTML.decode("utf-8")
        self.css = REVIEW_UI_CSS.decode("utf-8")
        self.js = REVIEW_UI_JS.decode("utf-8")
        self.http_api = (ROOT / "src/st_score_restore/http_api.py").read_text(encoding="utf-8")

    def test_static_asset_router_is_exact_and_closed(self) -> None:
        expectations = {
            "/review": ("text/html; charset=utf-8", REVIEW_UI_HTML),
            "/review/styles.css": ("text/css; charset=utf-8", REVIEW_UI_CSS),
            "/review/app.js": ("application/javascript; charset=utf-8", REVIEW_UI_JS),
        }
        for path, (media_type, body) in expectations.items():
            with self.subTest(path=path):
                asset = review_ui_asset(path)
                self.assertIsNotNone(asset)
                self.assertEqual(media_type, asset.content_type)
                self.assertEqual(body, asset.body)
        self.assertIsNone(review_ui_asset("/review/unknown"))
        self.assertIsNone(review_ui_asset("/api/v1/restoration-jobs/job-1"))

    def test_http_router_keeps_static_ui_before_auth_and_api_after_auth(self) -> None:
        self.assertIn("asset = review_ui_asset(path)", self.http_api)
        self.assertLess(
            self.http_api.index("asset = review_ui_asset(path)"),
            self.http_api.index("role, actor = self._authenticate(headers)"),
        )
        for marker in (
            '"X-Frame-Options": "DENY"',
            '"Referrer-Policy": "no-referrer"',
            "default-src 'none';",
            "connect-src 'self';",
            "frame-ancestors 'none'",
        ):
            self.assertIn(marker, self.http_api)

    def test_html_carries_required_accessibility_structure_and_order(self) -> None:
        self.assertEqual("1.0.0", UI_VERSION)
        for required in (
            '<html lang="en">',
            'class="skip-link"',
            'label for="job-id"',
            'label for="actor-id"',
            'label for="reviewer-key"',
            'role="alert"',
            'role="status"',
            'aria-live="polite"',
            'id="workspace-heading" tabindex="-1"',
            'id="source-view"',
            'id="candidate-view"',
            'id="zoom-mode"',
            'id="zoom-slider" type="range" min="0.25" max="8" step="0.25"',
            'value="fit_width"',
            'value="fit_region"',
            'value="actual_pixels"',
            'id="approve"',
            'id="reject"',
            'id="reprocess"',
        ):
            self.assertIn(required, self.html)

        ordered = [
            'id="previous-finding"',
            'id="next-finding"',
            'id="source-view"',
            'id="candidate-view"',
            'id="approve"',
            'id="reject"',
            'id="reprocess"',
        ]
        positions = [self.html.index(value) for value in ordered]
        self.assertEqual(positions, sorted(positions))

    def test_ui_discloses_evidence_and_color_boundaries(self) -> None:
        self.assertIn("does not claim semantic music recognition", self.html)
        self.assertIn("Evidence crops are grayscale", self.html)
        self.assertIn("color fidelity is not claimed", self.html)
        self.assertIn("not written to browser storage", self.html)

    def test_css_has_focus_touch_responsive_and_forced_color_support(self) -> None:
        self.assertIn(":focus-visible", self.css)
        self.assertIn('[tabindex="-1"]:focus-visible', self.css)
        self.assertIn("min-height: 44px", self.css)
        self.assertIn("@media (max-width: 700px)", self.css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.css)
        self.assertIn("@media (forced-colors: active)", self.css)
        self.assertIn("overflow: auto", self.css)

    def test_javascript_binds_every_decision_to_current_evidence(self) -> None:
        for required in (
            "evidenceBundleArtifactId",
            "?purpose=review",
            "stale_review_evidence",
            "review_evidence_not_ready",
            "candidate_not_current",
            "URL.revokeObjectURL",
            "submitDecision",
            'action === "reprocess"',
            'credentials: "same-origin"',
            'cache: "no-store"',
        ):
            self.assertIn(required, self.js)
        self.assertNotIn("localStorage", self.js)
        self.assertNotIn("sessionStorage", self.js)
        self.assertNotIn("training-consent", self.js)
        self.assertNotIn("http://", self.js)
        self.assertNotIn("https://", self.js)

    def test_stale_screen_alert_survives_evidence_reload(self) -> None:
        self.assertIn("await loadPage(state.pageIndex);", self.js)
        self.assertIn("showError(message);\n  alertRegion.focus();", self.js)
        self.assertIn("no decision was recorded from the stale screen", self.js)


if __name__ == "__main__":
    unittest.main()
