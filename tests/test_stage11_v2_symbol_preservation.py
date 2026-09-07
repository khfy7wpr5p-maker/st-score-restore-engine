import unittest
import numpy as np

from st_score_restore.stage11_v2_symbol_preservation import (
    LossWeights,
    Stage11V2SymbolPreservationError,
    build_patch_plan,
    centered_crop_box,
    composite_loss_numpy,
    development_gate,
    native_bbox_xywh,
    parse_deepscores_native_annotations,
    rasterize_symbol_mask,
    sampling_mix,
    stable_config_sha256,
    validate_evaluation_provenance,
)


class Stage11V2SymbolPreservationTests(unittest.TestCase):
    def native_payload(self):
        return {
            "images": [
                {"id": 1, "filename": "lg-1-aug-a--page-1.png", "ann_ids": ["10", "11"]},
                {"id": 2, "filename": "lg-2-aug-a--page-1.png", "ann_ids": ["12"]},
            ],
            "annotations": {
                "10": {"a_bbox": [10, 20, 18, 30], "cat_id": ["4"]},
                "11": {"a_bbox": [30, 40, 34, 70], "cat_id": ["5"]},
                "12": {"a_bbox": [3, 5, 13, 10], "cat_id": ["6"]},
            },
            "categories": {
                "4": {"name": "noteheadBlack"},
                "5": {"name": "stem"},
                "6": {"name": "accidentalSharp"},
            },
        }

    def test_corrected_native_a_bbox_is_ltrb_not_xywh(self):
        self.assertEqual(native_bbox_xywh({"a_bbox": [10, 20, 18, 30]}), (10.0, 20.0, 8.0, 10.0))
        parsed = parse_deepscores_native_annotations(self.native_payload())
        self.assertEqual(parsed["schema"], "deepscores-native-images-list-annotations-dict-ann_ids-a_bbox-ltrb")
        self.assertEqual(len(parsed["records"]), 3)
        self.assertEqual(parsed["records"][0]["bbox"], [10.0, 20.0, 8.0, 10.0])

    def test_parser_fails_closed_on_old_annotations_list_shape(self):
        payload = self.native_payload(); payload["annotations"] = []
        with self.assertRaises(Stage11V2SymbolPreservationError):
            parse_deepscores_native_annotations(payload)

    def test_mask_clips_boxes_and_preserves_symbol_area(self):
        mask = rasterize_symbol_mask(20, 20, [{"bbox": [18, 18, 10, 10]}], pad_px=0)
        self.assertEqual(mask.shape, (20, 20))
        self.assertEqual(float(mask.sum()), 4.0)

    def test_symbol_centered_crop_is_bounded(self):
        self.assertEqual(centered_crop_box(100, 80, [95, 75, 4, 4], patch_size=64), (36, 16, 64, 64))

    def test_sampling_plan_is_deterministic_and_exact_half_symbol_centered(self):
        parsed = parse_deepscores_native_annotations(self.native_payload())
        sizes = {"lg-1-aug-a--page-1.png": (100, 100), "lg-2-aug-a--page-1.png": (100, 100)}
        first = build_patch_plan(sizes, parsed["byImage"], patch_count=20, seed="fixed")
        second = build_patch_plan(sizes, parsed["byImage"], patch_count=20, seed="fixed")
        self.assertEqual(first, second)
        mix = sampling_mix(first)
        self.assertEqual(mix["symbolCentered"], 10)
        self.assertEqual(mix["random"], 10)

    def test_loss_penalizes_erasing_true_symbol_ink(self):
        target = np.ones((8, 8), dtype=np.float32); target[3:5, 3:5] = 0.0
        mask = np.zeros((8, 8), dtype=np.float32); mask[2:6, 2:6] = 1.0
        preserved = target.copy()
        erased = target.copy(); erased[3:5, 3:5] = 1.0
        a = composite_loss_numpy(preserved, target, mask)
        b = composite_loss_numpy(erased, target, mask)
        self.assertEqual(a["ink_recall_penalty"], 0.0)
        self.assertGreater(b["ink_recall_penalty"], 0.9)
        self.assertGreater(b["total"], a["total"])

    def test_weights_and_config_hash_are_stable(self):
        self.assertEqual(sum(LossWeights().as_dict().values()), 1.0)
        config = {"loss": LossWeights().as_dict(), "patch": 512, "symbolFraction": 0.5}
        self.assertEqual(stable_config_sha256(config), stable_config_sha256(dict(reversed(list(config.items())))))

    def test_development_gate_prioritizes_ink_recall(self):
        good = development_gate({"inkRecallDelta": -0.03, "pixelL1ImprovementPercent": 20, "edgeL1ImprovementPercent": 5, "psnrDeltaDb": 0.2})
        bad = development_gate({"inkRecallDelta": -0.10, "pixelL1ImprovementPercent": 60, "edgeL1ImprovementPercent": 20, "psnrDeltaDb": 1.0})
        self.assertTrue(good["eligibleForFrozenHeldOutEvaluation"])
        self.assertFalse(bad["eligibleForFrozenHeldOutEvaluation"])

    def test_evaluation_provenance_rejects_weight_mutation_and_tuning(self):
        evidence = {
            "commitSha": "a" * 40, "datasetMd5": "7237318e381e6e0848ec30eb82decb83",
            "configSha256": "b" * 64, "checkpointSha256": "c" * 64, "device": "CPU",
            "weightsMutated": False, "optimizerCreated": False, "backpropagationExecuted": False,
            "heldOutUsedForTraining": False, "heldOutUsedForTuning": False,
            "modelStateSha256Before": "d" * 64, "modelStateSha256After": "d" * 64,
        }
        self.assertTrue(validate_evaluation_provenance(evidence)["provenanceValid"])
        evidence["weightsMutated"] = True
        with self.assertRaises(Stage11V2SymbolPreservationError):
            validate_evaluation_provenance(evidence)


if __name__ == "__main__":
    unittest.main()
