from __future__ import annotations

import unittest

from st_score_restore.stage11_v2d_general_clef_successor import resolve_general_clef_successor


class Stage11V2dGeneralClefSuccessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.five_line = [
            {
                "staffIndex": 0,
                "lineRows": [100.0, 110.0, 120.0, 130.0, 140.0],
                "x1": 10.0,
                "x2": 490.0,
            }
        ]
        self.six_line = [
            {
                "staffIndex": 0,
                "lineRows": [100.0, 110.0, 120.0, 130.0, 140.0, 150.0],
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
            "clefType": clef_type,
            "presenceConfidence": presence,
            "typeConfidence": type_confidence,
            "candidateProvenance": provenance,
            **extra,
        }

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

        self.assertEqual(["start", "mid"], [d["candidateProvenance"] for d in result["detections"]])
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

        self.assertEqual(["tab"], [d["clefType"] for d in result["detections"]])
        self.assertEqual("ACCEPT_TYPED", result["detections"][0]["status"])

    def test_unknown_subtype_preserves_presence_without_forcing_type(self) -> None:
        result = resolve_general_clef_successor(
            [self._candidate(clef_type="unknown", type_confidence=0.0)],
            self.five_line,
            source_width=500,
            source_height=300,
        )

        self.assertEqual(1, len(result["detections"]))
        self.assertEqual("unknown", result["detections"][0]["clefType"])
        self.assertEqual("ACCEPT_PRESENCE_ONLY", result["detections"][0]["status"])

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

        self.assertEqual(["strong", "distinct"], [d["candidateProvenance"] for d in result["detections"]])
        self.assertEqual(1, len(result["suppressedDuplicates"]))

    def test_p414_collision_preserves_single_localization_and_defers_subtype(self) -> None:
        result = resolve_general_clef_successor(
            [self._candidate(bbox=(20.0, 92.0, 45.0, 148.0), clef_type="soprano")],
            self.five_line,
            source_width=500,
            source_height=300,
            p414_detections=[
                {
                    "bbox": [19.0, 91.0, 46.0, 149.0],
                    "staffIndex": 0,
                    "presenceConfidence": 0.99,
                }
            ],
        )

        self.assertEqual(1, len(result["detections"]))
        self.assertEqual([19.0, 91.0, 46.0, 149.0], result["detections"][0]["bbox"])
        self.assertEqual("unknown", result["detections"][0]["clefType"])
        self.assertEqual("REVIEW_REQUIRED", result["detections"][0]["status"])
        self.assertEqual("P4_14_COLLISION", result["detections"][0]["abstainReason"])

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
