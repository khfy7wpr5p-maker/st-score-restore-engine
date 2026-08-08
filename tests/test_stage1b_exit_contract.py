from __future__ import annotations

import copy
import unittest

from st_score_restore.stage1b_exit_contract import (
    Stage1BExitContractError,
    canonical_portability_digest,
    validate_exit_schema_contract,
    validate_provider_rollback,
    validate_security_evidence_retention,
    validate_source_provider_exit,
    validate_stage1b_exit_evidence,
)


def opaque(prefix: str, digit: str) -> str:
    return f"{prefix}:opq_{digit * 32}"


def exit_evidence() -> dict:
    classes = ["primary_replica", "replica", "cache", "transient_store", "backup", "archive"]
    package = {
        "packageDigest": "0" * 64,
        "artifactSha256": "a" * 64,
        "byteSize": 19,
        "custodyRecordId": opaque("custody", "1"),
        "state": "tombstoned",
        "recordVersion": 9,
        "purposeDecisionRef": opaque("policy", "2"),
        "environmentRef": opaque("policy", "3"),
        "storageClassRef": opaque("policy", "4"),
        "retentionPolicyRef": opaque("policy", "5"),
        "holdDecisionRef": opaque("policy", "6"),
        "revocationStatus": "effective",
        "deletionStatus": "completed",
        "auditChainHeadDigest": "b" * 64,
        "checkpointRef": opaque("checkpoint", "7"),
        "checkpointSequence": 9,
        "liveAnchorRef": opaque("anchor", "8"),
        "barrierSequence": 12,
        "barrierDigest": "c" * 64,
        "tombstoneStatus": "final",
        "pendingBackupReceiptRef": opaque("receipt", "9"),
        "finalDeletionReceiptRef": opaque("receipt", "a"),
        "restoreSourceEvidence": [
            {
                "sourceClass": name,
                "expiresAt": "2026-09-08T00:00:00Z",
                "disposition": "expired" if name in {"backup", "archive"} else "removed",
                "verified": True,
            }
            for name in classes
        ],
        "antiResurrectionHorizon": "2026-09-09T00:00:00Z",
        "encryptionPolicyRef": opaque("policy", "b"),
        "keyPolicyRef": opaque("policy", "c"),
    }
    package["packageDigest"] = canonical_portability_digest(package)
    return {
        "schemaVersion": "1.0.0",
        "portabilityPackage": package,
        "destinationValidation": {
            "artifactSha256": package["artifactSha256"],
            "custodyRecordId": package["custodyRecordId"],
            "recordVersion": 9,
            "checkpointSequence": 9,
            "barrierSequence": 12,
            "antiResurrectionHorizon": "2026-09-09T00:00:00Z",
            "tombstoneStatus": "final",
            "trustZoneEquivalent": True,
            "denyByDefault": True,
            "auditDurable": True,
            "removalBarrierEquivalent": True,
            "restoreSafeguardsEquivalent": True,
            "deletionEvidenceEquivalent": True,
            "currentPolicyValidated": True,
            "liveControlsValidated": True,
        },
        "sourceProviderExit": {
            "complete": True,
            "boundaries": [
                {
                    "sourceClass": name,
                    "disposition": "expired" if name in {"backup", "archive"} else "removed",
                    "verified": True,
                }
                for name in classes
            ],
            "pendingBackupReceiptRef": package["pendingBackupReceiptRef"],
            "finalDeletionReceiptRef": package["finalDeletionReceiptRef"],
        },
        "receiptRetention": {
            "antiResurrectionHorizon": "2026-09-09T00:00:00Z",
            "establishedMinimumValidThrough": "2026-09-09T00:00:00Z",
            "policyMinimumValidThrough": "2026-10-01T00:00:00Z",
            "pendingReceiptRef": package["pendingBackupReceiptRef"],
            "pendingReceiptValidThrough": "2026-10-01T00:00:00Z",
            "finalReceiptRef": package["finalDeletionReceiptRef"],
            "finalReceiptValidThrough": "2026-10-01T00:00:00Z",
            "barrierValidThrough": "2026-10-01T00:00:00Z",
            "auditValidThrough": "2026-10-01T00:00:00Z",
            "checkpointValidThrough": "2026-10-01T00:00:00Z",
            "tombstoneValidThrough": "2026-10-01T00:00:00Z",
        },
    }


