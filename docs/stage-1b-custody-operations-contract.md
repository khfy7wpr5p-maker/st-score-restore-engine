# Stage 1B Custody and Operations Contract

**Status:** Draft decision package in Issue #36  
**Parent:** #32  
**Decision:** `adr-0014-stage-1b-custody-operations-v1`  
**Base:** `a7e4e2b715194a0671cea2657d973b01b0fede79`  
**Artifact policy:** Provider-neutral and metadata-only in ordinary Git  
**Stage 1C authorization:** None

## 1. Purpose

This document defines the operational safety contract that any future custody
implementation must satisfy before the project may onboard real or
controlled-synthetic score, TAB or mixed-layout artifacts.

It is not a deployment guide and does not select a storage vendor, cloud region,
KMS/HSM product or production identity provider.

## 2. Safety boundary

Stage 1B may define and test custody behavior using project-authored,
non-sensitive test objects generated during test execution.

Stage 1B must not:

- add real, student, teacher, private or copyrighted document bytes,
- commit test-object payloads as dataset artifacts,
- create production accounts, buckets, databases or credentials,
- create real encryption keys or service accounts,
- activate dataset purpose permissions,
- freeze a real dataset split,
- begin Stage 1C onboarding,
- change quality metrics, music/TAB safety thresholds or restoration behavior,
- add PDF rendering, DocRes, comparator, selector, image-model or training work,
- modify music-application repositories.

## 3. Trust zones

| Zone | May contain | Must not contain | Key rule |
|---|---|---|---|
| Repository metadata | schemas, policies, opaque IDs, validators, tests | artifact bytes, secrets, real identity maps | ordinary Git remains metadata-only |
| Control | policy decisions, state versions, idempotency records | raw encryption keys | all operations fail closed |
| Quarantine | untrusted test/runtime bytes | processing eligibility | no restoration or dataset use |
| Approved artifacts | encrypted approved objects | quarantined or revoked objects | digest and policy must match |
| Audit/evidence | hash-chained events, receipts, tombstones | payload bytes, credentials, names/emails | append-only and redacted |
| Backup/recovery | encrypted copies and tombstone indexes | ungoverned restore copies | tombstones load before data |

## 4. Required custody record

A provider adapter must expose a logical custody record with at least:

- opaque custody record ID,
- immutable artifact SHA-256,
- exact byte size,
- state and monotonically increasing record version,
- opaque storage-class and environment codes,
- opaque locator reference when an active object exists,
- encryption-policy and key-policy references,
- custodian and access-policy references,
- created, retained-until and state-transition timestamps,
- revocation and deletion status,
- legal/policy hold status,
- last audit-event digest,
- backup/tombstone status,
- deletion receipt reference when completed.

Names, personal email addresses, student/teacher identifiers, local personal
paths, provider URLs, bucket names, account IDs and credentials are invalid in
repository-visible fields.

## 5. State machine

| Current state | Allowed next state | Required evidence | Processing eligibility |
|---|---|---|---|
| `absent` | `quarantined` | intake request, digest, size | no |
| `quarantined` | `available` | inspection, policy binding, independent promotion | no until transition completes |
| `quarantined` | `deletion_pending` | rejection or withdrawal decision | no |
| `available` | `deletion_pending` | expiry, revocation, incident or approved deletion | no immediately |
| `deletion_pending` | `revoked` | active-copy removal plus backup tombstone evidence | no |
| `revoked` | `tombstoned` | all completion conditions and receipt validation | no |

All other transitions are rejected. In particular:

- `revoked` cannot become `available`,
- `tombstoned` cannot be reactivated,
- `deletion_pending` cannot be read,
- restore cannot bypass the state machine,
- an unknown state cannot be interpreted as available.

## 6. Role matrix

| Operation | Initiates | Independently authorizes | Executes | Verifies |
|---|---|---|---|---|
| quarantine intake | custody operator | access authorizer | custody operator | audit reviewer |
| promotion to available | custody operator | rights/privacy/dataset gates plus access authorizer | custody operator | audit reviewer |
| ordinary read grant | requester | access authorizer | custody service | audit reviewer |
| key rotation | key custodian | separate key-policy approver | key custodian | audit reviewer |
| revocation | rights/privacy/purpose authority | access authorizer | custody operator | audit reviewer |
| physical deletion | custody operator | deletion authority | deletion executor | audit reviewer |
| receipt finalization | deletion executor | independent deletion authority | control service | audit reviewer |
| emergency access | requester | two-person emergency approval | custody service | mandatory post-event review |

The external identity registry must reject stale, disabled or conflicting role
mappings. A person must not independently authorize purpose, grant access and
finalize deletion for the same artifact.

## 7. Authorization decision

A read or processing authorization returns `allow` only when every required
condition passes:

1. the record exists and is `available`,
2. requested digest and byte size match,
3. identity and role are active,
4. purpose is explicitly allowed by Stage 1A metadata,
5. environment and storage-class restrictions match,
6. retention is valid,
7. no hold rule blocks the requested purpose,
8. no revocation, deletion or incident lock is active,
9. the grant is short-lived and bound to one artifact/purpose/environment,
10. an audit event can be durably recorded.

An audit-write failure denies the operation. Missing or ambiguous policy also
denies the operation.

