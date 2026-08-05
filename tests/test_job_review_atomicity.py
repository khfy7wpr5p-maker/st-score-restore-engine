from __future__ import annotations

import unittest

from st_score_restore.job_api_types import JobApiError

from test_job_api import make_service, page_bundle


class JobReviewAtomicityTests(unittest.TestCase):
    def test_invalid_later_page_leaves_entire_review_batch_unchanged(self):
        service, _, _ = make_service()
        created, _ = service.create_job(
            page_bundle(),
            idempotency_key="atomic-review-0001",
            actor="client-app",
        )
        job_id = created["jobId"]
        service.run_pending()
        current = service.get_job(job_id)
        candidate_one = current["pages"][0]["currentCandidateArtifactId"]
        event_count = len(service.get_audit(job_id)["events"])

        with self.assertRaises(JobApiError) as error:
            service.review_job(
                job_id,
                [
                    {
                        "pageNumber": 1,
                        "action": "approve",
                        "candidateArtifactId": candidate_one,
                    },
                    {"pageNumber": 2, "action": "invalid-action"},
                ],
                reviewer_id="teacher-1",
            )

        self.assertEqual("invalid_review_action", error.exception.code)
        unchanged = service.get_job(job_id)
        self.assertTrue(
            all(page["reviewDecision"] is None for page in unchanged["pages"])
        )
        self.assertTrue(
            all(page["selectedArtifactId"] is None for page in unchanged["pages"])
        )
        self.assertEqual(event_count, len(service.get_audit(job_id)["events"]))


if __name__ == "__main__":
    unittest.main()
