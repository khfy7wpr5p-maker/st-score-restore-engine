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
KMS/HSM product, production account or production identity provider.

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
| Control and policy | policy decisions, state versions, CAS/idempotency/fencing records | raw keys, real identity administration | all operations fail closed |
| Identity and authorization registry | real-identity mapping, active roles, conflict and staleness state | artifact bytes, key material | opaque tokens are resolved outside Git |
| Key management and recovery material | wrapping-key policy, key versions, recovery controls | artifact payloads, broad read grants | separate from storage and identity administration |
| Quarantine and inspection | untrusted test/runtime bytes, inspection results | processing eligibility | isolated, bounded and network-denied |
| Approved artifacts | encrypted approved objects | quarantined, revoked or unknown objects | digest and current policy must match |
| Audit and evidence | hash-chained events, checkpoints, receipts, tombstones | payload bytes, credentials, names/emails | append-only, fork-detecting and redacted |
| Backup and recovery | encrypted copies, audit checkpoints, tombstone indexes | ungoverned restore copies | evidence restores before payloads |

A physical component may host multiple logical zones only when access controls,
separate credentials, audit evidence and role separation prove equivalent
isolation. A zone cannot implicitly grant another zone broader rights.

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
- last audit-event digest and partition sequence,
- minimum accepted audit checkpoint reference,
- independent anti-rollback anchor reference,
- backup/tombstone status,
- pending-backup receipt reference where applicable,
- final deletion completion receipt reference where applicable.

Names, personal email addresses, student/teacher identifiers, local personal
paths, provider URLs, bucket names, account IDs and credentials are invalid in
repository-visible fields.

## 5. State machine

| Current state | Allowed next state | Required evidence | Processing eligibility |
|---|---|---|---|
| `absent` | `quarantined` | intake request, digest, size | no |
| `quarantined` | `available` | isolated inspection, policy binding, independent promotion | no until transition completes |
| `quarantined` | `deletion_pending` | rejection or withdrawal decision | no |
| `available` | `deletion_pending` | expiry, revocation, incident or approved deletion | no immediately |
| `deletion_pending` | `revoked` | active-copy unavailability plus valid backup tombstone and pending-backup receipt | no |
| `revoked` | `tombstoned` | final deletion completion receipt | no |

All other transitions are rejected. In particular:

- `revoked` cannot become `available`,
- `tombstoned` cannot be reactivated,
- `deletion_pending` cannot be read,
- restore cannot bypass the state machine,
- an unknown state cannot be interpreted as available,
- rollback to an older record version is invalid.

## 6. Role matrix and prohibited conflicts

| Operation | Initiates | Independently authorizes | Executes | Verifies |
|---|---|---|---|---|
| quarantine intake | custody operator | access authorizer | custody operator | audit reviewer |
| promotion to available | custody operator | rights/privacy/dataset gates plus access authorizer | custody operator | audit reviewer |
| ordinary read grant | requester | access authorizer | custody service | audit reviewer |
| key rotation | key custodian | key-policy approver | key custodian | audit reviewer |
| revocation | rights/privacy/purpose authority, retention policy or incident authority | none before effect; immediate policy action | custody control service | independent audit reviewer after effect |
| physical deletion | custody operator | deletion authority | deletion executor | audit reviewer |
| pending-backup receipt | deletion executor | deletion authority | control service | deletion receipt verifier |
| final deletion receipt | deletion executor | deletion authority | control service | deletion receipt verifier |
| emergency access | emergency requester | two independent emergency approvers | custody service | mandatory post-event audit reviewer |

The external identity registry must reject stale, disabled or conflicting role
mappings using real-person identity, not opaque-token equality.

For the same artifact, one real person must not hold both roles in any of these
pairs:

- access authorizer and custody operator,
- key custodian and artifact access operator,
- key-policy approver and key-operation executor,
- deletion authority and deletion executor,
- deletion executor and deletion receipt verifier,
- audit reviewer and executor of the reviewed operation,
- emergency requester and emergency approver.

