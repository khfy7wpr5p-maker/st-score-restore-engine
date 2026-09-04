from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage5_final_exit import validate_stage5_final_exit


ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage5FinalExitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.qa = load("evidence/stage5/qa/stage5-accessibility-display-qa.v1.json")
        self.acceptance = load("evidence/stage5/final-exit/stage5-final-exit-acceptance.v1.json")
        self.stage4 = load("evidence/stage4/final-exit/stage4-final-exit-acceptance.v1.json")
        self.entry = load("evidence/stage5/governance/stage5-entry-authorization.v1.json")
        self.start = load("evidence/stage5/governance/stage5-framework-start-authorization.v1.json")

    def validate(self, qa=None, acceptance=None, stage4=None, entry=None, start=None):
        return validate_stage5_final_exit(
            qa or self.qa,
            acceptance or self.acceptance,
            stage4 or self.stage4,
            entry or self.entry,
            start or self.start,
        )

    def test_accepts_exact_stage5_final_exit(self) -> None:
        summary = self.validate()
        self.assertEqual(summary["stage5State"], "COMPLETE_PASS")
        self.assertTrue(summary["stage5ExitPass"])
        self.assertTrue(summary["stage6EntryEligible"])
        self.assertFalse(summary["stage6EntryAuthorized"])
        self.assertFalse(summary["stage6Started"])
        self.assertFalse(summary["colorManagementValidated"])
        self.assertFalse(summary["colorFidelityCertified"])
        self.assertEqual(summary["qaEvidenceDigest"], "0e7ae71251db637ee9ba99cdcd5e2216fdfd3d655dc5eda23b676ea9ec5699fe")
        self.assertEqual(summary["acceptanceDigest"], "467eaf11c451d114d3ef41afd44c87cf2dce5cb68f89a5d6cfc45a81e1eed9fc")

    def test_rejects_screen_reader_without_real_speech(self) -> None:
        qa = copy.deepcopy(self.qa)
        qa["screenReaderExecution"]["assertions"]["realSpeechOutputObserved"] = False
        with self.assertRaises(ValueError):
            self.validate(qa=qa)

    def test_rejects_color_management_upgrade(self) -> None:
        qa = copy.deepcopy(self.qa)
        qa["boundedDisplayQa"]["contract"]["colorManagementValidated"] = True
        with self.assertRaises(ValueError):
            self.validate(qa=qa)

    def test_rejects_stage6_auto_authorization(self) -> None:
        acceptance = copy.deepcopy(self.acceptance)
        acceptance["stage6EntryAuthorized"] = True
        with self.assertRaises(ValueError):
            self.validate(acceptance=acceptance)

    def test_rejects_qa_digest_tampering(self) -> None:
        qa = copy.deepcopy(self.qa)
        qa["limitations"].append("tampered")
        with self.assertRaises(ValueError):
            self.validate(qa=qa)


if __name__ == "__main__":
    unittest.main()
