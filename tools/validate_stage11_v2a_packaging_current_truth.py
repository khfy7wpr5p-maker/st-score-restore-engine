from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage11_v2a_packaging import validate_candidate_package_evidence
from st_score_restore.stage11_v2a_packaging_current_truth import load_and_validate

truth_path = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_PACKAGING_CURRENT_TRUTH.json"
truth = load_and_validate(truth_path)

evidence_path = ROOT / truth["evidenceRepoPath"]
evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
evidence_result = validate_candidate_package_evidence(evidence)

if evidence_result["packageSha256"] != truth["packageSha256"]:
    raise SystemExit("packaging evidence/current-truth package SHA mismatch")
if int(evidence["package"]["sizeBytes"]) != int(truth["packageSizeBytes"]):
    raise SystemExit("packaging evidence/current-truth package size mismatch")
if evidence.get("repoCommitSha") != "b39b7d56aac5fccb12332d0336070bee80523cef":
    raise SystemExit("packaging evidence source commit mismatch")

print({**truth, "evidenceValidated": True})
