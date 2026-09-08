from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage11_v2c_full20_execution_evidence import validate_full20_repeat_execution
from st_score_restore.stage11_v2c_semantic_preservation import Stage11V2cSemanticPreservationError

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "stage11" / "v2c" / "v2c-full20-repeat-execution.v1.json"


class Stage11V2cFull20ExecutionEvidenceTests(unittest.TestCase):
    def _payload(self) -> dict:
        return json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_full20_repeat_evidence_passes_determinism_only(self) -> None:
        result = validate_full20_repeat_execution(self._payload())
        self.assertEqual("pass", result["status"])
        self.assertEqual(5, result["sourceFamilyCount"])
        self.assertEqual(20, result["pageCount"])
        self.assertEqual("PASS_FOR_CANONICAL_RUNTIME_AND_FULL_20_PAGE_DEVELOPMENT_CORPUS", result["determinism"])
        self.assertEqual("NOT_ESTABLISHED", result["semanticPreservation"])
        self.assertFalse(result["stage12EntryAuthorized"])

    def test_tampered_source_sha_is_rejected(self) -> None:
        payload = copy.deepcopy(self._payload())
        payload["sourceExactBytes"]["carulli"]["sha256"] = "0" * 64
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_full20_repeat_execution(payload)

    def test_tampered_page_stability_is_rejected(self) -> None:
        payload = copy.deepcopy(self._payload())
        payload["pages"][0]["changedPixelCount"] = 1
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_full20_repeat_execution(payload)

    def test_tampered_family_identity_is_rejected(self) -> None:
        payload = copy.deepcopy(self._payload())
        payload["pages"][7]["sourceFamilyId"] = "source.family.invalid.v1"
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_full20_repeat_execution(payload)

    def test_tampered_semantic_success_claim_is_rejected(self) -> None:
        payload = copy.deepcopy(self._payload())
        payload["aggregate"]["semanticPreservationEstablished"] = True
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_full20_repeat_execution(payload)

    def test_tampered_stage12_claim_is_rejected(self) -> None:
        payload = copy.deepcopy(self._payload())
        payload["claimBoundary"]["stage12EntryAuthorized"] = True
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_full20_repeat_execution(payload)


if __name__ == "__main__":
    unittest.main()
