from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage11_v2c_execution_evidence import validate_barley_repeat_execution
from st_score_restore.stage11_v2c_semantic_preservation import Stage11V2cSemanticPreservationError

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2c" / "v2c-barley-repeat-execution.v1.json"


class Stage11V2cExecutionEvidenceTests(unittest.TestCase):
    def _payload(self) -> dict:
        return json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_exact_barley_repeat_evidence_passes_determinism_only(self) -> None:
        result = validate_barley_repeat_execution(self._payload())
        self.assertEqual("pass", result["status"])
        self.assertEqual(2, result["pageCount"])
        self.assertEqual("PASS_FOR_BARLEY_CANONICAL_RUNTIME_AND_TWO_PAGE_SOURCE", result["determinism"])
        self.assertEqual("NOT_ESTABLISHED", result["semanticPreservation"])
        self.assertFalse(result["productionPromotionAuthorized"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_tampered_source_sha_is_rejected(self) -> None:
        payload = copy.deepcopy(self._payload())
        payload["sourcePdfSha256"] = "0" * 64
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_barley_repeat_execution(payload)

    def test_tampered_package_identity_is_rejected(self) -> None:
        payload = copy.deepcopy(self._payload())
        payload["packageSha256"] = "f" * 64
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_barley_repeat_execution(payload)

    def test_tampered_cpu_profile_is_rejected(self) -> None:
        payload = copy.deepcopy(self._payload())
        payload["runtime"]["intraopThreads"] = 4
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_barley_repeat_execution(payload)

    def test_tampered_repeat_hash_is_rejected(self) -> None:
        payload = copy.deepcopy(self._payload())
        payload["pages"][0]["repeats"][1]["outputSha256"] = "a" * 64
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_barley_repeat_execution(payload)

    def test_tampered_semantic_success_claim_is_rejected(self) -> None:
        payload = copy.deepcopy(self._payload())
        payload["claimBoundary"]["semanticPreservation"] = "PASS"
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_barley_repeat_execution(payload)

    def test_tampered_stage12_authorization_is_rejected(self) -> None:
        payload = copy.deepcopy(self._payload())
        payload["stage12EntryAuthorized"] = True
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_barley_repeat_execution(payload)


if __name__ == "__main__":
    unittest.main()
