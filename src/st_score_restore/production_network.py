"""Provider-neutral Stage 6 production-network security boundary.

This module deliberately does not create sockets, DNS records, certificates, WAF
rules, load balancers, VPCs or cloud resources. It validates evidence supplied by
an approved production edge/provider adapter and fails closed when required
network-security evidence is missing or ambiguous.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import ipaddress
from typing import Iterable, Mapping, Protocol, Sequence


class NetworkSecurityError(ValueError):
    """Raised when a production-network security boundary rejects an action."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class NetworkZone(str, Enum):
    PUBLIC_EDGE = "public_edge"
    APPLICATION = "application"
    WORKER = "worker"
    METADATA_DB = "metadata_db"
    OBJECT_STORAGE = "object_storage"
    QUEUE = "queue"
    QUARANTINE = "quarantine"
    IDENTITY = "identity"
    SECRET_MANAGER = "secret_manager"
    KMS = "kms"
    AUDIT = "audit"


class NetworkAuditSink(Protocol):
    def record(self, event: Mapping[str, object]) -> bool:
        """Return True only when privacy-safe audit evidence was durably accepted."""


@dataclass
class MemoryNetworkAuditSink:
    """Test-only audit sink. Production must supply its separately approved sink."""

    accept: bool = True
    events: list[dict[str, object]] = field(default_factory=list)

    def record(self, event: Mapping[str, object]) -> bool:
        if not self.accept:
            return False
        self.events.append(dict(event))
        return True


@dataclass(frozen=True)
class TrustedProxyPolicy:
    trusted_proxy_ids: frozenset[str]
    trusted_peer_networks: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]

    @classmethod
    def from_cidrs(cls, *, trusted_proxy_ids: Iterable[str], cidrs: Iterable[str]) -> "TrustedProxyPolicy":
        proxy_ids = frozenset(value.strip() for value in trusted_proxy_ids if value.strip())
        if not proxy_ids:
            raise NetworkSecurityError("trusted_proxy_config_empty", "at least one trusted proxy id is required")
        networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        for cidr in cidrs:
            try:
                networks.append(ipaddress.ip_network(cidr, strict=True))
            except ValueError as exc:
                raise NetworkSecurityError("trusted_proxy_cidr_invalid", "trusted proxy CIDR is invalid") from exc
        if not networks:
            raise NetworkSecurityError("trusted_proxy_config_empty", "at least one trusted proxy network is required")
        return cls(trusted_proxy_ids=proxy_ids, trusted_peer_networks=tuple(networks))

    def peer_is_trusted(self, *, proxy_id: str, peer_ip: str) -> bool:
        if proxy_id not in self.trusted_proxy_ids:
            return False
        try:
            address = ipaddress.ip_address(peer_ip)
        except ValueError:
            return False
        return any(address in network for network in self.trusted_peer_networks)


@dataclass(frozen=True)
class PublicEdgeEvidence:
    proxy_id: str
    peer_ip: str
    canonical_forwarded_for: str
    tls_terminated_by_managed_edge: bool
    tls_peer_policy_validated: bool
    proxy_workload_authenticated: bool
    forwarded_headers_rewritten_not_appended: bool
    hop_by_hop_headers_stripped: bool
    single_host_normalized: bool
    transfer_encoding_removed: bool
    content_length_canonicalized: bool
    request_target_normalized: bool
    request_smuggling_check_passed: bool
    waf_check_passed: bool
    rate_limit_check_passed: bool
    quota_check_passed: bool
    connection_limit_check_passed: bool
    request_body_limit_check_passed: bool
    header_limit_check_passed: bool
    slow_client_check_passed: bool
    multipart_boundary_check_passed: bool
    built_in_stdlib_server_publicly_exposed: bool = False


@dataclass(frozen=True)
class CanonicalIngressIdentity:
    client_ip: str
    proxy_id: str


