from __future__ import annotations

import ast
from pathlib import Path
import unittest

from st_score_restore import stage11_v2d_canonical_cpu_restore_gpu_notehead_semantic_rerun as gpu

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "src" / "st_score_restore" / "stage11_v2d_canonical_cpu_restore_gpu_notehead_semantic_rerun.py"
NOTEBOOK = ROOT / "notebooks" / "stage11_v2d_canonical_cpu_restore_gpu_notehead_semantic_rerun.ipynb"


class Stage11V2dCanonicalCpuRestoreGpuNoteheadSemanticRerunTests(unittest.TestCase):
    def test_restore_profile_remains_canonical_cpu(self) -> None:
        self.assertEqual("3.13.5", gpu.cpu.PYTHON)
        self.assertEqual("2.10.0+cpu", gpu.cpu.TORCH)
        self.assertEqual(5, gpu.cpu.INTRA)
        self.assertEqual(1, gpu.cpu.INTER)

    def test_detector_gpu_profile_is_explicit_and_cost_bounded(self) -> None:
        self.assertEqual("1.20.2", gpu.GPU_ORT)
        self.assertEqual("CUDAExecutionProvider", gpu.GPU_PROVIDER)
        self.assertEqual("DEFAULT", gpu.GPU_PROVIDER_OPTIONS["cudnn_conv_algo_search"])
        self.assertEqual("0", gpu.GPU_PROVIDER_OPTIONS["use_tf32"])
        self.assertEqual((16, 8, 4, 2, 1), gpu.GPU_BATCH_CANDIDATES)
        self.assertLessEqual(gpu.MAX_PROJECTED_GPU_SECONDS, 45 * 60)
        self.assertLessEqual(gpu.MAX_TOTAL_WALL_SECONDS, 60 * 60)

    def test_canary_exact_box_comparison_is_order_independent_and_strict(self) -> None:
        self.assertEqual("beethoven-op48-no3-p2", gpu.CANARY_PAGE_ID)
        a = {"boxes": [[2, 2, 4, 4], [1, 1, 3, 3]]}
        b = {"boxes": [[1.0, 1.0, 3.0, 3.0], [2.0, 2.0, 4.0, 4.0]]}
        c = {"boxes": [[1, 1, 3, 3], [2, 2, 5, 4]]}
        self.assertEqual(gpu._canonical_boxes(a), gpu._canonical_boxes(b))
        self.assertNotEqual(gpu._canonical_boxes(a), gpu._canonical_boxes(c))

    def test_runner_is_fail_closed_and_disables_whole_session_fallback(self) -> None:
        text = RUNNER.read_text(encoding="utf-8")
        tree = ast.parse(text)
        self.assertIn("BLOCKED_BY_CPU_GPU_EQUIVALENCE", text)
        self.assertIn("gpuDetectorAdmittedOnlyAfterCpuCanaryEquivalence", text)
        self.assertIn("sess.disable_fallback()", text)
        self.assertIn("TRUE GPU BATCH PROBE PASS", text)
        self.assertIn("cudnn_conv_algo_search", text)
        self.assertIn("Intentionally keep cpu.SCHEMA and cpu.RESTORE_DIR unchanged", text)
        self.assertIn("semanticPreservationEstablished", text)
        self.assertNotIn("optimizer.step", text)
        self.assertNotIn("backward()", text)
        self.assertIsInstance(tree, ast.Module)

    def test_notebook_requires_gpu_and_pins_gpu_ort(self) -> None:
        notebook = NOTEBOOK.read_text(encoding="utf-8")
        self.assertIn("onnxruntime-gpu==1.20.2", notebook)
        self.assertIn("CUDAExecutionProvider", notebook)
        self.assertIn("nvidia-smi", notebook)
        self.assertIn("TRUE GPU BATCH PROBE PASS", notebook)
        self.assertIn("whole-session fallback: disabled", notebook)
        self.assertIn("CPU↔GPU CANARY EQUIVALENCE PASS", notebook)
        self.assertIn("stage11_v2d_canonical_cpu_restore_gpu_notehead_semantic_rerun", notebook)


if __name__ == "__main__":
    unittest.main()
