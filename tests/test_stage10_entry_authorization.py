from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from st_score_restore.stage10_entry_authorization import (
    Stage10EntryAuthorizationError,
    validate_stage10_entry_authorization,
)

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "evidence/stage10/stage10-entry-authorization.v1.json"
TRUTH = ROOT / "docs/live/ST_SCORE_RESTORE_STAGE9A_FINAL_EXIT_CURRENT_TRUTH.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class Stage10EntryAuthorizationTests(unittest.TestCase):
    def test_committed_authorization_passes(self):
        result = validate_stage10_entry_authorization(load(AUTH), load(TRUTH))
        self.assertEqual(result["result"], "PASS")
        self.assertTrue(result["stage10EntryAuthorized"])
        self.assertFalse(result["liveSelectorActivationAuthorized"])
        self.assertFalse(result["stage11EntryAuthorized"])

    def test_live_activation_scope_expansion_fails(self):
        auth = load(AUTH)
        auth["scope"]["liveSelectorActivationAuthorized"] = True
        with self.assertRaises(Stage10EntryAuthorizationError):
            validate_stage10_entry_authorization(auth, load(TRUTH))

    def test_stage11_scope_expansion_fails(self):
        auth = load(AUTH)
        auth["scope"]["stage11EntryAuthorized"] = True
        with self.assertRaises(Stage10EntryAuthorizationError):
            validate_stage10_entry_authorization(auth, load(TRUTH))

    def test_mutated_stage9a_binding_fails(self):
        auth = load(AUTH)
        auth["stage9aFinalExitBinding"]["stage9aFinalMainSha"] = "tampered"
        with self.assertRaises(Stage10EntryAuthorizationError):
            validate_stage10_entry_authorization(auth, load(TRUTH))

    def test_baseline_truth_must_predate_stage10_start(self):
        truth = deepcopy(load(TRUTH))
        truth["stage10"]["started"] = True
        with self.assertRaises(Stage10EntryAuthorizationError):
            validate_stage10_entry_authorization(load(AUTH), truth)


if __name__ == "__main__":
    unittest.main()