def _audit_or_fail(sink: NetworkAuditSink, event: Mapping[str, object]) -> None:
    try:
        accepted = sink.record(event)
    except Exception as exc:  # pragma: no cover - defensive provider boundary
        raise NetworkSecurityError("network_audit_unavailable", "network audit dependency failed") from exc
    if accepted is not True:
        raise NetworkSecurityError("network_audit_unavailable", "network audit evidence was not accepted")


def _deny(sink: NetworkAuditSink, reason_code: str, *, category: str, subject: str) -> None:
    _audit_or_fail(
        sink,
        {
            "event": "network_security_decision",
            "category": category,
            "subject": subject,
            "decision": "deny",
            "reason_code": reason_code,
        },
    )
    raise NetworkSecurityError(reason_code, f"network security policy denied {category}")


def authorize_public_ingress(
    evidence: PublicEdgeEvidence,
    *,
    proxy_policy: TrustedProxyPolicy,
    audit_sink: NetworkAuditSink,
) -> CanonicalIngressIdentity:
    """Validate canonical ingress evidence from a trusted production edge.

    Forwarding headers are accepted only after a trusted, workload-authenticated
    edge rewrites them to one canonical client address. Raw multi-hop or
    caller-appended chains are rejected rather than interpreted heuristically.
    """

    if evidence.built_in_stdlib_server_publicly_exposed:
        _deny(audit_sink, "builtin_server_public_exposure_forbidden", category="ingress", subject="public_edge")
    if not proxy_policy.peer_is_trusted(proxy_id=evidence.proxy_id, peer_ip=evidence.peer_ip):
        _deny(audit_sink, "untrusted_proxy_peer", category="ingress", subject="public_edge")
    if not evidence.proxy_workload_authenticated:
        _deny(audit_sink, "proxy_workload_not_authenticated", category="ingress", subject=evidence.proxy_id)
    if not evidence.tls_terminated_by_managed_edge or not evidence.tls_peer_policy_validated:
        _deny(audit_sink, "managed_tls_evidence_missing", category="ingress", subject=evidence.proxy_id)
    if not evidence.forwarded_headers_rewritten_not_appended:
        _deny(audit_sink, "forwarded_header_policy_ambiguous", category="ingress", subject=evidence.proxy_id)

    raw_client = evidence.canonical_forwarded_for.strip()
    if not raw_client or "," in raw_client or " " in raw_client or "\t" in raw_client:
        _deny(audit_sink, "forwarded_client_ip_not_canonical", category="ingress", subject=evidence.proxy_id)
    try:
        client_ip = ipaddress.ip_address(raw_client).compressed
    except ValueError:
        _deny(audit_sink, "forwarded_client_ip_invalid", category="ingress", subject=evidence.proxy_id)
        raise AssertionError("unreachable")

    normalization_checks = {
        "hop_by_hop_headers_stripped": evidence.hop_by_hop_headers_stripped,
        "single_host_normalized": evidence.single_host_normalized,
        "transfer_encoding_removed": evidence.transfer_encoding_removed,
        "content_length_canonicalized": evidence.content_length_canonicalized,
        "request_target_normalized": evidence.request_target_normalized,
        "request_smuggling_check_passed": evidence.request_smuggling_check_passed,
        "multipart_boundary_check_passed": evidence.multipart_boundary_check_passed,
    }
    for name, passed in normalization_checks.items():
        if passed is not True:
            _deny(audit_sink, f"edge_normalization_failed:{name}", category="ingress", subject=evidence.proxy_id)

    admission_checks = {
        "waf": evidence.waf_check_passed,
        "rate_limit": evidence.rate_limit_check_passed,
        "quota": evidence.quota_check_passed,
        "connection_limit": evidence.connection_limit_check_passed,
        "request_body_limit": evidence.request_body_limit_check_passed,
        "header_limit": evidence.header_limit_check_passed,
        "slow_client": evidence.slow_client_check_passed,
    }
    for name, passed in admission_checks.items():
        if passed is not True:
            _deny(audit_sink, f"edge_admission_failed:{name}", category="ingress", subject=evidence.proxy_id)

    _audit_or_fail(
        audit_sink,
        {
            "event": "network_security_decision",
            "category": "ingress",
            "subject": evidence.proxy_id,
            "decision": "allow",
            "reason_code": "trusted_edge_admission_complete",
        },
    )
    return CanonicalIngressIdentity(client_ip=client_ip, proxy_id=evidence.proxy_id)


