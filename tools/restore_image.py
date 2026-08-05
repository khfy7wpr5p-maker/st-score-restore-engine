#!/usr/bin/env python3
"""Create one deterministic OpenCV restoration candidate and audit manifest."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.input_inspection import InputInspectionError  # noqa: E402
from st_score_restore.safe_restoration import RestorationError, restore_path  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path, help="New .png, .jpg/.jpeg, or .pdf candidate path")
    parser.add_argument("--audit", type=Path, required=True, help="New JSON audit-manifest path")
    parser.add_argument("--config", type=Path, help="Optional JSON configuration object")
    args = parser.parse_args()
    if args.audit.exists():
        print(json.dumps(RestorationError("audit_output_exists", "The audit output already exists.").to_dict(), indent=2), file=sys.stderr)
        return 2
    try:
        config = json.loads(args.config.read_text(encoding="utf-8")) if args.config else None
        if config is not None and not isinstance(config, dict):
            raise RestorationError("invalid_configuration", "The configuration JSON root must be an object.")
        manifest = restore_path(args.source, args.output, config=config)
        args.audit.parent.mkdir(parents=True, exist_ok=True)
        with args.audit.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except (RestorationError, InputInspectionError) as error:
        print(json.dumps(error.to_dict(), indent=2, sort_keys=True), file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as error:
        wrapped = RestorationError("cli_io_error", "The candidate or configuration could not be processed.", details={"error": str(error)})
        print(json.dumps(wrapped.to_dict(), indent=2, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
