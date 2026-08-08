# Stage 1B Decision Hardening Record

**Status:** Accepted normative Stage 1B hardening record; Stage 1B formally closed  
**Roadmap stage:** Stage 1B only  
**Parent issue:** #32  
**Implementation issue:** #36 — closed as `completed`  
**Applies to:** ADR 0014 and `docs/stage-1b-custody-operations-contract.md`  
**Base main commit:** `daeb3052fec5b03cd568bfa2c9deb29a25c9a5ed`  
**Stage 1C authorization:** None

## 1. Purpose and precedence

This record closes decision-level findings identified by the independent Stage 1B security audit after PR #37 was merged. It is normative for Stage 1B and remains the stricter rule wherever an older Stage 1B document is less specific.

The machine-enforceable Stage 1B implementation and operational drill were subsequently merged through PR #41, and ADR/technical-contract acceptance status was synchronized through PR #42. Final removal crash/restart evidence was added through PR #44, the required exact-head audit result was recorded, post-merge `main` CI passed, and Issue #36 closed as `completed` with an 11/11 exit matrix. This record does not onboard artifact bytes, create provider resources or credentials, or authorize Stage 1C or any later stage.

## 2. Threat model

Stage 1B must explicitly defend against the following threat classes:

| Threat | Required control | Required evidence |
|---|---|---|
| malicious or malformed input, parser bombs, decompression abuse | isolated network-denied quarantine with CPU, memory, wall-clock, byte, pixel and expansion limits | negative quarantine-limit and crash tests |
| malicious, compromised or mistaken operator | least privilege, real-person separation of duty, short-lived grants and durable audit | role-collision and unauthorized-operation tests |
| stale, disabled or replayed identity/grant | live identity validation, bounded grant lifetime, canonical request fingerprint and replay rejection | stale-identity and replay tests |
| audit fork, rollback or truncation | hash chain, monotonic sequence, checkpoints and independent live anti-rollback anchor | fork, truncation, rollback and anchor mismatch tests |
| revocation lost during crash or disaster recovery | live independent security-removal barrier consulted by authorization and restore | crash-window and pre-revocation-backup restore tests |
| incomplete deletion or stale replica/cache | multi-boundary deletion workflow and two-stage evidence | partial-deletion and premature-final-receipt tests |
| backup resurrection | live removal barrier, tombstones, anchored checkpoint minimum and restore-first policy validation | revoked-object restore rejection |
| compromised service principal | independently authenticated service identities, least privilege and service-to-role separation | unauthorized-principal and cross-zone denial tests |
| key/recovery abuse | key-management separation, dual control and audited recovery | key-role conflict and recovery-policy tests |
| clock manipulation or stale client time | authoritative UTC service time and bounded clock-skew policy | skew and expiry fail-closed tests |
| provider migration rollback or evidence loss | canonical portability package, dual validation and source exit evidence | migration and source-cleanup drill |

Unknown threat-relevant state, unavailable authoritative control evidence or ambiguous policy fails closed.

## 3. Live security-removal barrier

Periodic audit checkpoints alone are insufficient for rights/privacy/purpose revocation, retention expiry or incident lock because a crash may occur after local denial but before the next checkpoint is independently anchored.

Stage 1B therefore requires a **live security-removal barrier** in the independent anti-rollback control boundary outside ordinary audit partitions and outside every backup/restore snapshot.

For each security-removal event the barrier monotonically binds at least:

- artifact SHA-256,
- custody record ID,
- minimum forbidden custody record version,
- removal type (`rights_revocation`, `privacy_revocation`, `purpose_revocation`, `retention_expiry`, `incident_lock` or deletion tombstone),
- authoritative UTC time,
- canonical request fingerprint or event reference,
- independently protected barrier sequence/digest.

The authoritative producer of a valid security-removal event must durably retain the pending removal intent outside the artifact backup/restore boundary before or while publishing the barrier. It must publish the barrier before the custody service may acknowledge the event as durably received, and it must retry until the live barrier acknowledges the monotonic record. A producer crash or restart must not discard an unacknowledged removal intent.

Authorization and restore must query the live barrier before making an artifact available. A matching barrier always denies access regardless of older catalog, audit, snapshot or backup state. If the live barrier cannot be reached or validated, authorization and restore fail closed.

After barrier publication, the custody control service performs the immediate `available -> deletion_pending` security transaction, invalidates grants, fences work, records tombstone intent and durably appends the audit event. The normal independent checkpoint anchor must subsequently advance to include that event.

An object may not transition from `deletion_pending` to `revoked`, and no restore source containing the object may be accepted, until both the live security-removal barrier and the normal independently anchored checkpoint are consistent with the removal event.

Required negative tests include crashes or recovery at each boundary:

1. pending removal intent persisted but barrier not yet acknowledged,
2. barrier committed before local custody transition,
3. local transition/audit committed before checkpoint advancement,
4. restore from a backup created before the removal event,
5. live barrier unavailable or stale,
6. barrier and checkpoint disagree.

Every case must keep the artifact unavailable.

## 4. Security-evidence retention and anti-resurrection horizon

Audit records, checkpoints, live anti-rollback anchors, security-removal barriers, tombstones and deletion receipts must not expire while any backup, replica, disaster-recovery image, archive or other restore source could still contain the governed artifact.

Define the **anti-resurrection horizon** as the latest known expiry or verified destruction time across every storage, replica, cache, archive, backup and disaster-recovery boundary that could contain the artifact, plus a non-zero independently configured safety margin.

At minimum:

