from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage6_s6_04_authorization import (
    EXPECTED_CANONICAL_SHA256,
    Stage6S604AuthorizationError,
    canonical_sha256,
    validate_stage6_s6_04_authorization,
)

ROOT = Path(__file__).resolve().parents[1]


def load() -> dict:
    return json.loads(
        (ROOT / "evidence/stage6/governance/stage6-s6-04-secrets-kms-iam-authorization.v1.json").read_text(
            encoding="utf-8"
        )
    )


class Stage6S604AuthorizationTests(unittest.TestCase):
    def test_committed_authorization_is_valid_and_digest_bound(self):
        record = load()
        validated = validate_stage6_s6_04_authorization(record)
        self.assertEqual(EXPECTED_CANONICAL_SHA256, canonical_sha256(validated))
        self.assertTrue(validated["authorized_scope"]["least_privilege_deny_by_default"])
        self.assertFalse(validated["explicitly_not_authorized"]["live_key_creation"])

    def test_provider_cannot_be_silently_selected(self):
        record = load()
        record["safety_assertions"]["provider_remains_unselected"] = False
        with self.assertRaises(Stage6S604AuthorizationError):
            validate_stage6_s6_04_authorization(record)

    def test_live_resource_creation_cannot_be_broadened(self):
        record = load()
        record["explicitly_not_authorized"]["live_secret_creation"] = True
        with self.assertRaises(Stage6S604AuthorizationError):
            validate_stage6_s6_04_authorization(record)

    def test_entry_main_is_immutable(self):
        record = deepcopy(load())
        record["entry_checkpoint"]["main_sha"] = "0" * 40
        with self.assertRaises(Stage6S604AuthorizationError):
            validate_stage6_s6_04_authorization(record)


if __name__ == "__main__":
    unittest.main()
