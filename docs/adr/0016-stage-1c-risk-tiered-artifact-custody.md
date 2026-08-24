# ADR 0016: Stage 1C Risk-Tiered Artifact Custody

- **Status:** Proposed by approved Stage 1C architecture change; pending PR acceptance
- **Date:** 2026-08-24
- **Decision ID:** `adr-0016-stage-1c-risk-tiered-custody-v1`
- **Roadmap stage:** Stage 1C only
- **Parent issue:** #47
- **Supersedes:** the universal-storage portion of the Stage 1C G4 pre-byte binding
- **Does not supersede:** Stage 1A rights/privacy/purpose governance or the Stage 1B high-assurance custody contract

## Context

Stage 1C originally bound every real or controlled-synthetic artifact to one storage profile: a dedicated encrypted offline vault outside ordinary Git and automatic cloud-sync folders. That rule treated every external artifact as if it had the same confidentiality and custody risk.

That is unnecessarily restrictive for a large evaluation corpus built from artifact bytes that are themselves verified as public-domain or openly licensed, contain no personal/student information, and are authorized for the intended evaluation purpose.

The underlying musical composition and the artifact are separate rights objects. A Bach or Scarlatti composition may be public domain while a modern engraved edition, publisher layout, editorial material, or particular scan can still have separate rights or contractual restrictions. Therefore composer age or work age alone is never sufficient evidence for the storage tier.

The project needs a proportional rule: preserve strong protection where data is private, personal, consent-restricted, license-restricted, or otherwise sensitive, while allowing ordinary managed storage for verified low-risk corpus artifacts.

## Decision

Stage 1C adopts **artifact-specific risk-tiered custody**. Storage eligibility is derived only after rights, privacy, source, purpose, retention, and dataset-review evidence are evaluated for the exact artifact.

No storage profile can cure missing rights or privacy evidence. Unknown, pending, contradictory, or rejected governance remains fail-closed.

### 1. Artifact eligibility classes

Each candidate artifact is classified into exactly one class before it can become processing-eligible.

#### `open_corpus`

Allowed only when all of the following are true:

- the exact artifact has approved rights evidence establishing public-domain status or an open/license grant compatible with the intended Stage 1 purpose;
- privacy classification is `none`;
- dataset review is approved;
- required purpose authorization is granted and unexpired;
- retention terms permit the chosen storage profile;
- no source, edition, scan, site, donor, or license restriction requires stronger custody.

Examples may include verified public-domain scans or openly licensed score/TAB artifacts. The age or public-domain status of the composition by itself does not qualify an artifact.

#### `restricted_corpus`

Used when the exact artifact is lawfully usable for the intended purpose but carries non-public, contractual, donor, access, redistribution, or retention restrictions that require tighter operational controls. Privacy must still be `none` or an approved deidentified state compatible with the purpose.

#### `sensitive_custody`

Required for private/user-provided material, personal or student data, consent-restricted material, or an artifact whose approved policy explicitly requires the high-assurance custody boundary.

#### `blocked`

Required when rights, privacy, dataset review, purpose authorization, retention compatibility, or artifact provenance is missing, pending, rejected, expired, contradictory, or otherwise insufficient. `blocked` artifacts cannot become `external_available` and cannot enter a Stage 1 split.

### 2. Storage profiles

#### `managed_standard`

Permitted for `open_corpus` only.

The physical store may be local managed storage or a managed cloud/file-storage service. It does **not** have to be offline. Automatic synchronization is not prohibited when it is part of the approved managed storage profile rather than an accidental copy into a personal sync folder.

Minimum controls:

- artifact bytes remain outside ordinary Git;
- exact SHA-256 and byte size are verified against repository metadata;
- authenticated account access or an intentionally public immutable source is documented externally;
- storage behavior does not expose credentials or personal filesystem/provider details in Git;
- encryption in transit and at rest is required for non-public managed copies when the provider supports stored private objects;
- accidental public sharing is disabled for project-managed copies unless publication is independently authorized;
- retention/deletion behavior is documented;
- backup/version behavior is understood sufficiently to prevent silent corpus drift;
- corpus inclusion and split assignment remain governed by immutable digest metadata.

A consumer cloud-drive service can be considered for this profile only if its concrete configuration satisfies the profile. The architecture does not name or automatically approve any provider.

#### `managed_restricted`

Permitted for `restricted_corpus` only when all artifact-specific restrictions allow the selected provider and environment.

