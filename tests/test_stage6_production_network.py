from __future__ import annotations

import unittest

from st_score_restore.production_network import (
    ApprovedEgressTarget,
    EgressPolicy,
    EgressRequest,
    MemoryNetworkAuditSink,
    NetworkSecurityError,
    NetworkZone,
    PrivateTopologyPolicy,
    PublicEdgeEvidence,
    TrustedProxyPolicy,
    authorize_public_ingress,
)


def valid_edge(**overrides) -> PublicEdgeEvidence:
    values = dict(
        proxy_id="edge-a",
        peer_ip="10.0.0.10",
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
        built_in_stdlib_server_publicly_exposed=False,
    )
    values.update(overrides)
    return PublicEdgeEvidence(**values)


class ProductionNetworkTests(unittest.TestCase):
    def setUp(self):
        self.audit = MemoryNetworkAuditSink()
        self.proxy_policy = TrustedProxyPolicy.from_cidrs(
            trusted_proxy_ids={"edge-a"}, cidrs={"10.0.0.0/24"}
        )

    def test_valid_trusted_edge_admission_returns_canonical_client(self):
        identity = authorize_public_ingress(valid_edge(), proxy_policy=self.proxy_policy, audit_sink=self.audit)
        self.assertEqual("203.0.113.25", identity.client_ip)
        self.assertEqual("edge-a", identity.proxy_id)
        self.assertEqual("allow", self.audit.events[-1]["decision"])
        self.assertNotIn("client_ip", self.audit.events[-1])

    def test_untrusted_proxy_cannot_assert_forwarded_identity(self):
        with self.assertRaisesRegex(NetworkSecurityError, "ingress") as ctx:
            authorize_public_ingress(
                valid_edge(peer_ip="10.0.1.10"), proxy_policy=self.proxy_policy, audit_sink=self.audit
            )
        self.assertEqual("untrusted_proxy_peer", ctx.exception.reason_code)

    def test_multi_hop_or_caller_appended_forwarded_chain_is_rejected(self):
        with self.assertRaises(NetworkSecurityError) as ctx:
            authorize_public_ingress(
                valid_edge(canonical_forwarded_for="203.0.113.25, 198.51.100.8"),
                proxy_policy=self.proxy_policy,
                audit_sink=self.audit,
            )
        self.assertEqual("forwarded_client_ip_not_canonical", ctx.exception.reason_code)

    def test_missing_smuggling_or_abuse_control_evidence_fails_closed(self):
        for field in (
            "request_smuggling_check_passed",
            "waf_check_passed",
            "rate_limit_check_passed",
            "quota_check_passed",
            "connection_limit_check_passed",
            "request_body_limit_check_passed",
            "header_limit_check_passed",
            "slow_client_check_passed",
            "multipart_boundary_check_passed",
        ):
            with self.subTest(field=field):
                with self.assertRaises(NetworkSecurityError):
                    authorize_public_ingress(
                        valid_edge(**{field: False}), proxy_policy=self.proxy_policy, audit_sink=MemoryNetworkAuditSink()
                    )

    def test_builtin_stdlib_server_public_exposure_is_forbidden(self):
        with self.assertRaises(NetworkSecurityError) as ctx:
            authorize_public_ingress(
                valid_edge(built_in_stdlib_server_publicly_exposed=True),
                proxy_policy=self.proxy_policy,
                audit_sink=self.audit,
            )
        self.assertEqual("builtin_server_public_exposure_forbidden", ctx.exception.reason_code)

    def test_audit_failure_fails_closed_even_for_otherwise_valid_ingress(self):
        with self.assertRaises(NetworkSecurityError) as ctx:
            authorize_public_ingress(
                valid_edge(), proxy_policy=self.proxy_policy, audit_sink=MemoryNetworkAuditSink(accept=False)
            )
        self.assertEqual("network_audit_unavailable", ctx.exception.reason_code)

    def test_private_topology_allows_edge_only_to_application(self):
        topology = PrivateTopologyPolicy.stage6_default()
        topology.authorize(
            source=NetworkZone.PUBLIC_EDGE,
            destination=NetworkZone.APPLICATION,
            workload_authenticated=True,
            audit_sink=self.audit,
        )
        with self.assertRaises(NetworkSecurityError) as ctx:
            topology.authorize(
                source=NetworkZone.PUBLIC_EDGE,
                destination=NetworkZone.METADATA_DB,
                workload_authenticated=True,
                audit_sink=self.audit,
            )
        self.assertEqual("public_edge_internal_bypass_forbidden", ctx.exception.reason_code)

    def test_quarantine_has_no_outbound_network(self):
        topology = PrivateTopologyPolicy.stage6_default()
        with self.assertRaises(NetworkSecurityError) as ctx:
            topology.authorize(
                source=NetworkZone.QUARANTINE,
                destination=NetworkZone.OBJECT_STORAGE,
                workload_authenticated=True,
                audit_sink=self.audit,
            )
        self.assertEqual("quarantine_outbound_forbidden", ctx.exception.reason_code)

    def test_egress_requires_exact_alias_destination_and_dns_evidence(self):
        policy = EgressPolicy.from_targets(
            [ApprovedEgressTarget(alias="status-api", scheme="https", host="status.example.com", port=443)]
        )
        target = policy.authorize(
            EgressRequest(
                alias="status-api",
                scheme="https",
                host="status.example.com",
                port=443,
                resolved_ips=("8.8.8.8",),
                dns_security_evidence_valid=True,
                destination_not_user_controlled=True,
            ),
            source=NetworkZone.APPLICATION,
            workload_authenticated=True,
            audit_sink=self.audit,
        )
        self.assertEqual("status-api", target.alias)

        with self.assertRaises(NetworkSecurityError):
            policy.authorize(
                EgressRequest(
                    alias="status-api",
                    scheme="https",
                    host="evil.example",
                    port=443,
                    resolved_ips=("8.8.8.8",),
                    dns_security_evidence_valid=True,
                    destination_not_user_controlled=True,
                ),
                source=NetworkZone.APPLICATION,
                workload_authenticated=True,
                audit_sink=self.audit,
            )

    def test_ssrf_guards_reject_ip_literal_targets_and_private_rebinding(self):
        with self.assertRaises(NetworkSecurityError) as ctx:
            ApprovedEgressTarget(alias="metadata", scheme="https", host="169.254.169.254", port=443)
        self.assertEqual("egress_ip_literal_forbidden", ctx.exception.reason_code)

        policy = EgressPolicy.from_targets(
            [ApprovedEgressTarget(alias="external-api", scheme="https", host="api.example.com", port=443)]
        )
        with self.assertRaises(NetworkSecurityError) as ctx:
            policy.authorize(
                EgressRequest(
                    alias="external-api",
                    scheme="https",
                    host="api.example.com",
                    port=443,
                    resolved_ips=("10.10.10.10",),
                    dns_security_evidence_valid=True,
                    destination_not_user_controlled=True,
                ),
                source=NetworkZone.WORKER,
                workload_authenticated=True,
                audit_sink=self.audit,
            )
        self.assertEqual("private_resolution_not_allowed", ctx.exception.reason_code)

    def test_approved_private_service_resolution_must_be_explicit(self):
        policy = EgressPolicy.from_targets(
            [
                ApprovedEgressTarget(
                    alias="private-kms-endpoint",
                    scheme="https",
                    host="kms.service.example",
                    port=443,
                    allow_private_resolution=True,
                )
            ]
        )
        policy.authorize(
            EgressRequest(
                alias="private-kms-endpoint",
                scheme="https",
                host="kms.service.example",
                port=443,
                resolved_ips=("10.20.0.7",),
                dns_security_evidence_valid=True,
                destination_not_user_controlled=True,
            ),
            source=NetworkZone.WORKER,
            workload_authenticated=True,
            audit_sink=self.audit,
        )


if __name__ == "__main__":
    unittest.main()
