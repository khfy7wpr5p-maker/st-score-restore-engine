# ADR 0014: Stage 1B Provider-Neutral Custody and Operations Boundary

- **Status:** Proposed for independent Stage 1B review
- **Date:** 2026-08-06
- **Decision ID:** `adr-0014-stage-1b-custody-operations-v1`
- **Roadmap stage:** Stage 1B only
- **Parent issue:** #32
- **Implementation issue:** #36
- **Base commit:** `a7e4e2b715194a0671cea2657d973b01b0fede79`

## Context

Stage 1A established a metadata-only, purpose-bound dataset governance contract.
It deliberately did not choose a storage provider, create credentials, onboard
artifact bytes, activate permissions, freeze a real split or begin Stage 1C.

Before any real or controlled-synthetic artifact may be onboarded, the project
needs a custody and operations boundary that defines how an external artifact is
quarantined, encrypted, accessed, audited, retained, revoked, deleted and
restored. The boundary must remain testable without placing real/private music
artifacts or production secrets in ordinary Git.

This ADR defines the provider-neutral decisions required for Stage 1B. It does
not select a cloud vendor, region, KMS/HSM product or production account.

## Decision

### 1. Provider-neutral control contract

Stage 1B defines required behavior rather than a vendor configuration. A future
provider adapter must prove that it implements the same state transitions,
access policy, audit events, deletion evidence and restore safeguards.

Provider-specific resources, credentials and infrastructure definitions are not
permitted in this ADR or its first Draft PR.

### 2. Trust zones

The custody system has six separate trust zones:

1. **Repository metadata zone** — schemas, policies, opaque references and test
   code only; no document bytes, credentials or personal identity mapping.
2. **Control zone** — validates authorization, state transitions, idempotency and
   policy. It does not expose raw key material.
3. **Quarantine zone** — receives untrusted bytes. Quarantined objects cannot be
   used by restoration, evaluation, calibration, derivation or training.
4. **Approved artifact zone** — contains only objects that passed required
   custody, rights, privacy and dataset gates.
5. **Audit and evidence zone** — append-only operational events, deletion
   receipts and tombstones; no artifact payloads or secret values.
6. **Backup and recovery zone** — isolated copies governed by expiry and
   tombstone rules. Restore must apply revocation state before making any object
   available.

No zone may silently grant another zone broader rights.

### 3. Custody states

Every custody record is in exactly one state:

- `absent`
- `quarantined`
- `available`
- `deletion_pending`
- `revoked`
- `tombstoned`

State changes are explicit, append-only audited operations. Unknown states and
unsupported transitions fail closed.

`quarantined` and `deletion_pending` objects are never eligible for dataset
snapshots or processing. `revoked` and `tombstoned` objects retain only the
minimum digest and policy evidence required to prevent reuse and resurrection.

### 4. Immutable object identity

Artifact identity is the exact SHA-256 and byte length of the immutable source
object. Storage locators, encryption envelopes, replicas and backup copies may
change without changing artifact identity.

A locator is always an opaque non-semantic reference. Repository metadata must
not contain bucket names, local personal paths, account IDs, credentials or
provider URLs.

### 5. Encryption and key separation

Future storage implementations must use encryption in transit and at rest.
Envelope encryption is the required conceptual model:

- each object is protected by an object data-encryption key,
- data-encryption keys are wrapped by a separately governed key-encryption key,
- raw key material is never stored in ordinary Git, audit events or application
  logs,
- key policy and key-version references are opaque identifiers,
- key rotation re-wraps or re-encrypts under an audited operation,
- recovery material has stricter access than ordinary custody operations.

Cryptographic erasure may be supporting evidence but is not, by itself, proof
that replicas, caches and backups were handled correctly.

### 6. Roles and separation of duty

Stage 1B distinguishes these roles:

- rights verifier,
- privacy reviewer,
- purpose authorizer,
- dataset reviewer,
- custody operator,
- access authorizer,
- key custodian,
- audit reviewer,
- deletion executor.

The external identity registry maps opaque repository tokens to real identities
and enforces role-conflict rules. That registry is outside ordinary Git.

No single real person may independently authorize purpose, grant access and
finalize deletion evidence for the same artifact. Emergency access requires a
separate event type, narrow duration, independent approval and post-event audit.

### 7. Deny-by-default access

Access is denied unless all of the following are true:

- custody state is `available`,
- artifact identity matches the requested digest and size,
- the external identity is active and not stale or revoked,
- the role and purpose are explicitly permitted,
- environment and storage-class restrictions match,
- retention has not expired,
- no deletion, revocation or incident lock is active,
- the access grant is short-lived and independently auditable.

Static credentials, broad shared accounts and credentials stored in the
repository are prohibited.

### 8. Quarantine boundary

New bytes enter only the quarantine zone. Promotion to `available` requires:

- exact digest and size calculation,
- type and structural inspection,
- malware or unsafe-container inspection appropriate to the format,
- rights, privacy and dataset eligibility evidence,
- encryption and custody policy binding,
- independent promotion authorization.

Inspection failure leaves the object quarantined or moves it directly into the
deletion workflow. No parser or restoration engine consumes quarantined bytes.

### 9. Audit integrity

Every security-relevant operation produces an append-only event containing:

- opaque event ID,
- artifact digest and custody record version,
- operation type and result,
- opaque actor and authorization references,
- UTC timestamp,
- previous-event digest,
- request/idempotency reference,
- policy decision code,
- redacted failure code where applicable.

Events are hash chained per custody record. Duplicate request IDs must return
the existing result; conflicting replay attempts fail closed. Audit records may
not include artifact bytes, credentials, key material, names, emails or free-text
personal data.

### 10. Retention, hold and revocation

Retention expiry immediately blocks new use. A policy or legal hold may delay
physical deletion only when represented by an explicit, independently approved
hold record. A hold never restores processing eligibility.

Revocation starts by changing the object to `deletion_pending`, invalidating
access grants and recording a tombstone intent. Physical deletion then
propagates through active storage, replicas, caches and backup schedules.

### 11. Deletion evidence

A deletion operation is complete only when the receipt records the disposition
of every required boundary:

- primary object,
- replicas,
- caches and temporary material,
- queued work and derived transient copies,
- backup tombstone and maximum expiry date,
- key-envelope disposition,
- audit and metadata tombstone retention.

An incomplete boundary produces `deletion_pending`, never a successful receipt.
The final state is `revoked` while backup expiry remains outstanding and
`tombstoned` only after the contract's completion conditions are met.

### 12. Recovery cannot resurrect revoked data

Recovery and restore operations must load and validate tombstones before
restoring artifact availability. Any restored copy whose digest is revoked,
expired, deletion-pending or absent from the approved custody catalog is
quarantined and scheduled for deletion.

A backup snapshot without its corresponding tombstone/audit evidence is not a
valid restore source.

### 13. Non-sensitive operational drill

Stage 1B may use only project-authored, non-musical, non-personal test objects
generated during the test run. Test object bytes are not committed as dataset
artifacts.

The drill must demonstrate:

- quarantine and promotion,
- least-privilege read authorization,
- idempotent revocation,
- deletion propagation evidence,
- partial deletion failure remaining fail closed,
- replay rejection,
- restore after revocation remaining unavailable,
- deterministic receipt and tombstone validation.

### 14. Stage boundaries

Stage 1B may add provider-neutral documentation, schemas, validators, reference
interfaces and non-sensitive operational tests. It may not create production
infrastructure or onboard real/controlled-synthetic music artifacts.

Stage 1C remains blocked until Stage 1B evidence is independently audited,
accepted and merged, followed by a separate Stage 1C start approval.

## Consequences

The project gains an auditable and testable operational boundary before any
artifact onboarding. Provider selection and deployment can later be evaluated
against an explicit contract rather than becoming the source of policy.

The cost is additional metadata, role separation, deletion evidence and restore
complexity. That complexity is intentional because silent reuse or resurrection
of revoked music documents is unacceptable.

## Rejected alternatives

- **Store test documents directly in Git:** rejected because revocation and
  deletion cannot be reliably propagated through repository history.
- **Choose a cloud provider before defining policy:** rejected because provider
  defaults could become accidental security requirements.
- **Treat bucket encryption as sufficient:** rejected because access, replicas,
  backups, audit and deletion remain unresolved.
- **Let teacher approval grant custody permission:** rejected because teaching
  approval is independent from dataset and storage authorization.
- **Use deletion of a locator as deletion proof:** rejected because replicas,
  caches, backups and recovery paths could still contain the object.

## Review and merge gates

This ADR is proposed, not accepted merely because it exists. Its Draft PR must
receive:

1. complete diff and CI evidence,
2. independent security review,
3. separate Ready-for-review approval,
4. final exact-head merge review,
5. separate merge authorization.

Merging a Stage 1B decision package does not close #32 and does not authorize
Stage 1C.