from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from st_score_restore.stage3_real_corpus_execution import (
    BARLEY_ID,
    BEETHOVEN_ID,
    CHOPIN_ID,
    Stage3RealCorpusExecutionError,
    execute_stage3_real_corpus_batch,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"
DEFAULT_GRANTS = ROOT / "evidence" / "stage3" / "governance" / "purpose-grants.v1.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute the exact Stage 3 Beethoven/Barley/Chopin real-corpus batch in approved offline custody.",
    )
    parser.add_argument("--beethoven", required=True, type=Path)
    parser.add_argument("--barley", required=True, type=Path)
    parser.add_argument("--chopin", required=True, type=Path)
    parser.add_argument("--custody-output-dir", required=True, type=Path)
    parser.add_argument("--public-output", required=True, type=Path)
    parser.add_argument("--execution-date", required=True)
    parser.add_argument("--repository-main-sha", required=True)
    parser.add_argument("--post-merge-ci-run-number", required=True, type=int)
    parser.add_argument("--post-merge-ci-run-id", required=True, type=int)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--purpose-grants", type=Path, default=DEFAULT_GRANTS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    grants = json.loads(args.purpose_grants.read_text(encoding="utf-8"))
    try:
        result = execute_stage3_real_corpus_batch(
            catalog,
            grants,
            source_paths={
                BEETHOVEN_ID: args.beethoven,
                BARLEY_ID: args.barley,
                CHOPIN_ID: args.chopin,
            },
            custody_output_dir=args.custody_output_dir,
            repository_root=ROOT,
            execution_date=args.execution_date,
            repository_main_sha=args.repository_main_sha,
            post_merge_ci_run_number=args.post_merge_ci_run_number,
            post_merge_ci_run_id=args.post_merge_ci_run_id,
        )
    except Stage3RealCorpusExecutionError as exc:
        print(f"Stage 3 real-corpus execution: BLOCKED ({exc.code})", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        if exc.details:
            print(json.dumps(exc.details, sort_keys=True), file=sys.stderr)
        return 2

    public_output = args.public_output.resolve()
    public_output.parent.mkdir(parents=True, exist_ok=True)
    public_output.write_text(
        json.dumps(result.to_public_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("Stage 3 real-corpus execution: COMPLETE")
    print(f"- public evidence: {public_output}")
    print(f"- custody output: {result.custody_output_dir}")
    print("- Stage 3 exit: not accepted by this command")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
