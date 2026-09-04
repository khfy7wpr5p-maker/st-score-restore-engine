# Stage 6 S6-03 Identity and Authorization

- Status: IMPLEMENTATION CANDIDATE
- Authorization ID: `stage6.s6-03.identity-authz-implementation-authorization.v1`
- Authorization canonical SHA-256: `f82421eca0ed90defd04609054f47d1972b5327f71a7f35d644ac84c5f57ce39`
- Entry main: `ed55e10d57655e237e940e14d0af56dd62222ff2`
- Provider selection: `UNSELECTED`

## Scope

S6-03 implements the provider-neutral production identity and authorization
boundary approved by S6-02. It does not select or activate an IdP and does not
create live production resources.

The existing `ApiV1` remains the local/internal development adapter. Production
identity is implemented by `ProductionApiV1`, which wraps the existing API rather
than rewriting the Stage 1-5 job and review contracts.

## Production authentication

`ProductionIdentityAdapter` requires an injected cryptographic signature
verification backend. The backend must return `VerifiedTokenEvidence` only after
signature verification. The Stage 6 adapter independently requires:

- `signature_validated == true`;
- a non-empty verified key identifier;
- a non-empty algorithm other than `none`;
- trusted issuer matching;
- trusted audience matching;
- required `exp` and `nbf` numeric-date validation;
- required subject and tenant claims;
- required token identifier for revocation checks;
- a live revocation checker;
- exactly one permitted application role (`client` or `reviewer`).

Signature-verifier or revocation dependency failures fail closed. No provider
implementation is bundled because provider selection remains unapproved.

## Privacy-safe principal identity

Raw `sub` and tenant claim values are not forwarded to the local job API or audit
actor field. The production adapter derives stable opaque SHA-256 identifiers
scoped by issuer:

- `subject:sha256:<digest>`;
- `tenant:sha256:<digest>`.

This avoids storing names, email-like subjects or tenant labels in the existing
audit path.

## Caller header boundary

`ProductionApiV1` rejects:

- caller-supplied `X-Api-Key`;
- caller-supplied `X-Actor-Id`.

Only a production Bearer identity is accepted. After successful verification,
the wrapper uses process-local random capability values solely to call the
existing local `ApiV1`. These capabilities are not production user identity,
are not persisted, and are never accepted from callers.

## Tenant, ownership and idempotency authorization

Production job access requires a separate `JobAuthorizationStore` contract.
The production storage implementation is intentionally deferred to the later
Stage 6 storage boundary.

The store records only opaque `tenant_key` and `owner_key` values. Enforcement is
fail-closed:

- a missing job security binding is denied;
- an unavailable authorization store is denied;
- tenant mismatch is denied;
- `client` access additionally requires owner match;
- `reviewer` access is allowed only inside the same tenant;
- any other production role is denied.

Job creation binds the returned job ID to the authenticated tenant and owner and
then re-reads the binding before returning success.

Before the request reaches the local job service, an externally supplied
`Idempotency-Key` is validated using the existing 8-128 non-whitespace contract
and transformed into a deterministic internal key scoped to the authenticated
opaque tenant and subject. Therefore the same external idempotency key used by
two different principals cannot resolve to the same local job or race to claim
its ownership binding. The same principal continues to receive normal
idempotent replay semantics.

A failed authorization-store bind may leave a local job with no production
security binding; that job remains inaccessible because missing bindings fail
closed. Atomic durable co-commit of job state and authorization state is a later
production-storage concern and must not be claimed complete by S6-03.

## Local compatibility

The existing static-key `ApiV1` behavior is unchanged for local/development use.
No historical Stage 1-5 API, evidence, threshold, corpus or review semantics are
rewritten by S6-03.

## Explicitly not activated

S6-03 does not activate a provider-specific signature verifier, IdP tenant,
client registration, secret, KMS key, IAM role, public network edge, production
database, production authorization-store implementation, queue, object storage,
deployment, Stage 7, training, publication, held-out retuning or threshold /
resource-limit changes.

## Next safe boundary

The next separately authorized implementation boundary is S6-04 secrets, KMS and
IAM. A provider-specific identity backend may only be activated after provider
selection evidence exists.