## 8. Quarantine contract

Before promotion, the system must bind the exact received bytes to a digest and
perform format-appropriate inspection. Inspection produces codes, not free-text
personal descriptions.

Promotion requires all of:

- digest and size verification,
- supported-format structural inspection,
- unsafe-container/malware decision,
- rights, privacy and dataset gate references,
- encryption-policy binding,
- independent promotion authorization,
- successful append-only audit event.

Failure leaves the object unavailable. A retry uses the same idempotency key or
creates a new explicitly linked attempt.

## 9. Encryption contract

The logical contract assumes envelope encryption:

- object ciphertext is distinct from source identity,
- a data-encryption key is unique per object or equivalently isolated scope,
- wrapping-key access is separate from object-storage access,
- key references are opaque,
- key versions and rotation events are audited,
- application logs never contain key material,
- recovery keys are subject to narrower roles and dual control.

The contract must be testable with a non-production reference adapter without
claiming production cryptographic assurance.

## 10. Audit-event contract

Every security-relevant operation emits an event with:

- opaque event ID,
- custody record ID and record version,
- artifact SHA-256,
- operation code,
- result code,
- opaque actor, role and authorization references,
- UTC timestamp,
- previous-event digest,
- idempotency/request reference,
- policy-decision code,
- failure code where applicable.

Audit validation must reject:

- duplicate event IDs,
- broken previous-event digests,
- non-monotonic record versions,
- replay with different parameters,
- unknown actors or roles,
- free-text identity or secret-bearing fields,
- an `allow` result without a durable event.

## 11. Retention and holds

Retention expiry blocks access before deletion completes.

A legal or policy hold must include an opaque authority reference, reason code,
start time and review/expiry rule. A hold may prevent physical deletion but may
not restore evaluation, calibration, derivation, publication, demonstration or
training eligibility.

Expired or malformed holds fail closed and require independent review.

## 12. Revocation and deletion workflow

Deletion is a multi-boundary workflow:

1. atomically change state to `deletion_pending`,
2. invalidate active and cached access grants,
3. stop and fence queued/in-flight work,
4. remove primary object data,
5. remove replicas and caches,
6. remove or expire temporary/derived transient material,
7. record backup tombstone and maximum backup expiry,
8. dispose or revoke the object key envelope as policy requires,
9. validate audit continuity,
10. issue a deletion receipt only for completed boundaries.

A partial failure remains `deletion_pending`. Retrying with the same request is
idempotent; a conflicting replay is rejected.

## 13. Deletion receipt

A valid receipt includes:

- opaque receipt and request IDs,
- artifact digest and custody record version,
- revocation authority reference,
- start and completion times,
- disposition for primary, replicas, caches, temporary objects, queued work,
  backup tombstone and key envelope,
- maximum remaining backup expiry where physical deletion is delayed,
- executor and independent verifier references,
- final audit-event digest,
- canonical receipt SHA-256.

No successful receipt is issued when any required boundary is unknown,
unverified or failed.

## 14. Backup and restore contract

Backups must include or be paired with an integrity-protected tombstone index.
Restore order is mandatory:

1. restore and validate policy/audit/tombstone evidence,
2. identify revoked, expired, deletion-pending or unknown artifact digests,
3. quarantine those payloads,
4. restore only records still eligible under current policy,
5. audit every disposition.

A backup payload without matching policy and tombstone evidence is quarantined,
not made available.

## 15. Non-sensitive reference drill

The Stage 1B Draft PR may implement a provider-neutral in-memory or temporary
local reference adapter solely for operational testing. It uses test-run-created
bytes such as a fixed project-authored marker; it does not commit music-score or
TAB artifacts.

Required positive tests:

- quarantine then authorized promotion,
- narrowly scoped read grant,
- idempotent deletion request,
- complete receipt and tombstone generation,
- valid restore of a still-eligible test object.

Required negative tests:

- role collision,
- stale/disabled identity,
- unauthorized environment or storage class,
- read during `deletion_pending`,
- duplicate event and broken hash chain,
- conflicting idempotency replay,
- incomplete replica/cache deletion,
- missing backup tombstone,
- restore that attempts to resurrect revoked data,
- audit failure during an otherwise valid operation,
- receipt finalization by the deletion executor without independent verification.

## 16. CI and repository gates

A future Stage 1B implementation PR must prove:

- ordinary Git contains no artifact payloads or secrets,
- no provider-specific account/region/resource appears,
- no active Stage 1A permission or real split is introduced,
- all custody schemas and Python validators remain in parity,
- Python 3.11 and 3.12 tests pass,
- repository, fixture and Stage 1A dataset validators continue to pass,
- Stage 1B operational negative tests pass,
- compile validation passes,
- the exact PR head is independently audited.

## 17. Exit gate

Stage 1B is not complete until:

- ADR 0014 and this contract are accepted,
- machine-enforceable contracts and reference drill pass,
- deletion receipt and tombstone behavior are demonstrated,
- restore cannot resurrect revoked test objects,
- role conflicts and replay paths are negatively tested,
- no real/private artifact, credential or provider resource exists,
- independent security review passes,
- separate Ready and merge approvals are completed.

Issue #32 remains open after Stage 1B. Stage 1C requires separately accepted
Stage 1B evidence and a separate explicit start authorization.