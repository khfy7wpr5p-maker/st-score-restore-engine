from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage6_s6_04_current_truth import (
    Stage6S604CurrentTruthError,
    summarize_stage6_s6_04_current_truth,
    validate_stage6_s6_04_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage6S604CurrentTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_04_CURRENT_TRUTH.json")
        cls.authorization = load("evidence/stage6/governance/stage6-s6-04-secrets-kms-iam-authorization.v1.json")
        cls.previous = load("docs/live/ST_SCORE_RESTORE_STAGE6_S6_03_CURRENT_TRUTH.json")

    def test_committed_current_truth_is_valid(self):
        validated = validate_stage6_s6_04_current_truth(self.current, self.authorization, self.previous)
        self.assertEqual("ACTIVE_SECRETS_KMS_IAM_IMPLEMENTED_PROVIDER_UNSELECTED", validated["stage6"]["state"])
        summary = summarize_stage6_s6_04_current_truth(self.current, self.authorization, self.previous)
        self.assertTrue(summary["secretsKmsIamContractImplemented"])
        self.assertFalse(summary["providerSpecificSecretsKmsIamActivated"])
        self.assertFalse(summary["liveSecurityResourcesCreated"])

    def test_provider_cannot_be_silently_selected_or_activated(self):
        changed = deepcopy(self.current)
        changed["provider"]["selection_status"] = "SELECTED"
        with self.assertRaises(Stage6S604CurrentTruthError):
            validate_stage6_s6_04_current_truth(changed, self.authorization, self.previous)

        changed = deepcopy(self.current)
        changed["stage6"]["provider_specific_secrets_kms_iam_activated"] = True
        with self.assertRaises(Stage6S604CurrentTruthError):
            validate_stage6_s6_04_current_truth(changed, self.authorization, self.previous)

    def test_live_resources_cannot_be_claimed_created(self):
        for section, key in (
            ("secrets", "live_secret_resource_created"),
            ("kms", "live_key_created"),
            ("iam", "live_iam_roles_or_policies_created"),
        ):
            changed = deepcopy(self.current)
            changed[section][key] = True
            with self.subTest(section=section, key=key), self.assertRaises(Stage6S604CurrentTruthError):
                validate_stage6_s6_04_current_truth(changed, self.authorization, self.previous)

    def test_durable_audit_store_cannot_be_silently_claimed_complete(self):
        changed = deepcopy(self.current)
        changed["audit"]["durable_append_only_tamper_evident_audit_store_implemented"] = True
        with self.assertRaises(Stage6S604CurrentTruthError):
            validate_stage6_s6_04_current_truth(changed, self.authorization, self.previous)

    def test_historical_s6_03_checkpoint_cannot_be_rewritten(self):
        previous = deepcopy(self.previous)
        previous["stage6"]["production_secrets_kms_iam_implementation_authorized"] = True
        with self.assertRaises(Stage6S604CurrentTruthError):
            validate_stage6_s6_04_current_truth(self.current, self.authorization, previous)

    def test_network_and_deployment_remain_unauthorized(self):
        for key in ("production_network_implementation_authorized", "production_deployment_authorized"):
            changed = deepcopy(self.current)
            changed["stage6"][key] = True
            with self.subTest(key=key), self.assertRaises(Stage6S604CurrentTruthError):
                validate_stage6_s6_04_current_truth(changed, self.authorization, self.previous)

    def test_secret_or_key_material_cannot_be_reclassified_as_git_safe(self):
        for key in ("raw_secrets_in_ordinary_git", "cryptographic_key_material_in_ordinary_git"):
            changed = deepcopy(self.current)
            changed["assertions"][key] = True
            with self.subTest(key=key), self.assertRaises(Stage6S604CurrentTruthError):
                validate_stage6_s6_04_current_truth(changed, self.authorization, self.previous)


if __name__ == "__main__":
    unittest.main()
