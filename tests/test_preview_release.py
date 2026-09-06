from __future__ import annotations

import unittest

from st_score_restore.preview_release import (
    PreviewReleaseContractError,
    PreviewReleasePolicy,
    build_preview_status,
    build_privacy_safe_event,
    choose_preview_route,
    run_synthetic_preview_drills,
)


class PreviewReleaseTests(unittest.TestCase):
    def test_default_policy_is_fail_closed(self):
        policy = PreviewReleasePolicy()
        self.assertFalse(policy.activation_authorized)
        self.assertEqual(
            {"route": "original", "reasonCode": "preview_activation_not_authorized"},
            choose_preview_route(policy=policy, candidate_available=True, safety_verdict="pass"),
        )

    def test_kill_switch_forces_original_even_for_passing_candidate(self):
        policy = PreviewReleasePolicy(activation_authorized=True, kill_switch_engaged=True)
        self.assertEqual(
            {"route": "original", "reasonCode": "kill_switch_engaged"},
            choose_preview_route(policy=policy, candidate_available=True, safety_verdict="pass"),
        )

    def test_hard_reject_can_never_be_preview_winner(self):
        policy = PreviewReleasePolicy(activation_authorized=True)
        self.assertEqual(
            {"route": "original", "reasonCode": "candidate_hard_rejected"},
            choose_preview_route(policy=policy, candidate_available=True, safety_verdict="reject"),
        )

    def test_unknown_evidence_routes_to_review(self):
        policy = PreviewReleasePolicy(activation_authorized=True)
        self.assertEqual(
            {"route": "review", "reasonCode": "candidate_uncertain"},
            choose_preview_route(policy=policy, candidate_available=True, safety_verdict=None),
        )

    def test_status_distinguishes_original_restored_and_review_required(self):
        original = {
            "pages": [{
                "sourceArtifactId": "sha256:source",
                "currentCandidateArtifactId": "sha256:candidate",
                "selectedArtifactId": "sha256:source",
                "reviewDecision": {"action": "reject"},
                "safetyReport": {"verdict": "review_required"},
            }]
        }
        restored = {
            "pages": [{
                "sourceArtifactId": "sha256:source",
                "currentCandidateArtifactId": "sha256:candidate",
                "selectedArtifactId": "sha256:candidate",
                "reviewDecision": {"action": "approve"},
                "safetyReport": {"verdict": "pass"},
            }]
        }
        review = {
            "pages": [{
                "sourceArtifactId": "sha256:source",
                "currentCandidateArtifactId": "sha256:candidate",
                "selectedArtifactId": None,
                "reviewDecision": None,
                "safetyReport": {"verdict": "review_required"},
            }]
        }
        self.assertEqual("ORIGINAL", build_preview_status(original)["safetyStatus"])
        self.assertEqual("RESTORED", build_preview_status(restored)["safetyStatus"])
        self.assertEqual("REVIEW_REQUIRED", build_preview_status(review)["safetyStatus"])
        self.assertFalse(build_preview_status(restored)["omrCorrectnessClaimed"])
        self.assertFalse(build_preview_status(restored)["musicalTruthClaimed"])

    def test_rejected_candidate_status_fails_safe(self):
        snapshot = {
            "pages": [{
                "sourceArtifactId": "sha256:source",
                "currentCandidateArtifactId": "sha256:candidate",
                "selectedArtifactId": None,
                "reviewDecision": None,
                "safetyReport": {"verdict": "reject"},
            }]
        }
        status = build_preview_status(snapshot)
        self.assertEqual("FAILED_SAFE", status["safetyStatus"])
        self.assertTrue(status["originalFallbackAvailable"])

    def test_observability_contains_only_bounded_safe_fields(self):
        event = build_privacy_safe_event(
            event_type="preview_route_decision",
            job_id="job_private_123",
            route="original",
            reason_code="candidate_hard_rejected",
            latency_bucket="100_500ms",
            failure_class="validation",
        )
        self.assertNotIn("job_private_123", repr(event))
        self.assertTrue(event["jobRef"].startswith("sha256:"))
        self.assertFalse(event["containsArtifactBytes"])
        self.assertFalse(event["containsRawPrivateMetrics"])
        self.assertFalse(event["containsSecrets"])
        self.assertFalse(event["containsFreeText"])

    def test_observability_rejects_free_form_reason_codes(self):
        with self.assertRaises(PreviewReleaseContractError):
            build_privacy_safe_event(
                event_type="preview_route_decision",
                job_id="job-1",
                route="original",
                reason_code="user@example.com secret detail",
            )

    def test_synthetic_release_drills_pass_without_activation(self):
        result = run_synthetic_preview_drills()
        self.assertEqual("PASS", result["result"])
        self.assertTrue(result["syntheticOnly"])
        self.assertFalse(result["previewReleaseActivated"])
        self.assertFalse(result["productionDeploymentPerformed"])
        self.assertEqual("original", result["scenarios"]["kill_switch"]["route"])
        self.assertEqual("original", result["scenarios"]["hard_reject"]["route"])


if __name__ == "__main__":
    unittest.main()
