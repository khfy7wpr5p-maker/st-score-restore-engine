# Stage 6 S6-08 — Integration / Security Regression

## Status

Authorized on 2026-09-06 by explicit project-governance-owner approval.

This slice is provider-neutral and synthetic-only. It does not select a provider, create live resources, mutate production state, run production load/soak or penetration tests, perform production operational drills, deploy production, start Stage 7, change thresholds/resource limits, retune held-out evidence, train a model or publish a model.

## Purpose

S6-03 through S6-06 introduced separate provider-neutral production contracts for identity/authz, secrets/KMS/IAM, network security, storage/queue/recovery/audit and deployment. S6-07 added bounded synthetic operational recovery drills. S6-08 verifies that these contracts still agree when composed together and that cross-boundary bypass attempts fail closed.

The executable regression runner is:

`tools/run_stage6_s6_08_integration_security_regression.py`

The authorization validator is:

`tools/validate_stage6_s6_08_authorization.py`

Both are executed by Stage 6 governance CI on Python 3.11 and 3.12.

## Regression inventory

1. `trusted_edge_identity_iam_kms_storage_chain`
   - trusted managed-edge evidence is required;
   - signed identity produces opaque subject/tenant keys;
   - private topology rules permit only intended service paths;
   - exact least-privilege IAM grants authorize synthetic secret/KMS operations;
   - envelope context is tenant-bound;
   - production storage, queue, audit and deployment-candidate contracts agree;
   - deployment candidate validation does not authorize activation.

2. `legacy_identity_header_bypass_denied`
   - static API keys are rejected as production identity;
   - caller-supplied `X-Actor-Id` is rejected.

3. `cross_tenant_job_access_denied`
   - a valid signed identity from another tenant is rejected before local job access.

4. `identity_conflict_revocation_signature_denied`
   - conflicting application roles fail closed;
   - revoked tokens fail closed;
   - unvalidated signatures fail closed.

5. `cross_environment_secret_kms_denied`
   - production workload identity cannot read staging secrets;
   - production workload identity cannot use staging KMS resources.

6. `security_audit_dependency_fail_closed`
   - secret material is not released when security-audit persistence fails.

7. `edge_and_private_topology_bypass_denied`
   - untrusted proxy evidence is rejected;
   - the built-in standard-library server cannot be certified for public exposure;
   - quarantine outbound is denied;
   - public edge cannot bypass the application boundary to the metadata database.

8. `storage_queue_deployment_fail_closed`
   - stale fencing tokens are rejected;
   - production activation remains blocked without authorization;
   - storage-sensitive operations fail closed when audit evidence cannot be committed.

9. `s6_07_operational_regression_replay`
   - all accepted S6-07 deterministic synthetic operational drills are rerun and must still pass.

## Evidence boundary

The report intentionally contains only booleans, test names and privacy-safe assertion labels. Synthetic secret material, token contents and cryptographic payloads are never emitted in the report. No real score/corpus bytes or private raw metrics are used.

## What S6-08 does not certify

S6-08 is not provider-specific security certification. It does not establish production concurrency targets or failure budgets, does not perform distributed load/soak testing, does not perform an independent penetration test/security sign-off, and does not prove a live production deployment.

Provider remains `UNSELECTED` and production deployment remains unauthorized.

Next safe boundary: `separate_explicit_s6_09_final_exit_authorization`.
