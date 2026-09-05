from __future__ import annotations

from datetime import UTC, datetime, timedelta
import unittest

from st_score_restore.production_secrets_kms_iam import (
    EncryptionContext,
    IamGrant,
    KeyReference,
    KeyStateEvidence,
    KmsEnvelope,
    ProductionEnvelopeCrypto,
    ProductionIamAuthorizer,
    ProductionSecretResolver,
    ProductionSecurityBoundaryError,
    SecretBackendEvidence,
    SecretReference,
    WorkloadIdentity,
)

NOW = datetime(2026, 9, 5, 10, 0, tzinfo=UTC)
TENANT = "tenant:sha256:" + "a" * 64
PRINCIPAL = "workload:sha256:" + "b" * 64


class RecordingAudit:
    def __init__(self, *, fail: bool = False):
        self.events = []
        self.fail = fail

    def append(self, event):
        if self.fail:
            raise RuntimeError("audit unavailable")
        self.events.append(event)


class RotatingSecretBackend:
    def __init__(self):
        self.calls = 0
        self.revoked = False
        self.revocation_checked = True
        self.fail = False

    def resolve(self, reference, identity):
        if self.fail:
            raise RuntimeError("secret backend down")
        self.calls += 1
        version = f"v{self.calls}"
        return SecretBackendEvidence(
            material=f"synthetic-{version}".encode(),
            concrete_version=version,
            expires_at=NOW + timedelta(minutes=5),
            revocation_checked=self.revocation_checked,
            revoked=self.revoked,
            provider_evidence_id=f"secret-evidence-{version}",
        )


class FakeKmsBackend:
    def __init__(self):
        self.state = "ENABLED"
        self.revocation_checked = True
        self.fail_state = False
        self.fail_encrypt = False
        self.fail_decrypt = False

    def key_state(self, key, identity):
        if self.fail_state:
            raise RuntimeError("key state unavailable")
        return KeyStateEvidence(
            concrete_version="k1",
            state=self.state,
            revocation_checked=self.revocation_checked,
            provider_evidence_id="key-state-1",
            checked_at=NOW,
        )

    def encrypt(self, plaintext, key, context, identity):
        if self.fail_encrypt:
            raise RuntimeError("kms encrypt unavailable")
        digest = EncryptionContext(**context).canonical_digest()
        return KmsEnvelope(
            ciphertext=b"cipher:" + plaintext[::-1],
            wrapped_data_key=b"wrapped-synthetic-data-key",
            key_logical_name=key.logical_name,
            key_version="k1",
            algorithm="SYNTHETIC-TEST-ONLY",
            context_digest=digest,
            provider_evidence_id="kms-encrypt-1",
        )

    def decrypt(self, envelope, key, context, identity):
        if self.fail_decrypt:
            raise RuntimeError("kms decrypt unavailable")
        if not envelope.ciphertext.startswith(b"cipher:"):
            raise RuntimeError("invalid synthetic envelope")
        return envelope.ciphertext[len(b"cipher:") :][::-1]


def identity(*, environment="production", duty="runtime", verified=True, expires_at=None):
    return WorkloadIdentity(
        principal_key=PRINCIPAL,
        service="score-restore-api",
        environment=environment,
        duty=duty,
        expires_at=expires_at or NOW + timedelta(minutes=10),
        verification_evidence_id="workload-evidence-1",
        verified=verified,
    )


def secret_ref(environment="production"):
    return SecretReference(
        environment=environment,
        logical_name="score-restore-db",
        purpose="database-credential",
    )


def key_ref(environment="production"):
    return KeyReference(
        environment=environment,
        logical_name="score-artifact-key",
        purpose="artifact-encryption",
    )


def context(environment="production", tenant=TENANT):
    return EncryptionContext(
        environment=environment,
        purpose="artifact-encryption",
        tenant_key=tenant,
        object_key="job_12345",
    )