A person must not independently authorize purpose, grant access and finalize
deletion evidence for the same artifact.

A valid rights, privacy or purpose revocation, retention expiry or incident lock
takes effect immediately and cannot require, await or be vetoed by an access
authorizer. The independent audit reviewer verifies the event after access is
blocked; review failure cannot re-enable the artifact.

## 7. Authorization decision

A read or processing authorization returns `allow` only when every required
condition passes:

1. the record exists and is `available`,
2. requested digest and byte size match,
3. identity and role are active and non-conflicting,
4. purpose is explicitly allowed by Stage 1A metadata,
5. environment and storage-class restrictions match,
6. retention is valid under authoritative service time,
7. no hold rule blocks the requested purpose,
8. no revocation, deletion or incident lock is active,
9. the grant is short-lived and bound to one artifact, purpose and environment,
10. a durable audit event can be committed before access becomes effective.

An audit-write failure, missing policy, ambiguous policy, stale identity or
unknown state denies the operation.

## 8. Emergency access contract

Emergency access uses a separate request and event type, a narrow expiry, two
active independent approvers and mandatory post-event review.

Emergency access may never bypass:

- a state other than `available`,
- digest or byte-size mismatch,
- expired retention,
- missing, expired or revoked purpose authorization,
- rights or privacy denial,
- an active legal or policy hold that blocks the requested purpose,
- deletion, revocation or incident lock,
- storage-class or environment prohibition,
- failed audit durability,
- role-conflict rules.

Emergency approval cannot be supplied by the requester, the executing custody
operator or a stale/disabled identity.

## 9. Quarantine and inspection contract

Before promotion, the system binds the exact received bytes to digest and size
and runs format-appropriate inspection in an isolated, low-privilege process or
equivalent boundary.

The inspection boundary requires:

- no outbound network access,
- read-only access to the immutable input,
- no permission to replace or modify the source object,
- minimum writable temporary storage,
- explicit CPU, memory, wall-clock and output limits,
- source-byte, decoded-pixel and decompression limits,
- recursive archive rejection or a fixed tested depth and expansion ratio,
- fail-closed handling of parser crash, timeout and ambiguous output,
- structured result codes rather than free-text personal descriptions.

Promotion requires all of:

- digest and size verification after inspection,
- supported-format structural decision,
- unsafe-container/malware decision,
- rights, privacy and dataset gate references,
- encryption-policy binding,
- independent promotion authorization,
- successful durable audit event.

Failure leaves the object unavailable. A retry uses the same canonical request
fingerprint or creates a new explicitly linked attempt.

## 10. Encryption contract

The logical contract assumes envelope encryption:

- object ciphertext is distinct from source identity,
- a data-encryption key is unique per object or equivalently isolated scope,
- wrapping-key access is separate from object-storage access,
- key references are opaque,
- key versions and rotation events are audited,
- application logs never contain key material,
- recovery keys are subject to narrower roles and dual control,
- key custodian and artifact access operator are separate real people,
- key-policy approver and key-operation executor are separate real people.

The contract must be testable with a non-production reference adapter without
claiming production cryptographic assurance.

## 11. Audit event, ordering, checkpoint and anti-rollback contract

Every security-relevant operation emits a canonical event with:

- opaque event ID,
- custody record ID and record version,
- artifact SHA-256,
- operation code and result code,
- opaque actor, role and authorization references,
- authoritative UTC timestamp,
- previous-event digest,
- monotonically increasing partition sequence,
- canonical request fingerprint,
- idempotency reference,
- policy-decision code,
- redacted failure code where applicable.

Audit validation must reject:

- duplicate event IDs,
- broken previous-event digests,
- non-monotonic record versions or partition sequences,
- replay with different canonical parameters,
- rollback to an older custody version,
- unknown, stale or conflicting actors/roles,
- free-text identity or secret-bearing fields,
- an `allow` result without a durable event.