@dataclass(frozen=True)
class PrivateTopologyPolicy:
    allowed_connections: frozenset[tuple[NetworkZone, NetworkZone]]

    @classmethod
    def stage6_default(cls) -> "PrivateTopologyPolicy":
        return cls(
            allowed_connections=frozenset(
                {
                    (NetworkZone.PUBLIC_EDGE, NetworkZone.APPLICATION),
                    (NetworkZone.APPLICATION, NetworkZone.IDENTITY),
                    (NetworkZone.APPLICATION, NetworkZone.SECRET_MANAGER),
                    (NetworkZone.APPLICATION, NetworkZone.KMS),
                    (NetworkZone.APPLICATION, NetworkZone.METADATA_DB),
                    (NetworkZone.APPLICATION, NetworkZone.OBJECT_STORAGE),
                    (NetworkZone.APPLICATION, NetworkZone.QUEUE),
                    (NetworkZone.APPLICATION, NetworkZone.AUDIT),
                    (NetworkZone.APPLICATION, NetworkZone.QUARANTINE),
                    (NetworkZone.WORKER, NetworkZone.SECRET_MANAGER),
                    (NetworkZone.WORKER, NetworkZone.KMS),
                    (NetworkZone.WORKER, NetworkZone.METADATA_DB),
                    (NetworkZone.WORKER, NetworkZone.OBJECT_STORAGE),
                    (NetworkZone.WORKER, NetworkZone.QUEUE),
                    (NetworkZone.WORKER, NetworkZone.AUDIT),
                }
            )
        )

    def authorize(
        self,
        *,
        source: NetworkZone,
        destination: NetworkZone,
        workload_authenticated: bool,
        audit_sink: NetworkAuditSink,
    ) -> None:
        subject = f"{source.value}->{destination.value}"
        if source is NetworkZone.QUARANTINE:
            _deny(audit_sink, "quarantine_outbound_forbidden", category="service_connection", subject=subject)
        if source is NetworkZone.PUBLIC_EDGE and destination is not NetworkZone.APPLICATION:
            _deny(audit_sink, "public_edge_internal_bypass_forbidden", category="service_connection", subject=subject)
        if (source, destination) not in self.allowed_connections:
            _deny(audit_sink, "private_topology_connection_not_allowed", category="service_connection", subject=subject)
        if not workload_authenticated:
            _deny(audit_sink, "workload_identity_required", category="service_connection", subject=subject)
        _audit_or_fail(
            audit_sink,
            {
                "event": "network_security_decision",
                "category": "service_connection",
                "subject": subject,
                "decision": "allow",
                "reason_code": "private_topology_connection_allowed",
            },
        )


@dataclass(frozen=True)
class ApprovedEgressTarget:
    alias: str
    scheme: str
    host: str
    port: int
    allow_private_resolution: bool = False

    def __post_init__(self) -> None:
        alias = self.alias.strip()
        host = self.host.strip().lower().rstrip(".")
        if not alias or alias != self.alias:
            raise NetworkSecurityError("egress_target_alias_invalid", "egress target alias must be canonical")
        if self.scheme != "https":
            raise NetworkSecurityError("egress_target_scheme_invalid", "production egress targets must use https")
        if not host or host != self.host:
            raise NetworkSecurityError("egress_target_host_invalid", "egress target host must be canonical lowercase DNS")
        if self.port < 1 or self.port > 65535:
            raise NetworkSecurityError("egress_target_port_invalid", "egress target port is invalid")
        if host == "localhost" or host.endswith((".localhost", ".local")):
            raise NetworkSecurityError("egress_target_host_forbidden", "local hostnames are forbidden")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise NetworkSecurityError("egress_ip_literal_forbidden", "egress allowlists must use approved DNS names")
        if ":" in host or "/" in host or "@" in host or "#" in host or "?" in host:
            raise NetworkSecurityError("egress_target_host_invalid", "egress target host is not a DNS name")