def authorizer():
    return ProductionIamAuthorizer(
        [
            IamGrant(
                service="score-restore-api",
                environment="production",
                duty="runtime",
                action="secret.read",
                resource_kind="secret",
                resource_name="score-restore-db:database-credential",
            ),
            IamGrant(
                service="score-restore-api",
                environment="production",
                duty="runtime",
                action="kms.encrypt",
                resource_kind="kms-key",
                resource_name="score-artifact-key:artifact-encryption",
            ),
            IamGrant(
                service="score-restore-api",
                environment="production",
                duty="runtime",
                action="kms.decrypt",
                resource_kind="kms-key",
                resource_name="score-artifact-key:artifact-encryption",
            ),
        ],
        clock=lambda: NOW,
    )


class ProductionSecretsKmsIamTests(unittest.TestCase):
    def test_secret_resolution_is_redacted_and_rotation_aware_without_cache(self):
        backend = RotatingSecretBackend()
        audit = RecordingAudit()
        resolver = ProductionSecretResolver(authorizer(), backend, audit, clock=lambda: NOW)

        first = resolver.resolve(secret_ref(), identity())
        second = resolver.resolve(secret_ref(), identity())

        self.assertEqual(b"synthetic-v1", first.reveal())
        self.assertEqual(b"synthetic-v2", second.reveal())
        self.assertEqual("v1", first.concrete_version)
        self.assertEqual("v2", second.concrete_version)
        self.assertNotIn("synthetic-v1", repr(first))
        self.assertEqual("<redacted-secret>", str(first))
        self.assertEqual(2, backend.calls)
        self.assertEqual(["success", "success"], [event.outcome for event in audit.events])

    def test_secret_revocation_uncertainty_and_revoked_secret_fail_closed(self):
        backend = RotatingSecretBackend()
        resolver = ProductionSecretResolver(authorizer(), backend, RecordingAudit(), clock=lambda: NOW)

        backend.revocation_checked = False
        with self.assertRaises(ProductionSecurityBoundaryError) as unknown:
            resolver.resolve(secret_ref(), identity())
        self.assertEqual("secret_revocation_unknown", unknown.exception.code)

        backend.revocation_checked = True
        backend.revoked = True
        with self.assertRaises(ProductionSecurityBoundaryError) as revoked:
            resolver.resolve(secret_ref(), identity())
        self.assertEqual("secret_revoked", revoked.exception.code)

    def test_secret_backend_and_audit_failure_fail_closed(self):
        backend = RotatingSecretBackend()
        backend.fail = True
        resolver = ProductionSecretResolver(authorizer(), backend, RecordingAudit(), clock=lambda: NOW)
        with self.assertRaises(ProductionSecurityBoundaryError) as unavailable:
            resolver.resolve(secret_ref(), identity())
        self.assertEqual("secret_manager_unavailable", unavailable.exception.code)

        backend.fail = False
        resolver = ProductionSecretResolver(authorizer(), backend, RecordingAudit(fail=True), clock=lambda: NOW)
        with self.assertRaises(ProductionSecurityBoundaryError) as audit:
            resolver.resolve(secret_ref(), identity())
        self.assertEqual("security_audit_unavailable", audit.exception.code)

    def test_iam_is_exact_deny_by_default_and_environment_isolated(self):
        iam = authorizer()
        with self.assertRaises(ProductionSecurityBoundaryError) as missing:
            iam.authorize(identity(), "secret.read", SecretReference(
                environment="production",
                logical_name="other-secret",
                purpose="database-credential",
            ))
        self.assertEqual("iam_access_denied", missing.exception.code)

        with self.assertRaises(ProductionSecurityBoundaryError) as cross_env:
            iam.authorize(identity(environment="staging"), "secret.read", secret_ref("production"))
        self.assertEqual("iam_environment_boundary_violation", cross_env.exception.code)

    def test_administrative_duty_cannot_use_runtime_secret_or_kms_operations(self):
        with self.assertRaises(ProductionSecurityBoundaryError) as raised:
            authorizer().authorize(identity(duty="security-admin"), "secret.read", secret_ref())
        self.assertEqual("iam_separation_of_duties_violation", raised.exception.code)

    def test_unverified_and_expired_workload_identity_fail_closed(self):
        with self.assertRaises(ProductionSecurityBoundaryError) as unverified:
            authorizer().authorize(identity(verified=False), "secret.read", secret_ref())
        self.assertEqual("workload_identity_unverified", unverified.exception.code)

        with self.assertRaises(ProductionSecurityBoundaryError) as expired:
            authorizer().authorize(
                identity(expires_at=NOW - timedelta(seconds=1)),
                "secret.read",
                secret_ref(),
            )
        self.assertEqual("workload_identity_expired", expired.exception.code)

    def test_kms_envelope_roundtrip_binds_context_and_key_state(self):
        backend = FakeKmsBackend()
        audit = RecordingAudit()
        kms = ProductionEnvelopeCrypto(authorizer(), backend, audit, clock=lambda: NOW)
        plaintext = b"synthetic-score-bytes"

        envelope = kms.encrypt(plaintext, key_ref(), context(), identity())
        restored = kms.decrypt(envelope, key_ref(), context(), identity())

        self.assertNotEqual(plaintext, envelope.ciphertext)
        self.assertEqual(context().canonical_digest(), envelope.context_digest)
        self.assertEqual(plaintext, restored)
        self.assertNotIn("synthetic-score-bytes", repr(envelope))
        self.assertEqual(["kms.encrypt", "kms.decrypt"], [event.action for event in audit.events])

    def test_kms_context_tamper_key_disable_and_revocation_uncertainty_fail_closed(self):
        backend = FakeKmsBackend()
        kms = ProductionEnvelopeCrypto(authorizer(), backend, RecordingAudit(), clock=lambda: NOW)
        envelope = kms.encrypt(b"synthetic-score-bytes", key_ref(), context(), identity())

        tampered = EncryptionContext(
            environment="production",
            purpose="artifact-encryption",
            tenant_key="tenant:sha256:" + "c" * 64,
            object_key="job_12345",
        )
        with self.assertRaises(ProductionSecurityBoundaryError) as mismatch:
            kms.decrypt(envelope, key_ref(), tampered, identity())
        self.assertEqual("kms_context_digest_mismatch", mismatch.exception.code)

        backend.state = "DISABLED"
        with self.assertRaises(ProductionSecurityBoundaryError) as disabled:
            kms.decrypt(envelope, key_ref(), context(), identity())
        self.assertEqual("kms_key_not_enabled", disabled.exception.code)

        backend.state = "ENABLED"
        backend.revocation_checked = False
        with self.assertRaises(ProductionSecurityBoundaryError) as unknown:
            kms.decrypt(envelope, key_ref(), context(), identity())
        self.assertEqual("kms_key_revocation_unknown", unknown.exception.code)

    def test_kms_dependency_and_audit_failure_fail_closed(self):
        backend = FakeKmsBackend()
        backend.fail_state = True
        kms = ProductionEnvelopeCrypto(authorizer(), backend, RecordingAudit(), clock=lambda: NOW)
        with self.assertRaises(ProductionSecurityBoundaryError) as state:
            kms.encrypt(b"synthetic-score-bytes", key_ref(), context(), identity())
        self.assertEqual("kms_key_state_unavailable", state.exception.code)

        backend.fail_state = False
        kms = ProductionEnvelopeCrypto(authorizer(), backend, RecordingAudit(fail=True), clock=lambda: NOW)
        with self.assertRaises(ProductionSecurityBoundaryError) as audit:
            kms.encrypt(b"synthetic-score-bytes", key_ref(), context(), identity())
        self.assertEqual("security_audit_unavailable", audit.exception.code)

    def test_encryption_context_rejects_non_opaque_tenant(self):
        with self.assertRaises(ProductionSecurityBoundaryError) as raised:
            EncryptionContext(
                environment="production",
                purpose="artifact-encryption",
                tenant_key="school-name",
                object_key="job_12345",
            )
        self.assertEqual("invalid_encryption_context", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
