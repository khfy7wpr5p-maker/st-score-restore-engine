from __future__ import annotations

import unittest

from st_score_restore.docres_optional_candidate import (
    DocResCandidateContractError,
    DocResCandidatePolicy,
    apply_music_safety_handoff,
    request_docres_candidate,
    run_synthetic_docres_candidate_drills,
)


class DocResOptionalCandidateTests(unittest.TestCase):
    def test_normal_request_fails_closed_without_calling_executor(self):
        called = {"count": 0}

        def executor(value: bytes) -> bytes:
            called["count"] += 1
            return value + b"-candidate"

        result = request_docres_candidate(b"source", synthetic_executor=executor)
        self.assertEqual("runtime_blocked", result["status"])
        self.assertEqual("original", result["fallbackRoute"])
        self.assertFalse(result["candidateAvailable"])
        self.assertEqual(0, called["count"])

    def test_synthetic_candidate_has_provenance_and_never_selects_final_output(self):
        result = request_docres_candidate(
            b"source",
            synthetic_executor=lambda value: value + b"-candidate",
            synthetic_only=True,
        )
        self.assertEqual("candidate_ready_for_safety_validation", result["status"])
        self.assertTrue(result["sourceReturnedUnmodified"])
        self.assertEqual(result["sourceArtifactId"], result["candidate"]["derivedFrom"])
        self.assertFalse(result["candidate"]["teacherApproved"])
        self.assertFalse(result["stage9ComparatorSelectionAuthorized"])

    def test_music_safety_pass_only_enters_validated_hold(self):
        candidate = request_docres_candidate(
            b"source",
            synthetic_executor=lambda value: value + b"-candidate",
            synthetic_only=True,
        )
        handoff = apply_music_safety_handoff(candidate, {"verdict": "pass"})
        self.assertEqual("validated_candidate_hold", handoff["route"])
        self.assertTrue(handoff["stage9ComparatorEligible"])
        self.assertFalse(handoff["stage9ComparatorSelectionAuthorized"])
        self.assertFalse(handoff["automaticFinalSelectionAuthorized"])

    def test_reject_review_and_unknown_fail_safe(self):
        candidate = request_docres_candidate(
            b"source",
            synthetic_executor=lambda value: value + b"-candidate",
            synthetic_only=True,
        )
        self.assertEqual("original", apply_music_safety_handoff(candidate, {"verdict": "reject"})["route"])
        self.assertEqual("review", apply_music_safety_handoff(candidate, {"verdict": "review_required"})["route"])
        self.assertEqual("review", apply_music_safety_handoff(candidate, None)["route"])

    def test_live_capabilities_cannot_be_enabled_inside_stage8_contract(self):
        for kwargs in (
            {"dependency_approved": True},
            {"model_artifact_approved": True},
            {"external_package_installation_authorized": True},
            {"network_fetch_authorized": True},
            {"live_runtime_activation_authorized": True},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(DocResCandidateContractError):
                    DocResCandidatePolicy(**kwargs)

    def test_synthetic_drills_pass_without_live_runtime(self):
        report = run_synthetic_docres_candidate_drills()
        self.assertEqual("PASS", report["result"])
        self.assertTrue(report["syntheticOnly"])
        self.assertFalse(report["docresRuntimeDependencyApproved"])
        self.assertFalse(report["liveDocresRuntimeActivated"])
        self.assertFalse(report["externalPackageInstalled"])
        self.assertFalse(report["modelArtifactDownloaded"])
        self.assertFalse(report["networkFetchPerformed"])
        self.assertFalse(report["stage9ComparatorSelectionPerformed"])


if __name__ == "__main__":
    unittest.main()