The audit system periodically creates an integrity-protected checkpoint with the
accepted partition sequence and chain head. Each accepted checkpoint must be
verifiable through an independent anti-rollback anchor outside the audit
partition and outside any backup snapshot. The anchor must use a separately
governed signing key or independent witness and monotonically bind the accepted
partition sequence and chain head.

Validation must detect and reject:

- forks from an accepted sequence,
- chain truncation below the independently anchored minimum checkpoint,
- a checkpoint inconsistent with its event chain,
- a checkpoint whose signature or witness evidence is missing or invalid,
- a checkpoint whose sequence or chain head conflicts with the live anchor,
- restoration from a chain head older than the independently anchored minimum.

The minimum accepted checkpoint is read from the live anti-rollback anchor. It
must never be derived from, lowered by or replaced with a value inside the
snapshot being restored. Missing, stale, forked or mismatched anchor evidence
fails closed.

## 12. Atomic transition, CAS, fencing and time contract

Security-sensitive state changes require compare-and-swap against the expected
record version. A conflicting version returns a deterministic conflict and does
not partially apply the operation.

For `available → deletion_pending`, one fail-closed security transaction must:

1. verify expected state and record version,
2. write the new state and version,
3. invalidate active and cached grants,
4. fence queued and in-flight work,
5. record tombstone intent,
6. durably append the audit event.

No success response is allowed when audit durability or fencing is unknown. If a
backend cannot provide one physical transaction, a documented protocol must
make access unavailable first and prove crash recovery cannot reopen it.

Authorization and expiry use authoritative service time in UTC. Client
timestamps are evidence only and never control authorization. The implementation
must define maximum accepted clock skew and fail closed outside it.

Idempotency binds request ID to canonical request fingerprint, artifact ID,
expected record version and operation code. A different fingerprint under the
same request ID is a conflicting replay.

## 13. Retention, holds and immediate revocation

Retention expiry blocks access before deletion completes.

A legal or policy hold includes an opaque authority reference, typed reason
code, start time and review/expiry rule. A hold may prevent physical deletion
but may not restore evaluation, calibration, derivation, publication,
demonstration or training eligibility.

Expired, stale or malformed holds fail closed and require independent review.

A valid rights, privacy or purpose revocation, retention expiry or incident lock
is an immediate control event. The custody control service must atomically move
or recoverably fence the record into `deletion_pending`, invalidate active and
cached grants, stop queued/in-flight work, record tombstone intent and durably
audit the event. No access-authorizer approval is required before this security
effect, and an access authorizer cannot delay or veto it.

## 14. Revocation and deletion workflow

Deletion is a multi-boundary workflow:

1. atomically change state to `deletion_pending`,
2. invalidate active and cached access grants,
3. stop and fence queued/in-flight work,
4. remove primary object data,
5. remove replicas and caches,
6. remove or expire temporary and derived transient material,
7. record backup tombstone and maximum backup expiry,
8. dispose or revoke the object key envelope as policy requires,
9. validate audit continuity, checkpoint state and independent anchor,
10. issue only the evidence type whose completion conditions are met.

A partial failure remains `deletion_pending`. Retrying with the same request is
idempotent; a conflicting replay is rejected.

## 15. Two deletion evidence types

### 15.1 Revocation / pending-backup receipt

This receipt proves that active use is blocked and records:

- opaque receipt and request IDs,
- artifact digest and custody record version,
- revocation authority reference,
- transition time to `deletion_pending`,
- active-grant invalidation and work-fencing result,
- disposition of primary, replicas, caches and transient objects,
- backup tombstone status and maximum remaining backup expiry,
- key-envelope disposition,
- executor and independent verifier references,
- final audit-event digest, checkpoint and anchor references,
- canonical receipt SHA-256.

It must be explicitly typed `revocation_pending_backup` and must not set deletion
status to `completed`.

### 15.2 Final deletion completion receipt

This receipt is allowed only when every required boundary, including backup
expiry or verified destruction, is complete. It includes all pending-backup
fields plus final backup disposition and completion time.

