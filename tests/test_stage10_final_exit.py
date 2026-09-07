from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from st_score_restore.stage10_final_exit import Stage10FinalExitError, validate_stage10_final_exit

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage10FinalExitTests(unittest.TestCase):
    def args(self):
        return (
            load("evidence/stage10/final-exit/stage10-final-exit-acceptance.v1.json"),
            load("evidence/stage10/stage10-entry-authorization.v1.json"),
            load("docs/live/ST_SCORE_RESTORE_STAGE9A_FINAL_EXIT_CURRENT_TRUTH.json"),
            load("api/stage10-selector-contract.v1.json"),
        )

    def test_committed_acceptance_passes(self):
        result = validate_stage10_final_exit(*self.args())
        self.assertEqual(result["result"], "PASS")
        self.assertTrue(result["stage10ExitPass"])
        self.assertFalse(result["stage11EntryAuthorized"])

    def test_blocker_mutation_fails(self):
        args = list(self.args())
        args[0] = deepcopy(args[0]); args[0]["blockerCount"] = 1
        with self.assertRaises(Stage10FinalExitError):
            validate_stage10_final_exit(*args)

    def test_live_selector_mutation_fails(self):
        args = list(self.args())
        args[0] = deepcopy(args[0]); args[0]["boundaries"]["liveSelectorActivationAuthorized"] = True
        with self.assertRaises(Stage10FinalExitError):
            validate_stage10_final_exit(*args)

    def test_stage11_authorization_mutation_fails(self):
        args = list(self.args())
        args[0] = deepcopy(args[0]); args[0]["stage11"]["entryAuthorized"] = True
        with self.assertRaises(Stage10FinalExitError):
            validate_stage10_final_exit(*args)

    def test_ci_failure_mutation_fails(self):
        args = list(self.args())
        args[0] = deepcopy(args[0]); args[0]["capabilityCheckpoint"]["postmergeCi"]["stage10Governance"]["result"] = "FAILURE"
        with self.assertRaises(Stage10FinalExitError):
            validate_stage10_final_exit(*args)

    def test_capability_claim_mutation_fails(self):
        args = list(self.args())
        args[0] = deepcopy(args[0]); args[0]["acceptedCapabilities"]["stage9aEvidenceEnforcementComplete"] = False
        with self.assertRaises(Stage10FinalExitError):
            validate_stage10_final_exit(*args)


if __name__ == "__main__":
    unittest.main()
