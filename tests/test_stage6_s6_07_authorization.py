from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage6_s6_07_authorization import (
    EXPECTED_CANONICAL_SHA256,
    Stage6S607AuthorizationError,
    canonical_sha256,
    validate_stage6_s6_07_authorization,
)

ROOT = Path(__file__).resolve().parents[1]
AUTH_PATH = ROOT / "evidence/stage6/governance/stage6-s6-07-synthetic-operational-drills-authorization.v1.json"


class Stage6S607AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.authorization = json.loads(AUTH_PATH.read_text(encoding="utf-8"))

    def test_committed_authorization_is_valid(self):
        validated = validate_stage6_s6_07_authorization(self.authorization)
        self.assertEqual(EXPECTED_CANONICAL_SHA256, canonical_sha256(validated))

    def test_live_resource_creation_cannot_be_silently_authorized(self):
        value = deepcopy(self.authorization)
        value["explicitly_not_authorized"]["live_production_resource_creation"] = True
        with self.assertRaises(Stage6S607AuthorizationError):
            validate_stage6_s6_07_authorization(value)

    def test_production_operational_drills_cannot_be_silently_authorized(self):
        value = deepcopy(self.authorization)
        value["explicitly_not_authorized"]["production_operational_drills"] = True
        with self.assertRaises(Stage6S607AuthorizationError):
            validate_stage6_s6_07_authorization(value)

    def test_production_deployment_cannot_be_silently_authorized(self):
        value = deepcopy(self.authorization)
        value["safety_assertions"]["production_deployment_authorized"] = True
        with self.assertRaises(Stage6S607AuthorizationError):
            validate_stage6_s6_07_authorization(value)

    def test_authorization_digest_detects_mutation(self):
        value = deepcopy(self.authorization)
        value["decision_authority_reference"] += "-mutated"
        with self.assertRaises(Stage6S607AuthorizationError):
            validate_stage6_s6_07_authorization(value)


if __name__ == "__main__":
    unittest.main()
