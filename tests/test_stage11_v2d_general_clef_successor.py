from __future__ import annotations

import unittest

from st_score_restore.stage11_v2d_general_clef_successor import resolve_general_clef_successor


class Stage11V2dGeneralClefSuccessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.five_line = [
            {
                "staff_index": 0,
                "line_rows": [100.0, 110.0, 120.0, 130.0, 140.0],
                "x1": 10.0,
                "x2": 490.0,
            }
        ]
        self.six_line = [
            {
                "staff_index": 0,
                "line_rows": [100.0, 110.0, 120.0, 130.0, 140.0, 150.0],
                "x1": 10.0,
                "x2": 490.0,
            }
        ]

    @staticmethod
    def _candidate(
        bbox=(20.0, 92.0, 45.0, 148.0),
        clef_type="treble",
        presence=0.95,
        type_confidence=0.92,
        provenance="synthetic",
        **extra,
    ):
        return {
            "bbox": list(bbox),
            "clef_type_or_unknown": clef_type,
            "clef_presence_confidence": presence,
            "clef_type_confidence": type_confidence,
            "candidate_provenance": provenance,
            **extra,
        }

    def test_emits_required_stable_evidence_schema(self) -> None:
        result = resolve_general_clef_successor(
            [self._candidate()],
            self.five_line,
            source_width=500,
            source_height=300,
        )

        detection = result["detections"][0]
        self.assertEqual(
            {
                "bbox",
                "staff_index",
                "clef_presence_confidence",
                "clef_type_or_unknown",
                "clef_type_confidence",
                "abstain_reason",
                "candidate_provenance",
                "status",
            },
            set(detection),
        )

    def test_preserves_mid_staff_clef_and_orders_output_deterministically(self) -> None:
        candidates = [
            self._candidate(bbox=(310.0, 92.0, 335.0, 148.0), provenance="mid"),
            self._candidate(bbox=(20.0, 92.0, 45.0, 148.0), provenance="start"),
        ]

        result = resolve_general_clef_successor(
            candidates,
            self.five_line,
            source_width=500,
            source_height=300,
        )

        self.assertEqual(["start", "mid"], [d["candidate_provenance"] for d in result["detections"]])
        self.assertEqual(["ACCEPT_TYPED", "ACCEPT_TYPED"], [d["status"] for d in result["detections"]])

    def test_rejects_out_of_bounds_candidate_without_clipping(self) -> None:
        result = resolve_general_clef_successor(
            [self._candidate(bbox=(-1.0, 92.0, 45.0, 148.0))],
            self.five_line,
            source_width=500,
            source_height=300,
        )

        self.assertEqual([], result["detections"])
        self.assertEqual("INVALID_GEOMETRY", result["abstentions"][0]["reason"])

    def test_tab_requires_six_line_topology(self) -> None:
        result = resolve_general_clef_successor(
            [self._candidate(clef_type="tab")],
            self.five_line,
            source_width=500,
            source_height=300,
        )

        self.assertEqual([], result["detections"])
        self.assertEqual("TOPOLOGY_MISMATCH", result["abstentions"][0]["reason"])

    def test_tab_is_accepted_on_six_line_topology(self) -> None:
        result = resolve_general_clef_successor(
            [self._candidate(bbox=(20.0, 92.0, 60.0, 158.0), clef_type="tab")],
            self.six_line,
            source_width=500,
            source_height=300,
        )

        self.assertEqual(["tab"], [d["clef_type_or_unknown"] for d in result["detections"]])
        self.assertEqual("ACCEPT_TYPED", result["detections"][0]["status"])

    def test_unknown_subtype_preserves_presence_without_forcing_type(self) -> None:
        result = resolve_general_clef_successor(
            [self._candidate(clef_type="unknown", type_confidence=0.0)],
            self.five_line,
            source_width=500,
            source_height=300,
        )

        self.assertEqual(1, len(result["detections"]))
        self.assertEqual("unknown", result["detections"][0]["clef_type_or_unknown"])
        self.assertEqual("ACCEPT_PRESENCE_ONLY", result["detections"][0]["status"])

    def test_possible_c_clef_candidate_is_review_required_without_forcing_soprano(self) -> None:
        result = resolve_general_clef_successor(
            [
                self._candidate(
                    clef_type="unknown",
                    type_confidence=0.0,
                    provenance="source-only:c-clef-review:five-line-c1-compact",
                    review_required_reason="POSSIBLE_C_CLEF",
                )
            ],
            self.five_line,
            source_width=500,
            source_height=300,
        )

        self.assertEqual(1, len(result["detections"]))
        detection = result["detections"][0]
        self.assertEqual("unknown", detection["clef_type_or_unknown"])
        self.assertEqual("REVIEW_REQUIRED", detection["status"])
        self.assertEqual("POSSIBLE_C_CLEF", detection["abstain_reason"])

    def test_duplicate_candidates_collapse_but_distinct_mid_staff_clefs_remain(self) -> None:
        candidates = [
            self._candidate(bbox=(20.0, 92.0, 45.0, 148.0), presence=0.90, provenance="weak"),
            self._candidate(bbox=(21.0, 93.0, 46.0, 149.0), presence=0.97, provenance="strong"),
            self._candidate(bbox=(300.0, 92.0, 325.0, 148.0), presence=0.91, provenance="distinct"),
        ]

        result = resolve_general_clef_successor(
            candidates,
            self.five_line,
            source_width=500,
            source_height=300,
        )

        self.assertEqual(["strong", "distinct"], [d["candidate_provenance"] for d in result["detections"]])
        self.assertEqual(1, len(result["suppressed_duplicates"]))

    def test_conflicting_overlapping_subtypes_become_review_required_not_duplicate(self) -> None:
        result = resolve_general_clef_successor(
            [
                self._candidate(clef_type="treble", presence=0.96, provenance="treble-evidence"),
                self._candidate(
                    bbox=(21.0, 93.0, 46.0, 149.0),
                    clef_type="bass",
                    presence=0.95,
                    provenance="bass-evidence",
                ),
            ],
            self.five_line,
            source_width=500,
            source_height=300,
        )

        self.assertEqual([], result["suppressed_duplicates"])
        self.assertEqual(1, len(result["detections"]))
        self.assertEqual("unknown", result["detections"][0]["clef_type_or_unknown"])
        self.assertEqual("REVIEW_REQUIRED", result["detections"][0]["status"])
        self.assertEqual("MULTI_CLASS_AMBIGUOUS", result["detections"][0]["abstain_reason"])

    def test_p414_collision_preserves_single_localization_and_defers_subtype(self) -> None:
        result = resolve_general_clef_successor(
            [self._candidate(bbox=(20.0, 92.0, 45.0, 148.0), clef_type="soprano")],
            self.five_line,
            source_width=500,
            source_height=300,
            p414_detections=[
                {
                    "bbox": [19.0, 91.0, 46.0, 149.0],
                    "staff_index": 0,
                    "clef_presence_confidence": 0.99,
                }
            ],
        )

        self.assertEqual(1, len(result["detections"]))
        self.assertEqual([19.0, 91.0, 46.0, 149.0], result["detections"][0]["bbox"])
        self.assertEqual("unknown", result["detections"][0]["clef_type_or_unknown"])
        self.assertEqual("REVIEW_REQUIRED", result["detections"][0]["status"])
        self.assertEqual("P4_14_COLLISION", result["detections"][0]["abstain_reason"])

    def test_p414_frozen_staff_index_schema_does_not_cross_collide(self) -> None:
        second_staff = {
            "staff_index": 1,
            "line_rows": [100.0, 110.0, 120.0, 130.0, 140.0],
            "x1": 10.0,
            "x2": 490.0,
        }
        result = resolve_general_clef_successor(
            [self._candidate(clef_type="soprano")],
            [self.five_line[0], second_staff],
            source_width=500,
            source_height=300,
            p414_detections=[
                {
                    "bbox": [19.0, 91.0, 46.0, 149.0],
                    "staffIndex": 1,
                }
            ],
        )

        self.assertEqual(1, len(result["detections"]))
        self.assertEqual("soprano", result["detections"][0]["clef_type_or_unknown"])
        self.assertEqual("ACCEPT_TYPED", result["detections"][0]["status"])
        self.assertIsNone(result["detections"][0]["abstain_reason"])

    def test_non_inference_metadata_cannot_change_output(self) -> None:
        base = self._candidate()
        polluted = self._candidate(
            teacherBoxes=[[1, 2, 3, 4]],
            teacherLabel="bass",
            pageId="page-a",
            filename="secret.pdf",
            sourceFamily="family-a",
        )

        clean_result = resolve_general_clef_successor(
            [base],
            self.five_line,
            source_width=500,
            source_height=300,
        )
        polluted_result = resolve_general_clef_successor(
            [polluted],
            self.five_line,
            source_width=500,
            source_height=300,
        )

        self.assertEqual(clean_result, polluted_result)


if __name__ == "__main__":
    unittest.main()
