# ADR 0014: Stage 1B Provider-Neutral Custody and Operations Boundary

- **Status:** Accepted as the Stage 1B technical decision; Stage 1B formally closed
- **Date:** 2026-08-06
- **Decision ID:** `adr-0014-stage-1b-custody-operations-v1`
- **Roadmap stage:** Stage 1B only
- **Parent issue:** #32
- **Implementation issue:** #36 — closed as `completed`
- **Base commit:** `a7e4e2b715194a0671cea2657d973b01b0fede79`

> Closure note: this ADR is accepted as the Stage 1B technical decision. The machine-enforceable implementation and operational evidence were merged through PR #41, final removal crash/restart evidence was merged through PR #44, the required exact-head audit result was recorded, post-merge `main` CI passed, and Issue #36 closed as `completed` with an 11/11 exit matrix. This closure does not authorize Stage 1C.

## Context

Stage 1A established a metadata-only, purpose-bound dataset governance contract.
It deliberately did not choose a storage provider, create credentials, onboard
artifact bytes, activate permissions, freeze a real split or begin Stage 1C.

Before any real or controlled-synthetic artifact may be onboarded, the project
needs a custody and operations boundary that defines how an external artifact is
quarantined, encrypted, accessed, audited, retained, revoked, deleted and
restored. The boundary must remain testable without placing real/private music
artifacts or production secrets in ordinary Git.

This ADR defines provider-neutral decisions only. It does not select a cloud
vendor, region, KMS/HSM product, production account or identity provider.

## Decision

### 1. Provider-neutral control contract

Stage 1B defines required behavior rather than vendor configuration. A future
provider adapter must prove that it implements the same trust boundaries, state
transitions, access policy, audit integrity, deletion evidence and restore
safeguards.

Provider-specific resources, credentials and infrastructure definitions are not
permitted in this ADR or its first Draft PR.

### 2. Trust zones

The custody system has eight separate trust zones:

1. **Repository metadata zone** — schemas, policies, opaque references and test
   code only; no document bytes, credentials or personal identity mapping.
2. **Control and policy zone** — evaluates policy, state versions, compare-and-
   swap transitions, idempotency and fencing. It holds no raw key material and
   cannot independently assign real identities.
3. **Identity and authorization registry zone** — maps opaque actor tokens to
   real identities and active roles, enforces role conflicts, staleness,
   disabling and emergency-approval requirements. The real identity map remains
   outside ordinary Git and outside artifact storage.
4. **Key management and recovery-material zone** — governs wrapping keys,
   recovery material, rotation and key-policy approval. It is separated from
   object storage, artifact read execution and identity administration.
5. **Quarantine and inspection zone** — receives untrusted bytes and runs
   isolated inspection. Quarantined objects cannot be used by restoration,
   evaluation, calibration, derivation or training.
6. **Approved artifact zone** — contains only encrypted objects that passed
   custody, rights, privacy and dataset gates.
7. **Audit and evidence zone** — append-only events, checkpoints, deletion
   receipts and tombstones; no artifact payloads, real identities or secret
   values.
8. **Backup and recovery zone** — isolated copies governed by expiry,
   checkpoint and tombstone rules. Restore must validate policy, audit and
   revocation evidence before making any object available.

No zone may silently grant another zone broader rights. A single implementation
may host multiple logical zones only when access control, audit and
separation-of-duty evidence proves equivalent isolation.

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

- each object is protected by an object data-encryption key or equivalently
  isolated cryptographic scope,
- data-encryption keys are wrapped by a separately governed key-encryption key,
- raw key material is never stored in ordinary Git, audit events or application
  logs,
- key policy and key-version references are opaque identifiers,
- key rotation re-wraps or re-encrypts under an audited operation,
- recovery material has stricter access than ordinary custody operations,
- key custodian and artifact access operator cannot be the same real person for
  the same artifact,
- key-policy approval is independent from key-operation execution.

Cryptographic erasure may be supporting evidence but is not, by itself, proof
that replicas, caches and backups were handled correctly.

### 6. Roles and non-bypassable separation of duty

Stage 1B distinguishes these roles:

- rights verifier,
- privacy reviewer,
- purpose authorizer,
- dataset reviewer,
- custody operator,
- access authorizer,
- key custodian,
- key-policy approver,
- audit reviewer,
- deletion authority,
- deletion executor,
- deletion receipt verifier,
- emergency requester,
- emergency approver.

The identity registry maps opaque repository tokens to real identities and
enforces conflicts outside ordinary Git.

For the same artifact, the following role pairs are prohibited for one real
person:

