from __future__ import annotations

import json
import unittest

from st_score_restore.http_api import ApiV1
from st_score_restore.job_api_types import JobApiError

from test_job_api import CLIENT_KEY, REVIEWER_KEY, make_service, page_bundle


class ReviewEvidenceWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.service, self.config, _ = make_service()
        self.api = ApiV1(self.service, self.config)
        created, _ = self.service.create_job(
            [page_bundle()[0]],
            idempotency_key="evidence-workflow-0001",
            actor="client-app",
        )
        self.job_id = created["jobId"]
        self.service.run_pending()
        self.current = self.service.get_job(self.job_id)
        self.page = self.current["pages"][0]
        self.bundle_id = self.page["currentEvidenceBundleArtifactId"]
        self.candidate_id = self.page["currentCandidateArtifactId"]

    def test_bundle_route_and_artifacts_are_reviewer_only(self):
        self.assertIsNotNone(self.bundle_id)
        client = self.api.handle(
            "GET",
            f"/api/v1/restoration-jobs/{self.job_id}/pages/1/review-bundle",
            {"X-Api-Key": CLIENT_KEY},
        )
        self.assertEqual(403, client.status)
        reviewer = self.api.handle(
            "GET",
            f"/api/v1/restoration-jobs/{self.job_id}/pages/1/review-bundle",
            {"X-Api-Key": REVIEWER_KEY, "X-Actor-Id": "teacher-1"},
        )
        self.assertEqual(200, reviewer.status)
        payload = json.loads(reviewer.body)
        self.assertEqual(
            self.bundle_id,
            payload["evidenceBundleArtifactId"],
        )
        self.assertEqual(
            self.page["currentAttemptId"],
            payload["bundle"]["attemptId"],
        )
        if payload["bundle"]["artifacts"]:
            crop_id = payload["bundle"]["artifacts"][0]["artifactId"]
            denied = self.api.handle(
                "GET",
                f"/api/v1/restoration-jobs/{self.job_id}/artifacts/{crop_id}?purpose=review",
                {"X-Api-Key": CLIENT_KEY},
            )
            self.assertEqual(403, denied.status)
            allowed = self.api.handle(
                "GET",
                f"/api/v1/restoration-jobs/{self.job_id}/artifacts/{crop_id}?purpose=review",
                {
                    "X-Api-Key": REVIEWER_KEY,
                    "X-Actor-Id": "teacher-1",
                },
            )
            self.assertEqual(200, allowed.status)
            self.assertTrue(allowed.body.startswith(b"\x89PNG"))

    def test_api_requires_current_evidence_and_records_binding(self):
        headers = {
            "X-Api-Key": REVIEWER_KEY,
            "X-Actor-Id": "teacher-1",
            "Content-Type": "application/json",
        }
        missing = self.api.handle(
            "POST",
            f"/api/v1/restoration-jobs/{self.job_id}/review",
            headers,
            json.dumps(
                {"decisions": [{"pageNumber": 1, "action": "reject"}]}
            ).encode(),
        )
        self.assertEqual(409, missing.status)
        self.assertEqual(
            "missing_review_evidence",
            json.loads(missing.body)["error"]["code"],
        )

        stale = self.api.handle(
            "POST",
            f"/api/v1/restoration-jobs/{self.job_id}/review",
            headers,
            json.dumps(
                {
                    "decisions": [
                        {
                            "pageNumber": 1,
                            "action": "reject",
                            "evidenceBundleArtifactId": "sha256:" + "0" * 64,
                        }
                    ]
                }
            ).encode(),
        )
        self.assertEqual(409, stale.status)
        self.assertEqual(
            "stale_review_evidence",
            json.loads(stale.body)["error"]["code"],
        )

        valid = self.api.handle(
            "POST",
            f"/api/v1/restoration-jobs/{self.job_id}/review",
            headers,
            json.dumps(
                {
                    "decisions": [
                        {
                            "pageNumber": 1,
                            "action": "reject",
                            "evidenceBundleArtifactId": self.bundle_id,
                        }
                    ]
                }
            ).encode(),
        )
        self.assertEqual(200, valid.status)
        completed = json.loads(valid.body)
        self.assertEqual("COMPLETED", completed["state"])
        self.assertEqual(
            self.bundle_id,
            completed["pages"][0]["reviewDecision"][
                "evidenceBundleArtifactId"
            ],
        )
        audit = self.service.get_audit(self.job_id)["events"]
        review = [
            item
            for item in audit
            if item["eventType"] == "TEACHER_REVIEW_RECORDED"
        ][-1]
        self.assertTrue(review["details"]["reviewEvidenceBound"])
        self.assertEqual(
            self.bundle_id,
            review["details"]["decisions"][0]["evidenceBundleArtifactId"],
        )

    def test_retry_clears_current_pointer_and_preserves_old_artifact(self):
        retried = self.service.review_job(
            self.job_id,
            [
                {
                    "pageNumber": 1,
                    "action": "reprocess",
                    "evidenceBundleArtifactId": self.bundle_id,
                }
            ],
            reviewer_id="teacher-1",
        )
        self.assertEqual("READY_FOR_PROCESSING", retried["state"])
        self.assertIsNone(
            retried["pages"][0]["currentEvidenceBundleArtifactId"]
        )
        metadata, old_bytes = self.service.get_artifact(
            self.job_id,
            self.bundle_id,
            role="reviewer",
            purpose="review",
            actor="teacher-1",
        )
        self.assertEqual("review_evidence_bundle", metadata["role"])
        self.assertTrue(old_bytes.startswith(b"{"))
        self.service.run_pending()
        current = self.service.get_job(self.job_id)
        new_bundle = current["pages"][0]["currentEvidenceBundleArtifactId"]
        self.assertIsNotNone(new_bundle)
        self.assertNotEqual(self.bundle_id, new_bundle)

    def test_expiry_removes_evidence_bytes(self):
        self.service.expire_job(self.job_id)
        with self.assertRaises(JobApiError) as caught:
            self.service.get_artifact(
                self.job_id,
                self.bundle_id,
                role="reviewer",
                purpose="review",
                actor="teacher-1",
            )
        self.assertEqual("artifact_expired", caught.exception.code)

    def test_evidence_role_collision_does_not_hide_original_artifact(self):
        source_id = self.page["sourceArtifactId"]
        with self.service.store.lock:
            job = self.service._job(self.job_id)
            source_data = self.service._artifact_bytes(
                self.service._artifact(self.job_id, source_id)
            )
            self.service._store_artifact(
                job,
                artifact_id=source_id,
                attempt_id=self.page["currentAttemptId"],
                page_number=1,
                role="review_source_crop",
                name="page-1.finding-collision.source.png",
                media_type="image/png",
                data=source_data,
            )
        original_metadata, original_bytes = self.service.get_artifact(
            self.job_id,
            source_id,
            role="client",
            purpose="original",
            actor="client-app",
        )
        self.assertEqual("immutable_source", original_metadata["role"])
        self.assertEqual(source_data, original_bytes)
        evidence_metadata, evidence_bytes = self.service.get_artifact(
            self.job_id,
            source_id,
            role="reviewer",
            purpose="review",
            actor="teacher-1",
        )
        self.assertEqual("review_source_crop", evidence_metadata["role"])
        self.assertEqual(source_data, evidence_bytes)

    def test_invalid_second_bundle_keeps_entire_batch_unchanged(self):
        created, _ = self.service.create_job(
            page_bundle(),
            idempotency_key="evidence-workflow-0002",
            actor="client-app",
        )
        self.service.run_pending()
        current = self.service.get_job(created["jobId"])
        first = current["pages"][0]
        before_audit = len(
            self.service.get_audit(created["jobId"])["events"]
        )
        with self.assertRaises(JobApiError) as caught:
            self.service.review_job(
                created["jobId"],
                [
                    {
                        "pageNumber": 1,
                        "action": "reject",
                        "evidenceBundleArtifactId": first[
                            "currentEvidenceBundleArtifactId"
                        ],
                    },
                    {
                        "pageNumber": 2,
                        "action": "reject",
                        "evidenceBundleArtifactId": "sha256:" + "f" * 64,
                    },
                ],
                reviewer_id="teacher-1",
            )
        self.assertEqual("stale_review_evidence", caught.exception.code)
        unchanged = self.service.get_job(created["jobId"])
        self.assertIsNone(unchanged["pages"][0]["reviewDecision"])
        self.assertIsNone(unchanged["pages"][1]["reviewDecision"])
        self.assertEqual(
            before_audit,
            len(self.service.get_audit(created["jobId"])["events"]),
        )


if __name__ == "__main__":
    unittest.main()
