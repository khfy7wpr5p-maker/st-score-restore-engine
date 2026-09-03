from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from st_score_restore.stage5_entry_authorization import (
    Stage5EntryAuthorizationError,
    validate_stage5_entry_authorization,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage5EntryAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authorization = load("evidence/stage5/governance/stage5-entry-authorization.v1.json")
        self.stage4_final = load("evidence/stage4/final-exit/stage4-final-exit-acceptance.v1.json")
        self.stage4_truth = load("docs/live/ST_SCORE_RESTORE_STAGE4_FINAL_EXIT_CURRENT_TRUTH.json")

    def validate(self, raw: dict | None = None) -> dict:
        return validate_stage5_entry_authorization(
            self.authorization if raw is None else raw,
            self.stage4_final,
            self.stage4_truth,
        )

    def test_exact_authorization_is_valid(self) -> None:
        value = self.validate()
        self.assertTrue(value["scope"]["stage5EntryEligible"])
        self.assertTrue(value["scope"]["stage5EntryAuthorized"])
        self.assertFalse(value["scope"]["stage5Started"])
        self.assertFalse(value["scope"]["teacherReviewInterfaceImplementationAuthorized"])

    def test_entry_authorization_cannot_start_stage5(self) -> None:
        raw = deepcopy(self.authorization)
        raw["scope"]["stage5Started"] = True
        with self.assertRaises(Stage5EntryAuthorizationError):
            self.validate(raw)

    def test_entry_authorization_cannot_authorize_implementation(self) -> None:
        raw = deepcopy(self.authorization)
        raw["scope"]["teacherReviewInterfaceImplementationAuthorized"] = True
        with self.assertRaises(Stage5EntryAuthorizationError):
            self.validate(raw)

    def test_stage6_cannot_be_authorized(self) -> None:
        raw = deepcopy(self.authorization)
        raw["safetyBoundaries"]["stage6EntryAuthorized"] = True
        with self.assertRaises(Stage5EntryAuthorizationError):
            self.validate(raw)


if __name__ == "__main__":
    unittest.main()
