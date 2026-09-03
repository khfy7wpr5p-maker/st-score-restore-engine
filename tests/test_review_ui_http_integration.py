from __future__ import annotations

import unittest

from st_score_restore.http_api import ApiV1
from st_score_restore.job_api_types import JobApiConfig

CLIENT_KEY = "client-key-0123456789abcdef"
REVIEWER_KEY = "reviewer-key-0123456789abcdef"


class ReviewUiHttpIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = ApiV1(
            None,  # Static Stage 5 assets must not touch the job service.
            JobApiConfig(client_api_key=CLIENT_KEY, reviewer_api_key=REVIEWER_KEY),
        )

    def test_static_assets_are_public_same_origin_and_hardened(self) -> None:
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

    def test_api_remains_authenticated(self) -> None:
        response = self.api.handle("GET", "/api/v1/restoration-jobs/job-1", {})
        self.assertEqual(401, response.status)
        self.assertIn(b"authentication_required", response.body)

    def test_post_to_review_is_not_an_unauthenticated_action_route(self) -> None:
        response = self.api.handle("POST", "/review", {})
        self.assertEqual(401, response.status)


if __name__ == "__main__":
    unittest.main()