In addition to `managed_standard` controls, it requires deny-by-default project access, no public-link sharing, explicit access membership, auditable access/change history where available, retention/deletion enforcement appropriate to the restriction, and documented backup/restore behavior. A provider that cannot satisfy a binding restriction is not eligible.

#### `high_assurance_vault`

Required for `sensitive_custody`.

This profile uses the accepted Stage 1B custody/operations boundary, including encryption, least privilege, role separation, quarantine isolation, audit integrity/anti-rollback, immediate revocation, deletion evidence, retention enforcement, backup anti-resurrection, and the dedicated vault verification evidence introduced in Stage 1C C4.

For this profile the existing C4 vault-verification contract remains applicable. A passing C4 record is **not** required for `managed_standard` merely because the artifact is external.

### 3. Public-domain and license rule

`public_domain` means the rights review applies to the exact artifact used by the project, not merely the musical work embodied in it.

A rights verifier must distinguish, when relevant:

- composition/work rights;
- edition/editorial rights;
- engraving/layout rights;
- scan/photograph rights or contractual source restrictions;
- the source site's terms applicable to acquisition and reuse.

If the exact artifact's status is not established, the artifact is `blocked` even when the composition is centuries old.

### 4. Google Drive and similar services

This ADR is provider-neutral. Google Drive, OneDrive, Dropbox, object storage, NAS, or local managed storage are not approved by name.

A service may qualify for `managed_standard` or `managed_restricted` only after its actual configuration is checked against the selected profile. A normal synced folder is therefore neither automatically accepted nor automatically rejected. It is accepted only when the artifact class permits it and the required profile controls are demonstrated.

No consumer cloud-drive configuration qualifies as `high_assurance_vault` merely because the provider encrypts stored data.

### 5. Relationship to Stage 1B

ADR 0014 remains the authoritative **high-assurance** custody design. This ADR narrows when that full boundary is required; it does not weaken its controls for artifacts classified into `sensitive_custody`.

Stage 1B operational mechanisms may still be reused for lower tiers, but lower-risk artifacts do not inherit every high-assurance control merely because they are real documents.

### 6. Relationship to the existing Stage 1C G4 binding

The prior G4 storage-location rule requiring one dedicated encrypted offline vault for every artifact is superseded by this risk-tiered decision once this ADR is accepted on `main`.

The G4 purpose allowlist remains unchanged:

- `quality_evaluation`
- `held_out_evaluation`

The following remain unauthorized in Stage 1C unless separately approved in the correct roadmap stage:

- model training;
- publication;
- demonstration;
- quality calibration;
- safety calibration;
- PDF-pipeline evaluation;
- synthetic derivation.

### 7. Migration and fail-closed rollout

This ADR changes architecture first. It does not itself activate artifact onboarding.

Until a follow-up implementation PR updates the Stage 1A/1C machine-readable schema, validators, examples, and negative tests to represent the new classes and profiles, the currently merged validators remain authoritative and no new artifact may be marked `external_available` under the new profile names.

The follow-up implementation must be additive and migration-safe. Existing high-assurance records remain valid. It must not silently reinterpret an old `custody_external` record as `managed_standard`.

### 8. Invariants retained

- ordinary Git remains metadata-only for real corpus artifact bytes;
- every artifact is digest-addressed and immutable once admitted;
- rights, privacy, dataset review, purpose, retention, and split gates remain independent;
- teacher approval does not imply dataset or training permission;
- held-out data is not used for tuning;
- unresolved rights or privacy never fall back to a weaker storage tier;
- model training remains unauthorized in Stage 1;
- Stage 2 remains blocked until the full Stage 1 exit gate is accepted.

## Consequences

### Positive

- public-domain/openly licensed evaluation corpora can be assembled without an unnecessary universal offline-vault requirement;
- high-assurance controls remain available where they are actually justified;
- managed cloud storage becomes architecturally possible for low-risk data without making any provider a trusted default;
- rights analysis becomes more accurate by distinguishing the composition from the exact edition/scan artifact.

### Costs

- the dataset schema and validators need a versioned follow-up change;
- each artifact still needs evidence-backed classification;
- provider configuration for managed storage still needs verification;
- the project must prevent tier downgrade when rights/privacy state changes or is revoked.

## Acceptance criteria for this architecture change

- the decision is documented before implementation;
- the universal offline-vault rule is explicitly superseded rather than silently ignored;
- C4 vault evidence is retained for `high_assurance_vault`;
- low-risk storage never bypasses exact-artifact rights review;
- no artifact bytes, provider credentials, real provider URLs, or account identifiers are added by the architecture PR;
- no Stage 2 or later-stage implementation is started.