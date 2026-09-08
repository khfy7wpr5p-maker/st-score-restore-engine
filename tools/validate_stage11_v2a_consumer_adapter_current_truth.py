from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage11_v2a_consumer_adapter import validate_consumer_adapter_evidence
from st_score_restore.stage11_v2a_consumer_adapter_current_truth import (
    validate_stage11_v2a_consumer_adapter_current_truth,
)

TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2A_CONSUMER_ADAPTER_CURRENT_TRUTH.json"
EVIDENCE = ROOT / "evidence" / "stage11" / "v2a" / "v2a-consumer-adapter-evidence.v1.json"

truth_payload = json.loads(TRUTH.read_text(encoding="utf-8"))
evidence_payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
truth = validate_stage11_v2a_consumer_adapter_current_truth(truth_payload)
evidence = validate_consumer_adapter_evidence(evidence_payload)

assert truth["syntheticConsumerIntegrationPassed"] is True
assert evidence["syntheticIntegrationValidated"] is True
assert truth_payload["candidate"]["packageSha256"] == evidence_payload["packageSha256"]
assert truth_payload["candidate"]["packageSizeBytes"] == evidence_payload["packageSizeBytes"]
assert truth_payload["adapter"]["contractId"] == evidence_payload["contractId"]
assert truth_payload["execution"]["repeatMaxAbsDiff"] == evidence_payload["repeatMaxAbsDiff"]
assert truth_payload["execution"]["direct512ParityMaxAbsDiff"] == evidence_payload["direct512ParityMaxAbsDiff"]
assert evidence_payload["heldOutAccessed"] is False
assert evidence_payload["optimizerCreated"] is False
assert evidence_payload["backpropagationExecuted"] is False
assert evidence_payload["weightsMutated"] is False
assert truth["productionInferenceAuthorized"] is False
assert truth["stage12EntryAuthorized"] is False

print({"truth": truth, "evidence": evidence})
