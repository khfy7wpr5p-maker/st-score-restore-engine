from __future__ import annotations

import copy
import unittest

from st_score_restore.stage1b_exit_contract import (
    Stage1BExitContractError,
    canonical_portability_digest,
    canonical_security_state_digest,
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
            "validatedPackageDigest": package["packageDigest"],
            "artifactSha256": package["artifactSha256"],
            "custodyRecordId": package["custodyRecordId"],
            "state": package["state"],
            "recordVersion": 9,
            "purposeDecisionRef": package["purposeDecisionRef"],
            "environmentRef": package["environmentRef"],
            "storageClassRef": package["storageClassRef"],
            "retentionPolicyRef": package["retentionPolicyRef"],
            "holdDecisionRef": package["holdDecisionRef"],
            "revocationStatus": package["revocationStatus"],
            "deletionStatus": package["deletionStatus"],
            "auditChainHeadDigest": package["auditChainHeadDigest"],
            "checkpointRef": package["checkpointRef"],
            "checkpointSequence": 9,
            "liveAnchorRef": package["liveAnchorRef"],
            "barrierSequence": 12,
            "barrierDigest": package["barrierDigest"],
            "antiResurrectionHorizon": "2026-09-09T00:00:00Z",
            "tombstoneStatus": "final",
            "pendingBackupReceiptRef": package["pendingBackupReceiptRef"],
            "finalDeletionReceiptRef": package["finalDeletionReceiptRef"],
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
    value["destinationValidation"]["validatedPackageDigest"] = value["portabilityPackage"]["packageDigest"]
    return value


def trusted_live_state(evidence: dict) -> dict:
    destination = evidence["destinationValidation"]
    state = {
        "source": "live_independent",
        "fresh": True,
        "controlDigest": "0" * 64,
        "artifactSha256": destination["artifactSha256"],
        "custodyRecordId": destination["custodyRecordId"],
        "state": destination["state"],
        "recordVersion": destination["recordVersion"],
        "purposeDecisionRef": destination["purposeDecisionRef"],
        "environmentRef": destination["environmentRef"],
        "storageClassRef": destination["storageClassRef"],
        "retentionPolicyRef": destination["retentionPolicyRef"],
        "holdDecisionRef": destination["holdDecisionRef"],
        "revocationStatus": destination["revocationStatus"],
        "deletionStatus": destination["deletionStatus"],
        "auditChainHeadDigest": destination["auditChainHeadDigest"],
        "checkpointRef": destination["checkpointRef"],
        "checkpointSequence": destination["checkpointSequence"],
        "liveAnchorRef": destination["liveAnchorRef"],
        "barrierSequence": destination["barrierSequence"],
        "barrierDigest": destination["barrierDigest"],
        "tombstoneStatus": destination["tombstoneStatus"],
        "antiResurrectionHorizon": destination["antiResurrectionHorizon"],
        "pendingBackupReceiptRef": destination["pendingBackupReceiptRef"],
        "finalDeletionReceiptRef": destination["finalDeletionReceiptRef"],
    }
    state["controlDigest"] = canonical_security_state_digest(state)
    return state


def rollback_candidate(evidence: dict) -> dict:
    trusted = trusted_live_state(evidence)
    return {key: value for key, value in trusted.items() if key not in {"source", "fresh"}}


def redigest_security_state(value: dict) -> dict:
    value["controlDigest"] = canonical_security_state_digest(value)
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

    def test_destination_is_bound_to_package_policy_and_live_evidence(self) -> None:
        mutations = {
            "validatedPackageDigest": "d" * 64,
            "purposeDecisionRef": opaque("policy", "d"),
            "retentionPolicyRef": opaque("policy", "d"),
            "auditChainHeadDigest": "d" * 64,
            "checkpointRef": opaque("checkpoint", "d"),
            "liveAnchorRef": opaque("anchor", "d"),
            "barrierDigest": "d" * 64,
            "pendingBackupReceiptRef": opaque("receipt", "d"),
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

    def test_rollback_requires_independently_authenticated_live_state(self) -> None:
        evidence = exit_evidence()
        evidence["sourceProviderExit"]["complete"] = False
        candidate = rollback_candidate(evidence)
        with self.assertRaisesRegex(Stage1BExitContractError, "independently authenticated"):
            validate_provider_rollback(evidence, candidate)

        trusted = trusted_live_state(evidence)
        trusted["source"] = "snapshot"
        with self.assertRaises(Stage1BExitContractError):
            validate_provider_rollback(evidence, candidate, trusted_live_state=trusted)

    def test_stale_provider_rollback_is_bound_to_every_live_security_control(self) -> None:
        evidence = exit_evidence()
        evidence["sourceProviderExit"]["complete"] = False
        trusted = trusted_live_state(evidence)
        current = rollback_candidate(evidence)
        validate_provider_rollback(evidence, current, trusted_live_state=trusted)

        mutations = {
            "recordVersion": 8,
            "state": "revoked",
            "purposeDecisionRef": opaque("policy", "d"),
            "environmentRef": opaque("policy", "d"),
            "storageClassRef": opaque("policy", "d"),
            "retentionPolicyRef": opaque("policy", "d"),
            "holdDecisionRef": opaque("policy", "d"),
            "revocationStatus": "pending",
            "deletionStatus": "active_boundaries_complete",
            "auditChainHeadDigest": "d" * 64,
            "checkpointRef": opaque("checkpoint", "d"),
            "checkpointSequence": 8,
            "liveAnchorRef": opaque("anchor", "d"),
            "barrierSequence": 11,
            "barrierDigest": "d" * 64,
            "tombstoneStatus": "active",
            "antiResurrectionHorizon": "2026-09-08T23:59:59Z",
            "pendingBackupReceiptRef": opaque("receipt", "d"),
            "finalDeletionReceiptRef": opaque("receipt", "e"),
        }
        for field, stale in mutations.items():
            with self.subTest(field=field):
                candidate = copy.deepcopy(current)
                candidate[field] = stale
                redigest_security_state(candidate)
                with self.assertRaisesRegex(Stage1BExitContractError, "does not match"):
                    validate_provider_rollback(evidence, candidate, trusted_live_state=trusted)

    def test_rollback_candidate_cannot_forge_or_reuse_live_control_digest(self) -> None:
        evidence = exit_evidence()
        evidence["sourceProviderExit"]["complete"] = False
        trusted = trusted_live_state(evidence)
        candidate = rollback_candidate(evidence)

        candidate["auditChainHeadDigest"] = "d" * 64
        with self.assertRaisesRegex(Stage1BExitContractError, "digest"):
            validate_provider_rollback(evidence, candidate, trusted_live_state=trusted)

        candidate = rollback_candidate(evidence)
        candidate["controlDigest"] = "d" * 64
        with self.assertRaisesRegex(Stage1BExitContractError, "digest"):
            validate_provider_rollback(evidence, candidate, trusted_live_state=trusted)

        trusted = trusted_live_state(evidence)
        trusted["controlDigest"] = "d" * 64
        with self.assertRaisesRegex(Stage1BExitContractError, "digest"):
            validate_provider_rollback(evidence, rollback_candidate(evidence), trusted_live_state=trusted)

    def test_completed_source_provider_cannot_become_authoritative_again(self) -> None:
        evidence = exit_evidence()
        with self.assertRaisesRegex(Stage1BExitContractError, "completed source exit"):
            validate_provider_rollback(
                evidence,
                rollback_candidate(evidence),
                trusted_live_state=trusted_live_state(evidence),
            )

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
