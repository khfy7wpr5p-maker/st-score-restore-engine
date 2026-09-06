from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage9a_entry_authorization import (
    Stage9AEntryAuthorizationError,
    validate_stage9a_entry_authorization,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage9AEntryAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.authorization = load("evidence/stage9a/stage9a-entry-authorization.v1.json")
        self.stage9_truth = load("docs/live/ST_SCORE_RESTORE_STAGE9_FINAL_EXIT_CURRENT_TRUTH.json")

    def validate(self, authorization=None, truth=None):
        return validate_stage9a_entry_authorization(
            authorization or self.authorization,
            truth or self.stage9_truth,
        )

    def test_authorization_passes(self):
        result = self.validate()
        self.assertEqual(result["result"], "PASS")
        self.assertTrue(result["stage9aEntryAuthorized"])
        self.assertFalse(result["modelTrainingAuthorized"])
        self.assertFalse(result["stage10EntryAuthorized"])

    def test_training_cannot_be_silently_authorized(self):
        mutated = copy.deepcopy(self.authorization)
        mutated["scope"]["modelTrainingAuthorized"] = True
        with self.assertRaises(Stage9AEntryAuthorizationError):
            self.validate(mutated)

    def test_stage10_cannot_be_silently_started(self):
        mutated = copy.deepcopy(self.authorization)
        mutated["scope"]["stage10EntryAuthorized"] = True
        with self.assertRaises(Stage9AEntryAuthorizationError):
            self.validate(mutated)

    def test_binding_is_immutable(self):
        mutated = copy.deepcopy(self.authorization)
        mutated["stage9FinalExitBinding"]["stage9FinalMainSha"] = "deadbeef"
        with self.assertRaises(Stage9AEntryAuthorizationError):
            self.validate(mutated)


if __name__ == "__main__":
    unittest.main()