Only this receipt may be typed `final_deletion_complete`, set deletion status to
`completed` and authorize transition from `revoked` to `tombstoned`.

No receipt is successful when a required boundary is unknown, unverifiable or
failed.

## 16. Backup and restore contract

Backups must include or be paired with integrity-protected policy, audit
checkpoint and tombstone indexes. The independently maintained anti-rollback
anchor is not restored from the backup and remains authoritative across restore.

Restore order is mandatory:

1. obtain and validate the live independent anti-rollback anchor,
2. restore and validate policy, audit checkpoints and tombstones,
3. reject a source below or inconsistent with the anchored minimum checkpoint,
4. identify revoked, expired, deletion-pending or unknown artifact digests,
5. quarantine those payloads,
6. restore only records still eligible under current policy,
7. audit every disposition.

A backup payload without matching policy, tombstone, checkpoint and independent
anchor evidence is quarantined, not made available. Restore cannot reduce a
record version, lower the anchored checkpoint or replace a newer tombstone with
older evidence.

## 17. Non-sensitive reference drill

A future Stage 1B Draft PR may implement a provider-neutral in-memory or
temporary local reference adapter solely for operational testing. It uses
run-created, project-authored, non-musical marker bytes and does not commit
score/TAB artifacts.

Required positive tests:

- isolated quarantine then authorized promotion,
- narrowly scoped read grant,
- immediate revocation while the access authorizer is unavailable,
- idempotent revocation request,
- pending-backup receipt generation,
- final deletion completion receipt generation after backup completion,
- valid restore of a still-eligible test object from a current anchored checkpoint.

Required negative tests:

- every prohibited role collision,
- stale or disabled identity,
- access authorizer attempting to delay or veto valid revocation,
- emergency access attempting to bypass an active purpose-blocking hold,
- emergency access attempting each other non-bypassable denial,
- unauthorized environment or storage class,
- read during `deletion_pending`,
- inspection timeout, crash, expansion limit and network-attempt failure,
- compare-and-swap version conflict,
- state change with audit failure,
- state change with incomplete work fencing,
- duplicate event, broken hash chain and non-monotonic sequence,
- audit fork, truncation and checkpoint rollback,
- checkpoint with missing or invalid independent signature/witness evidence,
- checkpoint whose sequence or chain head conflicts with the live anchor,
- restore snapshot attempting to lower or replace the anchored minimum,
- conflicting idempotency replay,
- incomplete replica/cache deletion,
- missing backup tombstone,
- pending-backup receipt incorrectly claiming completion,
- final receipt before backup completion,
- restore attempting to resurrect revoked data,
- restore from a stale, missing or unanchored checkpoint,
- receipt finalization by deletion executor without independent verification.

## 18. CI and repository gates

A future Stage 1B implementation PR must prove:

- ordinary Git contains no artifact payloads or secrets,
- no provider-specific account, region or resource appears,
- no active Stage 1A permission or real split is introduced,
- custody schemas and Python validators remain in parity,
- Python 3.11 and 3.12 tests pass,
- repository, fixture and Stage 1A dataset validators continue to pass,
- Stage 1B operational positive and negative tests pass,
- compile validation passes,
- the exact PR head is independently audited.

## 19. Exit gate

Stage 1B is not complete until:

- ADR 0014 and this contract are accepted,
- machine-enforceable contracts and reference drill pass,
- role conflicts and emergency non-bypass rules are negatively tested,
- valid revocation is proven immediate and independent of access-authorizer approval,
- audit fork, rollback and truncation detection are demonstrated,
- independent checkpoint anti-rollback anchoring is demonstrated,
- atomic revocation and fencing behavior are demonstrated,
- pending-backup and final deletion receipts are distinguished and validated,
- restore cannot resurrect revoked test objects,
- no real/private artifact, credential or provider resource exists,
- independent security review passes,
- separate Ready and merge approvals are completed.

Issue #32 remains open after Stage 1B. Stage 1C requires separately accepted
Stage 1B evidence and a separate explicit start authorization.
