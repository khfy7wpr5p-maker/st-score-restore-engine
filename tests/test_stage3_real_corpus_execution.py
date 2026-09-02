from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from st_score_restore.stage3_real_corpus_execution import (
    BARLEY_ID,
    BEETHOVEN_ID,
    CHOPIN_ID,
    REQUIRED_RENDERER_BINDING_VERSION,
    Stage3RealCorpusExecutionError,
    execute_stage3_real_corpus_batch,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json").read_text(encoding="utf-8"))
GRANTS = json.loads((ROOT / "evidence" / "stage3" / "governance" / "purpose-grants.v1.json").read_text(encoding="utf-8"))


@dataclass
class _FakeResult:
    item_id: str
    split: str
    rendered: bool = False

    def to_public_dict(self) -> dict:
        return {
            "status": "completed",
            "datasetItemId": self.item_id,
            "split": self.split,
            "pageSummary": {
                "pageCount": 2,
                "renderedPageCount": 1 if self.rendered else 0,
                "reviewRequiredCount": 0,
                "classificationCounts": {"raster_only" if self.rendered else "vector_only": 2},
                "statusCounts": {"rendered_raster_page" if self.rendered else "preserved_vector_page": 2},
                "pageOrderPreserved": True,
                "vectorPagesRasterized": False,
            },
        }

    def restricted_manifest_for_custody(self) -> dict:
        return {
            "pageCount": 2,
            "pages": [
                {"pageIndex": 0},
                {"pageIndex": 1},
            ],
        }

    def restricted_page_bytes_for_custody(self, page_index: int) -> bytes | None:
        if self.rendered and page_index == 0:
            return b"synthetic-private-rendered-page"
        return None


class Stage3RealCorpusExecutionTests(unittest.TestCase):
    def _paths(self, base: Path) -> dict[str, Path]:
        source_dir = base / "sources"
        source_dir.mkdir(parents=True)
        paths = {
            BEETHOVEN_ID: source_dir / "beethoven.pdf",
            BARLEY_ID: source_dir / "barley.pdf",
            CHOPIN_ID: source_dir / "chopin.pdf",
        }
        for item_id, path in paths.items():
            path.write_bytes((item_id + "-synthetic-bytes").encode("utf-8"))
        return paths

    def test_wrong_renderer_version_fails_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            with patch(
                "st_score_restore.stage3_real_corpus_execution.RENDERER_BINDING_VERSION",
                "5.8.0",
            ):
                with self.assertRaises(Stage3RealCorpusExecutionError) as caught:
                    execute_stage3_real_corpus_batch(
                        CATALOG,
                        GRANTS,
                        source_paths=self._paths(base),
                        custody_output_dir=base / "custody",
                        repository_root=base / "repo",
                        execution_date="2026-09-02",
                        repository_main_sha="6ebe160309c562e9841a3c313d5ca507592f1386",
                        post_merge_ci_run_number=238,
                        post_merge_ci_run_id=33620323970,
                    )
        self.assertEqual("renderer_version_mismatch", caught.exception.code)

    def test_custody_output_inside_repository_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            with patch(
                "st_score_restore.stage3_real_corpus_execution.RENDERER_BINDING_VERSION",
                REQUIRED_RENDERER_BINDING_VERSION,
            ):
                with self.assertRaises(Stage3RealCorpusExecutionError) as caught:
                    execute_stage3_real_corpus_batch(
                        CATALOG,
                        GRANTS,
                        source_paths=self._paths(base),
                        custody_output_dir=repo / "private-output",
                        repository_root=repo,
                        execution_date="2026-09-02",
                        repository_main_sha="6ebe160309c562e9841a3c313d5ca507592f1386",
                        post_merge_ci_run_number=238,
                        post_merge_ci_run_id=33620323970,
                    )
        self.assertEqual("custody_output_inside_repository", caught.exception.code)

    def test_real_source_inside_repository_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            paths = self._paths(base)
            inside = repo / "beethoven.pdf"
            inside.write_bytes(b"not-real")
            paths[BEETHOVEN_ID] = inside
            with patch(
                "st_score_restore.stage3_real_corpus_execution.RENDERER_BINDING_VERSION",
                REQUIRED_RENDERER_BINDING_VERSION,
            ):
                with self.assertRaises(Stage3RealCorpusExecutionError) as caught:
                    execute_stage3_real_corpus_batch(
                        CATALOG,
                        GRANTS,
                        source_paths=paths,
                        custody_output_dir=base / "custody",
                        repository_root=repo,
                        execution_date="2026-09-02",
                        repository_main_sha="6ebe160309c562e9841a3c313d5ca507592f1386",
                        post_merge_ci_run_number=238,
                        post_merge_ci_run_id=33620323970,
                    )
        self.assertEqual("real_source_inside_repository", caught.exception.code)

    def test_batch_uses_grants_for_development_and_held_out_gate_for_chopin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            sources = self._paths(base)
            custody = base / "custody"
            dev_results = [
                _FakeResult(BEETHOVEN_ID, "development", rendered=True),
                _FakeResult(BARLEY_ID, "development", rendered=False),
            ]
            held_result = _FakeResult(CHOPIN_ID, "held_out", rendered=True)
            with (
                patch(
                    "st_score_restore.stage3_real_corpus_execution.RENDERER_BINDING_VERSION",
                    REQUIRED_RENDERER_BINDING_VERSION,
                ),
                patch(
                    "st_score_restore.stage3_real_corpus_execution.run_purpose_granted_pdf_pipeline_execution",
                    side_effect=dev_results,
                ) as granted_runner,
                patch(
                    "st_score_restore.stage3_real_corpus_execution.run_authorized_pdf_pipeline_execution",
                    return_value=held_result,
                ) as held_runner,
            ):
                result = execute_stage3_real_corpus_batch(
                    CATALOG,
                    GRANTS,
                    source_paths=sources,
                    custody_output_dir=custody,
                    repository_root=repo,
                    execution_date="2026-09-02",
                    repository_main_sha="6ebe160309c562e9841a3c313d5ca507592f1386",
                    post_merge_ci_run_number=238,
                    post_merge_ci_run_id=33620323970,
                )

            self.assertEqual(2, granted_runner.call_count)
            self.assertEqual("pdf_pipeline_evaluation", granted_runner.call_args_list[0].kwargs["purpose"])
            self.assertEqual("pdf_pipeline_evaluation", granted_runner.call_args_list[1].kwargs["purpose"])
            self.assertEqual(1, held_runner.call_count)
            self.assertEqual("held_out_evaluation", held_runner.call_args.kwargs["purpose"])

            public = result.to_public_dict()
            self.assertEqual("executed", public["status"])
            self.assertEqual(3, public["summary"]["itemCount"])
            self.assertEqual(2, public["summary"]["developmentCount"])
            self.assertEqual(1, public["summary"]["heldOutCount"])
            self.assertEqual(6, public["summary"]["pageCount"])
            self.assertEqual(2, public["summary"]["renderedPageCount"])
            self.assertTrue(public["summary"]["allPageOrderPreserved"])
            self.assertFalse(public["summary"]["anyVectorPagesRasterized"])
            self.assertFalse(public["assertions"]["stage3ExitPass"])
            self.assertFalse(public["assertions"]["stage4EntryAuthorized"])
            self.assertNotIn("custodyManifest", public)
            self.assertNotIn("renderedDerivatives", public)
            self.assertTrue((custody / "private-execution-index.json").is_file())
            self.assertTrue(any(path.suffix == ".png" for path in custody.iterdir()))


if __name__ == "__main__":
    unittest.main()
