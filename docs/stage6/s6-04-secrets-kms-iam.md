# Stage 6 S6-04 Secrets, KMS and IAM

- Status: IMPLEMENTATION CANDIDATE
- Authorization ID: `stage6.s6-04.secrets-kms-iam-implementation-authorization.v1`
- Authorization canonical SHA-256: `a14b4f6dfd8b7a32b3fd9acf9f5a79ecdf6d90cff40e0e842d5e33837d1c0cef`
- Entry main: `afc150c6709cb1a825767b72c44bd04cab4520e7`
- Provider selection: `UNSELECTED`

## Scope

S6-04 implements the provider-neutral production security boundary required by
the S6-02 trust-boundary decision. It does not select or activate a cloud,
secret manager, KMS/HSM service or IAM provider, and it creates no live
production resources.

The implementation is intentionally adapter-based. A later approved provider
must supply the concrete secret-manager, KMS and append-only audit backends.

## Workload identity and IAM

Production runtime operations use `WorkloadIdentity`, not static API keys or
caller-supplied actor headers. The identity contract requires:

- verified workload identity evidence;
- opaque `workload:sha256:` principal identifiers;
- isolated `staging` or `production` environment identity;
- expiry validation;
- an explicit service and runtime duty;
- deny-by-default authorization;
- exact grants with no wildcard resources;
- environment matching between identity and resource;
- separation of duties: administrative duty cannot invoke runtime secret/KMS data-plane operations.

The implemented runtime actions are limited to `secret.read`, `kms.encrypt` and
`kms.decrypt`. Provider-side IAM roles/policies remain uncreated.

## Secret manager boundary

`ProductionSecretResolver` accepts only provider-neutral logical
`SecretReference` values. Raw secret material is not configuration and is not
stored in Git.

Every resolution re-queries the injected secret-manager backend. The boundary
therefore does not create a local cache that could silently continue using a
rotated or revoked version.

A secret is released only when:

- IAM authorization succeeds;
- the backend returns a concrete version;
- revocation was explicitly checked;
- the concrete version is not revoked;
- the lease is still valid;
- material is non-empty;
- privacy-safe audit evidence is committed successfully.

`SecretValue` and backend evidence redact material from normal `repr` / `str`
output. Python does not provide a general secure-memory zeroization guarantee,
so S6-04 makes no such claim.

## KMS envelope boundary

`ProductionEnvelopeCrypto` delegates all cryptographic operations to an injected
approved KMS backend. The repository does not implement a custom production
cipher and does not generate or commit real key material.

Before encryption or decryption the boundary requires:

- exact IAM authorization;
- matching environment and purpose between key and encryption context;
- opaque tenant context;
- an enabled key state;
- an explicit key revocation check;
- a concrete key version.

The returned envelope must contain opaque ciphertext and wrapped data-key bytes,
a non-`none` algorithm, the verified concrete key version and the exact canonical
context digest. A backend that returns plaintext as ciphertext is rejected.

Decryption refuses context tampering before releasing plaintext to the caller.

## Audit boundary

Secret and KMS success/dependency events are emitted through a required
`SecurityAuditSink`. Events contain opaque principal/resource metadata and
provider evidence identifiers, not secret values, ciphertext payload contents,
artifact bytes, names, email addresses or free-text personal data.

If the audit sink cannot commit required security evidence, the operation fails
closed. The actual append-only/tamper-evident/WORM or equivalent persistence is a
later production storage/audit implementation concern and is not claimed by
S6-04.

## Development compatibility

Existing local development API keys and local SQLite/content-addressed storage
remain unchanged. S6-04 does not convert the local development server into a
production edge and does not change Stage 1-5 evidence or quality thresholds.

## Explicitly not activated

S6-04 does not activate or create:

- a provider selection;
- provider-specific secret-manager access;
- live secrets;
- provider-specific KMS/HSM integration;
- live encryption keys;
- provider IAM roles or policies;
- provider-specific identity adapter activation;
- public network/TLS/WAF infrastructure;
- production database/object storage/queue;
- durable production audit persistence;
- production deployment or operational drills;
- Stage 7;
- model training, publication, held-out retuning or threshold/resource-limit changes.

## Next safe boundary

The next separately authorized implementation boundary is S6-05 production
network and untrusted-network controls.
