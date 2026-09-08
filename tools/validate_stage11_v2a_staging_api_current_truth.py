from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage11_v2a_staging_api import validate_staging_api_evidence
from st_score_restore.stage11_v2a_staging_api_current_truth import validate_stage11_v2a_staging_api_current_truth

TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_STAGING_API_CURRENT_TRUTH.json"
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-staging-api-evidence.v1.json"

truth_payload = json.loads(TRUTH.read_text(encoding="utf-8"))
evidence_payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
truth = validate_stage11_v2a_staging_api_current_truth(truth_payload)
evidence = validate_staging_api_evidence(evidence_payload)

assert truth["stagingRequestResponseValidated"] is True
assert evidence["stagingRequestResponseValidated"] is True
assert truth_payload["candidate"]["packageSha256"] == evidence_payload["packageSha256"]
assert truth_payload["execution"]["requestSha256"] == evidence_payload["execution"]["requestSha256"]
assert truth_payload["execution"]["responseSha256"] == evidence_payload["execution"]["responseSha256"]
assert truth_payload["safety"]["networkRouteRegistered"] is False
assert truth_payload["safety"]["existingHttpApiModified"] is False
assert truth["productionInferenceAuthorized"] is False
assert truth["realUserRolloutAuthorized"] is False
assert truth["stage12EntryAuthorized"] is False

print({"truth": truth, "evidence": evidence})
