from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage6_s6_08_authorization import (
    EXPECTED_CANONICAL_SHA256,
    Stage6S608AuthorizationError,
    canonical_sha256,
    validate_stage6_s6_08_authorization,
)


class Stage6S608AuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = Path("evidence/stage6/governance/stage6-s6-08-integration-security-regression-authorization.v1.json")
        cls.authorization = json.loads(cls.path.read_text(encoding="utf-8"))

    def test_authorization_is_valid_and_digest_bound(self) -> None:
        validated = validate_stage6_s6_08_authorization(self.authorization)
        self.assertEqual(canonical_sha256(validated), EXPECTED_CANONICAL_SHA256)

    def test_production_deployment_cannot_be_silently_authorized(self) -> None:
        record = deepcopy(self.authorization)
        record["explicitly_not_authorized"]["production_deployment"] = True
        with self.assertRaises(Stage6S608AuthorizationError):
            validate_stage6_s6_08_authorization(record)

    def test_provider_activation_cannot_be_silently_authorized(self) -> None:
        record = deepcopy(self.authorization)
        record["explicitly_not_authorized"]["provider_specific_resource_activation"] = True
        with self.assertRaises(Stage6S608AuthorizationError):
            validate_stage6_s6_08_authorization(record)

    def test_stage7_cannot_be_silently_authorized(self) -> None:
        record = deepcopy(self.authorization)
        record["explicitly_not_authorized"]["stage7_entry"] = True
        with self.assertRaises(Stage6S608AuthorizationError):
            validate_stage6_s6_08_authorization(record)

    def test_entry_main_sha_is_immutable(self) -> None:
        record = deepcopy(self.authorization)
        record["entry_checkpoint"]["main_sha"] = "0" * 40
        with self.assertRaises(Stage6S608AuthorizationError):
            validate_stage6_s6_08_authorization(record)


if __name__ == "__main__":
    unittest.main()
