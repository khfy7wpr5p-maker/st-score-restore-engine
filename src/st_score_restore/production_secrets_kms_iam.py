"""Provider-neutral Stage 6 production secrets, KMS and IAM boundary.

This module deliberately contains no cloud/provider adapter and creates no live
resources. Provider-specific secret managers, KMS/HSM services and IAM bindings
must implement the protocols defined here after a separately evidenced provider
selection.

The boundary is fail-closed: unverified/expired workload identity, missing IAM
grants, secret/key revocation uncertainty, provider dependency failure, context
mismatch, or security-audit failure prevents secret release or KMS plaintext
release to the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import re
from typing import Callable, Mapping, Protocol, Sequence


_ALLOWED_ENVIRONMENTS = frozenset({"staging", "production"})
_ALLOWED_RUNTIME_ACTIONS = frozenset({"secret.read", "kms.encrypt", "kms.decrypt"})
_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9._:@/-]+$")


class ProductionSecurityBoundaryError(RuntimeError):
    """Fail-closed production secrets/KMS/IAM boundary error."""

    def __init__(self, code: str, message: str, *, http_status: int = 503) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status


@dataclass(frozen=True)
class WorkloadIdentity:
    """Verified opaque service identity supplied by an external workload IdP."""

    principal_key: str
    service: str
    environment: str
    duty: str
    expires_at: datetime
    verification_evidence_id: str
    verified: bool = True


@dataclass(frozen=True)
class IamGrant:
    """Exact runtime grant. Wildcards are intentionally unsupported."""

    service: str
    environment: str
    duty: str
    action: str
    resource_kind: str
    resource_name: str


class IamResource(Protocol):
    environment: str

    @property
    def resource_kind(self) -> str: ...

    @property
    def resource_name(self) -> str: ...


class ProductionIamAuthorizer:
    """Provider-neutral least-privilege, deny-by-default runtime IAM policy."""

    def __init__(
        self,
        grants: Sequence[IamGrant],
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))
        self._grants = tuple(grants)
        for grant in self._grants:
            self._validate_grant(grant)

    def authorize(self, identity: WorkloadIdentity, action: str, resource: IamResource) -> None:
        now = _as_utc(self._clock(), "IAM clock")
        _validate_workload_identity(identity, now)
        if action not in _ALLOWED_RUNTIME_ACTIONS:
            raise ProductionSecurityBoundaryError(
                "iam_action_not_supported",
                "The requested runtime IAM action is not supported.",
                http_status=403,
            )
        if identity.duty != "runtime":
            raise ProductionSecurityBoundaryError(
                "iam_separation_of_duties_violation",
                "Administrative or non-runtime duty cannot use production data-plane secrets or KMS operations.",
                http_status=403,
            )
        if resource.environment != identity.environment:
            raise ProductionSecurityBoundaryError(
                "iam_environment_boundary_violation",
                "Workload identity cannot cross environment security boundaries.",
                http_status=403,
            )
        expected = IamGrant(
            service=identity.service,
            environment=identity.environment,
            duty=identity.duty,
            action=action,
            resource_kind=resource.resource_kind,
            resource_name=resource.resource_name,
        )
        if expected not in self._grants:
            raise ProductionSecurityBoundaryError(
                "iam_access_denied",
                "No exact least-privilege IAM grant exists for this workload operation.",
                http_status=403,
            )

    @staticmethod
    def _validate_grant(grant: IamGrant) -> None:
        if grant.environment not in _ALLOWED_ENVIRONMENTS:
            raise ProductionSecurityBoundaryError("invalid_iam_grant", "IAM grant environment is invalid.")
        for label, value in (
            ("service", grant.service),
            ("duty", grant.duty),
            ("action", grant.action),
            ("resource_kind", grant.resource_kind),
            ("resource_name", grant.resource_name),
        ):
            _require_safe_token(value, f"IAM grant {label}")
        if grant.action not in _ALLOWED_RUNTIME_ACTIONS:
            raise ProductionSecurityBoundaryError("invalid_iam_grant", "IAM grant action is not a permitted runtime action.")
        if grant.duty != "runtime":
            raise ProductionSecurityBoundaryError(
                "invalid_iam_grant",
                "Only runtime duty may receive data-plane secret/KMS grants.",
            )
        if "*" in grant.resource_name or "*" in grant.service:
            raise ProductionSecurityBoundaryError("invalid_iam_grant", "Wildcard IAM grants are forbidden.")


@dataclass(frozen=True)
class SecretReference:
    environment: str
    logical_name: str
    purpose: str
    selector: str = "active"

    def __post_init__(self) -> None:
        _validate_environment(self.environment)
        _require_safe_token(self.logical_name, "secret logical name")
        _require_safe_token(self.purpose, "secret purpose")
        _require_safe_token(self.selector, "secret selector")

    @property
    def resource_kind(self) -> str:
        return "secret"

    @property
    def resource_name(self) -> str:
        return f"{self.logical_name}:{self.purpose}"


@dataclass(frozen=True, repr=False)
class SecretBackendEvidence:
    """Synthetic/provider response contract. Raw material is intentionally redacted from repr."""

    material: bytes
    concrete_version: str
    expires_at: datetime
    revocation_checked: bool
    revoked: bool
    provider_evidence_id: str

    def __repr__(self) -> str:
        return (
            "SecretBackendEvidence(material=<redacted>, concrete_version="
            f"{self.concrete_version!r}, expires_at={self.expires_at!r}, "
            f"revocation_checked={self.revocation_checked!r}, revoked={self.revoked!r}, "
            f"provider_evidence_id={self.provider_evidence_id!r})"
        )


class SecretManagerBackend(Protocol):
    def resolve(self, reference: SecretReference, identity: WorkloadIdentity) -> SecretBackendEvidence: ...


class SecretValue:
    """Redacted application-facing secret material wrapper.

    Python does not promise secure-memory zeroization. This class therefore makes
    no such claim; it only prevents routine repr/str serialization from exposing
    the value and requires an explicit reveal call by the authorized consumer.
    """

    __slots__ = ("_material", "reference", "concrete_version", "provider_evidence_id")

    def __init__(
        self,
        material: bytes,
        *,
        reference: SecretReference,
        concrete_version: str,
        provider_evidence_id: str,
    ) -> None:
        self._material = bytes(material)
        self.reference = reference
        self.concrete_version = concrete_version
        self.provider_evidence_id = provider_evidence_id

    def reveal(self) -> bytes:
        return bytes(self._material)

    def __repr__(self) -> str:
        return (
            "SecretValue(<redacted>, "
            f"reference={self.reference!r}, concrete_version={self.concrete_version!r})"
        )

    def __str__(self) -> str:
        return "<redacted-secret>"


@dataclass(frozen=True)
class KeyReference:
    environment: str
    logical_name: str
    purpose: str
    selector: str = "active"

    def __post_init__(self) -> None:
        _validate_environment(self.environment)
        _require_safe_token(self.logical_name, "key logical name")
        _require_safe_token(self.purpose, "key purpose")
        _require_safe_token(self.selector, "key selector")

    @property
    def resource_kind(self) -> str:
        return "kms-key"

    @property
    def resource_name(self) -> str:
        return f"{self.logical_name}:{self.purpose}"


@dataclass(frozen=True)
class EncryptionContext:
    environment: str
    purpose: str
    tenant_key: str
    object_key: str

    def __post_init__(self) -> None:
        _validate_environment(self.environment)
        _require_safe_token(self.purpose, "encryption purpose")
        if not self.tenant_key.startswith("tenant:sha256:"):
            raise ProductionSecurityBoundaryError(
                "invalid_encryption_context",
                "Encryption context tenant must be an opaque tenant digest.",
            )
        _require_safe_token(self.tenant_key, "encryption tenant key")
        _require_safe_token(self.object_key, "encryption object key")

    def canonical_digest(self) -> str:
        payload = json.dumps(
            {
                "environment": self.environment,
                "object_key": self.object_key,
                "purpose": self.purpose,
                "tenant_key": self.tenant_key,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def as_provider_context(self) -> Mapping[str, str]:
        return {
            "environment": self.environment,
            "object_key": self.object_key,
            "purpose": self.purpose,
            "tenant_key": self.tenant_key,
        }


@dataclass(frozen=True)
class KeyStateEvidence:
    concrete_version: str
    state: str
    revocation_checked: bool
    provider_evidence_id: str
    checked_at: datetime


@dataclass(frozen=True, repr=False)
class KmsEnvelope:
    ciphertext: bytes
    wrapped_data_key: bytes
    key_logical_name: str
    key_version: str
    algorithm: str
    context_digest: str
    provider_evidence_id: str

    def __repr__(self) -> str:
        return (
            "KmsEnvelope(ciphertext=<opaque>, wrapped_data_key=<opaque>, "
            f"key_logical_name={self.key_logical_name!r}, key_version={self.key_version!r}, "
            f"algorithm={self.algorithm!r}, context_digest={self.context_digest!r}, "
            f"provider_evidence_id={self.provider_evidence_id!r})"
        )


class KmsBackend(Protocol):
    def key_state(self, key: KeyReference, identity: WorkloadIdentity) -> KeyStateEvidence: ...

    def encrypt(
        self,
        plaintext: bytes,
        key: KeyReference,
        context: Mapping[str, str],
        identity: WorkloadIdentity,
    ) -> KmsEnvelope: ...

    def decrypt(
        self,
        envelope: KmsEnvelope,
        key: KeyReference,
        context: Mapping[str, str],
        identity: WorkloadIdentity,
    ) -> bytes: ...


@dataclass(frozen=True)
class SecurityAuditEvent:
    action: str
    outcome: str
    principal_key: str
    service: str
    environment: str
    resource_kind: str
    resource_name: str
    provider_evidence_id: str
    at: datetime

    def __post_init__(self) -> None:
        if self.outcome not in {"success", "denied", "dependency_failure"}:
            raise ProductionSecurityBoundaryError("invalid_security_audit_event", "Audit outcome is invalid.")
        for label, value in (
            ("action", self.action),
            ("principal_key", self.principal_key),
            ("service", self.service),
            ("environment", self.environment),
            ("resource_kind", self.resource_kind),
            ("resource_name", self.resource_name),
            ("provider_evidence_id", self.provider_evidence_id),
        ):
            _require_safe_token(value, f"audit {label}")


class SecurityAuditSink(Protocol):
    """Later Stage 6 storage work supplies append-only/tamper-evident persistence."""

    def append(self, event: SecurityAuditEvent) -> None: ...


class ProductionSecretResolver:
    """No-cache, revocation-aware secret resolution boundary."""

    def __init__(
        self,
        iam: ProductionIamAuthorizer,
        backend: SecretManagerBackend,
        audit: SecurityAuditSink,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if iam is None or backend is None or audit is None:
            raise ProductionSecurityBoundaryError(
                "invalid_secret_boundary_configuration",
                "Production secret resolution requires IAM, secret-manager and audit adapters.",
            )
        self._iam = iam
        self._backend = backend
        self._audit_sink = audit
        self._clock = clock or (lambda: datetime.now(UTC))

    def resolve(self, reference: SecretReference, identity: WorkloadIdentity) -> SecretValue:
        self._iam.authorize(identity, "secret.read", reference)
        try:
            evidence = self._backend.resolve(reference, identity)
        except ProductionSecurityBoundaryError:
            raise
        except Exception as error:
            self._audit_dependency_failure(identity, reference, "secret.read")
            raise ProductionSecurityBoundaryError(
                "secret_manager_unavailable",
                "Secret-manager evidence could not be verified.",
            ) from error

        now = _as_utc(self._clock(), "secret resolver clock")
        self._validate_secret_evidence(evidence, now)
        self._audit_success(
            identity,
            reference,
            "secret.read",
            evidence.provider_evidence_id,
            now,
        )
        return SecretValue(
            evidence.material,
            reference=reference,
            concrete_version=evidence.concrete_version,
            provider_evidence_id=evidence.provider_evidence_id,
        )

    @staticmethod
    def _validate_secret_evidence(evidence: SecretBackendEvidence, now: datetime) -> None:
        if not isinstance(evidence, SecretBackendEvidence):
            raise ProductionSecurityBoundaryError(
                "invalid_secret_evidence",
                "Secret manager returned malformed evidence.",
            )
        _require_safe_token(evidence.concrete_version, "secret concrete version")
        _require_safe_token(evidence.provider_evidence_id, "secret provider evidence id")
        expires_at = _as_utc(evidence.expires_at, "secret expiry")
        if not evidence.revocation_checked:
            raise ProductionSecurityBoundaryError(
                "secret_revocation_unknown",
                "Secret revocation state was not verified.",
            )
        if evidence.revoked:
            raise ProductionSecurityBoundaryError("secret_revoked", "Secret version is revoked.", http_status=403)
        if expires_at <= now:
            raise ProductionSecurityBoundaryError("secret_lease_expired", "Secret lease is expired.", http_status=403)
        if not isinstance(evidence.material, bytes) or not evidence.material:
            raise ProductionSecurityBoundaryError("invalid_secret_evidence", "Secret material is empty or malformed.")

    def _audit_success(
        self,
        identity: WorkloadIdentity,
        resource: IamResource,
        action: str,
        evidence_id: str,
        at: datetime,
    ) -> None:
        self._append_audit(
            SecurityAuditEvent(
                action=action,
                outcome="success",
                principal_key=identity.principal_key,
                service=identity.service,
                environment=identity.environment,
                resource_kind=resource.resource_kind,
                resource_name=resource.resource_name,
                provider_evidence_id=evidence_id,
                at=at,
            )
        )

    def _audit_dependency_failure(self, identity: WorkloadIdentity, resource: IamResource, action: str) -> None:
        self._append_audit(
            SecurityAuditEvent(
                action=action,
                outcome="dependency_failure",
                principal_key=identity.principal_key,
                service=identity.service,
                environment=identity.environment,
                resource_kind=resource.resource_kind,
                resource_name=resource.resource_name,
                provider_evidence_id="dependency-unavailable",
                at=_as_utc(self._clock(), "audit clock"),
            )
        )

    def _append_audit(self, event: SecurityAuditEvent) -> None:
        try:
            self._audit_sink.append(event)
        except Exception as error:
            raise ProductionSecurityBoundaryError(
                "security_audit_unavailable",
                "Security audit evidence could not be committed; operation failed closed.",
            ) from error


class ProductionEnvelopeCrypto:
    """Envelope-encryption orchestration that delegates cryptography to an approved KMS backend."""

    def __init__(
        self,
        iam: ProductionIamAuthorizer,
        backend: KmsBackend,
        audit: SecurityAuditSink,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if iam is None or backend is None or audit is None:
            raise ProductionSecurityBoundaryError(
                "invalid_kms_boundary_configuration",
                "Production KMS operations require IAM, KMS and audit adapters.",
            )
        self._iam = iam
        self._backend = backend
        self._audit_sink = audit
        self._clock = clock or (lambda: datetime.now(UTC))

    def encrypt(
        self,
        plaintext: bytes,
        key: KeyReference,
        context: EncryptionContext,
        identity: WorkloadIdentity,
    ) -> KmsEnvelope:
        self._validate_request(plaintext, key, context, identity, action="kms.encrypt")
        key_state = self._verified_key_state(key, identity)
        try:
            envelope = self._backend.encrypt(
                plaintext,
                key,
                context.as_provider_context(),
                identity,
            )
        except ProductionSecurityBoundaryError:
            raise
        except Exception as error:
            self._audit_dependency_failure(identity, key, "kms.encrypt")
            raise ProductionSecurityBoundaryError("kms_unavailable", "KMS encryption failed closed.") from error
        self._validate_envelope(envelope, key, key_state, context, plaintext=plaintext)
        self._audit_success(identity, key, "kms.encrypt", envelope.provider_evidence_id)
        return envelope

    def decrypt(
        self,
        envelope: KmsEnvelope,
        key: KeyReference,
        context: EncryptionContext,
        identity: WorkloadIdentity,
    ) -> bytes:
        self._validate_request(b"decrypt-marker", key, context, identity, action="kms.decrypt")
        key_state = self._verified_key_state(key, identity)
        self._validate_envelope(envelope, key, key_state, context, plaintext=None)
        try:
            plaintext = self._backend.decrypt(
                envelope,
                key,
                context.as_provider_context(),
                identity,
            )
        except ProductionSecurityBoundaryError:
            raise
        except Exception as error:
            self._audit_dependency_failure(identity, key, "kms.decrypt")
            raise ProductionSecurityBoundaryError("kms_unavailable", "KMS decryption failed closed.") from error
        if not isinstance(plaintext, bytes) or not plaintext:
            raise ProductionSecurityBoundaryError("invalid_kms_plaintext", "KMS returned malformed plaintext.")
        self._audit_success(identity, key, "kms.decrypt", envelope.provider_evidence_id)
        return plaintext

    def _validate_request(
        self,
        payload: bytes,
        key: KeyReference,
        context: EncryptionContext,
        identity: WorkloadIdentity,
        *,
        action: str,
    ) -> None:
        if not isinstance(payload, bytes) or not payload:
            raise ProductionSecurityBoundaryError("invalid_kms_payload", "KMS payload must be non-empty bytes.")
        if key.environment != context.environment or key.purpose != context.purpose:
            raise ProductionSecurityBoundaryError(
                "kms_context_mismatch",
                "KMS key and encryption context do not share the same environment and purpose.",
                http_status=403,
            )
        self._iam.authorize(identity, action, key)

    def _verified_key_state(self, key: KeyReference, identity: WorkloadIdentity) -> KeyStateEvidence:
        try:
            evidence = self._backend.key_state(key, identity)
        except ProductionSecurityBoundaryError:
            raise
        except Exception as error:
            self._audit_dependency_failure(identity, key, "kms.key_state")
            raise ProductionSecurityBoundaryError(
                "kms_key_state_unavailable",
                "KMS key state could not be verified.",
            ) from error
        if not isinstance(evidence, KeyStateEvidence):
            raise ProductionSecurityBoundaryError("invalid_kms_key_evidence", "KMS returned malformed key evidence.")
        _require_safe_token(evidence.concrete_version, "KMS key version")
        _require_safe_token(evidence.provider_evidence_id, "KMS provider evidence id")
        _as_utc(evidence.checked_at, "KMS key state timestamp")
        if not evidence.revocation_checked:
            raise ProductionSecurityBoundaryError(
                "kms_key_revocation_unknown",
                "KMS key revocation state was not verified.",
            )
        if evidence.state != "ENABLED":
            raise ProductionSecurityBoundaryError(
                "kms_key_not_enabled",
                "KMS key is not enabled for runtime use.",
                http_status=403,
            )
        return evidence

    @staticmethod
    def _validate_envelope(
        envelope: KmsEnvelope,
        key: KeyReference,
        key_state: KeyStateEvidence,
        context: EncryptionContext,
        *,
        plaintext: bytes | None,
    ) -> None:
        if not isinstance(envelope, KmsEnvelope):
            raise ProductionSecurityBoundaryError("invalid_kms_envelope", "KMS returned a malformed envelope.")
        if not envelope.ciphertext or not envelope.wrapped_data_key:
            raise ProductionSecurityBoundaryError("invalid_kms_envelope", "KMS envelope is missing opaque ciphertext material.")
        if plaintext is not None and envelope.ciphertext == plaintext:
            raise ProductionSecurityBoundaryError("invalid_kms_envelope", "KMS backend returned plaintext as ciphertext.")
        if envelope.key_logical_name != key.logical_name:
            raise ProductionSecurityBoundaryError("kms_key_binding_mismatch", "Envelope key binding does not match requested key.")
        if envelope.key_version != key_state.concrete_version:
            raise ProductionSecurityBoundaryError("kms_key_version_mismatch", "Envelope key version does not match verified key state.")
        if not envelope.algorithm or envelope.algorithm.lower() == "none":
            raise ProductionSecurityBoundaryError("invalid_kms_algorithm", "KMS envelope algorithm is invalid.")
        if envelope.context_digest != context.canonical_digest():
            raise ProductionSecurityBoundaryError(
                "kms_context_digest_mismatch",
                "Envelope encryption context does not match the requested security context.",
                http_status=403,
            )
        _require_safe_token(envelope.provider_evidence_id, "KMS envelope evidence id")

    def _audit_success(self, identity: WorkloadIdentity, key: KeyReference, action: str, evidence_id: str) -> None:
        self._append_audit(
            SecurityAuditEvent(
                action=action,
                outcome="success",
                principal_key=identity.principal_key,
                service=identity.service,
                environment=identity.environment,
                resource_kind=key.resource_kind,
                resource_name=key.resource_name,
                provider_evidence_id=evidence_id,
                at=_as_utc(self._clock(), "audit clock"),
            )
        )

    def _audit_dependency_failure(self, identity: WorkloadIdentity, key: KeyReference, action: str) -> None:
        self._append_audit(
            SecurityAuditEvent(
                action=action,
                outcome="dependency_failure",
                principal_key=identity.principal_key,
                service=identity.service,
                environment=identity.environment,
                resource_kind=key.resource_kind,
                resource_name=key.resource_name,
                provider_evidence_id="dependency-unavailable",
                at=_as_utc(self._clock(), "audit clock"),
            )
        )

    def _append_audit(self, event: SecurityAuditEvent) -> None:
        try:
            self._audit_sink.append(event)
        except Exception as error:
            raise ProductionSecurityBoundaryError(
                "security_audit_unavailable",
                "Security audit evidence could not be committed; operation failed closed.",
            ) from error


def _validate_workload_identity(identity: WorkloadIdentity, now: datetime) -> None:
    if not isinstance(identity, WorkloadIdentity):
        raise ProductionSecurityBoundaryError("invalid_workload_identity", "Workload identity is malformed.", http_status=401)
    if not identity.verified:
        raise ProductionSecurityBoundaryError("workload_identity_unverified", "Workload identity is not verified.", http_status=401)
    if not identity.principal_key.startswith("workload:sha256:"):
        raise ProductionSecurityBoundaryError(
            "workload_identity_not_opaque",
            "Production workload principal must be an opaque digest.",
            http_status=401,
        )
    _require_safe_token(identity.principal_key, "workload principal")
    _require_safe_token(identity.service, "workload service")
    _require_safe_token(identity.duty, "workload duty")
    _require_safe_token(identity.verification_evidence_id, "workload verification evidence id")
    _validate_environment(identity.environment)
    if _as_utc(identity.expires_at, "workload identity expiry") <= now:
        raise ProductionSecurityBoundaryError("workload_identity_expired", "Workload identity is expired.", http_status=401)


def _validate_environment(value: str) -> None:
    if value not in _ALLOWED_ENVIRONMENTS:
        raise ProductionSecurityBoundaryError(
            "invalid_production_environment",
            "Only isolated staging or production environments are valid for this boundary.",
        )


def _require_safe_token(value: str, label: str) -> None:
    if not isinstance(value, str) or not value or not _SAFE_TOKEN.fullmatch(value):
        raise ProductionSecurityBoundaryError(
            "invalid_security_metadata",
            f"{label} must be a non-empty privacy-safe token.",
        )


def _as_utc(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ProductionSecurityBoundaryError("invalid_security_timestamp", f"{label} must be timezone-aware.")
    return value.astimezone(UTC)


__all__ = [
    "EncryptionContext",
    "IamGrant",
    "KeyReference",
    "KeyStateEvidence",
    "KmsBackend",
    "KmsEnvelope",
    "ProductionEnvelopeCrypto",
    "ProductionIamAuthorizer",
    "ProductionSecretResolver",
    "ProductionSecurityBoundaryError",
    "SecretBackendEvidence",
    "SecretManagerBackend",
    "SecretReference",
    "SecretValue",
    "SecurityAuditEvent",
    "SecurityAuditSink",
    "WorkloadIdentity",
]
