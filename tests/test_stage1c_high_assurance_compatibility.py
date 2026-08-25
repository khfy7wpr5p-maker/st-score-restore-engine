from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.validate_stage1c_high_assurance_compatibility import (
    C4_ZERO_STATE_PATH,
    DATASET_SCHEMA_PATH,
    DEFAULT_RECORD_PATH,
    HighAssuranceCompatibilityError,
    load_json_object,
    load_schema,
    validate_compatibility,
    validate_record,
    validate_repository_contract,
)
from tools.validate_stage1c_vault_verification import (
    validate_file as validate_c4_file,
    validate_repository_contract as validate_c4_repository_contract,
)


class Stage1CHighAssuranceCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_schema()
        cls.record = load_json_object(DEFAULT_RECORD_PATH)
        cls.c4_schema = validate_c4_repository_contract()
        cls.dataset_schema = load_json_object(DATASET_SCHEMA_PATH)

    def test_repository_contract_is_valid(self) -> None:
        schema, record = validate_repository_contract()
        self.assertEqual(
            schema["properties"]["storageProfile"]["const"],
            "high_assurance_vault",
        )
        self.assertEqual(record["compatibilityState"], "pass")

    def test_record_binds_sensitive_to_high_assurance(self) -> None:
        validate_record(copy.deepcopy(self.record), schema=self.schema)
        validate_compatibility(
            copy.deepcopy(self.record),
            c4_schema=copy.deepcopy(self.c4_schema),
            dataset_schema=copy.deepcopy(self.dataset_schema),
        )

    def test_open_corpus_cannot_reuse_c4_compatibility(self) -> None:
        record = copy.deepcopy(self.record)
        record["eligibilityClass"] = "open_corpus"
        with self.assertRaises(HighAssuranceCompatibilityError):
            validate_record(record, schema=self.schema)

    def test_restricted_corpus_cannot_reuse_c4_compatibility(self) -> None:
        record = copy.deepcopy(self.record)
        record["eligibilityClass"] = "restricted_corpus"
        with self.assertRaises(HighAssuranceCompatibilityError):
            validate_record(record, schema=self.schema)

    def test_profile_cannot_drift_to_managed_standard(self) -> None:
        record = copy.deepcopy(self.record)
        record["storageProfile"] = "managed_standard"
        with self.assertRaises(HighAssuranceCompatibilityError):
            validate_record(record, schema=self.schema)

    def test_profile_cannot_drift_to_managed_restricted(self) -> None:
        record = copy.deepcopy(self.record)
        record["storageProfile"] = "managed_restricted"
        with self.assertRaises(HighAssuranceCompatibilityError):
            validate_record(record, schema=self.schema)

    def test_legacy_storage_binding_cannot_drift(self) -> None:
        record = copy.deepcopy(self.record)
        record["legacyC4StorageClass"] = "high_assurance_vault"
        with self.assertRaises(HighAssuranceCompatibilityError):
            validate_record(record, schema=self.schema)

    def test_c4_schema_storage_binding_drift_is_rejected(self) -> None:
        c4_schema = copy.deepcopy(self.c4_schema)
        c4_schema["properties"]["storageClass"]["const"] = "high_assurance_vault"
        with self.assertRaisesRegex(
            HighAssuranceCompatibilityError, "legacy C4 binding drifted"
        ):
            validate_compatibility(
                copy.deepcopy(self.record),
                c4_schema=c4_schema,
                dataset_schema=copy.deepcopy(self.dataset_schema),
            )

    def test_c4_control_set_drift_is_rejected(self) -> None:
        c4_schema = copy.deepcopy(self.c4_schema)
        c4_schema["properties"]["controls"]["required"] = c4_schema[
            "properties"
        ]["controls"]["required"][:-1]
        with self.assertRaisesRegex(
            HighAssuranceCompatibilityError, "legacy C4 control set drifted"
        ):
            validate_compatibility(
                copy.deepcopy(self.record),
                c4_schema=c4_schema,
                dataset_schema=copy.deepcopy(self.dataset_schema),
            )

    def test_dataset_schema_must_keep_high_assurance_profile(self) -> None:
        dataset_schema = copy.deepcopy(self.dataset_schema)
        storage_values = dataset_schema["$defs"]["item"]["properties"]["retention"][
            "properties"
        ]["storageClass"]["enum"]
        storage_values.remove("high_assurance_vault")
        with self.assertRaisesRegex(
            HighAssuranceCompatibilityError,
            "dataset schema no longer admits high_assurance_vault",
        ):
            validate_compatibility(
                copy.deepcopy(self.record),
                c4_schema=copy.deepcopy(self.c4_schema),
                dataset_schema=dataset_schema,
            )

    def test_dataset_schema_must_keep_sensitive_class(self) -> None:
        dataset_schema = copy.deepcopy(self.dataset_schema)
        dataset_schema["$defs"]["item"]["properties"]["eligibilityClass"][
            "enum"
        ].remove("sensitive_custody")
        with self.assertRaisesRegex(
            HighAssuranceCompatibilityError,
            "dataset schema no longer admits sensitive_custody",
        ):
            validate_compatibility(
                copy.deepcopy(self.record),
                c4_schema=copy.deepcopy(self.c4_schema),
                dataset_schema=dataset_schema,
            )

    def test_all_compatibility_claims_are_fail_closed(self) -> None:
        for claim in self.record["claims"]:
            record = copy.deepcopy(self.record)
            record["claims"][claim] = True
            with self.subTest(claim=claim):
                with self.assertRaises(HighAssuranceCompatibilityError):
                    validate_record(record, schema=self.schema)

    def test_unknown_top_level_field_is_rejected(self) -> None:
        record = copy.deepcopy(self.record)
        record["provider"] = "forbidden"
        with self.assertRaises(HighAssuranceCompatibilityError):
            validate_record(record, schema=self.schema)

    def test_required_c4_control_list_cannot_be_shortened(self) -> None:
        record = copy.deepcopy(self.record)
        record["requiredC4Controls"] = record["requiredC4Controls"][:-1]
        with self.assertRaises(HighAssuranceCompatibilityError):
            validate_record(record, schema=self.schema)

    def test_repository_c4_zero_state_remains_incomplete(self) -> None:
        record = validate_c4_file(C4_ZERO_STATE_PATH, schema=self.c4_schema)
        self.assertEqual(record["overallState"], "incomplete")
        self.assertFalse(record["claims"]["artifactOnboardingAuthorized"])
        self.assertFalse(record["claims"]["stage2Authorized"])

    def test_validation_does_not_mutate_record(self) -> None:
        record = copy.deepcopy(self.record)
        before = json.dumps(record, sort_keys=True)
        validate_record(record, schema=self.schema)
        validate_compatibility(
            record,
            c4_schema=copy.deepcopy(self.c4_schema),
            dataset_schema=copy.deepcopy(self.dataset_schema),
        )
        self.assertEqual(json.dumps(record, sort_keys=True), before)


if __name__ == "__main__":
    unittest.main()