def redigest(value: dict) -> dict:
    value["portabilityPackage"]["packageDigest"] = canonical_portability_digest(value["portabilityPackage"])
    return value


class Stage1BExitContractTests(unittest.TestCase):
    def test_positive_complete_exit_evidence(self) -> None:
        validate_exit_schema_contract()
        validate_stage1b_exit_evidence(exit_evidence())

    def test_provider_specific_or_unknown_fields_are_rejected(self) -> None:
        for field, value in (
            ("providerUrl", "https://provider.invalid/object"),
            ("bucketName", "real-bucket"),
            ("region", "region-1"),
            ("accountId", "123456"),
        ):
            with self.subTest(field=field):
                evidence = exit_evidence()
                evidence["portabilityPackage"][field] = value
                evidence = redigest(evidence)
                with self.assertRaises(Stage1BExitContractError):
                    validate_stage1b_exit_evidence(evidence)

    def test_portability_digest_binds_every_package_field(self) -> None:
        evidence = exit_evidence()
        evidence["portabilityPackage"]["byteSize"] += 1
        with self.assertRaisesRegex(Stage1BExitContractError, "digest"):
            validate_stage1b_exit_evidence(evidence)

    def test_destination_cannot_lower_security_state(self) -> None:
        mutations = {
            "recordVersion": 8,
            "checkpointSequence": 8,
            "barrierSequence": 11,
            "antiResurrectionHorizon": "2026-09-08T23:59:59Z",
            "tombstoneStatus": "active",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                evidence = exit_evidence()
                evidence["destinationValidation"][field] = value
                with self.assertRaises(Stage1BExitContractError):
                    validate_stage1b_exit_evidence(evidence)

    def test_destination_must_validate_equivalent_live_controls(self) -> None:
        controls = (
            "trustZoneEquivalent", "denyByDefault", "auditDurable",
            "removalBarrierEquivalent", "restoreSafeguardsEquivalent",
            "deletionEvidenceEquivalent", "currentPolicyValidated", "liveControlsValidated",
        )
        for field in controls:
            with self.subTest(field=field):
                evidence = exit_evidence()
                evidence["destinationValidation"][field] = False
                with self.assertRaises(Stage1BExitContractError):
                    validate_stage1b_exit_evidence(evidence)

    def test_restore_source_classes_must_be_complete_and_unique(self) -> None:
        evidence = exit_evidence()
        evidence["portabilityPackage"]["restoreSourceEvidence"][-1]["sourceClass"] = "backup"
        evidence = redigest(evidence)
        with self.assertRaisesRegex(Stage1BExitContractError, "exactly once"):
            validate_stage1b_exit_evidence(evidence)

    def test_source_provider_exit_cannot_complete_with_unresolved_boundaries(self) -> None:
        evidence = exit_evidence()
        evidence["sourceProviderExit"]["complete"] = False
        with self.assertRaisesRegex(Stage1BExitContractError, "incomplete"):
            validate_source_provider_exit(evidence)

        evidence = exit_evidence()
        evidence["sourceProviderExit"]["boundaries"][-1]["sourceClass"] = "backup"
        with self.assertRaises(Stage1BExitContractError):
            validate_source_provider_exit(evidence)

    def test_source_provider_exit_requires_both_receipts_bound_to_package(self) -> None:
        for field in ("pendingBackupReceiptRef", "finalDeletionReceiptRef"):
            with self.subTest(field=field):
                evidence = exit_evidence()
                evidence["sourceProviderExit"][field] = opaque("receipt", "f")
                with self.assertRaisesRegex(Stage1BExitContractError, "receipt"):
                    validate_source_provider_exit(evidence)

    def test_pending_and_final_receipts_must_survive_horizon_and_policy_minimum(self) -> None:
        protected = (
            "pendingReceiptValidThrough", "finalReceiptValidThrough",
            "barrierValidThrough", "auditValidThrough",
            "checkpointValidThrough", "tombstoneValidThrough",
        )
        for field in protected:
            with self.subTest(field=field):
                evidence = exit_evidence()
                evidence["receiptRetention"][field] = "2026-09-30T23:59:59Z"
                with self.assertRaisesRegex(Stage1BExitContractError, "expires before"):
                    validate_security_evidence_retention(evidence)

    def test_receipt_retention_cannot_be_detached_from_package(self) -> None:
        evidence = exit_evidence()
        evidence["receiptRetention"]["pendingReceiptRef"] = opaque("receipt", "f")
        with self.assertRaisesRegex(Stage1BExitContractError, "bound"):
            validate_security_evidence_retention(evidence)

        evidence = exit_evidence()
        evidence["receiptRetention"]["antiResurrectionHorizon"] = "2026-09-10T00:00:00Z"
        with self.assertRaisesRegex(Stage1BExitContractError, "horizon"):
            validate_security_evidence_retention(evidence)

    def test_stronger_policy_minimum_extends_receipt_retention(self) -> None:
        evidence = exit_evidence()
        evidence["receiptRetention"]["policyMinimumValidThrough"] = "2026-11-01T00:00:00Z"
        with self.assertRaises(Stage1BExitContractError):
            validate_security_evidence_retention(evidence)
        for field in (
            "pendingReceiptValidThrough", "finalReceiptValidThrough", "barrierValidThrough",
            "auditValidThrough", "checkpointValidThrough", "tombstoneValidThrough",
        ):
            evidence["receiptRetention"][field] = "2026-11-01T00:00:00Z"
        validate_security_evidence_retention(evidence)

    def test_stale_provider_rollback_is_rejected(self) -> None:
        evidence = exit_evidence()
        evidence["sourceProviderExit"]["complete"] = False
        current = {
            "recordVersion": 9,
            "checkpointSequence": 9,
            "barrierSequence": 12,
            "currentWithLiveBarrier": True,
            "currentWithCheckpoint": True,
            "currentWithPolicy": True,
            "currentWithCustodyVersion": True,
        }
        validate_provider_rollback(evidence, current)

        for field, stale in (("recordVersion", 8), ("checkpointSequence", 8), ("barrierSequence", 11)):
            with self.subTest(field=field):
                candidate = dict(current)
                candidate[field] = stale
                with self.assertRaisesRegex(Stage1BExitContractError, "stale"):
                    validate_provider_rollback(evidence, candidate)

        candidate = dict(current)
        candidate["currentWithLiveBarrier"] = False
        with self.assertRaises(Stage1BExitContractError):
            validate_provider_rollback(evidence, candidate)

    def test_completed_source_provider_cannot_become_authoritative_again(self) -> None:
        evidence = exit_evidence()
        candidate = {
            "recordVersion": 9,
            "checkpointSequence": 9,
            "barrierSequence": 12,
            "currentWithLiveBarrier": True,
            "currentWithCheckpoint": True,
            "currentWithPolicy": True,
            "currentWithCustodyVersion": True,
        }
        with self.assertRaisesRegex(Stage1BExitContractError, "completed source exit"):
            validate_provider_rollback(evidence, candidate)

    def test_schema_rejects_missing_receipt_retention_fields(self) -> None:
        evidence = exit_evidence()
        del evidence["receiptRetention"]["finalReceiptValidThrough"]
        with self.assertRaises(Stage1BExitContractError):
            validate_stage1b_exit_evidence(evidence)

    def test_schema_rejects_unverified_source_exit_boundary(self) -> None:
        evidence = exit_evidence()
        evidence["sourceProviderExit"]["boundaries"][0]["verified"] = False
        with self.assertRaises(Stage1BExitContractError):
            validate_stage1b_exit_evidence(evidence)


if __name__ == "__main__":
    unittest.main()
