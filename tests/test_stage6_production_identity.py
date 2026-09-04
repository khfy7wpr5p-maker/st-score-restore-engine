from __future__ import annotations

from datetime import UTC, datetime
import json
import unittest

from st_score_restore.job_api_types import JobApiConfig, JobApiError
from st_score_restore.production_http_auth import JobAuthorizationContext, ProductionApiV1
from st_score_restore.production_identity import (
    ProductionIdentityAdapter,
    ProductionIdentityPolicy,
    VerifiedTokenEvidence,
)


NOW = datetime(2026, 9, 4, 20, 30, tzinfo=UTC)
CLIENT_KEY = "local-client-key-0123456789abcdef"
REVIEWER_KEY = "local-reviewer-key-0123456789abcdef"


class FakeSignatureBackend:
    def __init__(self, evidence_by_token):
        self.evidence_by_token = evidence_by_token

    def verify(self, token: str) -> VerifiedTokenEvidence:
        try:
            return self.evidence_by_token[token]
        except KeyError as error:
            raise JobApiError("identity_verification_failed", "unknown token", http_status=401) from error


class FakeAuthorizationStore:
    def __init__(self):
        self.contexts: dict[str, JobAuthorizationContext] = {}
        self.fail_reads = False

    def bind_job(self, job_id: str, context: JobAuthorizationContext) -> None:
        current = self.contexts.get(job_id)
        if current is not None and current != context:
            raise JobApiError(
                "authorization_binding_conflict",
                "security binding conflict",
                http_status=403,
            )
        self.contexts[job_id] = context

    def get_job_context(self, job_id: str) -> JobAuthorizationContext | None:
        if self.fail_reads:
            raise RuntimeError("store unavailable")
        return self.contexts.get(job_id)


class FakeService:
    def __init__(self):
        self.created_actor = None
        self.created_count = 0

    def create_job(self, pages, *, idempotency_key, actor, restoration_config):
        self.created_actor = actor
        self.created_count += 1
        return {"jobId": "job_1", "state": "UPLOADED"}, self.created_count > 1

    def get_job(self, job_id: str):
        return {"jobId": job_id, "state": "UPLOADED"}


def evidence(
    *,
    subject: str,
    tenant: str,
    roles,
    issuer: str = "https://issuer.example",
    audience="st-score-restore",
    exp: float | None = None,
    nbf: float | None = None,
    jti: str = "token-1",
    signature_validated: bool = True,
    key_id: str = "kid-1",
    algorithm: str = "RS256",
):
    now = NOW.timestamp()
    return VerifiedTokenEvidence(
        claims={
            "iss": issuer,
            "aud": audience,
            "sub": subject,
            "tenant_id": tenant,
            "roles": roles,
            "exp": now + 600 if exp is None else exp,
            "nbf": now - 60 if nbf is None else nbf,
            "jti": jti,
        },
        key_id=key_id,
        algorithm=algorithm,
        signature_validated=signature_validated,
    )


def make_adapter(evidence_by_token, revoked=None):
    revoked = set(revoked or ())
    return ProductionIdentityAdapter(
        ProductionIdentityPolicy(
            trusted_issuers=("https://issuer.example",),
            trusted_audiences=("st-score-restore",),
            clock_skew_seconds=30,
        ),
        FakeSignatureBackend(evidence_by_token),
        lambda issuer, token_id: token_id in revoked,
        clock=lambda: NOW,
    )


class ProductionIdentityTests(unittest.TestCase):
    def test_verified_identity_derives_opaque_principal_and_tenant(self):
        adapter = make_adapter({"client": evidence(subject="person@example.com", tenant="school-a", roles=["client"])})
        identity = adapter.authenticate_bearer_token("client")
        self.assertEqual("client", identity.role)
        self.assertTrue(identity.production)
        self.assertTrue(identity.actor_id.startswith("subject:sha256:"))
        self.assertTrue(identity.tenant_key.startswith("tenant:sha256:"))
        self.assertNotIn("person@example.com", identity.actor_id)
        self.assertNotIn("school-a", identity.tenant_key)

    def test_role_conflict_is_denied(self):
        adapter = make_adapter({"conflict": evidence(subject="u1", tenant="t1", roles=["client", "reviewer"])})
        with self.assertRaises(JobApiError) as raised:
            adapter.authenticate_bearer_token("conflict")
        self.assertEqual("identity_role_conflict", raised.exception.code)
        self.assertEqual(403, raised.exception.http_status)

    def test_expired_revoked_and_unsigned_tokens_fail_closed(self):
        now = NOW.timestamp()
        adapter = make_adapter(
            {
                "expired": evidence(subject="u1", tenant="t1", roles=["client"], exp=now - 100),
                "revoked": evidence(subject="u1", tenant="t1", roles=["client"], jti="revoked-1"),
                "unsigned": evidence(subject="u1", tenant="t1", roles=["client"], signature_validated=False),
            },
            revoked={"revoked-1"},
        )
        expectations = {
            "expired": "identity_token_expired",
            "revoked": "identity_token_revoked",
            "unsigned": "identity_signature_not_validated",
        }
        for token, code in expectations.items():
            with self.subTest(token=token), self.assertRaises(JobApiError) as raised:
                adapter.authenticate_bearer_token(token)
            self.assertEqual(code, raised.exception.code)

    def test_wrong_issuer_audience_and_future_nbf_are_denied(self):
        now = NOW.timestamp()
        adapter = make_adapter(
            {
                "issuer": evidence(subject="u1", tenant="t1", roles=["client"], issuer="https://evil.example"),
                "aud": evidence(subject="u1", tenant="t1", roles=["client"], audience="other-service"),
                "nbf": evidence(subject="u1", tenant="t1", roles=["client"], nbf=now + 120),
            }
        )
        expectations = {
            "issuer": "identity_issuer_not_trusted",
            "aud": "identity_audience_mismatch",
            "nbf": "identity_token_not_yet_valid",
        }
        for token, code in expectations.items():
            with self.subTest(token=token), self.assertRaises(JobApiError) as raised:
                adapter.authenticate_bearer_token(token)
            self.assertEqual(code, raised.exception.code)