@dataclass(frozen=True)
class EgressRequest:
    alias: str
    scheme: str
    host: str
    port: int
    resolved_ips: tuple[str, ...]
    dns_security_evidence_valid: bool
    destination_not_user_controlled: bool


@dataclass(frozen=True)
class EgressPolicy:
    targets: Mapping[str, ApprovedEgressTarget]

    @classmethod
    def from_targets(cls, targets: Sequence[ApprovedEgressTarget]) -> "EgressPolicy":
        result: dict[str, ApprovedEgressTarget] = {}
        for target in targets:
            if target.alias in result:
                raise NetworkSecurityError("egress_target_alias_duplicate", "egress target aliases must be unique")
            result[target.alias] = target
        if not result:
            raise NetworkSecurityError("egress_allowlist_empty", "egress policy requires explicit targets")
        return cls(targets=result)

    def authorize(
        self,
        request: EgressRequest,
        *,
        source: NetworkZone,
        workload_authenticated: bool,
        audit_sink: NetworkAuditSink,
    ) -> ApprovedEgressTarget:
        if source is NetworkZone.QUARANTINE:
            _deny(audit_sink, "quarantine_outbound_forbidden", category="egress", subject=request.alias)
        target = self.targets.get(request.alias)
        if target is None:
            _deny(audit_sink, "egress_alias_not_allowed", category="egress", subject=request.alias)
        assert target is not None
        if not workload_authenticated:
            _deny(audit_sink, "workload_identity_required", category="egress", subject=request.alias)
        if not request.destination_not_user_controlled:
            _deny(audit_sink, "user_controlled_egress_destination_forbidden", category="egress", subject=request.alias)
        if not request.dns_security_evidence_valid:
            _deny(audit_sink, "dns_security_evidence_missing", category="egress", subject=request.alias)
        if (
            request.scheme != target.scheme
            or request.host.strip().lower().rstrip(".") != target.host
            or request.port != target.port
        ):
            _deny(audit_sink, "egress_destination_mismatch", category="egress", subject=request.alias)
        if not request.resolved_ips:
            _deny(audit_sink, "dns_resolution_evidence_missing", category="egress", subject=request.alias)

        for raw_address in request.resolved_ips:
            try:
                address = ipaddress.ip_address(raw_address)
            except ValueError:
                _deny(audit_sink, "resolved_address_invalid", category="egress", subject=request.alias)
            if address.is_loopback or address.is_link_local or address.is_multicast or address.is_unspecified or address.is_reserved:
                _deny(audit_sink, "resolved_address_forbidden", category="egress", subject=request.alias)
            if address.is_private and not target.allow_private_resolution:
                _deny(audit_sink, "private_resolution_not_allowed", category="egress", subject=request.alias)

        _audit_or_fail(
            audit_sink,
            {
                "event": "network_security_decision",
                "category": "egress",
                "subject": request.alias,
                "decision": "allow",
                "reason_code": "approved_egress_target",
            },
        )
        return target


__all__ = [
    "ApprovedEgressTarget",
    "CanonicalIngressIdentity",
    "EgressPolicy",
    "EgressRequest",
    "MemoryNetworkAuditSink",
    "NetworkAuditSink",
    "NetworkSecurityError",
    "NetworkZone",
    "PrivateTopologyPolicy",
    "PublicEdgeEvidence",
    "TrustedProxyPolicy",
    "authorize_public_ingress",
]
