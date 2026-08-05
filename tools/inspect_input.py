#!/usr/bin/env python3
"""Inspect one PDF, JPEG, or PNG and print deterministic JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.input_inspection import (  # noqa: E402
    DEFAULT_MAX_BYTES,
    InputInspectionError,
    inspect_path,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only inspection for PDF, JPEG, and PNG inputs."
    )
    parser.add_argument("path", type=Path)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()

    try:
        result = inspect_path(args.path, max_bytes=args.max_bytes)
    except InputInspectionError as error:
        print(
            json.dumps(
                error.to_dict(),
                ensure_ascii=False,
                indent=None if args.compact else 2,
                sort_keys=True,
            )
        )
        return 2

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=None if args.compact else 2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