- access authorizer and custody operator,
- key custodian and artifact access operator,
- deletion authority and deletion executor,
- deletion executor and deletion receipt verifier,
- audit reviewer and executor of the reviewed operation,
- emergency requester and emergency approver,
- key-policy approver and key-operation executor.

No single real person may independently authorize purpose, grant access and
finalize deletion evidence for the same artifact. Conflict checks use real
identity, not opaque token equality, and stale or disabled mappings fail closed.

### 7. Deny-by-default and emergency access

Ordinary access is denied unless all of the following are true:

- custody state is `available`,
- artifact identity matches the requested digest and size,
- the external identity is active and not stale or revoked,
- the role and purpose are explicitly permitted,
- environment and storage-class restrictions match,
- retention has not expired,
- no deletion, revocation, hold-based purpose block or incident lock is active,
- the access grant is short-lived and independently auditable,
- the durable audit event can be committed before access becomes effective.

Emergency access requires a distinct event type, narrow duration, two active
independent approvers and mandatory post-event review. It may never bypass:

- any state other than `available`,
- digest or byte-size mismatch,
- expired retention,
- revoked or missing purpose authorization,
- rights or privacy denial,
- an active legal or policy hold that blocks the requested purpose,
- deletion, revocation or incident lock,
- environment or storage-class prohibition,
- failed audit durability.

Static credentials, broad shared accounts and credentials stored in the
repository are prohibited.

### 8. Quarantine and inspection isolation

New bytes enter only the quarantine zone. Inspection must run in a separate,
low-privilege process or equivalent isolation with:

- no outbound network access,
- read-only input and no ability to alter the source object,
- minimum writable temporary storage,
- explicit CPU, memory, wall-clock and output limits,
- byte-size, decoded-pixel and decompression limits,
- recursive archive rejection or a fixed, tested depth and expansion limit,
- parser crash, timeout or ambiguous result treated as failure,
- no restoration, evaluation or dataset consumer access.

Promotion to `available` additionally requires exact digest and size
verification, supported-format structural inspection, unsafe-container/malware
decision, rights/privacy/dataset evidence, encryption-policy binding,
independent promotion authorization and a durable audit event.

Inspection failure leaves the object quarantined or moves it into the deletion
workflow.

### 9. Audit integrity, fork resistance and checkpoints

Every security-relevant operation produces a canonical append-only event with:

- opaque event ID,
- artifact digest and custody record version,
- operation type and result,
- opaque actor, role and authorization references,
- authoritative UTC timestamp,
- previous-event digest,
- monotonically increasing partition sequence,
- canonical request fingerprint and idempotency reference,
- policy decision code,
- redacted failure code where applicable.

Events are hash chained per custody record and ordered within an audit
partition. Duplicate request IDs with the same canonical fingerprint return the
existing result; conflicting replay attempts fail closed.

The audit system must periodically produce an integrity-protected checkpoint
containing the accepted partition sequence and chain head. Validation rejects:

- a fork from an already accepted sequence,
- truncation below the minimum accepted checkpoint,
- rollback to an older custody version,
- a chain head inconsistent with the checkpoint,
- an event with a non-canonical request fingerprint.

Each accepted checkpoint must also be verifiable through an independent
anti-rollback anchor outside the audit partition and outside any backup snapshot.
The anchor must use a separately governed signing key or independent witness and
must monotonically bind the accepted partition sequence and chain head. The
minimum accepted checkpoint used during authorization or restore must come from
the live anti-rollback anchor, never from the snapshot being restored. Missing,
stale, forked or mismatched anchor evidence fails closed.

Restore sources must include a checkpoint at or above the independently anchored
minimum accepted checkpoint. Audit records may not include artifact bytes,
credentials, key material, names, emails or free-text personal data.

### 10. Atomic state transitions, fencing and time

A security-sensitive transition is one compare-and-swap operation over the
expected custody record version. For `available → deletion_pending`, the
following effects form one fail-closed security transaction:

- verify expected state and version,
- write the new state/version,
- invalidate active and cached access grants,
- fence queued and in-flight work,
- record tombstone intent,
- durably append the audit event.

If durable audit commit or fencing cannot be proven, no access may continue and
the operation remains denied or recoverably `deletion_pending`; it must never
return success with an unrecorded state.

Client-provided timestamps are untrusted. Authorization and expiry decisions use
an authoritative service time source, UTC normalization and a documented
maximum clock-skew policy. Idempotency is bound to the canonical request
fingerprint, artifact ID and expected record version.

### 11. Retention, hold and revocation

