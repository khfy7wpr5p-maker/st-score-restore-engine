from __future__ import annotations

import argparse
import json
from pathlib import Path

from st_score_restore.stage11_cameraprimus import build_manifest, write_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Stage 11 CameraPrIMuS paired-restoration manifest")
    parser.add_argument("root", type=Path, help="Mounted TEST/CameraPrIMuS/Corpus directory")
    parser.add_argument("--output", type=Path, required=True, help="Output manifest JSON path")
    parser.add_argument("--rights-approved", action="store_true", help="Mark rights review approved only when documented clearance exists")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_manifest(args.root, rights_status="approved" if args.rights_approved else "review_required")
    write_manifest(manifest, args.output)
    print(json.dumps({
        "pairCount": manifest["pairCount"],
        "rejectedCount": manifest["rejectedCount"],
        "splitCounts": manifest["splitCounts"],
        "rightsStatus": manifest["rightsStatus"],
        "trainingExecutable": manifest["trainingExecutable"],
        "blockingReasonCodes": manifest["blockingReasonCodes"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
