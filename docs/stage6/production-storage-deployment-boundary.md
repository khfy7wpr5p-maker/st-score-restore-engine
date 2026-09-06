# Stage 6 S6-06 — Production Storage / Deployment Boundary

**Status:** provider-neutral implementation contract  
**Provider selection:** UNSELECTED  
**Live production resources:** NOT AUTHORIZED / NOT CREATED  
**Production deployment:** NOT AUTHORIZED

## Purpose

S6-06 surrounds the existing local SQLite/content-addressed persistence baseline with provider-neutral production contracts. It does not replace or silently promote `docs/durable-local-persistence.md`; that local baseline remains explicitly non-production.

The contract is designed so a later approved provider adapter can prove the required behavior before any production resource or deployment is activated.

## Metadata database

A production metadata database adapter must prove all of the following before admission:

- external durable database service,
- encryption at rest and encrypted transport,
- transactional writes,
- monotonic schema versioning,
- migration preflight and backward-compatibility evidence,
- validated rollback path,
- tenant-scoped access enforcement,
- workload identity rather than shared static credentials,
- point-in-time recovery capability.

Missing evidence fails closed.

## Object storage

Artifact storage must prove:

- encryption at rest with separated KMS/equivalent key authority,
- encrypted transport,
- content-address/integrity verification,
- tenant namespace isolation,
- public access blocked,
- lifecycle policy binding,
- versioning or equivalent recovery capability,
- workload identity enforcement.

No provider bucket or object resource is created by this slice.

## Durable queue, idempotency and fencing

The production queue contract requires an external durable broker. A worker claim is accepted only when:

- worker identity is authenticated,
- lease identity and persisted lease expiry exist,
- fencing token is strictly newer than the previous accepted token,
- idempotency digest is canonical SHA-256,
- state transition is committed before queue acknowledgement,
- redelivery is supported.

This converts the local lease baseline into a provider-neutral distributed safety contract without claiming that Issue #17 stress validation is complete. Bounded load/soak, failover and multi-instance stress remain later validation work.

## Crash recovery

A production adapter must demonstrate atomic metadata commit, artifact integrity, ack-after-commit, idempotent replay, partial-write cleanup and stale-worker fencing. Failure in any one of these items denies recovery publication.

## Retention and secure deletion

Deletion is two-stage:

1. persist deletion intent/tombstone and remove live references;
2. confirm physical/object deletion, propagate the tombstone into backup/recovery state, then persist the completion receipt.

A restore is not publishable unless deleted data is proven not to resurrect.

## Backup and restore

Restore publication requires encrypted backup material, verified integrity manifest, isolated restore target, consistent database/object generation, tombstone replay before publish, explicit anti-resurrection verification, recovery-point verification and durable audit evidence.

S6-07 is reserved for synthetic operational drills; no live disaster-recovery drill is authorized by S6-06.

## Audit durability

The storage/deployment contract now defines the required production audit-store behavior:

- append-only writes,
- validated hash chain,
- independent anti-rollback anchor,
- immutable retention,
- tenant scope,
- workload identity,
- privacy-safe payload policy.

This is a provider-neutral contract only. No WORM/audit provider resource is created here.

## Environment isolation

Development, staging and production must use isolated account/project, credentials, network, storage, queue and audit namespaces. Cross-environment writes are forbidden.

## Deployment candidate boundary

S6-06 validates release candidates but does not authorize production activation. A candidate must have:

- immutable `sha256:` artifact digest,
- signed provenance and verified artifact signature,
- staging health success,
- migration preflight success,
- validated rollback artifact/path,
- no baked-in secrets,
- environment-specific configuration separated from the artifact,
- privacy-safe observability readiness.

If production activation is requested while the production-deployment authorization flag is false, the contract rejects it.

## Fail-closed dependencies

Storage, queue and audit evidence is mandatory. If the audit sink or required durability/isolation/recovery evidence is unavailable, the operation is denied rather than downgraded to the local baseline.

## Explicitly not activated

S6-06 does **not** select a provider and does **not** create or activate:

- production database,
- object-storage bucket,
- external queue,
- backup/DR infrastructure,
- durable provider audit store,
- deployment platform,
- DNS/network resources,
- production credentials or secrets,
- live production deployment,
- production operational drills,
- Stage 7 preview release,
- model training/publication,
- threshold or resource-limit changes.

## Next safe boundary

`S6-07 — synthetic operational safety / recovery drills` requires a separate explicit authorization.
