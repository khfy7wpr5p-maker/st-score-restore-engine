"""Deterministic synthetic Stage 6 S6-08 integration/security regression suite.

The suite composes the provider-neutral Stage 6 boundaries without contacting a
provider, creating live resources, reading corpus bytes, mutating production
state, or authorizing deployment. It proves that boundary contracts still agree
when exercised together and that important bypass attempts fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import hashlib
import json
from typing import Mapping

from .job_api_types import JobApiConfig, JobApiError
from .production_http_auth import JobAuthorizationContext, ProductionApiV1
from .production_identity import (
    ProductionIdentityAdapter,
    ProductionIdentityPolicy,
    VerifiedTokenEvidence,
)
from .production_network import (
    MemoryNetworkAuditSink,
    NetworkSecurityError,
    NetworkZone,
    PrivateTopologyPolicy,
    PublicEdgeEvidence,
    TrustedProxyPolicy,
    authorize_public_ingress,
)
from .production_secrets_kms_iam import (
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
    SecurityAuditEvent,
    WorkloadIdentity,
)
from .production_storage_deployment import (
    AuditStoreEvidence,
    DeploymentCandidateEvidence,
    EnvironmentIsolationEvidence,
    MemoryStorageAuditSink,
    MetadataDatabaseEvidence,
    ObjectStorageEvidence,
    QueueClaimEvidence,
    StorageDeploymentError,
    authorize_audit_store,
    authorize_deployment_candidate,
    authorize_environment_isolation,
    authorize_metadata_database,
    authorize_object_storage,
    authorize_queue_claim,
)
from .stage6_operational_drills import run_synthetic_operational_drills

_NOW = datetime(2026, 9, 6, 18, 0, tzinfo=UTC)
_IMAGE_DIGEST = "sha256:" + ("d" * 64)
_ROLLBACK_DIGEST = "sha256:" + ("e" * 64)
_IDEMPOTENCY_DIGEST = "f" * 64


class IntegrationSecurityRegressionError(RuntimeError):
    pass


@dataclass(frozen=True)
class RegressionResult:
    name: str
    passed: bool
    assertions: tuple[str, ...]


@dataclass(frozen=True)
class IntegrationSecurityRegressionReport:
    schema_version: str
    synthetic_only: bool
    provider_calls_performed: bool
    live_resources_created: bool
    production_state_mutated: bool
    production_deployment_performed: bool
    results: tuple[RegressionResult, ...]

    @property
    def passed(self) -> bool:
        return bool(self.results) and all(result.passed for result in self.results)

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": self.schema_version,
            "syntheticOnly": self.synthetic_only,
            "providerCallsPerformed": self.provider_calls_performed,
            "liveResourcesCreated": self.live_resources_created,
            "productionStateMutated": self.production_state_mutated,
            "productionDeploymentPerformed": self.production_deployment_performed,
            "passed": self.passed,
            "results": [
                {
                    "name": result.name,
                    "passed": result.passed,
                    "assertions": list(result.assertions),
                }
                for result in self.results
            ],
        }


class _SignatureBackend:
    def __init__(self, claims: Mapping[str, object], *, signature_validated: bool = True) -> None:
        self.claims = dict(claims)
        self.signature_validated = signature_validated

    def verify(self, token: str) -> VerifiedTokenEvidence:
        return VerifiedTokenEvidence(
            claims=self.claims,
            key_id="synthetic-kid-1",
            algorithm="RS256",
            signature_validated=self.signature_validated,
        )


class _AuthorizationStore:
    def __init__(self, contexts: Mapping[str, JobAuthorizationContext] | None = None) -> None:
        self.contexts = dict(contexts or {})

    def bind_job(self, job_id: str, context: JobAuthorizationContext) -> None:
        current = self.contexts.get(job_id)
        if current is not None and current != context:
            raise JobApiError("authorization_binding_conflict", "synthetic binding conflict", http_status=403)
        self.contexts[job_id] = context

    def get_job_context(self, job_id: str) -> JobAuthorizationContext | None:
        return self.contexts.get(job_id)


@dataclass
class _SecurityAuditMemory:
    accept: bool = True
    events: list[SecurityAuditEvent] = field(default_factory=list)

    def append(self, event: SecurityAuditEvent) -> None:
        if not self.accept:
            raise RuntimeError("synthetic audit unavailable")
        self.events.append(event)


class _SecretBackend:
    def resolve(self, reference: SecretReference, identity: WorkloadIdentity) -> SecretBackendEvidence:
        return SecretBackendEvidence(
            material=b"synthetic-secret-material",
            concrete_version="v1",
            expires_at=_NOW + timedelta(hours=1),
            revocation_checked=True,
            revoked=False,
            provider_evidence_id="synthetic-secret-evidence-1",
        )


class _KmsBackend:
    def key_state(self, key: KeyReference, identity: WorkloadIdentity) -> KeyStateEvidence:
        return KeyStateEvidence(
            concrete_version="k1",
            state="ENABLED",
            revocation_checked=True,
            provider_evidence_id="synthetic-kms-state-1",
            checked_at=_NOW,
        )

    def encrypt(
        self,
        plaintext: bytes,
        key: KeyReference,
        context: Mapping[str, str],
        identity: WorkloadIdentity,
    ) -> KmsEnvelope:
        context_digest = hashlib.sha256(
            json.dumps(dict(context), sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return KmsEnvelope(
            ciphertext=b"synthetic-cipher:" + plaintext[::-1],
            wrapped_data_key=b"synthetic-wrapped-key",
            key_logical_name=key.logical_name,
            key_version="k1",
            algorithm="SYNTHETIC-AEAD",
            context_digest=context_digest,
            provider_evidence_id="synthetic-kms-envelope-1",
        )

    def decrypt(
        self,
        envelope: KmsEnvelope,
        key: KeyReference,
        context: Mapping[str, str],
        identity: WorkloadIdentity,
    ) -> bytes:
        prefix = b"synthetic-cipher:"
        if not envelope.ciphertext.startswith(prefix):
            raise RuntimeError("synthetic ciphertext malformed")
        return envelope.ciphertext[len(prefix):][::-1]


def _claims(*, tenant: str = "tenant-a", roles: tuple[str, ...] = ("client",)) -> dict[str, object]:
    return {
        "iss": "https://synthetic-idp.invalid",
        "aud": "st-score-restore",
        "exp": (_NOW + timedelta(hours=1)).timestamp(),
        "nbf": (_NOW - timedelta(minutes=1)).timestamp(),
        "sub": "synthetic-user-a",
        "tenant_id": tenant,
        "jti": "synthetic-token-id-1",
        "roles": list(roles),
    }


def _identity_adapter(
    *,
    tenant: str = "tenant-a",
    roles: tuple[str, ...] = ("client",),
    revoked: bool = False,
    signature_validated: bool = True,
) -> ProductionIdentityAdapter:
    policy = ProductionIdentityPolicy(
        trusted_issuers=("https://synthetic-idp.invalid",),
        trusted_audiences=("st-score-restore",),
        clock_skew_seconds=0,
    )
    return ProductionIdentityAdapter(
        policy,
        _SignatureBackend(_claims(tenant=tenant, roles=roles), signature_validated=signature_validated),
        lambda issuer, token_id: revoked,
        clock=lambda: _NOW,
    )


def _workload_identity(*, environment: str = "production") -> WorkloadIdentity:
    return WorkloadIdentity(
        principal_key="workload:sha256:" + ("1" * 64),
        service="st-score-restore",
        environment=environment,
        duty="runtime",
        expires_at=_NOW + timedelta(hours=1),
        verification_evidence_id="synthetic-workload-evidence-1",
        verified=True,
    )


def _iam(secret: SecretReference, key: KeyReference) -> ProductionIamAuthorizer:
    return ProductionIamAuthorizer(
        (
            IamGrant("st-score-restore", "production", "runtime", "secret.read", secret.resource_kind, secret.resource_name),
            IamGrant("st-score-restore", "production", "runtime", "kms.encrypt", key.resource_kind, key.resource_name),
            IamGrant("st-score-restore", "production", "runtime", "kms.decrypt", key.resource_kind, key.resource_name),
        ),
        clock=lambda: _NOW,
    )


def _edge_evidence(*, built_in_public: bool = False, proxy_id: str = "edge-1") -> PublicEdgeEvidence:
    return PublicEdgeEvidence(
        proxy_id=proxy_id,
        peer_ip="10.20.30.4",
        canonical_forwarded_for="203.0.113.25",
        tls_terminated_by_managed_edge=True,
        tls_peer_policy_validated=True,
        proxy_workload_authenticated=True,
        forwarded_headers_rewritten_not_appended=True,
        hop_by_hop_headers_stripped=True,
        single_host_normalized=True,
        transfer_encoding_removed=True,
        content_length_canonicalized=True,
        request_target_normalized=True,
        request_smuggling_check_passed=True,
        waf_check_passed=True,
        rate_limit_check_passed=True,
        quota_check_passed=True,
        connection_limit_check_passed=True,
        request_body_limit_check_passed=True,
        header_limit_check_passed=True,
        slow_client_check_passed=True,
        multipart_boundary_check_passed=True,
        built_in_stdlib_server_publicly_exposed=built_in_public,
    )


def _deployment_candidate(*, activate: bool = False) -> DeploymentCandidateEvidence:
    return DeploymentCandidateEvidence(
        artifact_digest=_IMAGE_DIGEST,
        rollback_artifact_digest=_ROLLBACK_DIGEST,
        provenance_signed=True,
        artifact_signature_verified=True,
        immutable_artifact=True,
        staging_health_checks_passed=True,
        migration_preflight_passed=True,
        rollback_path_validated=True,
        secrets_not_baked_into_artifact=True,
        environment_config_separated=True,
        privacy_safe_observability_ready=True,
        production_activation_requested=activate,
    )


def _response_error_code(response) -> str | None:
    try:
        body = json.loads(response.body.decode("utf-8"))
    except Exception:
        return None
    error = body.get("error") if isinstance(body, dict) else None
    return error.get("code") if isinstance(error, dict) else None


def _expect_job_error(action, code: str) -> bool:
    try:
        action()
    except JobApiError as exc:
        return exc.code == code
    return False


def _expect_network_error(action, code: str) -> bool:
    try:
        action()
    except NetworkSecurityError as exc:
        return exc.reason_code == code
    return False


def _expect_security_error(action, code: str) -> bool:
    try:
        action()
    except ProductionSecurityBoundaryError as exc:
        return exc.code == code
    return False


def _expect_storage_error(action, code: str) -> bool:
    try:
        action()
    except StorageDeploymentError as exc:
        return exc.reason_code == code
    return False


def _regression_trusted_chain() -> RegressionResult:
    network_audit = MemoryNetworkAuditSink()
    proxy = TrustedProxyPolicy.from_cidrs(trusted_proxy_ids=("edge-1",), cidrs=("10.20.30.0/24",))
    ingress = authorize_public_ingress(_edge_evidence(), proxy_policy=proxy, audit_sink=network_audit)
    topology = PrivateTopologyPolicy.stage6_default()
    for source, destination in (
        (NetworkZone.PUBLIC_EDGE, NetworkZone.APPLICATION),
        (NetworkZone.APPLICATION, NetworkZone.IDENTITY),
        (NetworkZone.APPLICATION, NetworkZone.SECRET_MANAGER),
        (NetworkZone.APPLICATION, NetworkZone.KMS),
        (NetworkZone.APPLICATION, NetworkZone.METADATA_DB),
        (NetworkZone.APPLICATION, NetworkZone.OBJECT_STORAGE),
        (NetworkZone.APPLICATION, NetworkZone.QUEUE),
        (NetworkZone.APPLICATION, NetworkZone.AUDIT),
    ):
        topology.authorize(source=source, destination=destination, workload_authenticated=True, audit_sink=network_audit)

    identity = _identity_adapter().authenticate_bearer_token("synthetic-token")
    if identity.tenant_key is None or identity.subject_key is None:
        raise IntegrationSecurityRegressionError("opaque production identity was not derived")

    secret = SecretReference("production", "db-credential", "database")
    key = KeyReference("production", "artifact-key", "score-artifact")
    workload = _workload_identity()
    audit = _SecurityAuditMemory()
    iam = _iam(secret, key)
    secret_value = ProductionSecretResolver(iam, _SecretBackend(), audit, clock=lambda: _NOW).resolve(secret, workload)
    context = EncryptionContext(
        environment="production",
        purpose="score-artifact",
        tenant_key=identity.tenant_key,
        object_key="synthetic-object-1",
    )
    crypto = ProductionEnvelopeCrypto(iam, _KmsBackend(), audit, clock=lambda: _NOW)
    envelope = crypto.encrypt(b"synthetic-score-bytes", key, context, workload)
    plaintext = crypto.decrypt(envelope, key, context, workload)

    storage_audit = MemoryStorageAuditSink()
    authorize_metadata_database(
        MetadataDatabaseEvidence(
            database_alias="synthetic-db",
            managed_external_service=True,
            encryption_at_rest=True,
            transport_encryption=True,
            transactional_writes=True,
            migration_plan_validated=True,
            backward_compatibility_validated=True,
            rollback_path_validated=True,
            tenant_scope_enforced=True,
            workload_identity_required=True,
            point_in_time_recovery_capable=True,
            schema_version_monotonic=True,
        ),
        audit_sink=storage_audit,
    )
    authorize_object_storage(
        ObjectStorageEvidence(
            bucket_alias="synthetic-object-store",
            encrypted_at_rest=True,
            kms_or_equivalent_key_separation=True,
            transport_encryption=True,
            content_address_integrity=True,
            tenant_namespace_enforced=True,
            versioning_or_equivalent_recovery=True,
            lifecycle_policy_bound=True,
            public_access_blocked=True,
            workload_identity_required=True,
        ),
        audit_sink=storage_audit,
    )
    authorize_audit_store(
        AuditStoreEvidence(
            store_alias="synthetic-audit",
            append_only=True,
            hash_chain_validated=True,
            independent_anti_rollback_anchor=True,
            immutable_retention=True,
            tenant_scope_enforced=True,
            workload_identity_required=True,
            privacy_safe_payload_policy=True,
        ),
        audit_sink=storage_audit,
    )
    authorize_environment_isolation(
        EnvironmentIsolationEvidence(
            environment="production",
            account_or_project_isolated=True,
            credentials_isolated=True,
            network_namespace_isolated=True,
            storage_namespace_isolated=True,
            queue_namespace_isolated=True,
            audit_namespace_isolated=True,
            cross_environment_write_forbidden=True,
        ),
        audit_sink=storage_audit,
    )
    claim = authorize_queue_claim(
        QueueClaimEvidence(
            queue_alias="synthetic-queue",
            job_id="synthetic-job",
            lease_token="lease-1",
            fencing_token=1,
            idempotency_digest=_IDEMPOTENCY_DIGEST,
            durable_broker=True,
            worker_identity_authenticated=True,
            lease_expiry_persisted=True,
            state_transition_committed_before_ack=True,
            redelivery_supported=True,
        ),
        previous_fencing_token=0,
        audit_sink=storage_audit,
    )
    authorize_deployment_candidate(
        _deployment_candidate(activate=False),
        production_deployment_authorized=False,
        audit_sink=storage_audit,
    )

    passed = (
        ingress.proxy_id == "edge-1"
        and identity.production is True
        and secret_value.concrete_version == "v1"
        and plaintext == b"synthetic-score-bytes"
        and envelope.context_digest == context.canonical_digest()
        and claim.fencing_token == 1
        and len(audit.events) == 3
        and len(storage_audit.events) >= 6
    )
    return RegressionResult(
        name="trusted_edge_identity_iam_kms_storage_chain",
        passed=passed,
        assertions=(
            "trusted_edge_admitted",
            "signed_identity_opaque_tenant_derived",
            "least_privilege_secret_read",
            "tenant_bound_envelope_round_trip",
            "durable_storage_queue_contracts_agree",
            "deployment_candidate_does_not_activate_production",
        ),
    )


def _regression_legacy_identity_bypass_denied() -> RegressionResult:
    adapter = _identity_adapter()
    api = ProductionApiV1(
        object(),
        JobApiConfig("development-client-key-123", "development-reviewer-key-456"),
        adapter,
        _AuthorizationStore(),
    )
    static_response = api.handle(
        "GET",
        "/api/v1/restoration-jobs/synthetic-job",
        {"X-Api-Key": "legacy-key-that-must-not-work"},
    )
    actor_response = api.handle(
        "GET",
        "/api/v1/restoration-jobs/synthetic-job",
        {"Authorization": "Bearer synthetic-token", "X-Actor-Id": "caller-controlled"},
    )
    return RegressionResult(
        name="legacy_identity_header_bypass_denied",
        passed=(
            static_response.status == 401
            and _response_error_code(static_response) == "production_static_credential_forbidden"
            and actor_response.status == 400
            and _response_error_code(actor_response) == "caller_supplied_identity_forbidden"
        ),
        assertions=("static_api_key_denied", "caller_supplied_actor_id_denied"),
    )


def _regression_cross_tenant_job_access_denied() -> RegressionResult:
    adapter = _identity_adapter(tenant="tenant-a")
    other_identity = _identity_adapter(tenant="tenant-b").authenticate_bearer_token("synthetic-token-b")
    assert other_identity.tenant_key is not None and other_identity.subject_key is not None
    store = _AuthorizationStore(
        {
            "synthetic-job": JobAuthorizationContext(
                tenant_key=other_identity.tenant_key,
                owner_key=other_identity.subject_key,
            )
        }
    )
    api = ProductionApiV1(
        object(),
        JobApiConfig("development-client-key-123", "development-reviewer-key-456"),
        adapter,
        store,
    )
    response = api.handle(
        "GET",
        "/api/v1/restoration-jobs/synthetic-job",
        {"Authorization": "Bearer synthetic-token"},
    )
    return RegressionResult(
        name="cross_tenant_job_access_denied",
        passed=response.status == 403 and _response_error_code(response) == "tenant_access_forbidden",
        assertions=("tenant_binding_enforced_before_local_job_access",),
    )


def _regression_identity_conflict_revocation_signature_denied() -> RegressionResult:
    conflict = _expect_job_error(
        lambda: _identity_adapter(roles=("client", "reviewer")).authenticate_bearer_token("synthetic-token"),
        "identity_role_conflict",
    )
    revoked = _expect_job_error(
        lambda: _identity_adapter(revoked=True).authenticate_bearer_token("synthetic-token"),
        "identity_token_revoked",
    )
    unsigned = _expect_job_error(
        lambda: _identity_adapter(signature_validated=False).authenticate_bearer_token("synthetic-token"),
        "identity_signature_not_validated",
    )
    return RegressionResult(
        name="identity_conflict_revocation_signature_denied",
        passed=conflict and revoked and unsigned,
        assertions=("role_conflict_denied", "revoked_token_denied", "unvalidated_signature_denied"),
    )


def _regression_cross_environment_secret_kms_denied() -> RegressionResult:
    secret = SecretReference("production", "db-credential", "database")
    key = KeyReference("production", "artifact-key", "score-artifact")
    iam = _iam(secret, key)
    workload = _workload_identity()
    audit = _SecurityAuditMemory()
    staging_secret = SecretReference("staging", "db-credential", "database")
    staging_key = KeyReference("staging", "artifact-key", "score-artifact")
    secret_denied = _expect_security_error(
        lambda: ProductionSecretResolver(iam, _SecretBackend(), audit, clock=lambda: _NOW).resolve(staging_secret, workload),
        "iam_environment_boundary_violation",
    )
    context = EncryptionContext(
        environment="staging",
        purpose="score-artifact",
        tenant_key="tenant:sha256:" + ("2" * 64),
        object_key="synthetic-object-2",
    )
    kms_denied = _expect_security_error(
        lambda: ProductionEnvelopeCrypto(iam, _KmsBackend(), audit, clock=lambda: _NOW).encrypt(
            b"synthetic", staging_key, context, workload
        ),
        "iam_environment_boundary_violation",
    )
    return RegressionResult(
        name="cross_environment_secret_kms_denied",
        passed=secret_denied and kms_denied,
        assertions=("secret_environment_isolation", "kms_environment_isolation"),
    )


def _regression_security_audit_dependency_fail_closed() -> RegressionResult:
    secret = SecretReference("production", "db-credential", "database")
    key = KeyReference("production", "artifact-key", "score-artifact")
    iam = _iam(secret, key)
    blocked = _expect_security_error(
        lambda: ProductionSecretResolver(
            iam,
            _SecretBackend(),
            _SecurityAuditMemory(accept=False),
            clock=lambda: _NOW,
        ).resolve(secret, _workload_identity()),
        "security_audit_unavailable",
    )
    return RegressionResult(
        name="security_audit_dependency_fail_closed",
        passed=blocked,
        assertions=("secret_not_released_when_security_audit_commit_fails",),
    )


def _regression_edge_and_topology_bypass_denied() -> RegressionResult:
    proxy = TrustedProxyPolicy.from_cidrs(trusted_proxy_ids=("edge-1",), cidrs=("10.20.30.0/24",))
    untrusted = _expect_network_error(
        lambda: authorize_public_ingress(
            _edge_evidence(proxy_id="attacker-edge"),
            proxy_policy=proxy,
            audit_sink=MemoryNetworkAuditSink(),
        ),
        "untrusted_proxy_peer",
    )
    builtin = _expect_network_error(
        lambda: authorize_public_ingress(
            _edge_evidence(built_in_public=True),
            proxy_policy=proxy,
            audit_sink=MemoryNetworkAuditSink(),
        ),
        "builtin_server_public_exposure_forbidden",
    )
    quarantine = _expect_network_error(
        lambda: PrivateTopologyPolicy.stage6_default().authorize(
            source=NetworkZone.QUARANTINE,
            destination=NetworkZone.APPLICATION,
            workload_authenticated=True,
            audit_sink=MemoryNetworkAuditSink(),
        ),
        "quarantine_outbound_forbidden",
    )
    edge_bypass = _expect_network_error(
        lambda: PrivateTopologyPolicy.stage6_default().authorize(
            source=NetworkZone.PUBLIC_EDGE,
            destination=NetworkZone.METADATA_DB,
            workload_authenticated=True,
            audit_sink=MemoryNetworkAuditSink(),
        ),
        "public_edge_internal_bypass_forbidden",
    )
    return RegressionResult(
        name="edge_and_private_topology_bypass_denied",
        passed=untrusted and builtin and quarantine and edge_bypass,
        assertions=(
            "untrusted_proxy_denied",
            "builtin_server_public_exposure_denied",
            "quarantine_egress_denied",
            "public_edge_database_bypass_denied",
        ),
    )


def _regression_storage_and_deployment_fail_closed() -> RegressionResult:
    sink = MemoryStorageAuditSink()
    stale = _expect_storage_error(
        lambda: authorize_queue_claim(
            QueueClaimEvidence(
                queue_alias="synthetic-queue",
                job_id="synthetic-job",
                lease_token="lease-stale",
                fencing_token=4,
                idempotency_digest=_IDEMPOTENCY_DIGEST,
                durable_broker=True,
                worker_identity_authenticated=True,
                lease_expiry_persisted=True,
                state_transition_committed_before_ack=True,
                redelivery_supported=True,
            ),
            previous_fencing_token=4,
            audit_sink=sink,
        ),
        "stale_or_invalid_fencing_token",
    )
    activation = _expect_storage_error(
        lambda: authorize_deployment_candidate(
            _deployment_candidate(activate=True),
            production_deployment_authorized=False,
            audit_sink=sink,
        ),
        "production_deployment_not_authorized",
    )
    no_audit = _expect_storage_error(
        lambda: authorize_metadata_database(
            MetadataDatabaseEvidence(
                database_alias="synthetic-db",
                managed_external_service=True,
                encryption_at_rest=True,
                transport_encryption=True,
                transactional_writes=True,
                migration_plan_validated=True,
                backward_compatibility_validated=True,
                rollback_path_validated=True,
                tenant_scope_enforced=True,
                workload_identity_required=True,
                point_in_time_recovery_capable=True,
                schema_version_monotonic=True,
            ),
            audit_sink=MemoryStorageAuditSink(accept=False),
        ),
        "storage_audit_unavailable",
    )
    return RegressionResult(
        name="storage_queue_deployment_fail_closed",
        passed=stale and activation and no_audit,
        assertions=("stale_worker_denied", "production_activation_denied", "storage_audit_required"),
    )


def _regression_s6_07_replay() -> RegressionResult:
    report = run_synthetic_operational_drills()
    return RegressionResult(
        name="s6_07_operational_regression_replay",
        passed=(
            report.passed
            and report.synthetic_only is True
            and report.provider_calls_performed is False
            and report.production_state_mutated is False
            and report.production_deployment_performed is False
        ),
        assertions=("all_s6_07_drills_still_pass", "no_live_boundary_crossed"),
    )


def run_integration_security_regression() -> IntegrationSecurityRegressionReport:
    report = IntegrationSecurityRegressionReport(
        schema_version="1.0.0",
        synthetic_only=True,
        provider_calls_performed=False,
        live_resources_created=False,
        production_state_mutated=False,
        production_deployment_performed=False,
        results=(
            _regression_trusted_chain(),
            _regression_legacy_identity_bypass_denied(),
            _regression_cross_tenant_job_access_denied(),
            _regression_identity_conflict_revocation_signature_denied(),
            _regression_cross_environment_secret_kms_denied(),
            _regression_security_audit_dependency_fail_closed(),
            _regression_edge_and_topology_bypass_denied(),
            _regression_storage_and_deployment_fail_closed(),
            _regression_s6_07_replay(),
        ),
    )
    validate_integration_security_regression_report(report)
    return report


def validate_integration_security_regression_report(report: IntegrationSecurityRegressionReport) -> None:
    if report.schema_version != "1.0.0":
        raise IntegrationSecurityRegressionError("integration regression schema drifted")
    if report.synthetic_only is not True:
        raise IntegrationSecurityRegressionError("S6-08 integration regression must remain synthetic-only")
    if (
        report.provider_calls_performed
        or report.live_resources_created
        or report.production_state_mutated
        or report.production_deployment_performed
    ):
        raise IntegrationSecurityRegressionError("S6-08 crossed an unauthorized production boundary")
    expected_names = (
        "trusted_edge_identity_iam_kms_storage_chain",
        "legacy_identity_header_bypass_denied",
        "cross_tenant_job_access_denied",
        "identity_conflict_revocation_signature_denied",
        "cross_environment_secret_kms_denied",
        "security_audit_dependency_fail_closed",
        "edge_and_private_topology_bypass_denied",
        "storage_queue_deployment_fail_closed",
        "s6_07_operational_regression_replay",
    )
    if tuple(result.name for result in report.results) != expected_names:
        raise IntegrationSecurityRegressionError("integration security regression inventory drifted")
    failed = [result.name for result in report.results if result.passed is not True]
    if failed:
        raise IntegrationSecurityRegressionError("integration security regressions failed: " + ", ".join(failed))


__all__ = [
    "IntegrationSecurityRegressionError",
    "IntegrationSecurityRegressionReport",
    "RegressionResult",
    "run_integration_security_regression",
    "validate_integration_security_regression_report",
]