class ProductionApiAuthorizationTests(unittest.TestCase):
    def setUp(self):
        tokens = {
            "client-a": evidence(subject="client-a", tenant="school-a", roles=["client"], jti="c-a"),
            "client-b": evidence(subject="client-b", tenant="school-a", roles=["client"], jti="c-b"),
            "reviewer-a": evidence(subject="reviewer-a", tenant="school-a", roles=["reviewer"], jti="r-a"),
            "reviewer-b": evidence(subject="reviewer-b", tenant="school-b", roles=["reviewer"], jti="r-b"),
        }
        self.adapter = make_adapter(tokens)
        self.store = FakeAuthorizationStore()
        self.service = FakeService()
        self.api = ProductionApiV1(
            self.service,
            JobApiConfig(client_api_key=CLIENT_KEY, reviewer_api_key=REVIEWER_KEY),
            self.adapter,
            self.store,
        )

    def create_job(self, token="client-a"):
        return self.api.handle(
            "POST",
            "/api/v1/restoration-jobs",
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "image/png",
                "X-Filename": "page.png",
                "Idempotency-Key": "prod-0001",
            },
            b"synthetic-image-bytes",
        )

    def test_create_binds_opaque_owner_and_same_tenant_reviewer_can_read(self):
        created = self.create_job()
        self.assertEqual(202, created.status)
        context = self.store.contexts["job_1"]
        self.assertTrue(context.owner_key.startswith("subject:sha256:"))
        self.assertTrue(context.tenant_key.startswith("tenant:sha256:"))
        self.assertEqual(context.owner_key, self.service.created_actor)

        reviewer = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_1",
            {"Authorization": "Bearer reviewer-a"},
        )
        self.assertEqual(200, reviewer.status)

    def test_client_ownership_and_tenant_isolation_fail_closed(self):
        self.assertEqual(202, self.create_job().status)
        other_client = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_1",
            {"Authorization": "Bearer client-b"},
        )
        self.assertEqual(403, other_client.status)
        self.assertEqual("job_ownership_forbidden", json.loads(other_client.body)["error"]["code"])

        other_tenant = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_1",
            {"Authorization": "Bearer reviewer-b"},
        )
        self.assertEqual(403, other_tenant.status)
        self.assertEqual("tenant_access_forbidden", json.loads(other_tenant.body)["error"]["code"])

    def test_static_key_and_caller_actor_headers_are_rejected(self):
        static_key = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_1",
            {"Authorization": "Bearer client-a", "X-Api-Key": CLIENT_KEY},
        )
        self.assertEqual(401, static_key.status)
        self.assertEqual("production_static_credential_forbidden", json.loads(static_key.body)["error"]["code"])

        actor = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_1",
            {"Authorization": "Bearer client-a", "X-Actor-Id": "attacker-controlled"},
        )
        self.assertEqual(400, actor.status)
        self.assertEqual("caller_supplied_identity_forbidden", json.loads(actor.body)["error"]["code"])

    def test_missing_or_unavailable_authorization_state_is_denied(self):
        missing = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_404",
            {"Authorization": "Bearer client-a"},
        )
        self.assertEqual(403, missing.status)
        self.assertEqual("job_security_context_missing", json.loads(missing.body)["error"]["code"])

        self.store.fail_reads = True
        unavailable = self.api.handle(
            "GET",
            "/api/v1/restoration-jobs/job_1",
            {"Authorization": "Bearer client-a"},
        )
        self.assertEqual(503, unavailable.status)
        self.assertEqual("authorization_store_unavailable", json.loads(unavailable.body)["error"]["code"])

    def test_idempotent_replay_cannot_rebind_job_to_another_owner(self):
        self.assertEqual(202, self.create_job("client-a").status)
        replay = self.create_job("client-b")
        self.assertEqual(403, replay.status)
        self.assertEqual("authorization_binding_conflict", json.loads(replay.body)["error"]["code"])

    def test_health_remains_non_identity_liveness_probe(self):
        response = self.api.handle("GET", "/health", {})
        self.assertEqual(200, response.status)


if __name__ == "__main__":
    unittest.main()
