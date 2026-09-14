from __future__ import annotations

import ast
from pathlib import Path
import unittest

from st_score_restore.stage11_v2d_canonical_cpu_notehead_semantic_rerun import (
    BATCH,
    DETECTOR_SCHEMA,
    LOGIC,
    MAX_PROJECTED_DETECTOR_SECONDS,
    MAX_TOTAL_WALL_SECONDS,
    PROVIDER,
    STEP,
    _positions,
)

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "src" / "st_score_restore" / "stage11_v2d_canonical_cpu_notehead_semantic_rerun.py"
NOTEBOOK = ROOT / "notebooks" / "stage11_v2d_canonical_cpu_notehead_semantic_rerun.ipynb"


class Stage11V2dCanonicalCpuNoteheadSemanticRerunTests(unittest.TestCase):
    def test_fast_notehead_detector_contract_is_cpu_only_and_cost_bounded(self) -> None:
        self.assertEqual("CPUExecutionProvider", PROVIDER)
        self.assertEqual(256, STEP)
        self.assertEqual(32, BATCH)
        self.assertEqual(90 * 60, MAX_PROJECTED_DETECTOR_SECONDS)
        self.assertEqual(110 * 60, MAX_TOTAL_WALL_SECONDS)
        self.assertEqual("stage11.v2d.notehead-fast-detector-record.v1", DETECTOR_SCHEMA)
        self.assertIn("segnet-notehead-fast-step256", LOGIC)

    def test_tiling_is_unique_and_reaches_last_edge_without_original_duplicate_tail(self) -> None:
        ys = _positions(1698, 288)
        xs = _positions(2164, 288)
        self.assertEqual(len(ys), len(set(ys)))
        self.assertEqual(len(xs), len(set(xs)))
        self.assertEqual(1698 - 288, ys[-1])
        self.assertEqual(2164 - 288, xs[-1])
        self.assertEqual(63, len(ys) * len(xs))

    def test_runner_does_not_use_full_oemer_or_gpu_detector(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertNotIn("CUDAExecutionProvider", source)
        self.assertNotIn("generate_pred", source)
        self.assertNotIn('SEG_REL = "unet_big', source)
        self.assertIn('SEG_REL = "seg_net/model.onnx"', source)
        self.assertIn('"fullOemerPipelineExecuted": False', source)
        self.assertIn('"unetBigExecuted": False', source)
        self.assertIn('"segNetOnly": True', source)
        self.assertIn('"crossHostPixelIdentityToEarlierV2cAssumed": False', source)
        self.assertIn('torch.device("cpu")', source)

    def test_notebook_pins_exact_runner_commit_and_refuses_hours_long_projection(self) -> None:
        text = NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("3.13.5", text)
        self.assertIn("torch==2.10.0", text)
        self.assertIn("onnxruntime==1.20.1", text)
        self.assertIn("d88c11dbcc2688adeb6e2bb8f2e8d737cc4336cd", text)
        self.assertIn("st_score_restore.stage11_v2d_canonical_cpu_notehead_semantic_rerun", text)
        self.assertIn("CPU ONLY", text)
        self.assertIn("CANARY COST BUDGET PASS", text)
        self.assertIn("90 minutes", text)


if __name__ == "__main__":
    unittest.main()
