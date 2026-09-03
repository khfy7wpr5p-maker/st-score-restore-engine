from __future__ import annotations

import unittest

from st_score_restore.http_api import ApiV1
from st_score_restore.job_api_types import JobApiConfig
from st_score_restore.review_ui import REVIEW_UI_CSS, REVIEW_UI_HTML, REVIEW_UI_JS, UI_VERSION, review_ui_asset

CLIENT_KEY = "client-key-0123456789abcdef"
REVIEWER_KEY = "reviewer-key-0123456789abcdef"


class ReviewUiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = ApiV1(
            None,  # Static Stage 5 UI assets do not touch the job service.
            JobApiConfig(client_api_key=CLIENT_KEY, reviewer_api_key=REVIEWER_KEY),
        )
        self.html = REVIEW_UI_HTML.decode("utf-8")
        self.css = REVIEW_UI_CSS.decode("utf-8")
        self.js = REVIEW_UI_JS.decode("utf-8")

    def test_static_assets_are_same_origin_and_public_without_api_credentials(self) -> None:
        expectations = {
            "/review": "text/html; charset=utf-8",
            "/review/styles.css": "text/css; charset=utf-8",
            "/review/app.js": "application/javascript; charset=utf-8",
        }
        for path, media_type in expectations.items():
            with self.subTest(path=path):
                response = self.api.handle("GET", path, {})
                self.assertEqual(200, response.status)
                self.assertEqual(media_type, response.headers["Content-Type"])
                self.assertEqual("nosniff", response.headers["X-Content-Type-Options"])
                self.assertEqual("DENY", response.headers["X-Frame-Options"])
                self.assertEqual("no-referrer", response.headers["Referrer-Policy"])
                self.assertIn("no-store", response.headers["Cache-Control"])
                self.assertIn("default-src 'none'", response.headers["Content-Security-Policy"])
                self.assertIn("connect-src 'self'", response.headers["Content-Security-Policy"])
                self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])

    def test_api_still_requires_authentication(self) -> None:
        response = self.api.handle("GET", "/api/v1/restoration-jobs/job-1", {})
        self.assertEqual(401, response.status)
        self.assertIn(b"authentication_required", response.body)

    def test_post_to_review_ui_is_not_an_unauthenticated_action_route(self) -> None:
        response = self.api.handle("POST", "/review", {})
        self.assertEqual(401, response.status)

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
            'data-action="approve"' if False else "submitDecision",
            'action === "reprocess"',
            "credentials: \"same-origin\"",
            "cache: \"no-store\"",
        ):
            self.assertIn(required, self.js)
        self.assertNotIn("localStorage", self.js)
        self.assertNotIn("sessionStorage", self.js)
        self.assertNotIn("training-consent", self.js)
        self.assertNotIn("http://", self.js)
        self.assertNotIn("https://", self.js)

    def test_asset_lookup_is_closed_to_unknown_paths(self) -> None:
        self.assertIsNone(review_ui_asset("/review/unknown"))


if __name__ == "__main__":
    unittest.main()
