#!/usr/bin/env python3
"""Compare a source score image with a restoration candidate and write a safety report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.music_safety_validator import (  # noqa: E402
    MusicSafetyValidationError,
    validate_candidate,
)


def _load_json(path: Path | None) -> dict | None:
    if path is None:
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise MusicSafetyValidationError("invalid_json_object", f"{path.name} must contain a JSON object.")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--report", type=Path, required=True, help="New JSON risk-report path")
    parser.add_argument("--candidate-manifest", type=Path)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    if args.report.exists():
        error = MusicSafetyValidationError("report_output_exists", "The risk report already exists.")
        print(json.dumps(error.to_dict(), indent=2, sort_keys=True), file=sys.stderr)
        return 2
    try:
        report = validate_candidate(
            args.source.read_bytes(),
            args.candidate.read_bytes(),
            source_name=args.source.name,
            candidate_name=args.candidate.name,
            candidate_manifest=_load_json(args.candidate_manifest),
            config=_load_json(args.config),
        )
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except (MusicSafetyValidationError, OSError, json.JSONDecodeError) as error:
        if isinstance(error, MusicSafetyValidationError):
            payload = error.to_dict()
        else:
            payload = MusicSafetyValidationError(
                "validator_cli_error",
                "The source, candidate, manifest, configuration, or report could not be processed.",
                details={"error": str(error)},
            ).to_dict()
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["verdict"] == "pass" else 3 if report["verdict"] == "review_required" else 4


if __name__ == "__main__":
    raise SystemExit(main())
