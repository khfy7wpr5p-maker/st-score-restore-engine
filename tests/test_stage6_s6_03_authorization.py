from __future__ import annotations

from copy import deepcopy
import json
import unittest
from pathlib import Path

from st_score_restore.stage6_s6_03_authorization import (
    AUTHORIZATION_PATH,
    Stage6S603AuthorizationError,
    canonical_sha256,
    validate_stage6_s6_03_authorization,
)


class Stage6S603AuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(Path(AUTHORIZATION_PATH).read_text(encoding="utf-8"))

    def test_committed_authorization_is_valid(self):
        validated = validate_stage6_s6_03_authorization(self.record)
        self.assertEqual("AUTHORIZE_S6_03_IDENTITY_AUTHZ_IMPLEMENTATION", validated["decision"])
        self.assertEqual(
            "f82421eca0ed90defd04609054f47d1972b5327f71a7f35d644ac84c5f57ce39",
            canonical_sha256(validated),
        )

    def test_expanding_scope_without_authorization_fails(self):
        changed = deepcopy(self.record)
        changed["explicitly_not_authorized"]["production_deployment"] = True
        with self.assertRaises(Stage6S603AuthorizationError):
            validate_stage6_s6_03_authorization(changed)

    def test_entry_checkpoint_cannot_move_silently(self):
        changed = deepcopy(self.record)
        changed["entry_checkpoint"]["main_sha"] = "0" * 40
        with self.assertRaises(Stage6S603AuthorizationError):
            validate_stage6_s6_03_authorization(changed)


if __name__ == "__main__":
    unittest.main()