- audit chain segments needed to prove the relevant removal/deletion history are retained through the anti-resurrection horizon,
- removal barriers and tombstone evidence are retained through the anti-resurrection horizon,
- the checkpoint/anchor evidence needed to validate those barriers is retained through the same horizon,
- both `revocation_pending_backup` and `final_deletion_complete` receipts are retained through at least the anti-resurrection horizon and longer when audit/legal policy requires it,
- an unknown backup expiry, unknown archive lifetime or unverified destruction extends retention and fails closed,
- a legal/policy requirement that mandates longer evidence retention overrides the minimum horizon,
- `final_deletion_complete` does not by itself authorize immediate deletion of anti-resurrection evidence.

Retention-policy changes are security-relevant audited operations and may not retroactively shorten an already established minimum horizon without independent authorization and proof that no older restore source remains.

## 5. Provider-neutral portability and exit strategy

A provider change must preserve the security meaning of Stage 1B rather than merely copy bytes.

Before cutover, the source side must produce a canonical portability package containing or referencing at least:

- artifact digest and exact byte size,
- custody record ID, state and monotonically increasing version,
- current purpose, environment, storage-class, retention and hold decisions,
- current revocation/deletion state,
- audit chain head and accepted checkpoint,
- live anti-rollback anchor reference,
- live security-removal barrier state,
- tombstone and deletion-receipt references,
- backup-expiry/disposition evidence,
- encryption/key-policy references without exporting raw key material.

The destination must validate the package independently and prove equivalent or stricter trust-zone isolation, deny-by-default authorization, audit durability, removal-barrier behavior, restore safeguards and deletion evidence.

Cutover is not successful until the destination has validated current policy and security evidence against the live independent controls. Migration must never lower record versions, checkpoint minima, barrier sequence, retention constraints or tombstone state.

After cutover, the old provider is treated as a deletion boundary. Exit remains incomplete until its primary, replica, cache, transient and backup copies have entered the normal deletion workflow and the applicable pending-backup and final deletion evidence has been produced. Unknown source-side copies keep provider exit incomplete.

A migration rollback may return service to the previous provider only if that provider remains fully current with the live barrier, checkpoint, policy and custody version. A stale provider may not become authoritative again.

## 6. Role, authority and service-principal taxonomy

Stage 1B distinguishes three classes.

### 6.1 Real-person roles

- rights verifier,
- privacy reviewer,
- purpose authorizer,
- dataset reviewer,
- custody operator,
- artifact access operator,
- access authorizer,
- key custodian,
- key-policy approver,
- audit reviewer,
- deletion authority,
- deletion executor,
- deletion receipt verifier,
- emergency requester,
- emergency approver.

`artifact access operator` means any real person who can cause or supervise plaintext artifact access. The existing prohibition between key custodian and artifact access operator therefore has a defined real-person meaning.

### 6.2 Policy/control authorities

- rights authority,
- privacy authority,
- purpose authority,
- retention policy authority,
- incident authority.

An authority may be represented by an independently authenticated service or an authorized real person. Human-backed authorities remain subject to real-person conflict checks; service-backed authorities require separate service identity, least privilege and durable audit.

### 6.3 Service principals

- custody service,
- custody control service,
- quarantine/inspection service,
- audit service,
- independent anchor/removal-barrier service,
- backup/restore service.

A service principal is not silently treated as a human reviewer or approver. Human approvals, service execution and policy authority must remain distinguishable in audit evidence.

## 7. Governance corrective record

PR #37 merged on 2026-08-07 even though its own text required the PR to remain Draft until separate Ready-for-review and merge approvals and described current-head CI as pending.

That merge remains recorded as a **governance nonconformity**. It did not retroactively prove Stage 1B exit acceptance.

The corrective governance rules were retained for subsequent Stage 1B work:

- exact-head CI evidence is required before acceptance,
- Ready-for-review requires separate explicit authorization,
- merge requires a later separate explicit authorization tied to the exact head SHA,
- machine-enforceable Stage 1B contracts and the non-sensitive operational drill require direct evidence,
- Stage 1C stays blocked until formal Stage 1B closure and a separate Stage 1C start authorization.

PR #41 followed separate Ready and merge gates and was merged at accepted exact head `92c6fbccc8eb4d04e1959f206794b21ccc344db8`. PR #42 subsequently synchronized ADR/contract acceptance status through separate Ready and merge gates. PR #44 then closed the remaining removal crash/restart evidence gap, passed exact-head CI, received the recorded remediation-independent exact-head audit PASS, followed separate Ready and merge gates, and merged as `e47907d6dabe604a7f7877d48959fc50b4b74d1e`; post-merge Run #89 passed. Issue #36 then closed as `completed`. These later actions do not erase the PR #37 nonconformity and do not authorize Stage 1C.

## 8. Required implementation evidence before Stage 1B exit

The machine-enforceable Stage 1B implementation must provide deterministic tests for all rules in this corrective record, including:

- live removal-barrier creation and monotonic validation,
- authorization/restore denial when the barrier is unavailable, stale or mismatched,
- pending-removal intent durability across producer crash/restart,
- every removal crash window listed above,
- evidence-retention horizon calculation and unknown-expiry fail-closed behavior,
- provider portability package validation and stale-provider rollback rejection,
- source-provider exit remaining incomplete while any deletion boundary is unresolved,
- exact role/authority/service-principal taxonomy and conflict enforcement.

These implementation and operational requirements were exercised through PR #41 and the final removal crash/restart hardening in PR #44. PR #44 exact head `2c66f98f1d62c8727dddda5e5cbebfda034bf283` received the recorded remediation-independent audit PASS, was merged, and post-merge `main` Run #89 passed on Python 3.11 and 3.12 with 292 tests on each version.

Issue #36 is formally closed with an 11/11 PASS exit matrix. The accepted controls in this record remain binding. Stage 1C remains unauthorized and has not started; it requires a separate explicit start approval under the roadmap gate.
