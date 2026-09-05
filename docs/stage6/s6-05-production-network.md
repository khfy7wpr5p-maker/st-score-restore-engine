# Stage 6 S6-05 Production Network / Untrusted-Network Security

- Status: IMPLEMENTATION AUTHORIZED, PROVIDER-NEUTRAL CONTRACT IMPLEMENTED
- Date: 2026-09-05
- Authorization: `stage6.s6-05.production-network-implementation-authorization.v1`
- Entry main: `1c9ff79041bacd89a8e4991ffe698929d2637774`
- Provider selection: `UNSELECTED`

## Purpose

S6-05 implements the provider-neutral security contract that must sit between an
untrusted/public network and the existing ST Score Restore application boundary.
It does not select or provision a reverse proxy, API gateway, WAF, certificate,
DNS record, VPC, firewall, NAT gateway or cloud provider.

The built-in standard-library HTTP server remains a local/internal adapter and is
explicitly forbidden as the public production edge.

## Public ingress contract

A request may enter the application only when a trusted production-edge adapter
provides complete evidence for all of the following:

- managed TLS termination and validated TLS peer policy;
- workload-authenticated trusted proxy identity;
- peer address inside an explicitly approved trusted-proxy network;
- forwarding headers rewritten by the edge rather than appended to caller input;
- exactly one canonical forwarded client IP;
- hop-by-hop headers stripped;
- single Host normalization;
- Transfer-Encoding removed before application ingress;
- one canonical Content-Length decision;
- normalized request target;
- request-smuggling check passed;
- strict multipart boundary check passed;
- WAF decision passed;
- rate-limit and quota decision passed;
- connection-limit decision passed;
- approved body/header limit decision passed;
- slow-client defense decision passed.

Missing, ambiguous or failed evidence is deny-by-default. The application does
not guess how to interpret a multi-hop `Forwarded`/`X-Forwarded-For` chain.
Caller-supplied forwarding identity is never trusted directly.

S6-05 intentionally does not change production threshold or resource-limit
values. It requires evidence that the separately approved limits were enforced.

## Request-smuggling boundary

The local adapter already rejects duplicate/ambiguous `Content-Length`, all
`Transfer-Encoding`, protocol upgrades, trailers, expectations, folded headers,
unsafe targets and malformed multipart framing. S6-05 adds the production-edge
contract: the selected edge must normalize ambiguous framing before forwarding
and must attest that hop-by-hop headers and transfer encodings were removed.

Provider-specific proxy-stack differential tests remain impossible until a
provider/proxy stack is selected. This implementation therefore does not claim a
provider-specific request-smuggling certification.

## Private topology

The provider-neutral topology is deny-by-default. The public edge may connect
only to the application boundary. Direct public-edge access to workers, metadata
database, object storage, queue, KMS, secret manager, audit or quarantine is
forbidden.

Application and worker connections to approved internal services require
workload-authenticated service identity. The topology is represented as explicit
directed grants rather than broad network reachability.

## Quarantine

The quarantine zone has no outbound network permission. Attempts to originate a
network connection from quarantine are denied before provider-specific routing
is considered.

## Egress and SSRF boundary

Outbound destinations use exact service aliases bound to canonical HTTPS DNS
names and ports. Runtime requests must match the approved alias, scheme, host and
port exactly and must not be constructed from user-controlled destinations.

The contract rejects:

- raw IP-literal allowlist targets;
- localhost and `.local` destinations;
- destination mismatch against the approved alias;
- missing DNS-security or resolution evidence;
- loopback, link-local, multicast, unspecified or reserved resolved addresses;
- private-address resolution unless that exact service target explicitly permits
  private resolution.

This is a provider-neutral SSRF/DNS-rebinding guard contract. Provider DNS,
service-mesh or private-endpoint activation is still separate work.

## Privacy-safe audit

Ingress, service-topology and egress decisions require a security-audit sink. A
required audit failure causes the network authorization itself to fail closed.
The network module records reason codes, zones/service aliases and decisions; it
does not place client IPs, request bodies, filenames, secrets, emails or free-text
personal data into its audit event contract.

The durable append-only tamper-evident audit store is still not implemented; that
remains part of later production infrastructure work.

## Not activated by S6-05

S6-05 does not activate or create:

- a provider or provider-specific proxy/API gateway/WAF;
- TLS certificates or DNS;
- VPCs, subnets, security groups, firewall rules or private links;
- NAT/egress gateways;
- live secrets/KMS/IAM bindings;
- live penetration tests or attacks against third-party systems;
- production storage/deployment;
- operational drills on live resources;
- production deployment;
- Stage 7;
- model training, publication, held-out retuning or threshold/resource-limit changes.

## Remaining provider-specific verification

Issue #18 remains relevant after this slice. Once a provider/proxy stack is
separately selected, the project still needs stack-specific TLS/proxy/WAF
configuration evidence, differential request-smuggling tests, longer-running
malformed-input fuzzing, load/slow-client evidence, dependency scanning and an
independent production security sign-off before public exposure.

## Next safe boundary

The next separately authorized implementation boundary is S6-06 production
storage/deployment infrastructure. Provider selection and live resource creation
remain separate decisions.
