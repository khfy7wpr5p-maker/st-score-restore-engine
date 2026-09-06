from __future__ import annotations

import json

from st_score_restore.preview_release import run_synthetic_preview_drills


def main() -> int:
    result = run_synthetic_preview_drills()
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    if result["result"] != "PASS":
        raise SystemExit("Stage 7 synthetic preview release drills blocked")
    if result["syntheticOnly"] is not True:
        raise SystemExit("Stage 7 drills were not bounded to synthetic execution")
    if result["previewReleaseActivated"] is not False:
        raise SystemExit("Stage 7 drills unexpectedly activated preview release")
    if result["productionDeploymentPerformed"] is not False:
        raise SystemExit("Stage 7 drills unexpectedly performed production deployment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