Retention expiry immediately blocks new use. A policy or legal hold may delay
physical deletion only when represented by an explicit, independently approved
hold record. A hold never restores processing eligibility.

A valid rights, privacy or purpose revocation, retention expiry or incident lock
is an immediate control event. It does not require access-authorizer approval and
cannot be delayed or vetoed by an access authorizer. The control zone must
atomically block access, invalidate grants, fence work and begin the
`deletion_pending` workflow. Independent audit verification occurs after the
security effect and may not re-enable the artifact.

Revocation starts with the atomic transition to `deletion_pending`, access-grant
invalidation, work fencing and tombstone intent. Physical deletion then
propagates through active storage, replicas, caches and backup schedules.

### 12. Two-stage deletion evidence

Deletion evidence has two distinct types:

1. **Revocation / pending-backup receipt** — proves active use is blocked,
   primary/replica/cache/transient handling is complete or explicitly pending,
   a backup tombstone is active, and the maximum remaining backup expiry is
   recorded. It does not claim final physical deletion.
2. **Final deletion completion receipt** — proves every required boundary,
   including backup expiry or verified destruction, is complete. Only this
   receipt may set deletion status to `completed` and allow `tombstoned`.

Required boundaries are:

- primary object,
- replicas,
- caches and temporary material,
- queued work and derived transient copies,
- backup tombstone and maximum expiry,
- key-envelope disposition,
- audit and metadata tombstone retention.

An unknown, failed or unverifiable boundary keeps the object
`deletion_pending`. The state may become `revoked` only when active copies are
unavailable and backup tombstone evidence is valid; `tombstoned` requires the
final completion receipt.

### 13. Recovery cannot resurrect revoked data

Recovery and restore operations must first obtain the live independent
anti-rollback anchor and then validate policy, audit checkpoints and tombstones.
Any copy whose digest is revoked, expired, `deletion_pending`, absent from the
approved custody catalog or backed by a stale, forked or unanchored audit
checkpoint is quarantined and scheduled for deletion.

A backup snapshot without corresponding tombstone, audit and independently
anchored minimum-checkpoint evidence is not a valid restore source.

### 14. Non-sensitive operational drill

Stage 1B may use only project-authored, non-musical, non-personal test objects
generated during the test run. Test object bytes are not committed as dataset
artifacts.

The drill must demonstrate:

- quarantine and promotion,
- sandbox-limit failure remaining unavailable,
- least-privilege read authorization,
- role-conflict rejection,
- immediate revocation without access-authorizer approval,
- emergency-access rejection under an active purpose-blocking hold,
- emergency-access non-bypass conditions,
- compare-and-swap conflict rejection,
- atomic revocation and work fencing,
- idempotent revocation,
- audit fork, truncation and replay rejection,
- independent checkpoint-anchor mismatch and rollback rejection,
- pending-backup and final-completion receipt distinction,
- partial deletion failure remaining fail closed,
- restore after revocation remaining unavailable,
- deterministic receipt, checkpoint, anchor and tombstone validation.

### 15. Stage boundaries

Stage 1B may add provider-neutral documentation, schemas, validators, reference
interfaces and non-sensitive operational tests. It may not create production
infrastructure or onboard real/controlled-synthetic music artifacts.

Stage 1B is now formally closed. Stage 1C remains blocked until a separate explicit Stage 1C start approval is recorded; the Stage 1B closure itself does not authorize onboarding.

## Consequences

The project gains an auditable and testable operational boundary before any
artifact onboarding. Provider selection and deployment can later be evaluated
against an explicit contract rather than becoming the source of policy.

The additional identity, key, audit-checkpoint, anti-rollback-anchor,
transaction and deletion-proof complexity is intentional because silent reuse
or resurrection of revoked music documents is unacceptable.

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
- **Use a per-record hash chain without checkpoints:** rejected because chain
  truncation, rollback and fork may remain undetected.
- **Store the minimum accepted checkpoint only inside the backup:** rejected
  because the backup and its rollback boundary could be restored together.
- **Require access-authorizer approval before revocation takes effect:** rejected
  because an access-control role must not delay or veto a valid safety removal.
- **Use one generic deletion receipt:** rejected because it can misrepresent a
  backup-tombstoned but not yet physically expired copy as fully deleted.

## Review and merge gates

This ADR is accepted as the Stage 1B technical decision, and all Issue #36 closure gates have been satisfied. The Stage 1B review process required:

1. complete diff and CI evidence,
2. independent security review,
3. separate Ready-for-review approval,
4. final exact-head merge review,
5. separate merge authorization.

Merging and closing Stage 1B did not close #32 and did not authorize
Stage 1C.
