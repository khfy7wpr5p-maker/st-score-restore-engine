# Stage 6 S6-02 Production Trust-Boundary Decision

- Status: APPROVED DECISION PACKAGE
- Date: 2026-09-04
- Decision ID: `stage6.s6-02.production-trust-boundary-decision.v1`
- Evidence: `evidence/stage6/governance/stage6-production-trust-boundary-decision.v1.json`
- Evidence canonical SHA-256: `9485e51f1398c6cff2d9be9264eb8acdf47f8c4ca0fc750062fd9e80298e3865`
- Entry current main: `1addd8f8f403c1d038a951842b114eb487bfa044`

## Decision

S6-02 freezes the production trust boundaries and provider-selection criteria.
It authorizes provider-specific evaluation, but no cloud, identity provider,
KMS, database, queue, storage or deployment provider is selected by this
package. Provider selection remains `UNSELECTED` until supported by an explicit
decision record.

This decision does not create production resources and does not authorize live
production deployment.

## Identity architecture

The identity plane is designed to be reusable across applications, but the only
initial relying party is ST Score Restore. Future applications may integrate only
through a separate authorization and must not become implicit dependencies of
ST Score Restore.

Production identity must not trust caller-supplied `X-Actor-Id` or equivalent
identity headers. Static API keys are not accepted as production user identity.
The future production identity adapter must validate signed identity evidence,
including issuer, audience, expiry, not-before and key identity, and support
revocation.

Authorization is deny-by-default and must enforce tenant isolation, ownership,
role-conflict checks and service-to-service workload identity. Audit output must
remain privacy-safe.

## Public edge and network

The built-in standard-library HTTP server remains a local/internal adapter and
must not be the public production edge. Public ingress requires managed TLS
termination or equivalent reverse-proxy/API-gateway protection, trusted-proxy
policy, WAF/rate controls and explicit request-size/concurrency protections.

Application, workers, metadata database, object storage and queue are private by
default. Quarantine has no outbound network access. Production design must cover
egress control, SSRF, request smuggling, multipart parser abuse and denial-of-
service limits.

## Secrets, KMS and IAM

Production requires managed secret storage, envelope encryption, least-privilege
IAM, separation of duties, rotation and revocation. Raw secret material must not
be stored in ordinary Git, committed environment files, application logs or
audit events.

## Persistence and queue

Production requires a transactional relational metadata store, encrypted object
storage and an external durable queue. State changes must preserve idempotency,
fencing and transactional safety. Retention, deletion receipts, backup expiry
and anti-resurrection behavior remain mandatory.

## Audit and recovery

Security-relevant operations require append-only tamper-evident audit evidence,
hash-chain or equivalent integrity, and an independent anti-rollback mechanism.
Audit must not contain artifact bytes, secrets, names, emails or free-text
personal data.

Backup and restore must preserve revocation/tombstone state and must not
resurrect revoked or deleted artifacts.

## Deployment boundary

Production deployment requires immutable artifacts/images, signed provenance,
staging validation, health checks and rollback capability. S6-02 itself does not
authorize deployment or resource creation.

Development, staging and production must use separate security boundaries and
must not share production credentials.

## Provider selection criteria

A future provider decision must demonstrate all of the following before
implementation is activated:

1. managed OIDC or equivalent identity and workload identity;
2. managed KMS/HSM-backed key governance and secret rotation;
3. TLS ingress, WAF/rate controls, private networking and egress control;
4. transactional relational metadata storage;
5. encrypted object storage with lifecycle controls;
6. durable queue with acknowledgement, retry, dead-letter and idempotency;
7. append-only audit with independent anti-rollback evidence;
8. isolated backup/restore and anti-resurrection controls;
9. separate development/staging/production security boundaries;
10. privacy-safe observability;
11. immutable deploy artifacts with rollback.

## Explicitly not authorized

S6-02 does not authorize production identity implementation, production
secrets/KMS/IAM implementation, production network implementation, production
storage/deployment implementation, operational drills against live resources,
production deployment, Stage 7, model training, publication, held-out retuning,
or threshold/resource-limit changes.

## Next safe boundary

The next implementation boundary is a separately authorized S6-03 identity and
authorization implementation. Any provider adapter activation still requires
provider decision evidence; no provider may be invented from this document.
