from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from st_score_restore.stage6_s6_06_authorization import (
    AUTHORIZATION_PATH,
    EXPECTED_CANONICAL_SHA256,
    Stage6S606AuthorizationError,
    canonical_sha256,
    validate_stage6_s6_06_authorization,
)


class Stage6S606AuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads(Path(AUTHORIZATION_PATH).read_text(encoding="utf-8"))

    def test_authorization_is_valid_and_digest_frozen(self) -> None:
        validated = validate_stage6_s6_06_authorization(self.record)
        self.assertEqual(canonical_sha256(validated), EXPECTED_CANONICAL_SHA256)

    def test_live_resource_creation_cannot_be_enabled(self) -> None:
        changed = copy.deepcopy(self.record)
        changed["explicitly_not_authorized"]["live_production_resource_creation"] = True
        with self.assertRaises(Stage6S606AuthorizationError):
            validate_stage6_s6_06_authorization(changed)

    def test_provider_must_remain_unselected(self) -> None:
        changed = copy.deepcopy(self.record)
        changed["safety_assertions"]["provider_remains_unselected"] = False
        with self.assertRaises(Stage6S606AuthorizationError):
            validate_stage6_s6_06_authorization(changed)


if __name__ == "__main__":
    unittest.main()
